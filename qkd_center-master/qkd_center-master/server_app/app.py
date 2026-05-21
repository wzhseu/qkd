import os

from flask import Flask, jsonify, request, send_from_directory

from server_app.hub import MultiDeviceHub
from server_app.physical_keys import PhysicalKeyStore


def create_app(hub):
    app = Flask(__name__, static_folder="frontend", static_url_path="")
    physical_keys = PhysicalKeyStore()
    physical_keys.start()

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/devices")
    def devices():
        return jsonify(hub.list_devices())

    @app.route("/api/sessions", methods=["GET"])
    def sessions():
        return jsonify(hub.list_sessions())

    @app.route("/api/sessions", methods=["POST"])
    def create_session():
        payload = request.get_json(silent=True) or {}
        source = payload.get("source_device_id")
        target = payload.get("target_device_id")
        if not source or not target:
            return jsonify({"error": "source_device_id and target_device_id are required"}), 400
        try:
            session = hub.create_session(source, target)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"success": True, "session": session})

    @app.route("/api/sessions/<session_id>", methods=["DELETE"])
    def delete_session(session_id):
        try:
            session = hub.delete_session(session_id)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify({"success": True, "session": session})

    @app.route("/api/logs")
    def logs():
        limit = request.args.get("limit", default=200, type=int)
        return jsonify(hub.list_logs(limit=limit))

    @app.route("/api/physical-keys/current")
    def current_physical_key():
        key = physical_keys.get_current_key()
        if not key:
            return jsonify({"error": "no physical key available"}), 404
        return jsonify({"success": True, "key": key})

    @app.route("/api/physical-keys/<physical_key_id>")
    def physical_key(physical_key_id):
        key = physical_keys.get_key(physical_key_id)
        if not key:
            return jsonify({"error": "physical key not found"}), 404
        return jsonify({"success": True, "key": key})

    @app.route("/api/physical-keys/stats")
    def physical_key_stats():
        return jsonify(physical_keys.stats())

    app.config["PHYSICAL_KEY_STORE"] = physical_keys
    return app


def main():
    socket_host = os.environ.get("QKD_CENTER_SOCKET_HOST", "0.0.0.0")
    socket_port = int(os.environ.get("QKD_CENTER_SOCKET_PORT", "8080"))
    web_host = os.environ.get("QKD_CENTER_WEB_HOST", "0.0.0.0")
    web_port = int(os.environ.get("QKD_CENTER_WEB_PORT", "8088"))
    auto_pair = os.environ.get("QKD_CENTER_AUTO_PAIR_CAR_AB", "1") != "0"

    hub = MultiDeviceHub(host=socket_host, port=socket_port, auto_pair_car_ab=auto_pair)
    hub.start()

    app = create_app(hub)
    try:
        print("=" * 70)
        print("QKD cloud communication center")
        print(f"Device socket: {socket_host}:{socket_port}")
        print(f"Management UI: http://localhost:{web_port}")
        print("=" * 70)
        app.run(host=web_host, port=web_port, debug=False, use_reloader=False)
    finally:
        physical_keys = app.config.get("PHYSICAL_KEY_STORE")
        if physical_keys:
            physical_keys.stop()
        hub.stop()


if __name__ == "__main__":
    main()
