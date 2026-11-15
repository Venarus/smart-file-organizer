"""
Smart File Organizer v2.1.0 — Repeatable Navigation & UI Performance Test Suite
Verifies:
1. Initial launch and all 18 page cold initializations complete smoothly
2. Cached page switching (< 100 ms target; < 50 ms interaction response) across all 18 pages
3. Rapid 54-switch stress loop without UI freezes, race conditions, or timer leaks
4. Navigation responsiveness while background scanning/analysis workers are running
5. Memory stability (< 250 KB delta across 54 switches) and singleton CTkFont cache efficiency
6. Differential on_page_show() lifecycle (zero widget recreation when data is unchanged)
"""

import os
import sys
import gc
import time
import unittest
import tracemalloc
import statistics

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import SmartFileOrganizerApp
from theme import FluentTheme
from animation import FluidAnimator, UIBridge
from security_backup import SecurityBackupEngine

ALL_PAGES = [
    'home',
    'files',
    'media',
    'ai',
    'search',
    'smart_org',
    'automation',
    'duplicates',
    'storage',
    'activity',
    'security',
    'settings',
    'qf_desktop',
    'qf_downloads',
    'qf_documents',
    'qf_pictures',
    'qf_music',
    'qf_videos',
]


class TestNavigationPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tracemalloc.start()
        t0 = time.perf_counter()
        cls.app = SmartFileOrganizerApp(start_minimized=True)
        cls.app.update_idletasks()
        UIBridge.drain_now()
        cls.launch_ms = (time.perf_counter() - t0) * 1000.0

    @classmethod
    def tearDownClass(cls):
        tracemalloc.stop()
        try:
            FluidAnimator.cancel_all()
            UIBridge.stop()
            cls.app.watcher.stop()
            if cls.app._ipc_server:
                cls.app._ipc_server.close()
            if cls.app.tray_icon:
                cls.app.tray_icon.stop()
            cls.app.destroy()
        except Exception:
            pass

    def test_01_cold_navigation_all_18_pages(self):
        """Tüm 18 sayfaya ilk (soğuk) geçişlerin donma olmadan tamamlandığını doğrular."""
        cold_times = {}
        for pid in ALL_PAGES:
            t0 = time.perf_counter()
            self.app.navigate_to(pid)
            self.app.update_idletasks()
            UIBridge.drain_now()
            cold_times[pid] = (time.perf_counter() - t0) * 1000.0
            self.assertIn(pid, self.app._view_cache)
            self.assertTrue(self.app._view_cache[pid].winfo_exists())

        avg_cold = statistics.mean(cold_times.values())
        self.assertLess(avg_cold, 350.0, f"Ortalama soğuk sayfa açılışı çok yavaş: {avg_cold:.2f} ms")

    def test_02_cached_navigation_under_100ms_and_50ms_target(self):
        """Önbellekli sayfa geçişlerinin < 100 ms (ve etkileşim yanıtının < 50 ms) olduğunu doğrular."""
        time.sleep(0.15)
        UIBridge.drain_now()
        self.app.update_idletasks()

        cached_times = {}
        for pid in ALL_PAGES:
            t0 = time.perf_counter()
            self.app.navigate_to(pid)
            self.app.update_idletasks()
            UIBridge.drain_now()
            elapsed = (time.perf_counter() - t0) * 1000.0
            cached_times[pid] = elapsed
            self.assertLess(
                elapsed,
                100.0,
                f"'{pid}' önbellekli sayfa geçişi 100 ms sınırını aştı: {elapsed:.2f} ms"
            )

        avg_cached = statistics.mean(cached_times.values())
        self.assertLess(avg_cached, 50.0, f"Ortalama önbellekli geçiş 50 ms sınırını aştı: {avg_cached:.2f} ms")

    def test_03_differential_lifecycle_zero_widget_recreation(self):
        """Veri değişmediğinde on_page_show() çağrısının bileşenleri silip yeniden oluşturmadığını doğrular."""
        self.app.navigate_to('activity')
        self.app.update_idletasks()
        UIBridge.drain_now()
        act_view = self.app._view_cache['activity']
        children_before = [id(w) for w in act_view.scroll.winfo_children()]

        # Başka sayfaya geçip tekrar dön
        self.app.navigate_to('home')
        self.app.navigate_to('activity')
        self.app.update_idletasks()
        children_after = [id(w) for w in act_view.scroll.winfo_children()]

        self.assertEqual(
            children_before,
            children_after,
            "Veri değişmediği halde ActivityView alt bileşenleri yeniden oluşturuldu!"
        )

    def test_04_rapid_54_page_switching_and_memory_stability(self):
        """54 hızlı sayfa geçişinde gecikmenin < 50 ms ve bellek artışının < 250 KB olduğunu doğrular."""
        # İlk soğuk yüklemeden kalan tek seferlik arka plan önbellek görevlerinin tamamlanmasını bekle
        deadline = time.perf_counter() + 2.5
        while time.perf_counter() < deadline:
            UIBridge.drain_now()
            self.app.update_idletasks()
            media_v = self.app._view_cache.get('media')
            storage_v = self.app._view_cache.get('storage')
            if (not media_v or not getattr(media_v, '_is_loading', False)) and (
                not storage_v or not getattr(storage_v, '_is_loading', False)
            ):
                break
            time.sleep(0.05)

        # Bir ısınma turu çalıştır ve çöp toplayıcıyı (GC) temizle
        for pid in ALL_PAGES:
            self.app.navigate_to(pid)
        UIBridge.drain_now()
        self.app.update_idletasks()
        gc.collect()

        mem_before, _ = tracemalloc.get_traced_memory()
        switch_times = []

        for _ in range(3):
            for pid in ALL_PAGES:
                t0 = time.perf_counter()
                self.app.navigate_to(pid)
                self.app.update_idletasks()
                switch_times.append((time.perf_counter() - t0) * 1000.0)

        gc.collect()
        mem_after, _ = tracemalloc.get_traced_memory()
        delta_kb = (mem_after - mem_before) / 1024.0
        avg_ms = statistics.mean(switch_times)

        self.assertLess(avg_ms, 50.0, f"Hızlı geçiş ortalaması 50 ms sınırını aştı: {avg_ms:.2f} ms")
        self.assertLess(delta_kb, 250.0, f"54 sayfa geçişinde bellek sızıntısı tespit edildi: +{delta_kb:.1f} KB")
        self.assertGreater(len(FluentTheme._font_cache), 0)
        self.assertLess(len(FluentTheme._font_cache), 40)

    def test_05_navigation_during_background_operations(self):
        """Arka plan tarama iş parçacıkları çalışırken sayfa geçişlerinin < 50 ms kaldığını doğrular."""
        self.app.trigger_manual_scan()
        nav_latencies = []
        for pid in ['home', 'qf_desktop', 'files', 'storage', 'security', 'media', 'ai', 'settings']:
            t0 = time.perf_counter()
            self.app.navigate_to(pid)
            self.app.update_idletasks()
            nav_latencies.append((time.perf_counter() - t0) * 1000.0)

        avg_bg_nav = statistics.mean(nav_latencies)
        self.assertLess(avg_bg_nav, 50.0, f"Arka plan işlemi sırasında navigasyon gecikmesi: {avg_bg_nav:.2f} ms")

    def test_06_ledger_in_memory_cache_speed(self):
        """SecurityBackupEngine bellek içi önbelleğinin 1 ms altında yanıt verdiğini doğrular."""
        t0 = time.perf_counter()
        for _ in range(50):
            _ = SecurityBackupEngine.get_history(limit=50, active_only=True)
            _ = SecurityBackupEngine.get_revision()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(elapsed_ms, 15.0, f"50 ardışık ledger sorgusu çok yavaş: {elapsed_ms:.2f} ms")


if __name__ == "__main__":
    unittest.main(verbosity=2)
