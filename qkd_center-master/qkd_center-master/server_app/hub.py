import json
import socket
import threading
import time
import uuid
from collections import deque
from datetime import datetime


class DeviceConnection:
    # 初始化设备连接类，包含设备的基本信息和状态
    def __init__(self, sock, address, device_id, name, legacy=False, buffer_unpaired=True):
        self.sock = sock
        self.address = address
        self.device_id = device_id
        self.name = name
        self.legacy = legacy
        self.buffer_unpaired = buffer_unpaired
        self.connected_at = datetime.now()
        self.last_seen = self.connected_at
        self.current_peer = None
        self.session_id = None
        self.status = "online"
        self.bytes_forwarded = 0
        self.messages_forwarded = 0
        self.pending_payloads = deque(maxlen=20)
        self._send_lock = threading.Lock()

    # 发送数据到设备连接的socket
    def send(self, payload):
        with self._send_lock:
            self.sock.sendall(payload)

    # 将设备连接的信息转换为字典格式
    def to_dict(self):
        return {
            "device_id": self.device_id,
            "name": self.name,
            "ip": self.address[0],
            "port": self.address[1],
            "connected_at": self.connected_at.isoformat(timespec="seconds"),
            "last_seen": self.last_seen.isoformat(timespec="seconds"),
            "status": self.status,
            "current_peer": self.current_peer,
            "session_id": self.session_id,
            "legacy": self.legacy,
            "buffer_unpaired": self.buffer_unpaired,
            "bytes_forwarded": self.bytes_forwarded,
            "messages_forwarded": self.messages_forwarded,
        }


