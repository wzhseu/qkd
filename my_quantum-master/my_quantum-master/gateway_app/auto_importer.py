import threading
import time
import os
from gateway_app.db_ops import ingest_keys_from_dir


class AutoImporter:
    """自动监控目录并导入密钥文件"""
    
    def __init__(self, dir_path: str, source: str = 'auto-import',
                 per_line: bool = False, recursive: bool = True, interval_sec: int = 5,
                 patterns: list = None, app=None):
        self.dir_path = dir_path
        self.source = source
        self.per_line = per_line
        self.recursive = recursive
        self.interval_sec = interval_sec
        self.patterns = patterns
        # 可选的 Flask app，用于在后台线程中创建应用上下文
        self.app = app
        self._stop_flag = False
        self._thread = None

    def start(self):
        """启动自动导入线程"""
        if self._thread and self._thread.is_alive():
            print(f"[AutoImporter] Already running")
            return
        
        self._stop_flag = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[AutoImporter] Started watching: {self.dir_path}")

    def stop(self):
        """停止自动导入线程"""
        self._stop_flag = True
        if self._thread:
            self._thread.join(timeout=5)
        print(f"[AutoImporter] Stopped")

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
        """循环监控目录"""
        while not self._stop_flag:
            try:
                # 在有 Flask app 时确保在应用上下文中执行数据库操作
                if self.app:
                    with self.app.app_context():
                        summary = ingest_keys_from_dir(
                            self.dir_path,
                            source=self.source,
                            per_line=self.per_line,
                            recursive=self.recursive,
                            file_patterns=self.patterns,
                            skip_imported=True,
                        )
                else:
                    summary = ingest_keys_from_dir(
                        self.dir_path,
                        source=self.source,
                        per_line=self.per_line,
                        recursive=self.recursive,
                        file_patterns=self.patterns,
                        skip_imported=True,
                    )
                if summary.get('ingested', 0) > 0:
                    print(f"[AutoImporter] Imported {summary['ingested']} key(s) from {summary['files']} file(s)")
            except Exception as e:
                print(f"[AutoImporter] Error: {e}")
            
            time.sleep(self.interval_sec)
