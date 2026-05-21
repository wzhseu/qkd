from socketserver import BaseRequestHandler, ThreadingTCPServer
import argparse
import signal
import threading
import time


DEFAULT_LISTENERS = [
    {
        "name": "device-log",
        "port": 8000,
        "file": "log.txt",
        "header": "---- qkd-device-log ----\n",
        "format": "multiline",
    },
    {
        "name": "catch-key-1",
        "port": 8001,
        "file": "log2.txt",
        "header": "---- qkd-catch-key-1 ----\n",
        "format": "inline",
    },
    {
        "name": "catch-key-2",
        "port": 8002,
        "file": "log3.txt",
        "header": "---- qkd-catch-key-2 ----\n",
        "format": "inline",
    },
]


class ReusableThreadingTCPServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def current_time_text():
    return time.strftime("%y-%m-%d-%H:%M:%S", time.localtime())


def decode_message(data):
    return data.decode("utf-8", errors="replace")


def build_log_entry(message, log_format):
    now = current_time_text()
    if log_format == "multiline":
        return f"{now}\n{message}\n"
    return f"{now} {message}\n"


def make_handler(listener):
    class LogHandler(BaseRequestHandler):
        def handle(self):
            address, _ = self.client_address
            print(f"[{listener['name']}] {address} connected")

            while True:
                data = self.request.recv(1024)
                if not data:
                    print(f"[{listener['name']}] {address} closed")
                    break

                message = decode_message(data)
                log = build_log_entry(message, listener["format"])
                print(f"[{listener['name']}] {log}", end="")
                with open(listener["file"], "a", encoding="utf-8") as log_file:
                    log_file.write(log)

                self.request.sendall(b"response")

    return LogHandler


def start_listener(host, listener):
    with open(listener["file"], "w", encoding="utf-8") as log_file:
        log_file.write(listener["header"])

    server = ReusableThreadingTCPServer((host, listener["port"]), make_handler(listener))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[{listener['name']}] listening on {host}:{listener['port']} -> {listener['file']}")
    return server


def parse_args():
    parser = argparse.ArgumentParser(description="Start all QKD log listener ports.")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Listening host, default: 0.0.0.0",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    servers = [start_listener(args.host, listener) for listener in DEFAULT_LISTENERS]
    stop_event = threading.Event()

    def request_stop(signum=None, frame=None):
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    print("All log listeners are running. Press Ctrl+C to stop.")
    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    finally:
        print("Stopping log listeners...")
        for server in servers:
            server.shutdown()
            server.server_close()
        print("Stopped.")


if __name__ == "__main__":
    main()
