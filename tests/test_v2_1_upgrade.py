"""
Comprehensive Automated Quality Assurance & Regression Test Suite for v2.1.0
Tests:
1. Centralized Animation Engine (Easing curves, duration scaling, color interpolation)
2. Thread-Safe UIBridge Queue Dispatching (Worker thread -> Main thread)
3. Accessibility & Reduced Motion Settings (Full, Reduced, Disabled, OS SPI check)
4. Notification Center (Unread badge count, mark read, clear)
5. Command Palette (Ctrl+K command registry, live search filtering, action callbacks)
6. Core AI File Intelligence, Safe File Organization, Desktop Baseline Protection, & 1-Click Undo
7. Path Portability Audit (Zero hardcoded user paths across codebase)
"""

import os
import sys
import tempfile
import threading
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import (
    APP_VERSION,
    DEFAULT_CONFIG,
    get_system_reduced_motion,
    get_effective_animation_mode
)
from theme import FluentTheme
from glass_engine import WindowsGlassCompositor, GlassArtEngine
from animation import Easing, FluidAnimator, UIBridge
from notification_center import NotificationCenter
from command_palette import CommandPalette
from organizer import organize_file, scan_and_organize
from security_backup import SecurityBackupEngine


class TestV21Upgrade(unittest.TestCase):

    def test_01_version_and_config_defaults(self):
        self.assertEqual(APP_VERSION, "2.1.0")
        self.assertIn('animation_mode', DEFAULT_CONFIG)
        self.assertIn('respect_system_motion', DEFAULT_CONFIG)
        self.assertIn('glass_opacity', DEFAULT_CONFIG)
        self.assertEqual(DEFAULT_CONFIG['animation_mode'], 'full')
        self.assertAlmostEqual(DEFAULT_CONFIG['glass_opacity'], 0.95, places=2)
        self.assertIsInstance(get_system_reduced_motion(), bool)

    def test_02_easing_curves(self):
        # Boundary conditions
        for fn in (Easing.linear, Easing.ease_out, Easing.ease_in, Easing.ease_in_out):
            self.assertAlmostEqual(fn(0.0), 0.0, places=5)
            self.assertAlmostEqual(fn(1.0), 1.0, places=5)
            self.assertAlmostEqual(fn(-0.5), 0.0, places=5)
            self.assertAlmostEqual(fn(1.5), 1.0, places=5)

        # Ease-out is faster at start (> 0.5 at t=0.5), ease-in is slower at start (< 0.5 at t=0.5)
        self.assertGreater(Easing.ease_out(0.5), 0.5)
        self.assertLess(Easing.ease_in(0.5), 0.5)
        self.assertAlmostEqual(Easing.ease_in_out(0.5), 0.5, places=5)

    def test_03_animation_modes_and_timing(self):
        FluidAnimator.set_animation_mode('full')
        self.assertEqual(FluidAnimator.get_duration(200), 200)

        FluidAnimator.set_animation_mode('reduced')
        reduced_dur = FluidAnimator.get_duration(200)
        self.assertTrue(40 <= reduced_dur < 200)

        FluidAnimator.set_animation_mode('disabled')
        self.assertEqual(FluidAnimator.get_duration(200), 0)

        # Restore default
        FluidAnimator.set_animation_mode(None)

        # Test config-based effective animation mode
        self.assertEqual(get_effective_animation_mode({'animation_mode': 'disabled'}), 'disabled')
        self.assertEqual(
            get_effective_animation_mode({'animation_mode': 'full', 'respect_system_motion': False}),
            'full'
        )

    def test_04_color_interpolation_and_tokens(self):
        self.assertEqual(FluentTheme.interpolate_color("#000000", "#FFFFFF", 0.0), "#000000")
        self.assertEqual(FluentTheme.interpolate_color("#000000", "#FFFFFF", 1.0), "#FFFFFF")
        mid = FluentTheme.interpolate_color("#000000", "#FFFFFF", 0.5)
        self.assertIn(mid, ("#7F7F7F", "#808080"))

        # Verify v2.1 tokens exist in both DARK and LIGHT palettes
        required_tokens = [
            'bg_primary', 'bg_mica', 'bg_secondary', 'bg_card', 'bg_elevated',
            'border', 'border_hover', 'border_focus', 'accent', 'accent_light',
            'accent_subtle', 'nav_indicator', 'skeleton_base', 'skeleton_highlight'
        ]
        for token in required_tokens:
            self.assertIn(token, FluentTheme.DARK)
            self.assertIn(token, FluentTheme.LIGHT)

    def test_05_ui_bridge_thread_safety(self):
        results = []

        def worker():
            for i in range(5):
                UIBridge.post(lambda val=i: results.append(val))

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        processed = UIBridge.drain_now()
        self.assertEqual(processed, 5)
        self.assertEqual(results, [0, 1, 2, 3, 4])

    def test_06_notification_center(self):
        NotificationCenter.clear()
        self.assertEqual(NotificationCenter.get_unread_count(), 0)

        NotificationCenter.add("Test Başlık 1", "Mesaj 1", level="success")
        NotificationCenter.add("Test Başlık 2", "Mesaj 2", level="warning")
        self.assertEqual(NotificationCenter.get_unread_count(), 2)

        NotificationCenter.mark_all_read()
        self.assertEqual(NotificationCenter.get_unread_count(), 0)
        self.assertEqual(len(NotificationCenter.get_all()), 2)

        NotificationCenter.clear()
        self.assertEqual(len(NotificationCenter.get_all()), 0)

    def test_07_command_palette_filtering(self):
        class DummyApp:
            theme_mode = 'dark'
            cfg = DEFAULT_CONFIG.copy()
            def navigate_to(self, pid): self.last_nav = pid
            def trigger_manual_scan(self): self.scanned = True
            def open_target_folder(self): pass
            def toggle_theme_quick(self): pass
            def update_status_footer(self): pass

        dummy = DummyApp()
        all_cmds = CommandPalette.get_all_commands(dummy)
        self.assertGreaterEqual(len(all_cmds), 20)

        # Filter for 'Kopya'
        filtered = CommandPalette.filter_commands(dummy, "Kopya")
        self.assertTrue(any(c['id'] == 'nav_duplicates' for c in filtered))

        # Filter for 'Masaüstü'
        filtered_dt = CommandPalette.filter_commands(dummy, "Masaüstü")
        self.assertTrue(any(c['id'] == 'pin_desktop' for c in filtered_dt))

        # Execute a command action
        nav_cmd = next(c for c in all_cmds if c['id'] == 'nav_storage')
        nav_cmd['action']()
        self.assertEqual(dummy.last_nav, 'storage')

    def test_08_file_organization_baseline_and_undo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "Desktop")
            tgt_dir = os.path.join(tmpdir, "Folders")
            os.makedirs(src_dir, exist_ok=True)
            os.makedirs(tgt_dir, exist_ok=True)

            protected_file = os.path.join(src_dir, "keep_on_desktop.lnk")
            new_file = os.path.join(src_dir, "fatura_2026_rapor.pdf")
            with open(protected_file, "w", encoding="utf-8") as f:
                f.write("shortcut")
            with open(new_file, "w", encoding="utf-8") as f:
                f.write("PDF invoice content")

            baseline = {"keep_on_desktop.lnk"}
            events = scan_and_organize([src_dir], tgt_dir, allow_new_categories=True, desktop_baseline=baseline)

            # Protected file must remain untouched on Desktop
            self.assertTrue(os.path.exists(protected_file))
            # New file must be organized into Folders
            self.assertFalse(os.path.exists(new_file))
            self.assertEqual(len(events), 1)
            moved_target = events[0]['target_path']
            self.assertTrue(os.path.exists(moved_target))

            # Undo transaction and verify file returns to original path
            tx_id = events[0].get('tx_id')
            if tx_id:
                undo_res = SecurityBackupEngine.undo_transaction(tx_id)
                self.assertTrue(undo_res.get('success'))
                self.assertTrue(os.path.exists(new_file))

    def test_09_zero_hardcoded_user_paths(self):
        forbidden = "C:\\Users\\senem"
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'build', 'dist', 'tests')]
            for fname in files:
                if fname.endswith(('.py', '.bat', '.vbs', '.spec')):
                    fpath = os.path.join(root, fname)
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    self.assertNotIn(
                        forbidden.lower(),
                        content.lower(),
                        f"Hardcoded user path found in {fpath}"
                    )

    def test_10_gui_navigation_caching_and_overlays(self):
        from app import SmartFileOrganizerApp
        app = SmartFileOrganizerApp(start_minimized=True)
        try:
            all_pages = [
                'home', 'files', 'media', 'ai', 'search', 'smart_org',
                'automation', 'duplicates', 'storage', 'activity',
                'security', 'settings',
                'qf_desktop', 'qf_downloads', 'qf_documents',
                'qf_pictures', 'qf_music', 'qf_videos'
            ]
            for pid in all_pages:
                app.navigate_to(pid)
                self.assertEqual(app.current_page_id, pid)
                self.assertIn(pid, app._view_cache)

            # Test Command Palette open & close
            CommandPalette.open(app, initial_query="Kopya")
            self.assertTrue(CommandPalette.is_open())
            CommandPalette.close()
            self.assertFalse(CommandPalette.is_open())

            # Test Notification Center Flyout toggle
            NotificationCenter.toggle_flyout(app)
            self.assertIsNotNone(NotificationCenter._active_flyout)
            NotificationCenter.close_flyout()
            self.assertIsNone(NotificationCenter._active_flyout)

            # Test Sidebar collapsible section toggle
            app._toggle_sidebar_section("sec_pinned", "SABİTLENEN KLASÖRLER 📌")
            self.assertTrue(app.section_collapsed.get("sec_pinned"))
            app._toggle_sidebar_section("sec_pinned", "SABİTLENEN KLASÖRLER 📌")
            self.assertFalse(app.section_collapsed.get("sec_pinned"))

            # Test Glass Engine & Live Glass Opacity Cycling
            orb = GlassArtEngine.get_glass_orb(38, "#38BDF8", "dark")
            self.assertIsNotNone(orb)
            banner = GlassArtEngine.get_hero_banner(600, 100, "dark")
            self.assertIsNotNone(banner)
            badge_txt, _, _, _ = FluentTheme.file_badge_style("rapor.pdf", "dark")
            self.assertEqual(badge_txt, "DOC")
            app.cycle_glass_opacity()
            self.assertIn(round(float(app.cfg.get('glass_opacity', 0.95)), 2), (0.88, 0.95, 1.00))
            app.set_glass_opacity(0.95)
        finally:
            FluidAnimator.cancel_all()
            UIBridge.stop()
            app.watcher.stop()
            if app._ipc_server:
                try:
                    app._ipc_server.close()
                except Exception:
                    pass
            if app.tray_icon:
                try:
                    app.tray_icon.stop()
                except Exception:
                    pass
            app.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
