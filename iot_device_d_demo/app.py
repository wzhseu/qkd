import json
import socket
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request


DEVICE_ID = "car-d"
DEVICE_NAME = "IoT Device D"
DEFAULT_CLOUD_IP = "10.38.174.164"
DEFAULT_SOCKET_PORT = 8080
WEB_PORT = 5203


app = Flask(__name__)


class DemoDeviceClient:
    def __init__(self, device_id, device_name):
        self.device_id = device_id
        self.device_name = device_name
        self.sock = None
        self.connected = False
        self.cloud_ip = DEFAULT_CLOUD_IP
        self.socket_port = DEFAULT_SOCKET_PORT
        self.messages = []
        self.status = "未连接"
        self._lock = threading.RLock()
        self._receiver = None

    def connect(self, cloud_ip, socket_port):
        with self._lock:
            self.disconnect()
            self.cloud_ip = cloud_ip
            self.socket_port = int(socket_port)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.cloud_ip, self.socket_port))
            register = {
                "type": "register",
                "device_id": self.device_id,
                "name": self.device_name,
                "buffer_unpaired": False,
            }
            self.sock.sendall((json.dumps(register) + "\n").encode("utf-8"))
            self.connected = True
            self.status = "已接入服务器，等待配对"
            self._add_message("system", f"已接入服务器 {self.cloud_ip}:{self.socket_port}")
            self._receiver = threading.Thread(target=self._receive_loop, daemon=True)
            self._receiver.start()

    def disconnect(self):
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.connected = False
        self.status = "未连接"

    def send_message(self, text):
        if not self.connected or not self.sock:
            raise RuntimeError("设备尚未接入服务器")
        payload = {
            "from": self.device_id,
            "name": self.device_name,
            "time": datetime.now().isoformat(timespec="seconds"),
            "text": text,
        }
        raw = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.sock.sendall(raw)
        self._add_message("sent", text)

    def snapshot(self):
        with self._lock:
            return {
                "device_id": self.device_id,
                "device_name": self.device_name,
                "connected": self.connected,
                "cloud_ip": self.cloud_ip,
                "socket_port": self.socket_port,
                "status": self.status,
                "messages": list(self.messages),
            }

    def _receive_loop(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                for line in data.splitlines():
                    if not line:
                        continue
                    self._handle_incoming(line)
            except OSError:
                break
            except Exception as exc:
                self._add_message("system", f"接收异常: {exc}")
                break
        with self._lock:
            self.connected = False
            self.status = "连接已断开"

    def _handle_incoming(self, line):
        text = line.decode("utf-8", errors="ignore")
        try:
            payload = json.loads(text)
            label = payload.get("name") or payload.get("from") or "peer"
            text = f"{label}: {payload.get('text', '')}"
        except json.JSONDecodeError:
            pass
        self._add_message("received", text)

    def _add_message(self, kind, text):
        with self._lock:
            self.messages.append({
                "kind": kind,
                "text": text,
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            self.messages = self.messages[-100:]


client = DemoDeviceClient(DEVICE_ID, DEVICE_NAME)


PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ device_name }}</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #f4f7fb; color: #182230; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }
    header { background: #12324f; color: #fff; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; }
    h1 { margin: 0; font-size: 22px; }
    main { max-width: 1040px; margin: 0 auto; padding: 22px; }
    .panel { background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }
    .panel h2 { margin: 0; padding: 14px 16px; border-bottom: 1px solid #d8e0ea; font-size: 17px; }
    .body { padding: 16px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    input { height: 38px; border: 1px solid #cfd8e3; border-radius: 6px; padding: 0 10px; font: inherit; }
    input.wide { min-width: 360px; flex: 1; }
    button { height: 38px; border: 1px solid #1d6fdc; border-radius: 6px; background: #1d6fdc; color: #fff; padding: 0 14px; font-weight: 650; cursor: pointer; }
    button.secondary { background: #fff; color: #1d6fdc; }
    .status { display: inline-flex; align-items: center; height: 28px; padding: 0 10px; border-radius: 999px; background: #eef2f6; font-weight: 650; }
    .status.online { color: #0b8a5b; background: #e8f7f1; }
    .hint { color: #667085; margin-top: 10px; line-height: 1.6; }
    .messages { height: 360px; overflow: auto; background: #0f1f33; color: #dce8f6; border-radius: 8px; padding: 12px; }
    .msg { padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,.12); }
    .msg.sent { color: #b9dcff; }
    .msg.received { color: #c8f7dc; }
    .msg.system { color: #ffd89b; }
    .time { color: #8ea4bd; margin-right: 8px; }
  </style>
</head>
<body>
  <header>
    <h1>{{ device_name }}</h1>
    <div id="badge" class="status">未连接</div>
  </header>
  <main>
    <section class="panel">
      <h2>接入服务器</h2>
      <div class="body">
        <div class="row">
          <input id="cloudIp" value="{{ cloud_ip }}" placeholder="服务器 IP">
          <input id="socketPort" value="{{ socket_port }}" placeholder="端口">
          <button onclick="connectDevice()">接入</button>
          <button class="secondary" onclick="disconnectDevice()">断开</button>
        </div>
        <div class="hint">设备 ID：{{ device_id }}。未在服务器管理界面配对前，发送的消息会被服务器丢弃；配对后可与另一端正常互发。</div>
      </div>
    </section>

    <section class="panel">
      <h2>通信演示</h2>
      <div class="body">
        <div class="row">
          <input id="messageText" class="wide" placeholder="输入要发送给对端的普通消息">
          <button onclick="sendMessage()">发送消息</button>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>实时消息</h2>
      <div class="body">
        <div id="messages" class="messages"></div>
      </div>
    </section>
  </main>
  <script>
    async function api(path, options) {
      const res = await fetch(path, options || {});
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || res.statusText);
      return body;
    }
    async function connectDevice() {
      try {
        await api('/api/connect', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            cloud_ip: document.getElementById('cloudIp').value,
            socket_port: document.getElementById('socketPort').value
          })
        });
        refresh();
      } catch (err) { alert(err.message); }
    }
    async function disconnectDevice() {
      await api('/api/disconnect', {method: 'POST'});
      refresh();
    }
    async function sendMessage() {
      const input = document.getElementById('messageText');
      if (!input.value.trim()) return;
      try {
        await api('/api/send', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: input.value})
        });
        input.value = '';
        refresh();
      } catch (err) { alert(err.message); }
    }
    async function refresh() {
      const state = await api('/api/state');
      const badge = document.getElementById('badge');
      badge.textContent = state.status;
      badge.className = 'status' + (state.connected ? ' online' : '');
      const messages = document.getElementById('messages');
      messages.innerHTML = state.messages.map(m => `<div class="msg ${m.kind}"><span class="time">[${m.time}]</span>${escapeHtml(m.text)}</div>`).join('');
      messages.scrollTop = messages.scrollHeight;
    }
    function escapeHtml(text) {
      return String(text).replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
    }
    setInterval(refresh, 1000);
    refresh();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        PAGE,
        device_id=DEVICE_ID,
        device_name=DEVICE_NAME,
        cloud_ip=DEFAULT_CLOUD_IP,
        socket_port=DEFAULT_SOCKET_PORT,
    )


@app.route("/api/state")
def state():
    return jsonify(client.snapshot())


@app.route("/api/connect", methods=["POST"])
def connect():
    payload = request.get_json(silent=True) or {}
    cloud_ip = payload.get("cloud_ip") or DEFAULT_CLOUD_IP
    socket_port = payload.get("socket_port") or DEFAULT_SOCKET_PORT
    try:
        client.connect(cloud_ip, int(socket_port))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"success": True})


@app.route("/api/disconnect", methods=["POST"])
def disconnect():
    client.disconnect()
    return jsonify({"success": True})


@app.route("/api/send", methods=["POST"])
def send():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "消息不能为空"}), 400
    try:
        client.send_message(text)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)
