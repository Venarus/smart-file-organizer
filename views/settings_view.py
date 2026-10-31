import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from theme import FluentTheme
from config import save_config, set_windows_startup, get_desktop_current_items

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # Başlık
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(10, 14))

        ctk.CTkLabel(
            title_box,
            text="Ayarlar (Settings)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Uygulama görünümü, Windows başlangıç seçenekleri ve güvenlik tercihleri",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # 1. Kart: Tema ve Görünüm
        theme_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        theme_card.pack(fill="x", pady=(0, 12))

        inner_theme = ctk.CTkFrame(theme_card, fg_color="transparent")
        inner_theme.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_theme, text="🎨 Tema ve Görünüm (Windows 11 Fluent Design)", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        theme_row = ctk.CTkFrame(inner_theme, fg_color="transparent")
        theme_row.pack(fill="x")

        ctk.CTkLabel(theme_row, text="Uygulama Teması:", font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_row,
            values=["Koyu Tema (Dark)", "Açık Tema (Light)"],
            width=170,
            height=28,
            corner_radius=6,
            command=self._on_theme_select
        )
        self.theme_menu.pack(side="right")
        current_m = self.app.cfg.get('theme_mode', 'dark')
        self.theme_menu.set("Koyu Tema (Dark)" if current_m == 'dark' else "Açık Tema (Light)")

        # 2. Kart: Windows Entegrasyonu
        win_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        win_card.pack(fill="x", pady=(0, 12))

        inner_win = ctk.CTkFrame(win_card, fg_color="transparent")
        inner_win.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_win, text="🖥️ Windows Entegrasyonu", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        # Windows ile Başlat
        row_startup = ctk.CTkFrame(inner_win, fg_color="transparent")
        row_startup.pack(fill="x", pady=4)
        ctk.CTkLabel(row_startup, text="Windows Açıldığında Otomatik Başlat:", font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")
        self.switch_start = ctk.CTkSwitch(row_startup, text="", command=self._toggle_startup)
        self.switch_start.pack(side="right")
        if self.app.cfg.get('start_with_windows', False): self.switch_start.select()
        else: self.switch_start.deselect()

        # Sistem Tepsisine Küçült
        row_tray = ctk.CTkFrame(inner_win, fg_color="transparent")
        row_tray.pack(fill="x", pady=4)
        ctk.CTkLabel(row_tray, text="Pencere Kapatıldığında Sistem Tepsisine Küçült:", font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")
        self.switch_tray = ctk.CTkSwitch(row_tray, text="", command=self._toggle_tray)
        self.switch_tray.pack(side="right")
        if self.app.cfg.get('minimize_to_tray_on_close', True): self.switch_tray.select()
        else: self.switch_tray.deselect()

        # 3. Kart: Masaüstü Koruması & Klasörler
        safe_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        safe_card.pack(fill="x", pady=(0, 12))

        inner_safe = ctk.CTkFrame(safe_card, fg_color="transparent")
        inner_safe.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_safe, text="🛡️ Masaüstü ve Hedef Güvenliği", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        # Yeni Kategori İzni
        row_cat = ctk.CTkFrame(inner_safe, fg_color="transparent")
        row_cat.pack(fill="x", pady=4)
        ctk.CTkLabel(row_cat, text="Gerektiğinde Yeni Kategori Klasörü Aç:", font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")
        self.switch_new_cat = ctk.CTkSwitch(row_cat, text="", command=self._toggle_new_cat)
        self.switch_new_cat.pack(side="right")
        if self.app.cfg.get('allow_new_categories', True): self.switch_new_cat.select()
        else: self.switch_new_cat.deselect()

        # Masaüstü Koruma Tabanı
        base_count = len(self.app.cfg.get('desktop_baseline', []))
        row_base = ctk.CTkFrame(inner_safe, fg_color="transparent")
        row_base.pack(fill="x", pady=6)
        ctk.CTkLabel(row_base, text=f"Masaüstü Koruma Listesi: {base_count} dosya/klasör korunuyor", font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")
        ctk.CTkButton(
            row_base,
            text="Koruma Listesini Yenile",
            font=ctk.CTkFont(size=11),
            fg_color=c('bg_mica'),
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            width=160,
            height=26,
            corner_radius=6,
            command=self._refresh_desktop_baseline
        ).pack(side="right")

        # 4. Kart: Hakkında
        about_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        about_card.pack(fill="x", pady=(0, 12))

        inner_ab = ctk.CTkFrame(about_card, fg_color="transparent")
        inner_ab.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_ab, text="Smart File Organizer V2", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w")
        ctk.CTkLabel(inner_ab, text="Windows 11 Fluent Design System • AI File Intelligence Engine\nVersiyon 2.0.0 — Senem Özel Derleme", font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(anchor="w", pady=(2, 0))

    def _on_theme_select(self, val):
        mode = 'light' if 'Açık' in val else 'dark'
        self.app.cfg['theme_mode'] = mode
        save_config(self.app.cfg)
        self.app.set_theme(mode)

    def _toggle_startup(self):
        en = bool(self.switch_start.get())
        self.app.cfg['start_with_windows'] = en
        save_config(self.app.cfg)
        set_windows_startup(en)

    def _toggle_tray(self):
        en = bool(self.switch_tray.get())
        self.app.cfg['minimize_to_tray_on_close'] = en
        save_config(self.app.cfg)

    def _toggle_new_cat(self):
        en = bool(self.switch_new_cat.get())
        self.app.cfg['allow_new_categories'] = en
        save_config(self.app.cfg)

    def _refresh_desktop_baseline(self):
        new_items = get_desktop_current_items()
        self.app.cfg['desktop_baseline'] = new_items
        save_config(self.app.cfg)
        messagebox.showinfo("Koruma Güncellendi", f"Masaüstündeki {len(new_items)} mevcut dosya ve klasör koruma altına alındı.")
        self._build_ui()
