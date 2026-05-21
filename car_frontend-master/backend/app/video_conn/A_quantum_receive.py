import base64
import configparser
import json
import os
import re
import socket
import time
import urllib.request
import uuid

from gmssl.sm4 import CryptSM4, SM4_DECRYPT


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(APP_DIR, 'config.ini')
HEX_64_RE = re.compile(r'^[0-9a-fA-F]{64}$')
HEX_32_RE = re.compile(r'^[0-9a-fA-F]{32}$')


cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH, encoding='utf-8')
cloud_ip = cfg.get('constants', 'cloud_ip')
to_ip = cfg.get('constants', 'to_ip')
edge_ip = cfg.get('constants', 'edge_ip')
cloud_key_api = cfg.get(
    'constants',
    'cloud_key_api',
    fallback=f'http://{cloud_ip}:8088/api/physical-keys',
).rstrip('/')

port_device = 8084
port_edge = 9000


def quantum_key_agree():
    print("********************** quantum session key agree (A) **********************")
    session_id = str(uuid.uuid4())
    notify_peer(session_id)

    response = request_session_key(session_id=session_id, self_id='car-a', peer_id='car-b')
    quantum_key = decrypt_gateway_response(response)
    write_catch_key(quantum_key)
    print(f"Device A got session key: session={session_id}, length={len(quantum_key)}")
    return quantum_key


def notify_peer(session_id):
    payload = {
        'type': 'session_key_agree',
        'session_id': session_id,
        'from': 'car-a',
        'to': 'car-b',
    }
    deadline = time.time() + 30
    last_error = None
    while time.time() < deadline:
        try:
            with socket.create_connection((to_ip, port_device), timeout=5) as sock:
                sock.sendall((json.dumps(payload) + '\n').encode('utf-8'))
                print(f"Device A sent session_id to B: {session_id}")
                return
        except OSError as exc:
            last_error = exc
            time.sleep(1)
    raise TimeoutError(f"Device A could not notify B about session_id: {last_error}")


def request_session_key(session_id, self_id, peer_id):
    payload = {
        'command': 'get_session_key',
        'session_id': session_id,
        'self_id': self_id,
        'peer_id': peer_id,
    }
    with socket.create_connection((edge_ip, port_edge), timeout=10) as sock:
        sock.sendall(json.dumps(payload).encode('utf-8'))
        raw = sock.recv(8192)
    if not raw:
        raise ValueError('edge gateway returned empty response')
    response = json.loads(raw.decode('utf-8').strip())
    if response.get('status') != 'ok':
        raise ValueError(f"edge gateway session key error: {response.get('error')}")
    return response


def decrypt_gateway_response(response):
    physical_key_id = response['physical_key_id']
    encrypted_key = base64.b64decode(response['encrypted_key_b64'])
    physical_key = fetch_physical_key(physical_key_id)
    try:
        return decrypt_quantum_key(encrypted_key, physical_key)
    except Exception as exc:
        print(f"Physical-key decrypt failed, trying legacy SecretKey fallback: {exc}")
        legacy_key = load_legacy_secret_key()
        return decrypt_quantum_key(encrypted_key, legacy_key)


def fetch_physical_key(physical_key_id):
    url = f'{cloud_key_api}/{physical_key_id}'
    with urllib.request.urlopen(url, timeout=10) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    if not payload.get('success'):
        raise ValueError(f"cloud physical key error: {payload}")
    key_value = payload['key']['key_value']
    if not HEX_32_RE.match(key_value):
        raise ValueError('cloud physical key must be 32 hex characters')
    return key_value


def decrypt_quantum_key(encrypted_key, physical_key):
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(sm4_key_bytes(physical_key), SM4_DECRYPT)
    plaintext = crypt_sm4.crypt_ecb(encrypted_key).decode('utf-8', errors='ignore')
    quantum_key = plaintext.rstrip('\0').strip()
    if not HEX_64_RE.match(quantum_key):
        raise ValueError(f'decrypted quantum key is invalid: length={len(quantum_key)}')
    return quantum_key.lower()


def sm4_key_bytes(key_value):
    key_value = key_value.strip()
    if HEX_32_RE.match(key_value):
        return bytes.fromhex(key_value)
    raw = key_value.encode('utf-8')
    return raw[:16].ljust(16, b'\0')


def load_legacy_secret_key():
    secret_key_path = os.path.join(os.path.dirname(__file__), 'SecretKey.txt')
    with open(secret_key_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def write_catch_key(quantum_key):
    paths = [
        os.path.join(APP_DIR, 'catch_q_key.txt'),
        os.path.join(os.path.dirname(__file__), 'catch_q_key.txt'),
    ]
    for path in paths:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(quantum_key)


if __name__ == '__main__':
    quantum_key_agree()
