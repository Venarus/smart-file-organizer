"""
Smart File Organizer V2 — Windows 11 Fluent Design & AI Intelligence System
Main Application Container, Fluent Navigation Sidebar, Global Search, and View Switcher.
"""

import os
import sys
import subprocess
from tkinter import filedialog, messagebox
import customtkinter as ctk
import windnd

from theme import FluentTheme
from config import load_config, save_config, set_windows_startup, PINNED_FOLDERS
from organizer import scan_and_organize, organize_item
from watcher import BackgroundWatcher
from tray import SystemTrayApp
from security_backup import SecurityBackupEngine
from search_engine import SearchEngine
from storage_analyzer import StorageAnalyzer
from thumbnail_engine import ThumbnailEngine

# Görünüm sayfaları
from views import (
    HomeView,
    MyFilesView,
    MediaGalleryView,
    AIIntelligenceView,
    SemanticSearchView,
    SmartOrgView,
    AutomationView,
    DuplicateView,
    StorageView,
    ActivityView,
    SecurityBackupView,
    SettingsView,
    QuickFolderView
)
from animation import FluidAnimator

class SmartFileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.cfg = load_config()
        self.theme_mode = self.cfg.get('theme_mode', 'dark')

        # CustomTkinter genel teması
        ctk.set_appearance_mode(self.theme_mode)
        ctk.set_default_color_theme("blue")

        # Pencere temel özellikleri
        self.title("Akıllı Dosya Yöneticisi V2 — Windows 11 Fluent Design")
        self.geometry("1060x740")
        self.minsize(960, 640)

        # İkon ayarı
        app_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(app_dir, 'app_icon.ico')
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Sistem tepsisi entegrasyonu
        self.tray = SystemTrayApp(
            on_show_window=self.show_window_safe,
            on_organize_now=self.organize_now_safe,
            on_toggle_watch=self.toggle_watch_safe,
            on_open_folder=self.open_target_folder,
            on_exit_app=self.quit_completely
        )
        self.tray.start()

        # Arka plan izleyici
        self.watcher = BackgroundWatcher(
            config_getter=lambda: self.cfg,
            on_event_callback=self.handle_background_events
        )
        self.watcher.start()

        # Aktif sayfa referansı
        self.active_page_key = 'home'
        self.nav_buttons = {}
        self.current_view = None

        # Ana Arayüzü İnşa Et
        self._build_main_layout()

        # Sürükle-Bırak (Drag & Drop) kancası
        try:
            windnd.hook_dropfiles(self, func=self.on_files_dropped, force_unicode=True)
        except Exception as e:
            print(f"Sürükle bırak kancası hatası: {e}")

        # Kapatma butonunu sistem tepsisine yönlendir
        self.protocol("WM_DELETE_WINDOW", self.on_close_clicked)

        # Durum çubuğunu periyodik güncelle
        self._periodic_status_update()

        # Tekil Örnek IPC Dinleyicisi (Kısayola tekrar basıldığında pencereyi anında öne getirir)
        self._pending_restore = False
        self._periodic_ipc_check()
        self._start_single_instance_listener()

    def _build_main_layout(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.configure(fg_color=c('bg_mica'))

        # Üst Header Bar (Global Search, Hızlı Eylemler, Tema)
        self._build_top_header()

        # Ana Gövde (Sidebar + Content Container)
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True)

        # 1. Sabit Gezinme Paneli (Sol Sidebar)
        self._build_sidebar(body_frame)

        # 2. Ana İçerik Alanı (Sağ Bölge)
        self.content_container = ctk.CTkFrame(body_frame, fg_color="transparent")
        self.content_container.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=(0, 10))

        # İlk sayfayı yükle
        self.navigate_to('home')

    def _build_top_header(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.header_bar = ctk.CTkFrame(
            self,
            fg_color=c('bg_mica'),
            height=54,
            corner_radius=0
        )
        self.header_bar.pack(fill="x", padx=16, pady=(8, 4))
        self.header_bar.pack_propagate(False)

        # Sol: Logo, Başlık ve Fluent AI Rozeti
        brand_box = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        brand_box.pack(side="left", fill="y", padx=(4, 16))

        self.lbl_logo = ctk.CTkLabel(
            brand_box,
            text="📂",
            font=ctk.CTkFont(size=22)
        )
        self.lbl_logo.pack(side="left", padx=(0, 8))

        self.lbl_app_name = ctk.CTkLabel(
            brand_box,
            text="Smart File Organizer",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        )
        self.lbl_app_name.pack(side="left")

        # Windows 11 Fluent Sürüm Rozeti
        lbl_badge = ctk.CTkLabel(
            brand_box,
            text="AI Fluent V2",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#FFFFFF",
            fg_color=c('accent'),
            corner_radius=10,
            padx=8,
            pady=2
        )
        lbl_badge.pack(side="left", padx=(8, 0))

        # Orta: Windows 11 Fluent Search Bar
        search_box = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        search_box.pack(side="left", fill="both", expand=True, padx=16)

        self.global_search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Dosya, klasör veya kategori ara... (Enter)",
            font=ctk.CTkFont(size=12),
            height=34,
            corner_radius=8,
            fg_color=c('bg_input'),
            border_color=c('border'),
            text_color=c('text_primary')
        )
        self.global_search_entry.pack(fill="x", pady=10)
        self.global_search_entry.bind("<Return>", self._on_global_search_enter)

        # Sağ: Aksiyon Butonları & Tema Butonu
        right_box = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        right_box.pack(side="right", fill="y")

        self.btn_quick_scan = ctk.CTkButton(
            right_box,
            text="⚡ Şimdi Tara",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self.manual_organize
        )
        self.btn_quick_scan.pack(side="left", padx=4, pady=10)

        self.btn_open_target = ctk.CTkButton(
            right_box,
            text="📂 Folders",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=self.open_target_folder
        )
        self.btn_open_target.pack(side="left", padx=4, pady=10)

        theme_icon = "☀️" if self.theme_mode == 'dark' else "🌙"
        self.btn_theme_toggle = ctk.CTkButton(
            right_box,
            text=theme_icon,
            font=ctk.CTkFont(size=14),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            width=38,
            height=34,
            corner_radius=8,
            command=self.toggle_theme
        )
        self.btn_theme_toggle.pack(side="left", padx=(4, 0), pady=10)

    def _build_sidebar(self, parent):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.sidebar_frame = ctk.CTkFrame(
            parent,
            fg_color=c('bg_sidebar'),
            width=236,
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=(16, 12), pady=(0, 10))
        self.sidebar_frame.pack_propagate(False)

        # Sabitlenen klasörlerin Windows 11 Fluent ikonları
        self.pinned_icons = {}
        for p_info in PINNED_FOLDERS:
            try:
                pil_img = ThumbnailEngine._extract_shell_image(p_info['path'], 20, 20)
                if pil_img:
                    self.pinned_icons[p_info['id']] = ctk.CTkImage(
                        light_image=pil_img, dark_image=pil_img, size=(20, 20)
                    )
            except Exception:
                pass

        # Gezinme Menüsü (Akıcı ve Kaydırılabilir Container)
        self.nav_container = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_container.pack(fill="both", expand=True, padx=6, pady=(6, 4))
        try:
            self.nav_container._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self.nav_buttons = {}

        # 1. BÖLÜM: Windows 11 Hızlı Erişim (Sabitlenen Klasörler)
        sec_pin_lbl = ctk.CTkLabel(
            self.nav_container,
            text="SABİTLENENLER 📌",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=c('section_header')
        )
        sec_pin_lbl.pack(anchor="w", padx=8, pady=(4, 2))

        for p_info in PINNED_FOLDERS:
            key = p_info['key']
            name = p_info['name']
            icon = self.pinned_icons.get(p_info['id'])

            btn = ctk.CTkButton(
                self.nav_container,
                text=f"  {name}",
                image=icon,
                compound="left",
                anchor="w",
                font=ctk.CTkFont(size=12, weight="normal"),
                fg_color="transparent",
                hover_color=c('sidebar_hover'),
                text_color=c('text_primary'),
                height=32,
                corner_radius=6,
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=1)

            pin_lbl = ctk.CTkLabel(
                btn,
                text="📌",
                font=ctk.CTkFont(size=9),
                text_color=c('text_muted'),
                fg_color="transparent"
            )
            pin_lbl.place(relx=1.0, rely=0.5, x=-10, anchor="e")
            pin_lbl.bind("<Button-1>", lambda e, k=key: self.navigate_to(k))

            self.nav_buttons[key] = btn

        # Bölücü İnce Çizgi
        divider = ctk.CTkFrame(self.nav_container, fg_color=c('border_subtle'), height=1)
        divider.pack(fill="x", padx=6, pady=(8, 4))

        # 2. BÖLÜM: Uygulama Gezinme Menüsü
        nav_sections = [
            ("UYGULAMA", [
                ('home', '🏠  Genel Bakış'),
                ('my_files', '📂  Folders Gezgini'),
                ('media', '🎬  Medya & Galeri'),
            ]),
            ("YAPAY ZEKA & ARAMA", [
                ('intelligence', '🧠  AI Zekâsı'),
                ('search', '🔍  Akıllı Arama'),
                ('smart_org', '⚡  Hızlı Düzenle'),
            ]),
            ("YÖNETİM & ARAÇLAR", [
                ('automation', '🔄  Otomasyon'),
                ('duplicates', '📑  Kopya Yönetici'),
                ('storage', '📊  Depolama Analizi'),
            ]),
            ("SİSTEM", [
                ('activity', '📜  Aktivite Merkezi'),
                ('security', '🛡️  Güvenlik & Yedek'),
                ('settings', '⚙️  Ayarlar'),
            ])
        ]

        for section_title, items in nav_sections:
            sec_lbl = ctk.CTkLabel(
                self.nav_container,
                text=section_title,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=c('section_header')
            )
            sec_lbl.pack(anchor="w", padx=8, pady=(6, 2))

            for key, label in items:
                btn = ctk.CTkButton(
                    self.nav_container,
                    text=label,
                    font=ctk.CTkFont(size=12, weight="normal"),
                    fg_color="transparent",
                    hover_color=c('sidebar_hover'),
                    text_color=c('text_primary'),
                    anchor="w",
                    height=30,
                    corner_radius=6,
                    command=lambda k=key: self.navigate_to(k)
                )
                btn.pack(fill="x", pady=1)
                self.nav_buttons[key] = btn

        # Alt Bölüm: Windows 11 Akıcı Durum Kartı
        self.bottom_status_card = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        self.bottom_status_card.pack(fill="x", padx=10, pady=(4, 10))

        inner_stat = ctk.CTkFrame(self.bottom_status_card, fg_color="transparent")
        inner_stat.pack(fill="x", padx=12, pady=10)

        self.lbl_status_badge = ctk.CTkLabel(
            inner_stat,
            text="🟢 İzleme: Aktif",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('success')
        )
        self.lbl_status_badge.pack(anchor="w")

        self.lbl_monitored_info = ctk.CTkLabel(
            inner_stat,
            text=f"📁 İzlenen: {len(self.cfg.get('sources', []))} Klasör",
            font=ctk.CTkFont(size=10),
            text_color=c('text_secondary')
        )
        self.lbl_monitored_info.pack(anchor="w", pady=(2, 0))

        self.lbl_last_scan_info = ctk.CTkLabel(
            inner_stat,
            text="⏱️ Son Tarama: Hazır",
            font=ctk.CTkFont(size=9),
            text_color=c('text_muted')
        )
        self.lbl_last_scan_info.pack(anchor="w")

        # Linux GNOME tarzı nefes alan canlı sistem durumu nabzı
        FluidAnimator.start_pulse_badge(self.lbl_status_badge, color_base="#10B981", color_glow="#34D399")

    def navigate_to(self, page_key, extra_data=None):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.active_page_key = page_key

        # Sidebar buton vurgularını güncelle
        for k, btn in self.nav_buttons.items():
            if k == page_key:
                btn.configure(
                    fg_color=c('sidebar_active'),
                    text_color=c('accent_light'),
                    font=ctk.CTkFont(size=12, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=c('text_primary'),
                    font=ctk.CTkFont(size=12, weight="normal")
                )

        # Önceki görünümü tamamen yok et — Aktif widget sayısını ~40'ta tutarak CustomTkinter kasmasını çözer
        if hasattr(self, 'current_view') and self.current_view:
            try:
                self.current_view.destroy()
            except Exception:
                pass
            self.current_view = None

        # Windows 11 Sabitlenen Klasör Sayfaları
        if page_key.startswith('quick_'):
            folder_id = page_key.replace('quick_', '')
            self.current_view = QuickFolderView(self.content_container, self, folder_id=folder_id)
            self.current_view.pack(fill="both", expand=True)
            FluidAnimator.slide_in_view(self.current_view)
            return

        # Sayfa örneğini oluştur (Önbellek 3 mikrosaniyede yüklendiğinden anında açılır)
        view_map = {
            'home': HomeView,
            'my_files': MyFilesView,
            'media': MediaGalleryView,
            'intelligence': AIIntelligenceView,
            'search': SemanticSearchView,
            'smart_org': SmartOrgView,
            'automation': AutomationView,
            'duplicates': DuplicateView,
            'storage': StorageView,
            'activity': ActivityView,
            'security': SecurityBackupView,
            'settings': SettingsView
        }

        view_class = view_map.get(page_key, HomeView)
        self.current_view = view_class(self.content_container, self)
        self.current_view.pack(fill="both", expand=True)

        # Linux Libadwaita / Fluent akıcı sayfa mikro-kayma geçişi
        FluidAnimator.slide_in_view(self.current_view, start_offset_y=12, duration_ms=160, steps=8)

        if page_key == 'intelligence' and extra_data:
            self.current_view.analyze_file(extra_data)
        elif page_key == 'search' and extra_data:
            self.current_view.set_query_and_search(extra_data)

    def _on_global_search_enter(self, event=None):
        q = self.global_search_entry.get().strip()
        if q:
            self.navigate_to('search', extra_data=q)

    def toggle_theme(self):
        new_mode = 'light' if self.theme_mode == 'dark' else 'dark'
        self.set_theme(new_mode)

    def set_theme(self, new_mode):
        self.theme_mode = new_mode
        self.cfg['theme_mode'] = new_mode
        save_config(self.cfg)
        ctk.set_appearance_mode(new_mode)

        self.current_view = None
        for w in self.winfo_children():
            w.destroy()
        self._build_main_layout()

    def update_status_footer(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        stat = self.watcher.get_status_summary()

        # Yalnızca değerler gerçekten değiştiyse Canvas güncelleyerek gereksiz CPU yükünü önle
        current_state = (stat['is_active'], stat['monitored_count'], stat['last_scan'])
        if getattr(self, '_last_status_state', None) == current_state:
            return
        self._last_status_state = current_state

        if stat['is_active']:
            self.lbl_status_badge.configure(text="🟢 İzleme: Aktif", text_color=c('success'))
        else:
            self.lbl_status_badge.configure(text="⏸️ İzleme: Duraklatıldı", text_color=c('warning'))

        self.lbl_monitored_info.configure(text=f"İzlenen: {stat['monitored_count']} Klasör")
        self.lbl_last_scan_info.configure(text=f"Son: {stat['last_scan']}")

    def _periodic_status_update(self):
        self.update_status_footer()
        self.after(3000, self._periodic_status_update)

    def on_files_dropped(self, files):
        """Pencereye herhangi bir dosya/klasör sürüklendiğinde çalışır."""
        if not files:
            return

        # Eğer kullanıcı şu anda AI Intelligence sayfasındaysa, ilk dosyayı analiz et
        if self.active_page_key == 'intelligence' and len(files) == 1:
            f = files[0]
            if isinstance(f, bytes):
                f = f.decode('utf-8', errors='ignore')
            self.current_view.analyze_file(f)
            return

        target_base = self.cfg.get('target', '')
        allow_new = self.cfg.get('allow_new_categories', True)

        events = []
        for f in files:
            if isinstance(f, bytes):
                f = f.decode('utf-8', errors='ignore')
            if os.path.exists(f):
                res = organize_item(f, target_base, allow_new)
                if res:
                    events.append(res)

        if events:
            self.handle_background_events(events)
            c = lambda token: FluentTheme.c(token, self.theme_mode)
            FluidAnimator.show_toast(
                self,
                f"{len(events)} dosya akıllıca analiz edilip Folders'a organize edildi!",
                icon="🚀",
                bg_color=c('bg_card'),
                border_color=c('accent')
            )
            # Eğer Home sayfasındaysa tazele
            if self.active_page_key == 'home':
                self.navigate_to('home')

    def manual_organize(self):
        """Tüm giriş klasörlerini şimdi tara."""
        sources = self.cfg.get('sources', [])
        target = self.cfg.get('target', '')
        allow_new = self.cfg.get('allow_new_categories', True)
        desktop_baseline = set(self.cfg.get('desktop_baseline', []))

        events = scan_and_organize(sources, target, allow_new, desktop_baseline)
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        if events:
            self.handle_background_events(events)
            FluidAnimator.show_toast(
                self,
                f"Tarama tamamlandı: {len(events)} dosya organize edildi.",
                icon="⚡",
                bg_color=c('bg_card'),
                border_color=c('accent')
            )
        else:
            FluidAnimator.show_toast(
                self,
                "İzlenen klasörlerde taşınacak yeni dosya bulunamadı.",
                icon="ℹ️",
                bg_color=c('bg_card'),
                border_color=c('border')
            )
            messagebox.showinfo("Bilgi", "İzlenen klasörlerde taşınacak yeni dosya bulunamadı.")

        if self.active_page_key == 'home':
            self.navigate_to('home')

    def undo_last_action(self):
        res = SecurityBackupEngine.undo_last()
        if res['success']:
            messagebox.showinfo("Geri Alındı", res['message'])
            if self.active_page_key in ('home', 'security', 'activity'):
                self.navigate_to(self.active_page_key)
        else:
            messagebox.showwarning("Bilgi", res['message'])

    def handle_background_events(self, events):
        # Arka plan olaylarını UI thread'inde işle
        self.after(0, self.update_status_footer)

    def open_target_folder(self):
        target = self.cfg.get('target', '')
        if os.path.exists(target):
            os.startfile(target)

    def show_window_safe(self):
        self.after(0, self._restore_window)

    def _restore_window(self):
        try:
            self.deiconify()
            self.state('normal')
            self.lift()
            self.focus_force()
            self.attributes('-topmost', True)
            self.after(150, lambda: self.attributes('-topmost', False))

            # Windows API ile ön plana zorla çıkarma
            import ctypes
            hwnd = self.winfo_id()
            user32 = ctypes.windll.user32
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Pencere öne getirme hatası: {e}")

    def _periodic_ipc_check(self):
        if getattr(self, '_pending_restore', False):
            self._pending_restore = False
            self._restore_window()
        if getattr(self, '_is_alive', True):
            self.after(100, self._periodic_ipc_check)

    def _start_single_instance_listener(self):
        """Arka planda çalışırken masaüstü kısayoluna basıldığında pencereyi anında öne getirir."""
        import socket
        import threading

        self._is_alive = True
        self._single_instance_server = None

        def listener():
            try:
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
                server.listen(5)
                self._single_instance_server = server
                while getattr(self, '_is_alive', True):
                    try:
                        conn, _ = server.accept()
                        data = conn.recv(64)
                        if b'ACTIVATE' in data:
                            self._pending_restore = True
                        conn.close()
                    except Exception:
                        break
            except Exception as e:
                print(f"Tekil örnek IPC dinleyici hatası: {e}")

        t = threading.Thread(target=listener, daemon=True)
        t.start()

    def organize_now_safe(self):
        self.after(0, self.manual_organize)

    def toggle_watch_safe(self):
        self.after(0, self._toggle_watch_action)

    def _toggle_watch_action(self):
        new_val = not self.cfg.get('auto_watch', True)
        self.cfg['auto_watch'] = new_val
        save_config(self.cfg)
        self.update_status_footer()

    def on_close_clicked(self):
        if self.cfg.get('minimize_to_tray_on_close', True):
            self.withdraw()
        else:
            self.quit_completely()

    def quit_completely(self):
        self._is_alive = False
        if hasattr(self, '_single_instance_server') and self._single_instance_server:
            try:
                self._single_instance_server.close()
            except Exception:
                pass
        self.watcher.stop()
        self.tray.stop()
        self.after(100, self.destroy)

SINGLE_INSTANCE_PORT = 49285

def try_activate_running_instance():
    """
    Eğer arka planda zaten çalışan bir uygulama örneği varsa, ona TCP üzerinden 'ACTIVATE' sinyali gönderir.
    Pencereyi ekrana getirir ve True döner (yeni sürecin sessizce kapanması gerekir).
    """
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        s.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
        s.sendall(b'ACTIVATE\n')
        s.close()
        return True
    except Exception:
        return False

if __name__ == '__main__':
    # Eğer uygulama arka planda veya sistem tepsisinde zaten açıksa, onu öne getir ve sessizce çık!
    if try_activate_running_instance():
        sys.exit(0)

    try:
        app = SmartFileOrganizerApp()
        app.mainloop()
    except Exception as e:
        import traceback
        crash_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_crash.log')
        with open(crash_log, 'w', encoding='utf-8') as f:
            traceback.print_exc(file=f)
