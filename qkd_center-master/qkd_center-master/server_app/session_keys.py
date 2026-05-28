import os
import sqlite3
from datetime import datetime


class CloudSessionKeyCoordinator:
    """Coordinates cross-gateway A/B session keys without owning key pools."""

    def __init__(self, quantum_store, physical_store, base_dir=None, db_path=None):
        self.quantum_store = quantum_store
        self.physical_store = physical_store
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path or os.path.join(self.base_dir, "server_data", "cloud_key_sessions.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cloud_key_sessions (
                    session_id TEXT PRIMARY KEY,
                    party_a TEXT NOT NULL,
                    party_b TEXT NOT NULL,
                    gateway_a TEXT,
                    gateway_b TEXT,
                    quantum_key_id INTEGER NOT NULL,
                    physical_key_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    claimed_a_at TEXT,
                    claimed_b_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    used_at TEXT
                )
                """
            )

    def claim(self, session_id, self_id, peer_id, gateway_id=None, request_ip=None):
        session_id = (session_id or "").strip()
        self_id = (self_id or "").strip()
        peer_id = (peer_id or "").strip()
        gateway_id = (gateway_id or request_ip or "unknown-gateway").strip()
        if not session_id or not self_id or not peer_id:
            raise ValueError("session_id, self_id, and peer_id are required")
        if self_id == peer_id:
            raise ValueError("self_id and peer_id must be different")

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                session = conn.execute(
                    "SELECT * FROM cloud_key_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                created = False
                if not session:
                    quantum_key = self.quantum_store.reserve_key(session_id)
                    try:
                        physical_key = self.physical_store.reserve_key(session_id, quantum_key["id"])
                    except Exception:
                        self.quantum_store.release_key(quantum_key["id"], session_id)
                        raise

                    now = datetime.utcnow().isoformat()
                    conn.execute(
                        """
                        INSERT INTO cloud_key_sessions(
                            session_id, party_a, party_b, gateway_a, quantum_key_id,
                            physical_key_id, status, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                        """,
                        (session_id, self_id, peer_id, gateway_id, quantum_key["id"], physical_key["id"], now, now),
                    )
                    session = conn.execute(
                        "SELECT * FROM cloud_key_sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    created = True

                side = self._claim_side(session, self_id, peer_id)
                first_claim = not session[f"claimed_{side}_at"]
                other_side = "b" if side == "a" else "a"
                will_be_used = bool(session[f"claimed_{other_side}_at"])
                now = datetime.utcnow().isoformat()

                assignments = [
                    f"gateway_{side} = ?",
                    f"claimed_{side}_at = COALESCE(claimed_{side}_at, ?)",
                    "updated_at = ?",
                ]
                params = [gateway_id, now, now]
                if will_be_used:
                    assignments.extend(["status = 'used'", "used_at = COALESCE(used_at, ?)"])
                    params.append(now)
                params.append(session_id)
                conn.execute(
                    f"UPDATE cloud_key_sessions SET {', '.join(assignments)} WHERE session_id = ?",
                    params,
                )
                session = conn.execute("SELECT * FROM cloud_key_sessions WHERE session_id = ?", (session_id,)).fetchone()
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        if first_claim:
            self.quantum_store.mark_distributed(session["quantum_key_id"], self_id)
            self.physical_store.record_claim_distribution(
                session["physical_key_id"],
                requestor=self_id,
                request_ip=request_ip,
                session_id=session_id,
                quantum_key_id=session["quantum_key_id"],
                gateway_id=gateway_id,
            )
        if will_be_used:
            self.quantum_store.mark_used(session["quantum_key_id"])
            self.physical_store.mark_used(session["physical_key_id"])

        quantum_key = self.quantum_store.get_key(session["quantum_key_id"], include_secret=True)
        physical_key = self.physical_store.get_key_record(session["physical_key_id"], include_secret=True)
        return self._response(session, quantum_key, physical_key, self_id, peer_id, gateway_id, created)

    def _claim_side(self, session, self_id, peer_id):
        if self_id == session["party_a"] and peer_id == session["party_b"]:
            return "a"
        if self_id == session["party_b"] and peer_id == session["party_a"]:
            return "b"
        raise ValueError("session_id is already bound to different parties")

    def _response(self, session, quantum_key, physical_key, self_id, peer_id, gateway_id, created):
        return {
            "session_id": session["session_id"],
            "party_a": session["party_a"],
            "party_b": session["party_b"],
            "gateway_a": session["gateway_a"],
            "gateway_b": session["gateway_b"],
            "self_id": self_id,
            "peer_id": peer_id,
            "gateway_id": gateway_id,
            "quantum_key_id": session["quantum_key_id"],
            "quantum_key_value": quantum_key["key_value"],
            "quantum_key_hash": quantum_key["key_hash"],
            "physical_key_id": session["physical_key_id"],
            "physical_key_value": physical_key["key_value"],
            "physical_key_hash": physical_key["key_hash"],
            "status": session["status"],
            "claimed_a": bool(session["claimed_a_at"]),
            "claimed_b": bool(session["claimed_b_at"]),
            "claimed_a_at": session["claimed_a_at"],
            "claimed_b_at": session["claimed_b_at"],
            "created": created,
        }

    def list_bindings(self, limit=100):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    session_id, party_a, party_b, gateway_a, gateway_b,
                    quantum_key_id, physical_key_id, status,
                    claimed_a_at, claimed_b_at, created_at, used_at
                FROM cloud_key_sessions
                ORDER BY COALESCE(updated_at, created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM cloud_key_sessions GROUP BY status").fetchall()
            total = conn.execute("SELECT COUNT(*) FROM cloud_key_sessions").fetchone()[0]
        by_status = {row["status"]: row["count"] for row in rows}
        return {
            "total": total,
            "pending": by_status.get("pending", 0),
            "used": by_status.get("used", 0),
            "by_status": by_status,
        }
