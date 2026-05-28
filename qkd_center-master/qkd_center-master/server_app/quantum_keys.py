import hashlib
import os
import re
import sqlite3
import threading
import time
from datetime import datetime


HEX_64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class CloudQuantumKeyStore:
    """Independent cloud-side quantum key pool."""

    def __init__(self, base_dir=None, key_file=None, db_path=None, interval_sec=5):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.key_file = key_file or os.path.join(self.base_dir, "QKD_Keys", "a.txt")
        self.db_path = db_path or os.path.join(self.base_dir, "server_data", "quantum_keys.db")
        self.interval_sec = interval_sec
        self._stop_flag = False
        self._thread = None
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
                CREATE TABLE IF NOT EXISTS quantum_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT NOT NULL,
                    key_hash TEXT UNIQUE,
                    status TEXT NOT NULL DEFAULT 'unused',
                    source_file TEXT,
                    session_id TEXT,
                    distributed_to TEXT,
                    distributed_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    reserved_at TEXT,
                    used_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_quantum_files (
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
        print(f"[CloudQuantumKeyStore] Started watching: {self.key_file}")

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
                print(f"[CloudQuantumKeyStore] Import error: {exc}")
            time.sleep(self.interval_sec)

    def import_file(self, force=False):
        if not os.path.exists(self.key_file):
            self._record_import_status(0, 0, 1, "quantum key file does not exist")
            return {"imported": 0, "skipped": 0, "errors": 1}

        stat = os.stat(self.key_file)
        abs_path = os.path.abspath(self.key_file)
        if not force:
            with self._connect() as conn:
                previous = conn.execute(
                    "SELECT size, mtime FROM imported_quantum_files WHERE file_path = ?",
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
                key_value = raw_line.strip().lower()
                if not key_value or key_value.startswith("#"):
                    continue
                if not HEX_64_RE.match(key_value):
                    errors += 1
                    last_error = f"line {line_no}: expected 64hex"
                    continue
                if self.save_key(key_value):
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
                INSERT OR REPLACE INTO imported_quantum_files(
                    file_path, size, mtime, imported_at, imported_count,
                    skipped_count, error_count, last_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (abs_path, size, mtime, datetime.utcnow().isoformat(), imported, skipped, errors, last_error),
            )

    def save_key(self, key_value):
        key_hash = self.compute_hash(key_value)
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM quantum_keys WHERE key_hash = ?", (key_hash,)).fetchone()
            if existing:
                return False
            conn.execute(
                """
                INSERT INTO quantum_keys(key_value, key_hash, status, source_file, created_at, updated_at)
                VALUES (?, ?, 'unused', ?, ?, ?)
                """,
                (
                    key_value,
                    key_hash,
                    os.path.abspath(self.key_file),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
        return True

    def reserve_key(self, session_id):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM quantum_keys WHERE status = 'unused' ORDER BY created_at ASC, id ASC LIMIT 1"
            ).fetchone()
            if not row:
                conn.rollback()
                raise ValueError("no unused quantum key available")
            conn.execute(
                """
                UPDATE quantum_keys
                SET status = 'reserved', session_id = ?, reserved_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (session_id, now, now, row["id"]),
            )
            conn.commit()
        return self.get_key(row["id"], include_secret=True)

    def release_key(self, key_id, session_id):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE quantum_keys
                SET status = 'unused', session_id = NULL, reserved_at = NULL, updated_at = ?
                WHERE id = ? AND session_id = ? AND status = 'reserved'
                """,
                (now, key_id, session_id),
            )

    def mark_distributed(self, key_id, requestor):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            row = conn.execute("SELECT distributed_to FROM quantum_keys WHERE id = ?", (key_id,)).fetchone()
            conn.execute(
                """
                UPDATE quantum_keys
                SET distributed_to = ?, distributed_count = COALESCE(distributed_count, 0) + 1, updated_at = ?
                WHERE id = ?
                """,
                (self._merge_csv(row["distributed_to"] if row else None, requestor), now, key_id),
            )

    def mark_used(self, key_id):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE quantum_keys
                SET status = 'used', used_at = COALESCE(used_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (now, now, key_id),
            )
        return self.get_key(key_id, include_secret=True)

    def get_key(self, key_id, include_secret=False):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM quantum_keys WHERE id = ?", (key_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["masked_key_value"] = self.mask_key(data.get("key_value"))
        if not include_secret:
            data.pop("key_value", None)
        return data

    def list_keys(self, status=None, limit=100, include_secret=False):
        sql = "SELECT * FROM quantum_keys"
        params = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data["masked_key_value"] = self.mask_key(data.get("key_value"))
            if not include_secret:
                data.pop("key_value", None)
            result.append(data)
        return result

    def import_status(self):
        abs_path = os.path.abspath(self.key_file)
        file_exists = os.path.exists(self.key_file)
        stat = os.stat(self.key_file) if file_exists else None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM imported_quantum_files WHERE file_path = ?",
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
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM quantum_keys GROUP BY status").fetchall()
            total = conn.execute("SELECT COUNT(*) FROM quantum_keys").fetchone()[0]
            last_import = conn.execute(
                "SELECT imported_at FROM imported_quantum_files ORDER BY imported_at DESC LIMIT 1"
            ).fetchone()
        by_status = {row["status"]: row["count"] for row in rows}
        return {
            "total": total,
            "unused": by_status.get("unused", 0),
            "reserved": by_status.get("reserved", 0),
            "used": by_status.get("used", 0),
            "by_status": by_status,
            "last_import_at": last_import["imported_at"] if last_import else None,
        }

    @staticmethod
    def _merge_csv(existing, value):
        items = [item for item in (existing or "").split(",") if item]
        if value and value not in items:
            items.append(value)
        return ",".join(items)

    @staticmethod
    def mask_key(value):
        if not value:
            return ""
        return f"{value[:8]}...{value[-8:]}"
