import os

from flask import Flask, jsonify, request, send_from_directory

from server_app.hub import MultiDeviceHub
from server_app.physical_keys import PhysicalKeyStore
from server_app.quantum_keys import CloudQuantumKeyStore
from server_app.session_keys import CloudSessionKeyCoordinator


def create_app(hub):
    app = Flask(__name__, static_folder="frontend", static_url_path="")
    physical_keys = PhysicalKeyStore()
    physical_keys.start()
    quantum_keys = CloudQuantumKeyStore()
    quantum_keys.start()
    session_keys = CloudSessionKeyCoordinator(quantum_keys, physical_keys)

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

    def _request_ip():
        forwarded = request.headers.get("X-Forwarded-For", request.remote_addr)
        if forwarded and "," in forwarded:
            return forwarded.split(",", 1)[0].strip()
        return forwarded

    @app.route("/api/physical-keys/current")
    def current_physical_key():
        key = physical_keys.get_current_key()
        if not key:
            return jsonify({"error": "no physical key available"}), 404
        return jsonify({"success": True, "key": key})

    @app.route("/api/physical-keys")
    def physical_key_list():
        status = request.args.get("status")
        limit = min(request.args.get("limit", default=100, type=int), 1000)
        reveal = request.args.get("reveal", "0") == "1"
        keys = physical_keys.list_keys(status=status, limit=limit, include_secret=reveal)
        return jsonify({"count": len(keys), "keys": keys})

    @app.route("/api/physical-keys/<physical_key_id>")
    def physical_key(physical_key_id):
        key = physical_keys.get_key(
            physical_key_id,
            requestor=request.args.get("requestor") or request.args.get("device_id"),
            request_ip=_request_ip(),
            session_id=request.args.get("session_id"),
            quantum_key_id=request.args.get("quantum_key_id"),
        )
        if not key:
            return jsonify({"error": "physical key not found"}), 404
        return jsonify({"success": True, "key": key})

    @app.route("/api/physical-keys/stats")
    def physical_key_stats():
        return jsonify(physical_keys.stats())

    @app.route("/api/physical-keys/distributions")
    def physical_key_distributions():
        limit = min(request.args.get("limit", default=100, type=int), 1000)
        records = physical_keys.list_distributions(limit=limit)
        return jsonify({"count": len(records), "distributions": records})

    @app.route("/api/physical-keys/import-status")
    def physical_key_import_status():
        return jsonify(physical_keys.import_status())

    @app.route("/api/physical-keys/bindings")
    def physical_key_bindings():
        limit = min(request.args.get("limit", default=100, type=int), 1000)
        bindings = session_keys.list_bindings(limit=limit)
        return jsonify({"count": len(bindings), "bindings": bindings})

    @app.route("/api/physical-keys/rescan", methods=["POST"])
    def physical_key_rescan():
        result = physical_keys.import_file(force=True)
        return jsonify({"success": True, **result, "import_status": physical_keys.import_status()})

    @app.route("/api/physical-keys/check-gateway", methods=["POST"])
    def physical_key_check_gateway():
        payload = request.get_json(silent=True) or {}
        gateway_url = (
            payload.get("gateway_url")
            or request.args.get("gateway_url")
            or os.environ.get("QKD_GATEWAY_API")
            or "http://localhost:5002"
        )
        try:
            result = physical_keys.check_gateway(gateway_url)
        except ValueError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        return jsonify({"success": True, "result": result})

    @app.route("/api/quantum-keys/stats")
    def quantum_key_stats():
        return jsonify(quantum_keys.stats())

    @app.route("/api/quantum-keys")
    def quantum_key_list():
        status = request.args.get("status")
        limit = min(request.args.get("limit", default=100, type=int), 1000)
        reveal = request.args.get("reveal", "0") == "1"
        keys = quantum_keys.list_keys(status=status, limit=limit, include_secret=reveal)
        return jsonify({"count": len(keys), "keys": keys})

    @app.route("/api/quantum-keys/import-status")
    def quantum_key_import_status():
        return jsonify(quantum_keys.import_status())

    @app.route("/api/quantum-keys/rescan", methods=["POST"])
    def quantum_key_rescan():
        result = quantum_keys.import_file(force=True)
        return jsonify({"success": True, **result, "import_status": quantum_keys.import_status()})

    @app.route("/api/session-keys/stats")
    def session_key_stats():
        return jsonify(session_keys.stats())

    @app.route("/api/session-keys/claim", methods=["POST"])
    def session_key_claim():
        payload = request.get_json(silent=True) or {}
        try:
            result = session_keys.claim(
                session_id=payload.get("session_id"),
                self_id=payload.get("self_id"),
                peer_id=payload.get("peer_id"),
                gateway_id=payload.get("gateway_id"),
                request_ip=_request_ip(),
            )
        except ValueError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        return jsonify({"success": True, "session_key": result})

    app.config["PHYSICAL_KEY_STORE"] = physical_keys
    app.config["QUANTUM_KEY_STORE"] = quantum_keys
    app.config["SESSION_KEY_COORDINATOR"] = session_keys
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
        quantum_keys = app.config.get("QUANTUM_KEY_STORE")
        if quantum_keys:
            quantum_keys.stop()
        hub.stop()


if __name__ == "__main__":
    main()
