import json
import urllib.error
import urllib.request


def claim_cloud_session_key(cloud_base_url, gateway_id, session_id, self_id, peer_id, timeout=10):
    cloud_base_url = (cloud_base_url or "").rstrip("/")
    if not cloud_base_url:
        raise ValueError("cloud_base_url is required")
    payload = {
        "session_id": session_id,
        "self_id": self_id,
        "peer_id": peer_id,
        "gateway_id": gateway_id,
    }
    request = urllib.request.Request(
        f"{cloud_base_url}/api/session-keys/claim",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            data = json.loads(exc.read().decode("utf-8"))
        except Exception:
            data = {"error": str(exc)}
        raise ValueError(data.get("error") or f"cloud session claim failed: {exc}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"failed to reach cloud session coordinator: {exc}") from exc

    if not data.get("success"):
        raise ValueError(data.get("error") or "cloud session claim failed")
    return data["session_key"]
