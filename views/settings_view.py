import customtkinter as ctk
from tkinter import messagebox
from theme import FluentTheme
from config import save_config, set_startup, refresh_desktop_baseline, APP_VERSION
from animation import FluidAnimator


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
            text="Ayarlar ve Erişilebilirlik (Settings)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Görünüm temasını, Fluent animasyon düzeyini, sistem başlangıcını ve masaüstü korumasını yapılandırın",
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
        theme_card.pack(fill="x", pady=6)
        FluidAnimator.bind_card_hover(theme_card, self.theme_mode)

        inner_t = ctk.CTkFrame(theme_card, fg_color="transparent")
        inner_t.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_t, text="🎨 Uygulama Teması (Fluent Theme)", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            inner_t,
            values=["Koyu (Dark)", "Açık (Light)"],
            width=170,
            height=30,
            corner_radius=6,
            command=self._on_theme_change
        )
        self.theme_menu.pack(side="right")
        self.theme_menu.set("Açık (Light)" if self.theme_mode == 'light' else "Koyu (Dark)")

        # 2. Kart: Animasyon ve Erişilebilirlik (Motion & Accessibility)
        motion_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        motion_card.pack(fill="x", pady=6)
        FluidAnimator.bind_card_hover(motion_card, self.theme_mode)

        inner_m = ctk.CTkFrame(motion_card, fg_color="transparent")
        inner_m.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            inner_m,
            text="✨ Animasyon ve Hareket Tercihleri (Motion & Accessibility)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        row_anim = ctk.CTkFrame(inner_m, fg_color="transparent")
        row_anim.pack(fill="x", pady=4)

        anim_text_box = ctk.CTkFrame(row_anim, fg_color="transparent")
        anim_text_box.pack(side="left")
        ctk.CTkLabel(anim_text_box, text="Arayüz Animasyon Düzeyi", font=ctk.CTkFont(size=13, weight="bold"), text_color=c('text_primary')).pack(anchor="w")
        ctk.CTkLabel(anim_text_box, text="Sayfa geçişleri, sayaçlar, kart efektleri ve bildirim animasyonlarının yoğunluğu.", font=ctk.CTkFont(size=11), text_color=c('text_secondary')).pack(anchor="w")

        self.anim_menu = ctk.CTkOptionMenu(
            row_anim,
            values=[
                "Tam Animasyonlar (Full)",
                "Azaltılmış Animasyonlar (Reduced)",
                "Devre Dışı (Disabled)"
            ],
            width=235,
            height=30,
            corner_radius=6,
            command=self._on_animation_mode_change
        )
        self.anim_menu.pack(side="right")

        cur_anim = self.app.cfg.get('animation_mode', 'full')
        if cur_anim == 'reduced':
            self.anim_menu.set("Azaltılmış Animasyonlar (Reduced)")
        elif cur_anim == 'disabled':
            self.anim_menu.set("Devre Dışı (Disabled)")
        else:
            self.anim_menu.set("Tam Animasyonlar (Full)")

        self.sw_sys_motion = ctk.CTkSwitch(
            inner_m,
            text="Windows 'Azaltılmış Hareket' (Accessibility) ayarını otomatik izle",
            font=ctk.CTkFont(size=12),
            command=self._on_sys_motion_toggle
        )
        self.sw_sys_motion.pack(anchor="w", pady=(8, 2))
        if self.app.cfg.get('respect_system_motion', True):
            self.sw_sys_motion.select()

        # 3. Kart: Sistem ve Bildirimler
        sys_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        sys_card.pack(fill="x", pady=6)
        FluidAnimator.bind_card_hover(sys_card, self.theme_mode)

        inner_s = ctk.CTkFrame(sys_card, fg_color="transparent")
        inner_s.pack(fill="x", padx=16, pady=14)

        self.sw_startup = ctk.CTkSwitch(
            inner_s,
            text="Windows Başlangıcında Otomatik Çalıştır (Arka Planda)",
            font=ctk.CTkFont(size=13),
            command=self._on_startup_toggle
        )
        self.sw_startup.pack(anchor="w", pady=6)
        if self.app.cfg.get('run_on_startup', False):
            self.sw_startup.select()

        self.sw_notif = ctk.CTkSwitch(
            inner_s,
            text="Uygulama İçi Akıllı Bildirimleri (Toast) Göster",
            font=ctk.CTkFont(size=13),
            command=self._on_notif_toggle
        )
        self.sw_notif.pack(anchor="w", pady=6)
        if self.app.cfg.get('notifications', True):
            self.sw_notif.select()

        self.sw_new_cat = ctk.CTkSwitch(
            inner_s,
            text="AI Motorunun Alt Klasörleri Otomatik Oluşturmasına İzin Ver",
            font=ctk.CTkFont(size=13),
            command=self._on_new_cat_toggle
        )
        self.sw_new_cat.pack(anchor="w", pady=6)
        if self.app.cfg.get('allow_new_categories', True):
            self.sw_new_cat.select()

        # 4. Kart: Masaüstü Koruma Yönetimi
        base_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        base_card.pack(fill="x", pady=6)
        FluidAnimator.bind_card_hover(base_card, self.theme_mode)

        inner_b = ctk.CTkFrame(base_card, fg_color="transparent")
        inner_b.pack(fill="x", padx=16, pady=14)

        left_b = ctk.CTkFrame(inner_b, fg_color="transparent")
        left_b.pack(side="left")

        ctk.CTkLabel(
            left_b,
            text="🛡️ Masaüstü Koruma Listesini Güncelle",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        baseline_cnt = len(self.app.cfg.get('desktop_baseline', []))
        self.lbl_base_info = ctk.CTkLabel(
            left_b,
            text=f"Şu an masaüstünüzdeki {baseline_cnt} mevcut dosya/klasör taşınmaya karşı korumalıdır.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        )
        self.lbl_base_info.pack(anchor="w")

        ctk.CTkButton(
            inner_b,
            text="Şu Anki Masaüstünü Koru",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=32,
            corner_radius=6,
            command=self._refresh_baseline
        ).pack(side="right")

        # 5. Kart: Klavye Kısayolları Rehberi
        kb_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        kb_card.pack(fill="x", pady=6)
        FluidAnimator.bind_card_hover(kb_card, self.theme_mode)

        inner_kb = ctk.CTkFrame(kb_card, fg_color="transparent")
        inner_kb.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(inner_kb, text="⌨️ Klavye Kısayolları ve Hızlı Etkileşim", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 6))

        shortcuts = [
            ("Ctrl + K", "Hızlı Komut Paletini (Command Palette) açar / kapatır"),
            ("Ctrl + F", "Üst bardaki genel arama kutusuna odaklanır"),
            ("F5", "Aktif sayfanın verilerini ve önbelleğini anında yeniler"),
            ("Esc", "Açık olan Komut Paleti, Bildirim Merkezi veya Bağlam Menüsünü kapatır"),
            ("Sağ Tık", "Dosya ve klasör satırlarında hızlı işlem menüsünü açar")
        ]
        for key_combo, desc in shortcuts:
            r = ctk.CTkFrame(inner_kb, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(
                r,
                text=key_combo,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=c('accent_light'),
                fg_color=c('bg_secondary'),
                corner_radius=4,
                width=90,
                padx=6,
                pady=2
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(r, text=desc, font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")

        # 6. Kart: Hakkında
        about_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        about_card.pack(fill="x", pady=6)

        inner_a = ctk.CTkFrame(about_card, fg_color="transparent")
        inner_a.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner_a,
            text=f"Smart File Organizer v{APP_VERSION} — Windows 11 Fluent Motion & AI File Intelligence System",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=c('accent_light')
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner_a,
            text="Masaüstünüzdeki Folders yapısını bozmadan dosyalarınızı yapay zekâ ve içerik analiziyle korur.",
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        ).pack(anchor="w")

    def _on_theme_change(self, val):
        mode = 'light' if "Açık" in val else 'dark'
        self.app.change_theme(mode)

    def _on_animation_mode_change(self, val):
        if "Azaltılmış" in val:
            mode = 'reduced'
        elif "Devre Dışı" in val:
            mode = 'disabled'
        else:
            mode = 'full'
        self.app.cfg['animation_mode'] = mode
        save_config(self.app.cfg)
        FluidAnimator.set_animation_mode(mode)
        FluidAnimator.show_toast(
            self.app,
            "Animasyon Tercihi Güncellendi",
            f"Etkin mod: {val}",
            theme_mode=self.theme_mode,
            duration_ms=2200,
            level='success'
        )

    def _on_sys_motion_toggle(self):
        self.app.cfg['respect_system_motion'] = bool(self.sw_sys_motion.get())
        save_config(self.app.cfg)
        FluidAnimator.set_animation_mode(None)

    def _on_startup_toggle(self):
        en = bool(self.sw_startup.get())
        if set_startup(en):
            self.app.cfg['run_on_startup'] = en
            save_config(self.app.cfg)

    def _on_notif_toggle(self):
        self.app.cfg['notifications'] = bool(self.sw_notif.get())
        save_config(self.app.cfg)

    def _on_new_cat_toggle(self):
        self.app.cfg['allow_new_categories'] = bool(self.sw_new_cat.get())
        save_config(self.app.cfg)

    def _refresh_baseline(self):
        cnt = refresh_desktop_baseline(self.app.cfg)
        self.lbl_base_info.configure(text=f"Şu an masaüstünüzdeki {cnt} mevcut dosya/klasör taşınmaya karşı korumalıdır.")
        messagebox.showinfo("Güncellendi", f"Masaüstünüzdeki mevcut {cnt} öğe koruma listesine kaydedildi.")
