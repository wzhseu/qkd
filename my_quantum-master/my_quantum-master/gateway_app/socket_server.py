#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Socket server for car key requests.

Supported commands:
- legacy plain text: get_key
- JSON: {"command": "get_session_key", "session_id": "...", "self_id": "car-a", "peer_id": "car-b"}
"""

import base64
import configparser
import json
import os
import re
import socket
import sys
import threading
import time
import traceback

from gmssl.sm4 import CryptSM4, SM4_ENCRYPT


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HEX_32_RE = re.compile(r"^[0-9a-fA-F]{32}$")


class KeySocketServer:
    def __init__(self, host='0.0.0.0', port=9000, app=None, sm4_key=None):
        self.host = host
        self.port = port
        self.app = app
        self.sm4_key = sm4_key
        self.server_socket = None
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            print(f"[SocketServer] Already running on {self.host}:{self.port}")
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        self.server_socket.settimeout(1.0)

        self.running = True
        self._thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._thread.start()
        print(f"[SocketServer] Started on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[SocketServer] Stopped")

    def _serve_forever(self):
        while self.running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_addr),
                    daemon=True,
                )
                client_thread.start()
            except socket.timeout:
                continue
            except OSError as exc:
                if self.running:
                    print(f"[SocketServer] Accept error: {exc}")

    def _handle_client(self, client_socket, client_addr):
        client_ip = client_addr[0]
        try:
            client_socket.settimeout(30.0)
            data = client_socket.recv(4096)
            if not data:
                return

            command_text = data.decode('utf-8', errors='ignore').strip()
            print(f"[SocketServer] Received from {client_ip}: {command_text}")

            if command_text.startswith('{'):
                self._handle_json_command(client_socket, client_ip, command_text)
            elif command_text.lower() == 'get_key':
                self._handle_legacy_get_key(client_socket, client_ip)
            else:
                client_socket.sendall(b"INVALID_COMMAND")
        except socket.timeout:
            print(f"[SocketServer] Timeout from {client_ip}")
        except Exception as exc:
            print(f"[SocketServer] Error handling {client_ip}: {exc}")
            traceback.print_exc()
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    def _handle_json_command(self, client_socket, client_ip, command_text):
        try:
            payload = json.loads(command_text)
            command = payload.get('command')
            if command != 'get_session_key':
                self._send_json(client_socket, {'status': 'error', 'error': 'unsupported command'})
                return

            session_id = str(payload.get('session_id') or '').strip()
            self_id = str(payload.get('self_id') or '').strip()
            peer_id = str(payload.get('peer_id') or '').strip()
            response = self._get_session_key_response(session_id, self_id, peer_id, client_ip)
            self._send_json(client_socket, response)
        except Exception as exc:
            self._send_json(client_socket, {'status': 'error', 'error': str(exc)})

    def _send_json(self, client_socket, payload):
        client_socket.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode('utf-8'))

    def _handle_legacy_get_key(self, client_socket, client_ip):
        key_value = self._get_key_for_device(client_ip)
        if not key_value:
            client_socket.sendall(b"NO_KEY")
            print(f"[SocketServer] No key available for {client_ip}")
            return

        encrypted_key = self._encrypt_key_legacy(key_value)
        if encrypted_key:
            client_socket.sendall(encrypted_key)
            print(f"[SocketServer] Sent legacy encrypted key to {client_ip} (original length={len(key_value)})")
        else:
            client_socket.sendall(b"ENCRYPTION_ERROR")

    def _get_key_for_device(self, client_ip):
        try:
            if not self.app:
                print("[SocketServer] Warning: No Flask app context")
                return None
            with self.app.app_context():
                from gateway_app.db_ops import consume_latest_key, save_log
                key = consume_latest_key(request_ip=client_ip)
                if key:
                    save_log(f"Socket legacy: IP {client_ip} consumed key {key.id}", source='socket')
                    return key.key_value
                return None
        except Exception as exc:
            print(f"[SocketServer] DB error: {exc}")
            return None

    def _get_session_key_response(self, session_id, self_id, peer_id, client_ip):
        if not self.app:
            raise ValueError('gateway app context is not available')

        with self.app.app_context():
            from gateway_app.db_ops import get_or_create_session_key, save_log

            session = get_or_create_session_key(session_id, self_id, peer_id)
            quantum_key = session.quantum_key.key_value
            physical_key = session.physical_key.key_value
            encrypted = self._encrypt_with_physical_key(quantum_key, physical_key)
            save_log(
                f"Socket session key: {self_id} from {client_ip} got session={session_id}, "
                f"quantum_key={session.quantum_key_id}, physical_key={session.physical_key_id}",
                source='socket',
            )
            return {
                'status': 'ok',
                'session_id': session.session_id,
                'self_id': self_id,
                'peer_id': peer_id,
                'quantum_key_id': session.quantum_key_id,
                'physical_key_id': session.physical_key_id,
                'encrypted_key_b64': base64.b64encode(encrypted).decode('ascii'),
            }

    def _encrypt_with_physical_key(self, key_value, physical_key_hex):
        if not HEX_32_RE.match(physical_key_hex or ''):
            raise ValueError('physical key must be 32 hex characters')
        crypt_sm4 = CryptSM4()
        crypt_sm4.set_key(bytes.fromhex(physical_key_hex), SM4_ENCRYPT)
        return crypt_sm4.crypt_ecb(key_value.encode('utf-8'))

    def _encrypt_key_legacy(self, key_value):
        try:
            if not self.sm4_key:
                print("[SocketServer] Warning: No SM4 key configured, sending plaintext")
                return key_value.encode('utf-8')

            crypt_sm4 = CryptSM4()
            crypt_sm4.set_key(self._legacy_sm4_key_bytes(), SM4_ENCRYPT)
            return crypt_sm4.crypt_ecb(key_value.encode('utf-8'))
        except Exception as exc:
            print(f"[SocketServer] Legacy encryption error: {exc}")
            traceback.print_exc()
            return None

    def _legacy_sm4_key_bytes(self):
        value = (self.sm4_key or '').strip()
        if HEX_32_RE.match(value):
            return bytes.fromhex(value)
        raw = value.encode('utf-8')
        return raw[:16].ljust(16, b'\0')


if __name__ == '__main__':
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, 'config.ini')
    cfg.read(config_path, encoding='utf-8')

    port = 9000
    sm4_key = None
    if cfg.has_section('socket_server'):
        port = cfg.getint('socket_server', 'port', fallback=9000)
        sm4_key = cfg.get('socket_server', 'sm4_secret_key', fallback=None)

    from gateway_app import create_app

    app = create_app()
    server = KeySocketServer(port=port, app=app, sm4_key=sm4_key)
    print("=" * 60)
    print("QKD edge gateway socket server")
    print(f"Listening port: {port}")
    print("=" * 60)
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        server.stop()
