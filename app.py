"""
Smart File Organizer V2.1 — Windows 11 Fluent Design + AI File Intelligence System
Main Application Window, Navigation Controller, View Cache, Command Palette,
Notification Center, System Tray, and Single-Instance IPC Manager.
"""

import os
import sys
import socket
import ctypes
import threading
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray

try:
    import windnd
    HAS_WINDND = True
except ImportError:
    HAS_WINDND = False

from config import (
    load_config,
    save_config,
    APP_VERSION,
    DEFAULT_DESKTOP,
    DEFAULT_DOWNLOADS,
    DEFAULT_DOCUMENTS,
    DEFAULT_PICTURES,
    DEFAULT_MUSIC,
    DEFAULT_VIDEOS
)
from theme import FluentTheme
from watcher import BackgroundWatcher
from organizer import organize_file
from storage_analyzer import StorageAnalyzer
from animation import FluidAnimator, UIBridge
from thumbnail_engine import ThumbnailEngine
from command_palette import CommandPalette
from notification_center import NotificationCenter, FluentContextMenu

# Sayfa Görünümleri (Views)
from views.home_view import HomeView
from views.my_files_view import MyFilesView
from views.ai_intelligence_view import AIIntelligenceView
from views.search_view import SemanticSearchView
from views.smart_org_view import SmartOrgView
from views.automation_view import AutomationView
from views.duplicate_view import DuplicateView
from views.storage_view import StorageView
from views.activity_view import ActivityView
from views.security_view import SecurityBackupView
from views.settings_view import SettingsView
from views.media_view import MediaGalleryView
from views.quick_folder_view import QuickFolderView

SINGLE_INSTANCE_PORT = 49285


def notify_existing_instance() -> bool:
    """
    Halihazırda arka planda çalışan bir örnek varsa ona 'SHOW' sinyali gönderir.
    Başarılı olursa True döner (böylece yeni açılan örnek kendisini kapatır).
    """
    try:
        with socket.create_connection(("127.0.0.1", SINGLE_INSTANCE_PORT), timeout=0.6) as s:
            s.sendall(b"SHOW_WINDOW")
            resp = s.recv(16)
            if resp == b"ACK":
                return True
    except Exception:
        pass
    return False


