import os
import threading
import time

from gateway_app.db_ops import ingest_physical_key_file


class PhysicalKeyImporter:
    """Watches b.txt and imports physical-layer keys into the gateway DB."""

    def __init__(self, file_path: str, source: str = 'physical-import',
                 interval_sec: int = 5, app=None):
        self.file_path = file_path
        self.source = source
        self.interval_sec = interval_sec
        self.app = app
        self._stop_flag = False
        self._thread = None
        self._last_size = None
        self._last_mtime = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
        self._stop_flag = False
        self._import_once()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[PhysicalKeyImporter] Started watching: {self.file_path}")

    def stop(self):
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
        while not self._stop_flag:
            try:
                self._import_once()
            except Exception as exc:
                print(f"[PhysicalKeyImporter] Error: {exc}")
            time.sleep(self.interval_sec)

    def _import_once(self):
        if not os.path.exists(self.file_path):
            return 0
        stat = os.stat(self.file_path)
        if self._last_size == stat.st_size and self._last_mtime == stat.st_mtime:
            return 0

        if self.app:
            with self.app.app_context():
                count = ingest_physical_key_file(self.file_path, source=self.source)
        else:
            count = ingest_physical_key_file(self.file_path, source=self.source)

        self._last_size = stat.st_size
        self._last_mtime = stat.st_mtime
        if count:
            print(f"[PhysicalKeyImporter] Imported {count} physical key(s)")
        return count
