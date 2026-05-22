import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime


HEX_32_RE = re.compile(r"^[0-9a-fA-F]{32}$")


class PhysicalKeyStore:
    """Physical-layer key pool for the cloud center."""

    def __init__(self, base_dir=None, key_file=None, db_path=None, interval_sec=5):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.key_file = key_file or os.path.join(self.base_dir, "Physical_Keys", "b.txt")
        self.db_path = db_path or os.path.join(self.base_dir, "server_data", "physical_keys.db")
        self.interval_sec = interval_sec
        self._stop_flag = False
        self._thread = None
        self._last_check_result = None
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
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
                CREATE TABLE IF NOT EXISTS physical_keys (
                    id TEXT PRIMARY KEY,
                    key_value TEXT NOT NULL,
                    key_hash TEXT,
                    status TEXT NOT NULL DEFAULT 'unused',
                    source_file TEXT,
                    session_id TEXT,
                    quantum_key_id TEXT,
                    distributed_to TEXT,
                    distributed_count INTEGER NOT NULL DEFAULT 0,
                    sync_status TEXT,
                    created_at TEXT NOT NULL,
                    distributed_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_physical_files (
                    file_path TEXT PRIMARY KEY,
                    size INTEGER,
                    mtime REAL,
                    imported_at TEXT NOT NULL,
                    imported_count INTEGER NOT NULL DEFAULT 0,
                    skipped_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS physical_key_distributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    physical_key_id TEXT,
                    requestor TEXT,
                    request_ip TEXT,
                    session_id TEXT,
                    quantum_key_id TEXT,
                    result TEXT NOT NULL,
                    message TEXT,
                    requested_at TEXT NOT NULL
                )
                """
            )
            self._ensure_columns(conn)

    def _ensure_columns(self, conn):
        table_columns = {
            "physical_keys": {
                "key_hash": "TEXT",
                "session_id": "TEXT",
                "quantum_key_id": "TEXT",
                "distributed_to": "TEXT",
                "distributed_count": "INTEGER NOT NULL DEFAULT 0",
                "sync_status": "TEXT",
                "updated_at": "TEXT",
            },
            "imported_physical_files": {
                "imported_count": "INTEGER NOT NULL DEFAULT 0",
                "skipped_count": "INTEGER NOT NULL DEFAULT 0",
                "error_count": "INTEGER NOT NULL DEFAULT 0",
                "last_error": "TEXT",
            },
        }
        for table, columns in table_columns.items():
            existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for column, column_type in columns.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        conn.execute("UPDATE physical_keys SET status = 'unused' WHERE status = 'available'")
        conn.execute(
            "UPDATE physical_keys SET key_hash = lower(hex(sha1_placeholder)) WHERE 1 = 0"
        )
        rows = conn.execute("SELECT id, key_value FROM physical_keys WHERE key_hash IS NULL OR key_hash = ''").fetchall()
        for row in rows:
            conn.execute(
                "UPDATE physical_keys SET key_hash = ? WHERE id = ?",
                (self.compute_hash(row["key_value"]), row["id"]),
            )

    @staticmethod
    def compute_hash(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag = False
        self.import_file(force=True)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[PhysicalKeyStore] Started watching: {self.key_file}")

    def stop(self):
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
        while not self._stop_flag:
            try:
                self.import_file()
            except Exception as exc:
                print(f"[PhysicalKeyStore] Import error: {exc}")
            time.sleep(self.interval_sec)

    def import_file(self, force=False):
        if not os.path.exists(self.key_file):
            self._record_import_status(0, 0, 1, "physical key file does not exist")
            return {"imported": 0, "skipped": 0, "errors": 1}

        stat = os.stat(self.key_file)
        abs_path = os.path.abspath(self.key_file)
        if not force:
            with self._connect() as conn:
                previous = conn.execute(
                    "SELECT size, mtime FROM imported_physical_files WHERE file_path = ?",
                    (abs_path,),
                ).fetchone()
                if previous and previous["size"] == stat.st_size and previous["mtime"] == stat.st_mtime:
                    return {"imported": 0, "skipped": 0, "errors": 0}

        imported = 0
        skipped = 0
        errors = 0
        last_error = None
        with open(self.key_file, "r", encoding="utf-8", errors="ignore") as fh:
            for line_no, raw_line in enumerate(fh, start=1):
                parsed = self._parse_line(raw_line)
                if not parsed:
                    if raw_line.strip() and not raw_line.strip().startswith("#"):
                        errors += 1
                        last_error = f"line {line_no}: expected physical_key_id,32hex"
                    continue
                key_id, key_value = parsed
                saved = self.save_key(key_id, key_value)
                if saved:
                    imported += 1
                else:
                    skipped += 1

        self._record_import_status(imported, skipped, errors, last_error, stat=stat)
        return {"imported": imported, "skipped": skipped, "errors": errors}

    def _record_import_status(self, imported, skipped, errors, last_error, stat=None):
        abs_path = os.path.abspath(self.key_file)
        size = stat.st_size if stat else 0
        mtime = stat.st_mtime if stat else 0
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO imported_physical_files(
                    file_path, size, mtime, imported_at, imported_count,
                    skipped_count, error_count, last_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    abs_path,
                    size,
                    mtime,
                    datetime.utcnow().isoformat(),
                    imported,
                    skipped,
                    errors,
                    last_error,
                ),
            )

    @staticmethod
    def _parse_line(raw_line):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return None
        if "," in line:
            key_id, key_value = [part.strip() for part in line.split(",", 1)]
        else:
            parts = line.split()
            if len(parts) != 2:
                return None
            key_id, key_value = parts
        if not key_id or not HEX_32_RE.match(key_value):
            return None
        return key_id, key_value.lower()

    def save_key(self, key_id, key_value):
        if not HEX_32_RE.match(key_value):
            raise ValueError("physical key must be 32 hex characters")
        with self._connect() as conn:
            existing = conn.execute("SELECT key_value FROM physical_keys WHERE id = ?", (key_id,)).fetchone()
            if existing:
                if existing["key_value"] != key_value.lower():
                    conn.execute(
                        "UPDATE physical_keys SET sync_status = 'conflict', updated_at = ? WHERE id = ?",
                        (datetime.utcnow().isoformat(), key_id),
                    )
                return False
            conn.execute(
                """
                INSERT INTO physical_keys(
                    id, key_value, key_hash, status, source_file, created_at, updated_at
                )
                VALUES (?, ?, ?, 'unused', ?, ?, ?)
                """,
                (
                    key_id,
                    key_value.lower(),
                    self.compute_hash(key_value.lower()),
                    os.path.abspath(self.key_file),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
        return True

    def get_key(self, key_id, requestor=None, request_ip=None, session_id=None, quantum_key_id=None):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM physical_keys WHERE id = ?
                """,
                (key_id,),
            ).fetchone()
            if not row:
                self.record_distribution(key_id, requestor, request_ip, session_id, quantum_key_id, "not_found", "physical key not found")
                return None

            now = datetime.utcnow().isoformat()
            distributed_to = self._merge_csv(row["distributed_to"], requestor)
            status = row["status"]
            if status in ("unused", "reserved"):
                status = "distributed"
            conn.execute(
                """
                UPDATE physical_keys
                SET status = ?, distributed_at = ?, distributed_to = ?,
                    distributed_count = COALESCE(distributed_count, 0) + 1,
                    session_id = COALESCE(session_id, ?),
                    quantum_key_id = COALESCE(quantum_key_id, ?),
                    updated_at = ?
                WHERE id = ?
                """,
                (status, now, distributed_to, session_id, quantum_key_id, now, key_id),
            )
            self.record_distribution(key_id, requestor, request_ip, session_id, quantum_key_id, "success", None, conn=conn)
        refreshed = self.get_key_record(key_id)
        refreshed["key_value"] = row["key_value"]
        return refreshed

    @staticmethod
    def _merge_csv(existing, value):
        if not value:
            return existing
        items = [item for item in (existing or "").split(",") if item]
        if value not in items:
            items.append(value)
        return ",".join(items)

    def record_distribution(self, key_id, requestor, request_ip, session_id, quantum_key_id, result, message=None, conn=None):
        close_conn = False
        if conn is None:
            conn = self._connect()
            close_conn = True
        conn.execute(
            """
            INSERT INTO physical_key_distributions(
                physical_key_id, requestor, request_ip, session_id,
                quantum_key_id, result, message, requested_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (key_id, requestor, request_ip, session_id, quantum_key_id, result, message, datetime.utcnow().isoformat()),
        )
        if close_conn:
            conn.commit()
            conn.close()

    def get_current_key(self):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM physical_keys ORDER BY created_at DESC LIMIT 1").fetchone()
        return self._row_to_dict(row, include_secret=True) if row else None

    def get_key_record(self, key_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM physical_keys WHERE id = ?", (key_id,)).fetchone()
        return self._row_to_dict(row, include_secret=False) if row else None

    def list_keys(self, status=None, limit=100):
        sql = "SELECT * FROM physical_keys"
        params = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_dict(row, include_secret=False) for row in rows]

    def list_distributions(self, limit=100):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM physical_key_distributions
                ORDER BY requested_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def session_bindings(self, limit=100):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    session_id,
                    quantum_key_id,
                    id AS physical_key_id,
                    distributed_to,
                    status,
                    distributed_at,
                    sync_status
                FROM physical_keys
                WHERE session_id IS NOT NULL OR quantum_key_id IS NOT NULL OR distributed_to IS NOT NULL
                ORDER BY COALESCE(distributed_at, created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def import_status(self):
        abs_path = os.path.abspath(self.key_file)
        file_exists = os.path.exists(self.key_file)
        stat = os.stat(self.key_file) if file_exists else None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM imported_physical_files WHERE file_path = ?",
                (abs_path,),
            ).fetchone()
        return {
            "running": self.is_running(),
            "file_path": abs_path,
            "file_exists": file_exists,
            "file_size": stat.st_size if stat else 0,
            "file_mtime": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None,
            "interval_sec": self.interval_sec,
            "last_import": dict(row) if row else None,
        }

    def stats(self):
        today = date.today().isoformat()
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM physical_keys GROUP BY status").fetchall()
            total = conn.execute("SELECT COUNT(*) FROM physical_keys").fetchone()[0]
            today_imported = conn.execute(
                "SELECT COALESCE(SUM(imported_count), 0) FROM imported_physical_files WHERE substr(imported_at, 1, 10) = ?",
                (today,),
            ).fetchone()[0]
            today_distributed = conn.execute(
                "SELECT COUNT(*) FROM physical_key_distributions WHERE result = 'success' AND substr(requested_at, 1, 10) = ?",
                (today,),
            ).fetchone()[0]
            bound_sessions = conn.execute(
                "SELECT COUNT(DISTINCT session_id) FROM physical_keys WHERE session_id IS NOT NULL AND session_id != ''"
            ).fetchone()[0]
            last_import = conn.execute(
                "SELECT imported_at FROM imported_physical_files ORDER BY imported_at DESC LIMIT 1"
            ).fetchone()
        by_status = {row["status"]: row["count"] for row in rows}
        return {
            "total": total,
            "unused": by_status.get("unused", 0),
            "reserved": by_status.get("reserved", 0),
            "distributed": by_status.get("distributed", 0),
            "used": by_status.get("used", 0),
            "expired": by_status.get("expired", 0),
            "conflict": by_status.get("conflict", 0),
            "by_status": by_status,
            "today_imported": today_imported,
            "today_distributed": today_distributed,
            "bound_sessions": bound_sessions,
            "last_import_at": last_import["imported_at"] if last_import else None,
            "last_consistency_check": self._last_check_result,
        }

    def check_gateway(self, gateway_base_url):
        gateway_base_url = (gateway_base_url or "").rstrip("/")
        if not gateway_base_url:
            raise ValueError("gateway_base_url is required")
        url = f"{gateway_base_url}/api/physical-keys?limit=10000"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ValueError(f"failed to reach gateway: {exc}") from exc

        gateway_items = payload.get("keys", [])
        gateway_by_id = {item.get("id"): item for item in gateway_items if item.get("id")}
        with self._connect() as conn:
            cloud_rows = conn.execute("SELECT * FROM physical_keys").fetchall()
            cloud_by_id = {row["id"]: row for row in cloud_rows}

            missing_on_gateway = []
            missing_on_cloud = []
            conflicts = []
            matched = []
            for key_id, row in cloud_by_id.items():
                gateway_item = gateway_by_id.get(key_id)
                if not gateway_item:
                    missing_on_gateway.append(key_id)
                    conn.execute("UPDATE physical_keys SET sync_status = 'missing_on_gateway', updated_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), key_id))
                    continue
                if gateway_item.get("key_hash") != row["key_hash"]:
                    conflicts.append(key_id)
                    conn.execute("UPDATE physical_keys SET sync_status = 'conflict', status = 'conflict', updated_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), key_id))
                else:
                    matched.append(key_id)
                    conn.execute("UPDATE physical_keys SET sync_status = 'matched', updated_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), key_id))

            for key_id in gateway_by_id:
                if key_id not in cloud_by_id:
                    missing_on_cloud.append(key_id)

        result = {
            "checked_at": datetime.utcnow().isoformat(),
            "gateway_url": gateway_base_url,
            "cloud_total": len(cloud_by_id),
            "gateway_total": len(gateway_by_id),
            "matched_count": len(matched),
            "missing_on_gateway": missing_on_gateway,
            "missing_on_cloud": missing_on_cloud,
            "conflicts": conflicts,
        }
        self._last_check_result = result
        return result

    @staticmethod
    def mask_key(value):
        if not value:
            return ""
        return f"{value[:6]}...{value[-6:]}"

    def _row_to_dict(self, row, include_secret=False):
        if not row:
            return None
        data = dict(row)
        data["physical_key_id"] = data["id"]
        data["masked_key_value"] = self.mask_key(data.get("key_value"))
        if not include_secret:
            data.pop("key_value", None)
        return data
