"""
Background Automation & Directory Watcher (Optimized V2)
Performs ultra-efficient monitoring of source directories using NTFS mtime caching:
- Zero CPU usage when directories are idle (no redundant file iterations)
- Instant event triggers when new files are downloaded or created
- Delivers event callbacks and maintains status statistics for the Fluent UI
"""

import os
import threading
import time
from datetime import datetime
from organizer import scan_and_organize

class BackgroundWatcher:
    def __init__(self, config_getter, on_event_callback=None):
        self.config_getter = config_getter
        self.on_event_callback = on_event_callback
        self.running = False
        self.thread = None
        self._lock = threading.Lock()

        # MTime önbelleği (Klasörde değişiklik yoksa disk okumasını engeller)
        self._folder_mtimes = {}

        # Durum istatistikleri
        self.last_scan_time = None
        self.session_organized_count = 0

    def start(self):
        with self._lock:
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._run_loop, daemon=True)
                self.thread.start()

    def stop(self):
        with self._lock:
            self.running = False

    def trigger_now(self):
        """Kullanıcı 'Şimdi Tara' butonuna bastığında mtime kontrolünü atlayarak anında zorla tarar."""
        self._folder_mtimes.clear()
        threading.Thread(target=self._scan_once, daemon=True).start()

    def get_status_summary(self):
        """Alt durum barı için anlık verileri döner."""
        cfg = self.config_getter()
        sources = cfg.get('sources', [])
        last_str = self.last_scan_time.strftime('%H:%M:%S') if self.last_scan_time else 'Henüz taranmadı'
        return {
            'is_active': cfg.get('auto_watch', True),
            'monitored_count': len(sources),
            'last_scan': last_str,
            'session_count': self.session_organized_count
        }

    def _scan_once(self):
        cfg = self.config_getter()
        sources = cfg.get('sources', [])
        target = cfg.get('target', '')
        allow_new = cfg.get('allow_new_categories', True)
        desktop_baseline = set(cfg.get('desktop_baseline', []))

        self.last_scan_time = datetime.now()

        if not sources or not target:
            return

        # Sadece mtime değeri değişmiş klasörleri belirle
        changed_sources = []
        for folder in sources:
            if os.path.exists(folder):
                try:
                    cur_mtime = os.path.getmtime(folder)
                    if self._folder_mtimes.get(folder) != cur_mtime:
                        changed_sources.append(folder)
                        self._folder_mtimes[folder] = cur_mtime
                except Exception:
                    changed_sources.append(folder)

        if not changed_sources:
            return

        events = scan_and_organize(changed_sources, target, allow_new, desktop_baseline)
        if events:
            self.session_organized_count += len(events)
            if self.on_event_callback:
                self.on_event_callback(events)

    def _run_loop(self):
        while self.running:
            cfg = self.config_getter()
            if cfg.get('auto_watch', True):
                self._scan_once()
            
            interval = cfg.get('check_interval', 4)
            for _ in range(int(interval * 2)):
                if not self.running:
                    break
                time.sleep(0.5)