class SmartFileOrganizerApp(ctk.CTk):
    def __init__(self, start_minimized=False):
        super().__init__()

        # Yapılandırmayı yükle
        self.cfg = load_config()
        self.theme_mode = self._resolve_theme(self.cfg.get('theme', 'dark'))
        FluentTheme.apply_appearance(self.cfg.get('theme', 'dark'))

        # Pencere Ayarları
        self.title(f"Smart File Organizer v{APP_VERSION} — AI File Intelligence")
        self.geometry("1220x780")
        self.minsize(1020, 660)

        # Windows 11 DWM Koyu Başlık Çubuğu & Mica/Yuvarlatılmış Köşe Desteği
        self._apply_windows_11_dwm()

        # Thread-Safe UI Köprüsünü Başlat (Python 3.15 Uyumluluğu)
        UIBridge.start(self)

        # Navigasyon ve Görünüm Önbelleği (Flicker-free Instant Navigation)
        self.nav_buttons = {}
        self.nav_indicators = {}
        self.section_frames = {}
        self.section_chevrons = {}
        self.section_collapsed = {}
        self.current_page_id = None
        self.current_view = None
        self._view_cache = {}
        self._pinned_icons = {}

        # Arka Plan İzleyiciyi Başlat
        self.watcher = BackgroundWatcher(
            config_getter=lambda: self.cfg,
            on_event_callback=self.handle_background_events
        )
        self.watcher.start()

        # Tek Örnek (Single Instance) IPC Dinleyicisini Başlat
        self._ipc_server = None
        self._start_single_instance_listener()

        # Ana Düzeni Oluştur
        self._preload_pinned_icons()
        self._build_layout()

        # Sürükle-Bırak Desteği (Pencere Geneli)
        if HAS_WINDND:
            try:
                windnd.hook_dropfiles(self, func=self._on_global_files_dropped)
            except Exception as e:
                print(f"Sürükle-bırak başlatılamadı: {e}")

        # Klavye Kısayollarını Bağla
        self._bind_shortcuts()

        # Pencere Kapatma Davranışı (Sistem Tepsisine Küçült)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Sistem Tepsisi İkonu
        self.tray_icon = None
        self._init_tray()

        # İlk Sayfayı Aç
        self.navigate_to('home')

        # Periyodik Durum Çubuğu Güncelleyici
        self._periodic_status_update()

        # Başlangıç bildirimi (Sadece bildirim merkezine sessiz kayıt)
        NotificationCenter.add(
            title="Sistem Hazır",
            message=f"Smart File Organizer v{APP_VERSION} arka plan izleme motoru aktif.",
            level="info"
        )
        self.update_notification_badge()

        if start_minimized:
            self.after(100, self.hide_to_tray)

    def _bind_shortcuts(self):
        """Uygulama geneli klavye kısayollarını bağlar."""
        self.bind("<Control-k>", lambda _e: CommandPalette.toggle(self))
        self.bind("<Control-K>", lambda _e: CommandPalette.toggle(self))
        self.bind("<Control-f>", lambda _e: self._focus_global_search())
        self.bind("<Control-F>", lambda _e: self._focus_global_search())
        self.bind("<F5>", lambda _e: self._refresh_active_view())
        self.bind("<Escape>", lambda _e: self._close_overlays())
        self.bind("<Button-1>", lambda e: self._on_global_left_click(e), add="+")

    def _focus_global_search(self):
        try:
            if hasattr(self, 'global_search_entry') and self.global_search_entry.winfo_exists():
                self.global_search_entry.focus_set()
        except Exception:
            pass

    def _refresh_active_view(self):
        StorageAnalyzer.invalidate_cache()
        if self.current_view:
            if hasattr(self.current_view, '_refresh_content'):
                self.current_view._refresh_content()
            elif hasattr(self.current_view, '_refresh_data'):
                self.current_view._refresh_data()
            elif hasattr(self.current_view, 'on_page_show'):
                self.current_view.on_page_show()
        FluidAnimator.show_toast(
            self,
            "Görünüm Yenilendi",
            "Sayfa verileri ve önbellek güncellendi.",
            theme_mode=self.theme_mode,
            duration_ms=1800,
            level='info'
        )

    def _close_overlays(self):
        CommandPalette.close()
        NotificationCenter.close_flyout()
        FluentContextMenu.close_active()

    def _on_global_left_click(self, event):
        """Açık bağlam menüsü varsa dışarı tıklandığında kapatır."""
        if FluentContextMenu._active_menu is not None:
            try:
                menu = FluentContextMenu._active_menu
                if menu.winfo_exists():
                    mx, my = event.x_root, event.y_root
                    wx, wy = menu.winfo_rootx(), menu.winfo_rooty()
                    ww, wh = menu.winfo_width(), menu.winfo_height()
                    if not (wx <= mx <= wx + ww and wy <= my <= wy + wh):
                        FluentContextMenu.close_active()
            except Exception:
                FluentContextMenu.close_active()

    def _start_single_instance_listener(self):
        """Arka planda çalışırken masaüstü kısayoluna tekrar tıklandığında pencereyi öne getirir."""
        def _listen():
            try:
                srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srv.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
                srv.listen(5)
                self._ipc_server = srv
                while True:
                    conn, _ = srv.accept()
                    try:
                        data = conn.recv(64)
                        if data == b"SHOW_WINDOW":
                            conn.sendall(b"ACK")
                            UIBridge.post(self.show_window_from_tray)
                    finally:
                        conn.close()
            except Exception:
                pass

        threading.Thread(target=_listen, daemon=True).start()

    def _preload_pinned_icons(self):
        """Windows 11 Hızlı Erişim klasörlerinin gerçek kabuk (shell) ikonlarını yükler."""
        folder_map = {
            'qf_desktop': DEFAULT_DESKTOP,
            'qf_downloads': DEFAULT_DOWNLOADS,
            'qf_documents': DEFAULT_DOCUMENTS,
            'qf_pictures': DEFAULT_PICTURES,
            'qf_music': DEFAULT_MUSIC,
            'qf_videos': DEFAULT_VIDEOS,
        }
        for key, path in folder_map.items():
            try:
                pil_img = ThumbnailEngine._extract_shell_image(path, 20, 20)
                if pil_img:
                    self._pinned_icons[key] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(18, 18))
            except Exception:
                pass

    def _resolve_theme(self, pref):
        if pref == 'light':
            return 'light'
        return 'dark'

    def _apply_windows_11_dwm(self):
        """Windows 11 DWM API ile koyu/açık pencere başlığı ve Mica/Yuvarlatılmış köşe uygular."""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()

            is_dark = 1 if self.theme_mode == 'dark' else 0
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(is_dark)), ctypes.sizeof(ctypes.c_int)
            )
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33 (DWMWCP_ROUND = 2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass

    def _build_layout(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.configure(fg_color=c('bg_primary'))

        # Grid Yapılandırması (Sol Sidebar Sabit, Sağ İçerik Esnek)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # 1. SOL GEZİNME PANELİ (SIDEBAR)
        self._build_sidebar()

        # 2. SAĞ ANA ALAN (ÜST BAR + SAYFA İÇERİĞİ)
        self.right_panel = ctk.CTkFrame(self, fg_color=c('bg_mica'), corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=0)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Üst Bar (Global Arama + Komut Paleti + Bildirim Merkezi + Tema + Hızlı Aksiyon)
        self._build_top_header()

        # Ana Sayfa İçerik Konteyneri
        self.content_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _build_sidebar(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=c('bg_secondary'),
            width=252,
            corner_radius=0,
            border_width=1,
            border_color=c('border_subtle')
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo & Uygulama Başlığı
        brand_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_box.pack(fill="x", padx=16, pady=(16, 8))

        logo_badge = ctk.CTkLabel(
            brand_box,
            text="⚡",
            font=ctk.CTkFont(size=22),
            fg_color=c('accent'),
            text_color="#FFFFFF",
            corner_radius=8,
            width=36,
            height=36
        )
        logo_badge.pack(side="left", padx=(0, 10))

        brand_text = ctk.CTkFrame(brand_box, fg_color="transparent")
        brand_text.pack(side="left")

        ctk.CTkLabel(
            brand_text,
            text="Smart Organizer",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text=f"Fluent Motion v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color=c('accent_light')
        ).pack(anchor="w")

        # Kaydırılabilir Menü Listesi
        nav_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('text_muted')
        )
        nav_scroll.pack(fill="both", expand=True, padx=6, pady=2)

        self.nav_buttons.clear()
        self.nav_indicators.clear()
        self.section_frames.clear()
        self.section_chevrons.clear()

        sections = [
            (
                "sec_pinned",
                "SABİTLENEN KLASÖRLER 📌",
                [
                    ('qf_desktop', 'Masaüstü 📌', '🖥️', self._pinned_icons.get('qf_desktop')),
                    ('qf_downloads', 'İndirilenler 📌', '📥', self._pinned_icons.get('qf_downloads')),
                    ('qf_documents', 'Belgeler 📌', '📑', self._pinned_icons.get('qf_documents')),
                    ('qf_pictures', 'Resimler 📌', '🖼️', self._pinned_icons.get('qf_pictures')),
                    ('qf_music', 'Müzikler 📌', '🎵', self._pinned_icons.get('qf_music')),
                    ('qf_videos', 'Videolar 📌', '🎬', self._pinned_icons.get('qf_videos')),
                ]
            ),
            (
                "sec_explore",
                "KEŞFET VE YÖNET",
                [
                    ('home', 'Genel Bakış', '🏠', None),
                    ('files', 'Folders Gezgini', '📁', None),
                    ('media', 'Medya & Videolar', '🎬', None),
                ]
            ),
            (
                "sec_ai",
                "AKILLI SİSTEMLER",
                [
                    ('ai', 'AI Dosya Zekâsı', '🧠', None),
                    ('search', 'Akıllı Arama', '🔍', None),
                    ('smart_org', 'Hızlı Düzenle', '✨', None),
                    ('automation', 'Otomasyon', '⚡', None),
                ]
            ),
            (
                "sec_tools",
                "ANALİZ VE GÜVENLİK",
                [
                    ('duplicates', 'Kopya Yönetici', '📑', None),
                    ('storage', 'Depolama Analizi', '📊', None),
                    ('activity', 'Aktivite Merkezi', '🕒', None),
                    ('security', 'Güvenlik & Yedek', '🛡️', None),
                    ('settings', 'Ayarlar', '⚙️', None),
                ]
            )
        ]

        for sec_id, sec_title, items in sections:
            is_collapsed = self.section_collapsed.get(sec_id, False)

            hdr_btn = ctk.CTkButton(
                nav_scroll,
                text=f"{'▸' if is_collapsed else '▾'}  {sec_title}",
                anchor="w",
                height=24,
                corner_radius=6,
                fg_color="transparent",
                hover_color=c('bg_card_hover'),
                text_color=c('text_muted'),
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda sid=sec_id, st=sec_title: self._toggle_sidebar_section(sid, st)
            )
            hdr_btn.pack(fill="x", padx=4, pady=(8, 2))
            self.section_chevrons[sec_id] = hdr_btn

            sec_container = ctk.CTkFrame(nav_scroll, fg_color="transparent")
            if not is_collapsed:
                sec_container.pack(fill="x")
            self.section_frames[sec_id] = (sec_container, hdr_btn)

            for page_id, label, fallback_emoji, icon_img in items:
                row_holder = ctk.CTkFrame(sec_container, fg_color="transparent", height=34)
                row_holder.pack(fill="x", pady=1)
                row_holder.pack_propagate(False)

                # Sol Aktif Vurgu Çubuğu (Fluent Active Indicator Pill)
                indicator = ctk.CTkFrame(
                    row_holder,
                    fg_color="transparent",
                    width=4,
                     height=18,
                    corner_radius=2
                )
                indicator.pack(side="left", padx=(2, 3), pady=8)
                self.nav_indicators[page_id] = indicator

                if icon_img is not None:
                    btn = ctk.CTkButton(
                        row_holder,
                        text=f"  {label}",
                        image=icon_img,
                        compound="left",
                        anchor="w",
                        font=ctk.CTkFont(size=12),
                        fg_color="transparent",
                        hover_color=c('bg_card_hover'),
                        text_color=c('text_secondary'),
                        height=32,
                        corner_radius=7,
                        command=lambda pid=page_id: self.navigate_to(pid)
                    )
                else:
                    btn = ctk.CTkButton(
                        row_holder,
                        text=f" {fallback_emoji}   {label}",
                        anchor="w",
                        font=ctk.CTkFont(size=12),
                        fg_color="transparent",
                        hover_color=c('bg_card_hover'),
                        text_color=c('text_secondary'),
                        height=32,
                        corner_radius=7,
                        command=lambda pid=page_id: self.navigate_to(pid)
                    )
                btn.pack(side="left", fill="both", expand=True, padx=(0, 2))
                self.nav_buttons[page_id] = btn

        # Alt Durum Özeti Kartı
        self.footer_card = ctk.CTkFrame(
            self.sidebar,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        self.footer_card.pack(fill="x", side="bottom", padx=12, pady=12)

        f_inner = ctk.CTkFrame(self.footer_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=12, pady=10)

        self.lbl_watch_state = ctk.CTkLabel(
            f_inner,
            text="🟢 İzleme Aktif",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=c('success')
        )
        self.lbl_watch_state.pack(anchor="w")

        self.lbl_watch_folders = ctk.CTkLabel(
            f_inner,
            text=f"İzlenen Klasör: {len(self.cfg.get('sources', []))}",
            font=ctk.CTkFont(size=11),
            text_color=c('text_secondary')
        )
        self.lbl_watch_folders.pack(anchor="w", pady=(2, 0))

        self.lbl_last_scan = ctk.CTkLabel(
            f_inner,
            text="Son Tarama: Şimdi",
            font=ctk.CTkFont(size=10),
            text_color=c('text_muted')
        )
        self.lbl_last_scan.pack(anchor="w")

    def _toggle_sidebar_section(self, sec_id: str, sec_title: str):
        """Gezinme panelindeki kategori bölümlerini yumuşak şekilde açar/kapatır."""
        pair = self.section_frames.get(sec_id)
        if not pair:
            return
        sec_container, hdr_btn = pair
        currently_collapsed = self.section_collapsed.get(sec_id, False)
        new_collapsed = not currently_collapsed
        self.section_collapsed[sec_id] = new_collapsed

        if new_collapsed:
            sec_container.pack_forget()
            hdr_btn.configure(text=f"▸  {sec_title}")
        else:
            sec_container.pack(fill="x", after=hdr_btn)
            hdr_btn.configure(text=f"▾  {sec_title}")

    def _build_top_header(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        self.top_bar = ctk.CTkFrame(
            self.right_panel,
            fg_color=c('bg_secondary'),
            height=58,
            corner_radius=0,
            border_width=1,
            border_color=c('border_subtle')
        )
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        inner_bar = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        inner_bar.pack(fill="both", expand=True, padx=16, pady=10)

        # Global Arama Çubuğu
        search_box = ctk.CTkFrame(inner_bar, fg_color="transparent")
        search_box.pack(side="left", fill="x", expand=True)

        self.global_search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Dosya, içerik veya etiket ara... (Ctrl+F)",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_input'),
            border_color=c('border'),
            text_color=c('text_primary'),
            width=340,
            height=34,
            corner_radius=8
        )
        self.global_search_entry.pack(side="left")
        self.global_search_entry.bind("<Return>", self._on_global_search_enter)
        FluidAnimator.bind_input_focus(self.global_search_entry, self.theme_mode)

        # Komut Paleti Tetikleyici Butonu (Ctrl+K)
        self.btn_cmd_palette = ctk.CTkButton(
            search_box,
            text="⌘ Komutlar (Ctrl+K)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            border_width=1,
            border_color=c('border'),
            height=34,
             width=136,
            corner_radius=8,
            command=lambda: CommandPalette.toggle(self)
        )
        self.btn_cmd_palette.pack(side="left", padx=(8, 0))

        # Sağ Üst Kontroller
        controls_box = ctk.CTkFrame(inner_bar, fg_color="transparent")
        controls_box.pack(side="right")

        # Şimdi Tara Butonu
        ctk.CTkButton(
            controls_box,
            text="⚡ Şimdi Tara",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=32,
            width=106,
            corner_radius=6,
            command=self.trigger_manual_scan
        ).pack(side="left", padx=5)

        # Bildirim Merkezi Butonu (🔔)
        self.btn_notifications = ctk.CTkButton(
            controls_box,
            text="🔔",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            width=46,
            height=32,
            corner_radius=6,
            command=lambda: NotificationCenter.toggle_flyout(self)
        )
        self.btn_notifications.pack(side="left", padx=4)

        # Tema Değiştirici
        self.theme_seg = ctk.CTkSegmentedButton(
            controls_box,
            values=["🌙 Koyu", "☀️ Açık"],
            font=ctk.CTkFont(size=11),
            height=30,
            command=self._on_top_theme_toggle
        )
        self.theme_seg.pack(side="left", padx=5)
        self.theme_seg.set("☀️ Açık" if self.theme_mode == 'light' else "🌙 Koyu")

        # Ayarlar Kısayol Butonu
        ctk.CTkButton(
            controls_box,
            text="⚙️",
            width=34,
            height=32,
            corner_radius=6,
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            command=lambda: self.navigate_to('settings')
        ).pack(side="left", padx=(4, 0))

    def update_notification_badge(self):
        """Üst bardaki 🔔 Bildirim Merkezi butonunun okunmamış sayacını günceller."""
        if not hasattr(self, 'btn_notifications'):
            return
        try:
            if not self.btn_notifications.winfo_exists():
                return
            unread = NotificationCenter.get_unread_count()
            c = lambda token: FluentTheme.c(token, self.theme_mode)
            if unread > 0:
                self.btn_notifications.configure(
                    text=f"🔔 {unread}",
                    text_color=c('accent_light')
                )
            else:
                self.btn_notifications.configure(
                    text="🔔",
                    text_color=c('text_primary')
                )
        except Exception:
            pass

    def navigate_to(self, page_id):
        """
        Sayfalar arası anlık, titreşimsiz (flicker-free) önbellekli geçiş sağlar
        ve aktif yan menü vurgu çubuğunu (indicator pill) günceller.
        """
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self._close_overlays()

        self.current_page_id = page_id

        # Sidebar butonlarının ve sol aktif gösterge çubuğunun stilini güncelle
        for pid, btn in self.nav_buttons.items():
            ind = self.nav_indicators.get(pid)
            if pid == page_id:
                btn.configure(
                    fg_color=c('bg_card_active'),
                    text_color=c('accent_light'),
                    font=ctk.CTkFont(size=12, weight="bold")
                )
                if ind:
                    ind.configure(fg_color=c('nav_indicator'))
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=c('text_secondary'),
                    font=ctk.CTkFont(size=12, weight="normal")
                )
                if ind:
                    ind.configure(fg_color="transparent")

        # Mevcut görünümü gizle (Yok etmeden önbellekte tut)
        if self.current_view is not None:
            try:
                self.current_view.pack_forget()
            except Exception:
                pass

        # Hedef görünümü önbellekten al veya ilk kez oluştur
        if page_id not in self._view_cache or not self._view_cache[page_id].winfo_exists():
            view_map = {
                'qf_desktop': lambda: QuickFolderView(self.content_container, self, 'desktop'),
                'qf_downloads': lambda: QuickFolderView(self.content_container, self, 'downloads'),
                'qf_documents': lambda: QuickFolderView(self.content_container, self, 'documents'),
                'qf_pictures': lambda: QuickFolderView(self.content_container, self, 'pictures'),
                'qf_music': lambda: QuickFolderView(self.content_container, self, 'music'),
                'qf_videos': lambda: QuickFolderView(self.content_container, self, 'videos'),
                'home': lambda: HomeView(self.content_container, self),
                'files': lambda: MyFilesView(self.content_container, self),
                'media': lambda: MediaGalleryView(self.content_container, self),
                'ai': lambda: AIIntelligenceView(self.content_container, self),
                'search': lambda: SemanticSearchView(self.content_container, self),
                'smart_org': lambda: SmartOrgView(self.content_container, self),
                'automation': lambda: AutomationView(self.content_container, self),
                'duplicates': lambda: DuplicateView(self.content_container, self),
                'storage': lambda: StorageView(self.content_container, self),
                'activity': lambda: ActivityView(self.content_container, self),
                'security': lambda: SecurityBackupView(self.content_container, self),
                'settings': lambda: SettingsView(self.content_container, self)
            }
            factory = view_map.get(page_id, view_map['home'])
            self._view_cache[page_id] = factory()

        self.current_view = self._view_cache[page_id]
        self.current_view.pack(fill="both", expand=True)

        if hasattr(self.current_view, 'on_page_show'):
            try:
                self.current_view.on_page_show()
            except Exception:
                pass

    def toggle_theme_quick(self):
        next_mode = 'light' if self.theme_mode == 'dark' else 'dark'
        self.change_theme(next_mode)

    def _on_top_theme_toggle(self, val):
        mode = 'light' if "Açık" in val else 'dark'
        self.change_theme(mode)

    def change_theme(self, mode_pref):
        self.cfg['theme'] = mode_pref
        save_config(self.cfg)
        FluentTheme.apply_appearance(mode_pref)
        self.theme_mode = self._resolve_theme(mode_pref)
        self._apply_windows_11_dwm()

        # Önbellekteki görünümleri temizle ve arayüzü yeni temayla oluştur
        self._view_cache.clear()
        self.current_view = None
        for w in self.winfo_children():
            w.destroy()
        self._build_layout()
        self.navigate_to(self.current_page_id or 'home')

    def _on_global_search_enter(self, _event=None):
        query = self.global_search_entry.get().strip()
        self.navigate_to('search')
        if self.current_view and hasattr(self.current_view, 'search_entry'):
            self.current_view.search_entry.delete(0, "end")
            self.current_view.search_entry.insert(0, query)
            self.current_view.execute_search()

    def trigger_manual_scan(self):
        self.watcher.trigger_now()
        self.after(300, self.update_status_footer)
        if self.cfg.get('notifications', True):
            FluidAnimator.show_toast(
                self,
                "Tarama Başlatıldı",
                "İzlenen klasörler taranıyor ve yeni dosyalar organize ediliyor.",
                theme_mode=self.theme_mode,
                duration_ms=2200,
                level='info'
            )

    def open_target_folder(self):
        target = self.cfg.get('target', '')
        if os.path.exists(target):
            os.startfile(target)

    def handle_background_events(self, events):
        """Arka plan izleyiciden veya sürükle-bırak işleminden gelen sonuçları UI thread'inde işler."""
        if not events:
            return

        def _process_on_ui():
            StorageAnalyzer.invalidate_cache()
            self.update_status_footer()
            if self.cfg.get('notifications', True):
                last_ev = events[-1]
                FluidAnimator.show_toast(
                    self,
                    "AI Dosya Organizasyonu",
                    f"{last_ev['file_name']} ➔ {last_ev['category']}",
                    theme_mode=self.theme_mode,
                    level='success'
                )
            if self.current_page_id == 'home' and self.current_view and hasattr(self.current_view, 'on_page_show'):
                self.current_view.on_page_show()

        UIBridge.post(_process_on_ui)

    def _on_global_files_dropped(self, file_bytes_list):
        """Kullanıcı pencereye dosya sürükleyip bıraktığında çalışır."""
        paths = []
        for b in file_bytes_list:
            if isinstance(b, bytes):
                try:
                    p = b.decode('utf-8')
                except UnicodeDecodeError:
                    p = b.decode('mbcs', errors='ignore')
            else:
                p = str(b)
            paths.append(p)
        self.on_files_dropped(paths)

    def on_files_dropped(self, paths):
        """Dosya veya klasör yolları listesini arka planda organize eder."""
        if not paths:
            return

        if self.current_page_id == 'ai' and len(paths) == 1 and os.path.isfile(paths[0]):
            self.current_view.analyze_file(paths[0])
            return

        target_base = self.cfg.get('target', '')
        allow_new = self.cfg.get('allow_new_categories', True)

        def run_drop():
            events = []
            for p in paths:
                if os.path.isfile(p):
                    ev = organize_file(p, target_base, allow_new)
                    if ev and ev.get('status') == 'success':
                        events.append(ev)
                elif os.path.isdir(p):
                    for item in os.listdir(p):
                        ip = os.path.join(p, item)
                        if os.path.isfile(ip):
                            ev = organize_file(ip, target_base, allow_new)
                            if ev and ev.get('status') == 'success':
                                events.append(ev)
            if events:
                self.handle_background_events(events)
            else:
                UIBridge.post(lambda: FluidAnimator.show_toast(
                    self,
                    "Sürükle & Bırak",
                    "Bırakılan öğeler zaten düzenli veya taşınmaya uygun değil.",
                    theme_mode=self.theme_mode,
                    level='warning'
                ))

        threading.Thread(target=run_drop, daemon=True).start()

    def update_status_footer(self):
        if not hasattr(self, 'lbl_watch_state'):
            return
        try:
            if not self.lbl_watch_state.winfo_exists():
                return
            c = lambda token: FluentTheme.c(token, self.theme_mode)
            summary = self.watcher.get_status_summary()

            if summary['is_active']:
                self.lbl_watch_state.configure(text="🟢 İzleme Aktif", text_color=c('success'))
            else:
                self.lbl_watch_state.configure(text="⏸️ İzleme Duraklatıldı", text_color=c('warning'))

            self.lbl_watch_folders.configure(text=f"İzlenen Klasör: {summary['monitored_count']}")
            self.lbl_last_scan.configure(text=f"Son Tarama: {summary['last_scan']}")
        except Exception:
            pass

    def _periodic_status_update(self):
        self.update_status_footer()
        self.after(5000, self._periodic_status_update)

    # --- SİSTEM TEPSİSİ (SYSTEM TRAY) ---
    def _create_tray_image(self):
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(image)
        d.rounded_rectangle((4, 12, 60, 54), radius=8, fill=(0, 120, 212))
        d.polygon([(4, 18), (26, 18), (32, 10), (8, 10)], fill=(96, 205, 255))
        return image

    def _init_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Uygulamayı Aç", self.show_window_from_tray, default=True),
            pystray.MenuItem("Şimdi Tara", lambda icon, item: self.trigger_manual_scan()),
            pystray.MenuItem("Folders Klasörünü Aç", lambda icon, item: self.open_target_folder()),
            pystray.MenuItem("Çıkış", self.quit_app)
        )
        self.tray_icon = pystray.Icon("SmartFileOrganizer", self._create_tray_image(), "Smart File Organizer v2.1", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.withdraw()

    def show_window_from_tray(self, icon=None, item=None):
        """Arka planda veya sistem tepsisinde olan pencereyi ekranın en önüne getirir."""
        def _restore():
            try:
                self.deiconify()
                self.state('normal')
                self.lift()
                self.focus_force()
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        UIBridge.post(_restore)

    def quit_app(self, icon=None, item=None):
        FluidAnimator.cancel_all()
        UIBridge.stop()
        self.watcher.stop()
        if self._ipc_server:
            try:
                self._ipc_server.close()
            except Exception:
                pass
        if self.tray_icon:
            self.tray_icon.stop()
        self.quit()
        sys.exit(0)


def main():
    # Eğer arka planda zaten çalışan bir örnek varsa onu öne getir ve çık
    if notify_existing_instance():
        sys.exit(0)

    start_min = "--minimized" in sys.argv
    app = SmartFileOrganizerApp(start_minimized=start_min)
    app.mainloop()


if __name__ == "__main__":
    main()

