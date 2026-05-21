import os
import re
import sqlite3
import threading
import time
from datetime import datetime


HEX_32_RE = re.compile(r"^[0-9a-fA-F]{32}$")


class PhysicalKeyStore:
    """Small physical-key pool used by the cloud center.

    The cloud imports b.txt and lets cars fetch the exact physical key selected
    by the edge gateway through physical_key_id.
    """

    def __init__(self, base_dir=None, key_file=None, db_path=None, interval_sec=5):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.key_file = key_file or os.path.join(self.base_dir, "Physical_Keys", "b.txt")
        self.db_path = db_path or os.path.join(self.base_dir, "server_data", "physical_keys.db")
        self.interval_sec = interval_sec
        self._stop_flag = False
        self._thread = None
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS physical_keys (
                    id TEXT PRIMARY KEY,
                    key_value TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    source_file TEXT,
                    created_at TEXT NOT NULL,
                    distributed_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_physical_files (
                    file_path TEXT PRIMARY KEY,
                    size INTEGER,
                    mtime REAL,
                    imported_at TEXT NOT NULL
                )
                """
            )

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag = False
        self.import_file()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[PhysicalKeyStore] Started watching: {self.key_file}")

    def stop(self):
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self):
        while not self._stop_flag:
            try:
                self.import_file()
            except Exception as exc:
                print(f"[PhysicalKeyStore] Import error: {exc}")
            time.sleep(self.interval_sec)

    def import_file(self):
        if not os.path.exists(self.key_file):
            return 0
        stat = os.stat(self.key_file)
        with self._connect() as conn:
            previous = conn.execute(
                "SELECT size, mtime FROM imported_physical_files WHERE file_path = ?",
                (os.path.abspath(self.key_file),),
            ).fetchone()
            if previous and previous[0] == stat.st_size and previous[1] == stat.st_mtime:
                return 0

        imported = 0
        with open(self.key_file, "r", encoding="utf-8", errors="ignore") as fh:
            for raw_line in fh:
                parsed = self._parse_line(raw_line)
                if not parsed:
                    continue
                key_id, key_value = parsed
                if self.save_key(key_id, key_value):
                    imported += 1

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO imported_physical_files(file_path, size, mtime, imported_at)
                VALUES (?, ?, ?, ?)
                """,
                (os.path.abspath(self.key_file), stat.st_size, stat.st_mtime, datetime.utcnow().isoformat()),
            )
        return imported

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
            row = conn.execute("SELECT key_value FROM physical_keys WHERE id = ?", (key_id,)).fetchone()
            if row:
                return False
            conn.execute(
                """
                INSERT INTO physical_keys(id, key_value, status, source_file, created_at)
                VALUES (?, ?, 'available', ?, ?)
                """,
                (key_id, key_value.lower(), os.path.abspath(self.key_file), datetime.utcnow().isoformat()),
            )
        return True

    def get_key(self, key_id):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, key_value, status, source_file, created_at, distributed_at
                FROM physical_keys WHERE id = ?
                """,
                (key_id,),
            ).fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE physical_keys SET distributed_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), key_id),
            )
        return self._row_to_dict(row)

    def get_current_key(self):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, key_value, status, source_file, created_at, distributed_at
                FROM physical_keys
                ORDER BY created_at DESC LIMIT 1
                """
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def stats(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) FROM physical_keys GROUP BY status").fetchall()
            total = conn.execute("SELECT COUNT(*) FROM physical_keys").fetchone()[0]
        return {"total": total, "by_status": {status: count for status, count in rows}}

    @staticmethod
    def _row_to_dict(row):
        return {
            "physical_key_id": row[0],
            "key_value": row[1],
            "status": row[2],
            "source_file": row[3],
            "created_at": row[4],
            "distributed_at": row[5],
        }
