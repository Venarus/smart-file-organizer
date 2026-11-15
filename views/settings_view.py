"""
Settings & Glass Customization Studio (V2.1 — Premium Glass Edition)
Allows live control of Windows 11 DWM Acrylic/Glass Opacity (85% - 100%),
Midnight/Crystal Themes, Fluent Motion Modes, Windows Startup, and Desktop Baseline Protection.
"""

import customtkinter as ctk
from tkinter import messagebox
from theme import FluentTheme
from glass_engine import GlassArtEngine
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

        # Üst Cam Başlık Kartı
        top_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        top_card.pack(fill="x", padx=12, pady=(6, 10))
        FluidAnimator.bind_card_hover(top_card, self.theme_mode)

        top_inner = ctk.CTkFrame(top_card, fg_color="transparent")
        top_inner.pack(fill="x", padx=18, pady=14)

        orb = GlassArtEngine.get_glass_orb(38, c('accent'), self.theme_mode)
        ctk.CTkLabel(top_inner, text="⚙️", image=orb, compound="center", font=ctk.CTkFont(size=17), width=38, height=38).pack(side="left", padx=(0, 12))

        title_col = ctk.CTkFrame(top_inner, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="Ayarlar, Şeffaf Cam (Acrylic) ve Erişilebilirlik",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=21, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Windows 11 DWM cam şeffaflığını, görünüm temasını, animasyon düzeyini ve güvenlik tercihlerini yönetin",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        try:
            scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # 1. Kart: Cam Şeffaflığı (Acrylic Glass Transparency) ve Tema
        glass_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        glass_card.pack(fill="x", pady=6, padx=4)
        FluidAnimator.bind_card_hover(glass_card, self.theme_mode)

        inner_g = ctk.CTkFrame(glass_card, fg_color="transparent")
        inner_g.pack(fill="x", padx=18, pady=16)

        ctk.CTkLabel(
            inner_g,
            text="💎 Windows 11 Cam Şeffaflığı (Acrylic Glass) ve Görünüm",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 10))

        # Tema Satırı
        row_t = ctk.CTkFrame(inner_g, fg_color="transparent")
        row_t.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(row_t, text="🎨 Görsel Cam Teması", font=ctk.CTkFont(size=13, weight="bold"), text_color=c('text_primary')).pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            row_t,
            values=["Gece Camı (Midnight Glass)", "Kristal Açık (Crystal Light)"],
            width=235,
            height=32,
            corner_radius=8,
            fg_color=c('bg_card_secondary'),
            button_color=c('accent'),
            button_hover_color=c('accent_hover'),
            text_color=c('text_primary'),
            command=self._on_theme_change
        )
        self.theme_menu.pack(side="right")
        self.theme_menu.set("Kristal Açık (Crystal Light)" if self.theme_mode == 'light' else "Gece Camı (Midnight Glass)")

        # Şeffaflık Kaydırıcısı Satırı
        row_op = ctk.CTkFrame(inner_g, fg_color="transparent")
        row_op.pack(fill="x", pady=4)

        cur_op = float(self.app.cfg.get('glass_opacity', 0.95))
        self.lbl_op_val = ctk.CTkLabel(
            row_op,
            text=f"Pencere Cam Opaklığı (Masaüstü Arka Plan Geçirgenliği): %{int(round(cur_op * 100))}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=c('accent_light')
        )
        self.lbl_op_val.pack(side="left")

        self.op_slider = ctk.CTkSlider(
            row_op,
            from_=0.85,
            to=1.00,
            number_of_steps=15,
            width=235,
            progress_color=c('accent'),
            button_color=c('accent_light'),
            button_hover_color=c('accent_hover'),
            command=self._on_opacity_slider
        )
        self.op_slider.set(cur_op)
        self.op_slider.pack(side="right")

        # 2. Kart: Animasyon ve Erişilebilirlik
        motion_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        motion_card.pack(fill="x", pady=6, padx=4)
        FluidAnimator.bind_card_hover(motion_card, self.theme_mode)

        inner_m = ctk.CTkFrame(motion_card, fg_color="transparent")
        inner_m.pack(fill="x", padx=18, pady=16)

        ctk.CTkLabel(
            inner_m,
            text="✨ Animasyon ve Hareket Tercihleri (Fluent Motion & Accessibility)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        row_anim = ctk.CTkFrame(inner_m, fg_color="transparent")
        row_anim.pack(fill="x", pady=4)

        anim_text_box = ctk.CTkFrame(row_anim, fg_color="transparent")
        anim_text_box.pack(side="left")
        ctk.CTkLabel(anim_text_box, text="Arayüz Animasyon Düzeyi", font=ctk.CTkFont(size=13, weight="bold"), text_color=c('text_primary')).pack(anchor="w")
        ctk.CTkLabel(anim_text_box, text="Sayfa geçişleri, cam kart parlamaları, sayaçlar ve bildirim animasyonları.", font=ctk.CTkFont(size=11), text_color=c('text_secondary')).pack(anchor="w")

        self.anim_menu = ctk.CTkOptionMenu(
            row_anim,
            values=[
                "Tam Animasyonlar (Full)",
                "Azaltılmış Animasyonlar (Reduced)",
                "Devre Dışı (Disabled)"
            ],
            width=235,
            height=32,
            corner_radius=8,
            fg_color=c('bg_card_secondary'),
            button_color=c('accent'),
            button_hover_color=c('accent_hover'),
            text_color=c('text_primary'),
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
            progress_color=c('accent'),
            command=self._on_sys_motion_toggle
        )
        self.sw_sys_motion.pack(anchor="w", pady=(8, 2))
        if self.app.cfg.get('respect_system_motion', True):
            self.sw_sys_motion.select()

        # 3. Kart: Sistem ve Bildirimler
        sys_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        sys_card.pack(fill="x", pady=6, padx=4)
        FluidAnimator.bind_card_hover(sys_card, self.theme_mode)

        inner_s = ctk.CTkFrame(sys_card, fg_color="transparent")
        inner_s.pack(fill="x", padx=18, pady=16)

        ctk.CTkLabel(inner_s, text="🚀 Sistem Entegrasyonu ve Otomasyon Davranışı", font=ctk.CTkFont(size=15, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        self.sw_startup = ctk.CTkSwitch(
            inner_s,
            text="Windows Başlangıcında Otomatik Çalıştır (Arka Planda)",
            font=ctk.CTkFont(size=13),
            progress_color=c('accent'),
            command=self._on_startup_toggle
        )
        self.sw_startup.pack(anchor="w", pady=6)
        if self.app.cfg.get('run_on_startup', False):
            self.sw_startup.select()

        self.sw_notif = ctk.CTkSwitch(
            inner_s,
            text="Uygulama İçi Akıllı Cam Bildirimlerini (Toast) Göster",
            font=ctk.CTkFont(size=13),
            progress_color=c('accent'),
            command=self._on_notif_toggle
        )
        self.sw_notif.pack(anchor="w", pady=6)
        if self.app.cfg.get('notifications', True):
            self.sw_notif.select()

        self.sw_new_cat = ctk.CTkSwitch(
            inner_s,
            text="AI Motorunun Alt Klasörleri Otomatik Oluşturmasına İzin Ver",
            font=ctk.CTkFont(size=13),
            progress_color=c('accent'),
            command=self._on_new_cat_toggle
        )
        self.sw_new_cat.pack(anchor="w", pady=6)
        if self.app.cfg.get('allow_new_categories', True):
            self.sw_new_cat.select()

        # 4. Kart: Masaüstü Koruma Yönetimi
        base_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        base_card.pack(fill="x", pady=6, padx=4)
        FluidAnimator.bind_card_hover(base_card, self.theme_mode)

        inner_b = ctk.CTkFrame(base_card, fg_color="transparent")
        inner_b.pack(fill="x", padx=18, pady=16)

        left_b = ctk.CTkFrame(inner_b, fg_color="transparent")
        left_b.pack(side="left")

        ctk.CTkLabel(
            left_b,
            text="🛡️ Masaüstü Koruma Kalkanını Güncelle",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        baseline_cnt = len(self.app.cfg.get('desktop_baseline', []))
        self.lbl_base_info = ctk.CTkLabel(
            left_b,
            text=f"Şu an masaüstünüzdeki {baseline_cnt} mevcut dosya/klasör taşınmaya karşı kilitlidir ve korunmaktadır.",
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
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._refresh_baseline
        ).pack(side="right")

        # 5. Kart: Klavye Kısayolları Rehberi
        kb_card = ctk.CTkFrame(scroll, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        kb_card.pack(fill="x", pady=6, padx=4)
        FluidAnimator.bind_card_hover(kb_card, self.theme_mode)

        inner_kb = ctk.CTkFrame(kb_card, fg_color="transparent")
        inner_kb.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(inner_kb, text="⌨️ Klavye Kısayolları ve Hızlı Etkileşim", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        shortcuts = [
            ("Ctrl + K", "Hızlı Komut Paletini (Command Palette) açar / kapatır"),
            ("Ctrl + F", "Üst bardaki genel arama kutusuna odaklanır"),
            ("F5", "Aktif sayfanın verilerini ve önbelleğini anında yeniler"),
            ("Esc", "Açık olan Komut Paleti, Bildirim Merkezi veya Bağlam Menüsünü kapatır"),
            ("Sağ Tık", "Dosya ve klasör satırlarında yarı-saydam hızlı işlem menüsünü açar")
        ]
        for key_combo, desc in shortcuts:
            r = ctk.CTkFrame(inner_kb, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(
                r,
                text=key_combo,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=c('accent_light'),
                fg_color=c('bg_card_secondary'),
                corner_radius=5,
                width=94,
                padx=6,
                pady=2
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(r, text=desc, font=ctk.CTkFont(size=12), text_color=c('text_secondary')).pack(side="left")

    def _on_theme_change(self, val):
        mode = 'light' if ("Kristal" in val or "Açık" in val) else 'dark'
        self.app.change_theme(mode)

    def _on_opacity_slider(self, val):
        pct = int(round(float(val) * 100))
        self.lbl_op_val.configure(text=f"Pencere Cam Opaklığı (Masaüstü Arka Plan Geçirgenliği): %{pct}")
        self.app.set_glass_opacity(val)

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
        self.lbl_base_info.configure(text=f"Şu an masaüstünüzdeki {cnt} mevcut dosya/klasör taşınmaya karşı kilitlidir ve korunmaktadır.")
        messagebox.showinfo("Güncellendi", f"Masaüstünüzdeki mevcut {cnt} öğe koruma listesine kaydedildi.")