class MultiDeviceHub:
    # 初始化多设备中心类，包含设备列表、会话信息和日志记录
    def __init__(self, host="0.0.0.0", port=8080, auto_pair_car_ab=True):
        self.host = host
        self.port = port
        self.auto_pair_car_ab = auto_pair_car_ab
        self.devices = {}
        self.device_history = {}
        self.sessions = {}
        self.logs = deque(maxlen=500)
        self._lock = threading.RLock()
        self._server_socket = None
        self._thread = None
        self._running = False
        self._legacy_counter = 0

    # 启动服务器，开始监听客户端连接
    def start(self):
        if self._running:
            return
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(100)
        self._server_socket.settimeout(1.0)
        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        self._log("info", f"Communication socket listening on {self.host}:{self.port}")

    # 停止服务器，关闭所有连接
    def stop(self):
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        with self._lock:
            devices = list(self.devices.values())
        for device in devices:
            self._safe_close(device.sock)
        if self._thread:
            self._thread.join(timeout=2)

    # 列出所有设备及其状态信息
    def list_devices(self):
        with self._lock:
            devices = [record.copy() for record in self.device_history.values()]
            online = sum(1 for device in devices if device["status"] == "online")
            idle = sum(1 for device in devices if device["status"] == "online" and not device.get("current_peer"))
            return {
                "stats": {
                    "online": online,
                    "total_seen": len(devices),
                    "idle": idle,
                    "active_sessions": len(self.sessions),
                },
                "devices": sorted(devices, key=lambda item: (item["status"] != "online", item["device_id"])),
            }

    # 列出所有会话信息
    def list_sessions(self):
        with self._lock:
            return {
                "count": len(self.sessions),
                "sessions": [session.copy() for session in self.sessions.values()],
            }

    # 列出日志信息
    def list_logs(self, limit=200):
        with self._lock:
            items = list(self.logs)[-limit:]
        return {"count": len(items), "logs": items}

    # 创建会话，将两个设备配对
    def create_session(self, source_device_id, target_device_id, created_by="api"):
        with self._lock:
            if source_device_id == target_device_id:
                raise ValueError("source and target devices must be different")
            source = self.devices.get(source_device_id)
            target = self.devices.get(target_device_id)
            if not source or source.status != "online":
                raise ValueError(f"source device is not online: {source_device_id}")
            if not target or target.status != "online":
                raise ValueError(f"target device is not online: {target_device_id}")

            self._remove_sessions_for_devices_locked([source_device_id, target_device_id])

            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat(timespec="seconds")
            source.current_peer = target_device_id
            source.session_id = session_id
            target.current_peer = source_device_id
            target.session_id = session_id
            self.sessions[session_id] = {
                "session_id": session_id,
                "source_device_id": source_device_id,
                "target_device_id": target_device_id,
                "created_at": now,
                "created_by": created_by,
                "bytes_forwarded": 0,
                "messages_forwarded": 0,
            }
            created_session = self.sessions[session_id].copy()
            self._sync_history_locked(source)
            self._sync_history_locked(target)
            pending_pairs = [
                (source, target, list(source.pending_payloads)),
                (target, source, list(target.pending_payloads)),
            ]
            source.pending_payloads.clear()
            target.pending_payloads.clear()
        self._log("info", f"Session {session_id} created: {source_device_id} <-> {target_device_id}")
        for sender, receiver, payloads in pending_pairs:
            for payload in payloads:
                self._send_payload(sender, receiver, payload, session_id)
        with self._lock:
            return self.sessions.get(session_id, created_session).copy()

    # 删除指定的会话
    def delete_session(self, session_id, reason="api"):
        with self._lock:
            removed = self._remove_session_locked(session_id)
        if not removed:
            raise ValueError(f"session not found: {session_id}")
        self._log("info", f"Session {session_id} closed by {reason}")
        return removed

    # 循环接受客户端连接
    def _accept_loop(self):
        while self._running:
            try:
                client, address = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    self._log("error", "Socket accept failed")
                break
            threading.Thread(target=self._handle_client, args=(client, address), daemon=True).start()

    # 处理客户端连接
    def _handle_client(self, sock, address):
        device = None
        initial_payload = b""
        try:
            device_id, name, legacy, buffer_unpaired, initial_payload = self._read_registration(sock, address)
            device = DeviceConnection(
                sock,
                address,
                device_id,
                name,
                legacy=legacy,
                buffer_unpaired=buffer_unpaired,
            )
            self._register_device(device)
            self._maybe_auto_pair()

            if initial_payload:
                self._forward_or_drop(device, initial_payload)

            while self._running:
                payload = sock.recv(4096)
                if not payload:
                    break
                device.last_seen = datetime.now()
                self._forward_or_drop(device, payload)
        except ConnectionResetError:
            if device:
                self._log("warning", f"Connection reset by {device.device_id}")
        except Exception as exc:
            label = device.device_id if device else f"{address[0]}:{address[1]}"
            stale = False
            if device:
                with self._lock:
                    stale = self.devices.get(device.device_id) is not device
            if stale and isinstance(exc, OSError):
                self._log("info", f"Stale connection closed: {label}")
            else:
                self._log("error", f"Client handler error for {label}: {exc}")
        finally:
            if device:
                self._unregister_device(device)
            self._safe_close(sock)

    # 读取设备注册信息
    def _read_registration(self, sock, address):
        sock.settimeout(2.0)
        try:
            data = sock.recv(4096)
        except socket.timeout:
            data = b""
        finally:
            sock.settimeout(None)

        if data:
            register_payload = None
            remaining = b""
            if b"\n" in data:
                first_line, remaining = data.split(b"\n", 1)
                register_payload = first_line.strip()
            else:
                register_payload = data.strip()

            if register_payload.startswith(b"{"):
                try:
                    message = json.loads(register_payload.decode("utf-8"))
                    if message.get("type") == "register":
                        device_id = str(message.get("device_id") or "").strip()
                        name = str(message.get("name") or device_id).strip()
                        buffer_unpaired = bool(message.get("buffer_unpaired", True))
                        if not device_id:
                            raise ValueError("device_id is required")
                        return device_id, name or device_id, False, buffer_unpaired, remaining
                except Exception as exc:
                    self._log("warning", f"Invalid registration from {address[0]}:{address[1]}: {exc}")
            device_id, name, legacy = self._next_legacy_identity(address)
            return device_id, name, legacy, True, data

        device_id, name, legacy = self._next_legacy_identity(address)
        return device_id, name, legacy, True, b""

    # 为旧设备生成新的标识符
    def _next_legacy_identity(self, address):
        with self._lock:
            self._legacy_counter += 1
            number = self._legacy_counter
        device_id = f"legacy-{number}"
        return device_id, f"Legacy Device {number} ({address[0]})", True

    # 注册设备
    def _register_device(self, device):
        with self._lock:
            old_device = self.devices.get(device.device_id)
            if old_device:
                self._remove_sessions_for_devices_locked([device.device_id])
                self._safe_close(old_device.sock)
                old_device.status = "offline"
                self._sync_history_locked(old_device)
            self.devices[device.device_id] = device
            self._sync_history_locked(device)
        self._log("info", f"Device online: {device.device_id} ({device.name}) from {device.address[0]}")

    # 注销设备
    def _unregister_device(self, device):
        with self._lock:
            current = self.devices.get(device.device_id)
            if current is not device:
                return
            self.devices.pop(device.device_id, None)
            self._remove_sessions_for_devices_locked([device.device_id])
            device.status = "offline"
            device.current_peer = None
            device.session_id = None
            device.last_seen = datetime.now()
            self._sync_history_locked(device)
        self._log("info", f"Device offline: {device.device_id}")

    # 自动配对设备
    def _maybe_auto_pair(self):
        if not self.auto_pair_car_ab:
            return
        with self._lock:
            can_pair_cars = (
                "car-a" in self.devices
                and "car-b" in self.devices
                and not self.devices["car-a"].current_peer
                and not self.devices["car-b"].current_peer
            )
            legacy_ids = [
                device_id for device_id, device in self.devices.items()
                if device.legacy and not device.current_peer
            ]
        if can_pair_cars:
            try:
                self.create_session("car-a", "car-b", created_by="auto")
            except ValueError:
                pass
        elif len(legacy_ids) >= 2:
            try:
                self.create_session(legacy_ids[0], legacy_ids[1], created_by="auto-legacy")
            except ValueError:
                pass

    # 转发或丢弃数据包
    def _forward_or_drop(self, device, payload):
        peer_id = None
        session_id = None
        with self._lock:
            current = self.devices.get(device.device_id)
            if current:
                peer_id = current.current_peer
                session_id = current.session_id
                self._sync_history_locked(current)
            peer = self.devices.get(peer_id) if peer_id else None

        if not peer:
            if device.buffer_unpaired:
                with self._lock:
                    current = self.devices.get(device.device_id)
                    if current:
                        current.pending_payloads.append(payload)
                        self._sync_history_locked(current)
                self._log("warning", f"Buffered {len(payload)} byte(s) from unpaired device {device.device_id}")
            else:
                self._log("warning", f"Dropped {len(payload)} byte(s) from unpaired device {device.device_id}")
            return

        self._send_payload(device, peer, payload, session_id)

    def _send_payload(self, device, peer, payload, session_id):
        try:
            peer.send(payload)
            size = len(payload)
            with self._lock:
                device.bytes_forwarded += size
                device.messages_forwarded += 1
                peer.last_seen = datetime.now()
                self._sync_history_locked(device)
                self._sync_history_locked(peer)
                session = self.sessions.get(session_id)
                if session:
                    session["bytes_forwarded"] += size
                    session["messages_forwarded"] += 1
        except OSError as exc:
            self._log("error", f"Forward failed {device.device_id} -> {peer.device_id}: {exc}")
            with self._lock:
                if session_id:
                    self._remove_session_locked(session_id)

    # 移除与指定设备相关的会话
    def _remove_sessions_for_devices_locked(self, device_ids):
        target = set(device_ids)
        session_ids = [
            session_id for session_id, session in self.sessions.items()
            if session["source_device_id"] in target or session["target_device_id"] in target
        ]
        for session_id in session_ids:
            self._remove_session_locked(session_id)

    # 移除指定的会话
    def _remove_session_locked(self, session_id):
        session = self.sessions.pop(session_id, None)
        if not session:
            return None
        for device_id in (session["source_device_id"], session["target_device_id"]):
            device = self.devices.get(device_id)
            if device:
                device.current_peer = None
                device.session_id = None
                self._sync_history_locked(device)
        return session

    # 将设备状态同步到历史记录中
    def _sync_history_locked(self, device):
        self.device_history[device.device_id] = device.to_dict()

    # 记录日志
    def _log(self, level, message):
        event = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "message": message,
        }
        with self._lock:
            self.logs.append(event)
        print(f"[{event['time']}] [{level.upper()}] {message}")

    # 安全关闭socket连接
    @staticmethod
    def _safe_close(sock):
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
