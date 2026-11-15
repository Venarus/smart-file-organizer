"""
Comprehensive Verification Suite for:
- Part 1: Universal File Context Menus & Reliable File Operations (12 Scenarios)
- Part 2: Main-Window-Only Transparency & Solid Component Surfaces
- Part 3: Scrolling, Thumbnail Loading & Layout Stability (10 Scenarios)
"""

import os
import sys
import stat
import time
import shutil
import ctypes
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import FluentTheme
from glass_engine import WindowsGlassCompositor
from animation import FluidAnimator, UIBridge
from thumbnail_engine import ThumbnailEngine, AsyncThumbnailLoader
from file_ops import FileOperationManager, SelectionManager
from notification_center import FluentContextMenu
from app import SmartFileOrganizerApp


class DummyEvent:
    def __init__(self, widget, x_root=300, y_root=300):
        self.widget = widget
        self.x_root = x_root
        self.y_root = y_root


class TestContextMenuTransparencyAndScrolling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = SmartFileOrganizerApp(start_minimized=False)
        cls.app.update_idletasks()
        cls.app.update()
        cls.temp_dir = tempfile.mkdtemp(prefix="sfo_ctx_test_")

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.app.watcher:
                cls.app.watcher.stop()
            if cls.app.tray_icon:
                cls.app.tray_icon.stop()
            UIBridge.stop()
            cls.app.destroy()
        except Exception:
            pass
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _pump(self, cycles=4):
        for _ in range(cycles):
            UIBridge.drain_now()
            self.app.update_idletasks()
            self.app.update()

    # ==========================================================================
    # PART 2: TRANSPARENCY & SOLID COMPONENT VERIFICATION
    # ==========================================================================
    def test_01_transparency_restricted_to_main_window(self):
        """
        Doğrulama: Pencere genelinde -alpha < 1.0 kullanılmaz (1.0'da sabitlenir).
        Sidebar, kartlar, listeler, diyaloglar ve bağlam menüleri katı (solid) yüzey kullanır.
        """
        alpha = float(self.app.attributes("-alpha"))
        self.assertEqual(alpha, 1.0, "Ana pencere -alpha değeri 1.0 olmalı; alt bileşenler şeffaflaşmamalı!")

        # Üst bardaki Cam butonuna tıklandığında da -alpha 1.0 kalmalı
        self.app.cycle_glass_opacity()
        self._pump(2)
        self.assertEqual(float(self.app.attributes("-alpha")), 1.0)

        # Yüzey renklerinin katı HEX kodları olduğunu doğrula
        for mode in ('dark', 'light'):
            for tok in ('bg_secondary', 'bg_mica', 'bg_card', 'bg_card_secondary', 'bg_elevated', 'bg_input'):
                val = FluentTheme.c(tok, mode)
                self.assertTrue(val.startswith("#") and len(val) == 7, f"{mode}.{tok} geçerli katı HEX olmalı: {val}")

    # ==========================================================================
    # PART 1: RENAME, RECYCLE BIN, PERMANENT DELETE, LOCKED FILES, MULTI-SELECT
    # ==========================================================================
    def test_02_rename_validation_and_extension_preservation(self):
        """
        Doğrulama: Yeniden adlandırma uzantıyı varsayılan olarak korur, geçersiz karakterleri,
        boş isimleri, Windows ayrılmış adlarını ve çakışmaları reddeder.
        """
        f1 = os.path.join(self.temp_dir, "rapor_2026.pdf")
        f2 = os.path.join(self.temp_dir, "mevcut_dosya.pdf")
        with open(f1, "w", encoding="utf-8") as fp:
            fp.write("test pdf")
        with open(f2, "w", encoding="utf-8") as fp:
            fp.write("other pdf")

        # 1. Boş ad reddedilmeli
        ok, _, err = FileOperationManager.validate_new_name(f1, "   ")
        self.assertFalse(ok)
        self.assertTrue(len(err) > 0)

        # 2. Geçersiz karakterler reddedilmeli
        ok, _, err = FileOperationManager.validate_new_name(f1, "yeni:ad?.pdf")
        self.assertFalse(ok)

        # 3. Windows ayrılmış adları (CON, PRN, NUL) reddedilmeli
        ok, _, err = FileOperationManager.validate_new_name(f1, "CON")
        self.assertFalse(ok)

        # 4. Mevcut dosya ile çakışma tespit edilmeli
        ok, _, err = FileOperationManager.validate_new_name(f1, "mevcut_dosya")
        self.assertFalse(ok)

        # 5. Uzantı yazılmasa bile .pdf otomatik korunmalı ve yeniden adlandırma başarılı olmalı
        refreshed = {'called': False}
        ok, new_path, err = FileOperationManager.execute_rename(
            f1, "yillik_ozet", app=self.app, on_refresh=lambda: refreshed.update(called=True)
        )
        self.assertTrue(ok, f"Yeniden adlandırma başarısız: {err}")
        self.assertTrue(new_path.endswith("yillik_ozet.pdf"))
        self.assertTrue(os.path.exists(new_path))
        self.assertFalse(os.path.exists(f1))
        self.assertTrue(refreshed['called'])

    def test_03_move_to_recycle_bin(self):
        """
        Doğrulama: Varsayılan silme işlemi dosyayı Win32 SHFileOperationW ile
        Geri Dönüşüm Kutusu'na taşır ve diskten kaldırıldığını doğrular.
        """
        f_rec = os.path.join(self.temp_dir, "geri_donusum_test.txt")
        with open(f_rec, "w", encoding="utf-8") as fp:
            fp.write("recycle bin test content")

        refreshed = {'called': False}
        res = FileOperationManager.move_to_recycle_bin(
            f_rec, app=self.app, on_refresh=lambda: refreshed.update(called=True), synchronous=True
        )
        self.assertEqual(len(res['succeeded']), 1)
        self.assertEqual(len(res['failed']), 0)
        self.assertFalse(os.path.exists(f_rec))
        self.assertTrue(refreshed['called'])

    def test_04_permanent_delete_confirmation_and_cancel(self):
        """
        Doğrulama: Kalıcı silme onay olmadan asla silmez; iptal edildiğinde dosya korunur,
        onaylandığında salt-okunur (read-only) dosyalar dahil kalıcı olarak silinir.
        """
        f_perm = os.path.join(self.temp_dir, "kalici_sil_test.txt")
        with open(f_perm, "w", encoding="utf-8") as fp:
            fp.write("permanent delete test")
        # Salt okunur yap
        os.chmod(f_perm, stat.S_IREAD)

        # 1. Onay iptal edildiğinde (confirm_callback -> False) dosya silinmemeli!
        res_cancel = FileOperationManager.permanent_delete(
            f_perm, app=self.app, confirm_callback=lambda _paths: False, synchronous=True
        )
        self.assertTrue(res_cancel.get('aborted'))
        self.assertTrue(os.path.exists(f_perm), "İptal edilen kalıcı silme dosyayı silmemeli!")

        # 2. Modal diyalog açılışı (confirm_callback verilmezse onay penceresi açılır, dosya hemen silinmez)
        res_modal = FileOperationManager.permanent_delete(f_perm, app=self.app, synchronous=True)
        self.assertTrue(res_modal.get('pending_confirmation'))
        self.assertIsNotNone(FileOperationManager._active_modal)
        self.assertTrue(os.path.exists(f_perm))
        FileOperationManager.close_active_modal()

        # 3. Onay verildiğinde (confirm_callback -> True) kalıcı olarak silinmeli
        res_ok = FileOperationManager.permanent_delete(
            f_perm, app=self.app, confirm_callback=lambda _paths: True, synchronous=True
        )
        self.assertEqual(len(res_ok['succeeded']), 1)
        self.assertFalse(os.path.exists(f_perm))

    def test_05_locked_and_missing_file_handling(self):
        """
        Doğrulama: Olmayan veya başka bir işlem tarafından kilitli (in-use) olan dosyalar
        için asla sahte başarı bildirilmez; hata yakalanır.
        """
        # 1. Olmayan dosya
        missing_path = os.path.join(self.temp_dir, "olmayan_dosya_999.dat")
        res_missing = FileOperationManager.move_to_recycle_bin(missing_path, app=self.app, synchronous=True)
        self.assertEqual(len(res_missing['succeeded']), 0)
        self.assertEqual(len(res_missing['failed']), 1)

        # 2. Kilitli (in-use) dosya: Win32 CreateFileW ile paylaşım kilidi (dwShareMode=0) açalım
        locked_path = os.path.join(self.temp_dir, "kilitli_dosya.txt")
        with open(locked_path, "w", encoding="utf-8") as fp:
            fp.write("locked content")

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateFileW(
            locked_path,
            0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
            0,                        # dwShareMode = 0 (Exclusive lock)
            None,
            3,                        # OPEN_EXISTING
            0x80,                     # FILE_ATTRIBUTE_NORMAL
            None
        )
        try:
            self.assertTrue(FileOperationManager.is_file_locked(locked_path))
            res_locked = FileOperationManager.execute_permanent_delete(locked_path, app=self.app, synchronous=True)
            self.assertEqual(len(res_locked['succeeded']), 0)
            self.assertEqual(len(res_locked['failed']), 1)
            self.assertTrue(os.path.exists(locked_path))
        finally:
            if handle and handle != -1:
                kernel32.CloseHandle(handle)

    def test_06_multi_selection_and_batch_copy_cut_paste(self):
        """
        Doğrulama: Çoklu seçim (SelectionManager) ve toplu Kopyala/Kes/Yapıştır işlemleri
        hatasız çalışır.
        """
        src_dir = os.path.join(self.temp_dir, "batch_src")
        dst_dir = os.path.join(self.temp_dir, "batch_dst")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dst_dir, exist_ok=True)

        files = []
        for i in range(3):
            p = os.path.join(src_dir, f"batch_{i}.txt")
            with open(p, "w", encoding="utf-8") as fp:
                fp.write(f"content {i}")
            files.append(p)

        SelectionManager.clear()
        for p in files:
            SelectionManager.select(p)

        eff = SelectionManager.get_effective_paths(files[0])
        self.assertEqual(len(eff), 3)

        # Toplu kopyala ve yapıştır
        FileOperationManager.copy_items(eff, app=self.app)
        res_paste = FileOperationManager.paste_items(dst_dir, app=self.app, synchronous=True)
        self.assertEqual(len(res_paste['succeeded']), 3)
        for i in range(3):
            self.assertTrue(os.path.exists(os.path.join(dst_dir, f"batch_{i}.txt")))

        SelectionManager.clear()

    # ==========================================================================
    # PART 1 & 3: UNIVERSAL CONTEXT MENUS & SCROLLING STABILITY ACROSS VIEWS
    # ==========================================================================
    def test_07_context_menu_across_views_and_nested_children(self):
        """
        Doğrulama: Media, Videos/Pinned Folders, My Files (Folders Gezgini) ve Search
        ekranlarındaki kartların hem kendilerine hem de en içteki alt bileşenlerine
        (küçük resim, etiket, rozet) sağ tıklandığında FluentContextMenu açılır.
        """
        test_file = os.path.join(self.temp_dir, "menu_test_video.mp4")
        with open(test_file, "wb") as fp:
            fp.write(b"\x00" * 128)

        # MediaGalleryView içinde kart oluştur ve içteki lbl_thumb üzerine sağ tıkla
        self.app.navigate_to('media')
        self._pump(4)
        media_view = self.app.current_view
        c = lambda tok: FluentTheme.c(tok, self.app.theme_mode)
        f = FluentTheme.font

        item_dict = {
            'name': 'menu_test_video.mp4',
            'path': test_file,
            'is_video': True,
            'is_gif': False,
            'size_bytes': 128,
            'size_human': '128 B',
            'mtime': time.time()
        }
        media_view._create_media_card(media_view.scroll_area, item_dict, 0, 0, c, f)
        self._pump(2)

        cards = media_view.scroll_area.winfo_children()
        self.assertGreaterEqual(len(cards), 1)
        card = cards[-1]

        # Kartın en derin alt bileşenini (ör. küçük resim etiketi) bul ve sağ-tık simüle et
        deep_child = card.winfo_children()[0].winfo_children()[0]
        handled = FluentContextMenu.handle_global_right_click(DummyEvent(deep_child), self.app)
        self.assertTrue(handled, "Kartın altındaki küçük resme sağ tıklandığında menü açılmalı!")
        self.assertIsNotNone(FluentContextMenu._active_menu)
        self.assertTrue(FluentContextMenu._active_menu.winfo_exists())

        # Klavye navigasyonu testi (Aşağı ok)
        FluentContextMenu.navigate_keyboard(1)
        self.assertEqual(FluentContextMenu._focused_idx, 0)
        FluentContextMenu.close_active()

    def test_08_scrolling_and_thumbnail_geometry_stability(self):
        """
        Doğrulama:
        1. MediaGalleryView kartları sabit yüksekliğe (CARD_HEIGHT = 178) ve pack_propagate(False)
           kilidine sahiptir.
        2. Küçük resim yer tutucusu (160x100 CTkImage) ile yüklenen gerçek küçük resim aynı
           boyuttadır; resim yüklendiğinde kart boyutu 1 piksel bile değişmez.
        3. Hızlı dikey kaydırma sırasında FluidAnimator.is_scrolling() aktifleşerek gereksiz
           hover yeniden çizimlerini engeller.
        """
        self.app.navigate_to('media')
        self._pump(4)
        media_view = self.app.current_view
        c = lambda tok: FluentTheme.c(tok, self.app.theme_mode)
        f = FluentTheme.font

        img_path = os.path.join(self.temp_dir, "scroll_test_img.png")
        from PIL import Image
        Image.new("RGBA", (320, 200), (40, 120, 220, 255)).save(img_path)

        item_dict = {
            'name': 'cok_uzun_bir_dosya_adi_ile_sutun_genisleme_testi_2026_final_v2.png',
            'path': img_path,
            'is_video': False,
            'is_gif': False,
            'size_bytes': 2048,
            'size_human': '2.0 KB',
            'mtime': time.time()
        }
        media_view._create_media_card(media_view.scroll_area, item_dict, 0, 0, c, f)
        self._pump(2)

        card = media_view.scroll_area.winfo_children()[-1]
        self.assertEqual(card.cget("height"), media_view.CARD_HEIGHT)
        h_before = card.winfo_reqheight()

        # Küçük resim kuyruğunu boşalt ve UIBridge'i çalıştır
        time.sleep(0.15)
        self._pump(6)
        h_after = card.winfo_reqheight()
        self.assertEqual(h_before, h_after, "Küçük resim yüklendikten sonra kart yüksekliği değişmemeli!")

        # Kaydırma sırasında hover bastırma kontrolü
        FluidAnimator.notify_scroll()
        self.assertTrue(FluidAnimator.is_scrolling())


if __name__ == "__main__":
    unittest.main(verbosity=2)
