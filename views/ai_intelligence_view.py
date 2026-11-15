"""
AI File Intelligence Studio (V2.1 — Premium Glass Edition)
Deep inspection of file content, metadata, semantic tags, and classification confidence
in a 2-column Bento Glass layout.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme
from glass_engine import GlassArtEngine
from intelligence import AIFileIntelligence
from organizer import organize_file
from animation import FluidAnimator


class AIIntelligenceView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.current_analysis = None
        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # 1. Üst Cam Başlık ve Dosya Seçici Kartı
        top_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        top_card.pack(fill="x", padx=12, pady=(6, 12))
        FluidAnimator.bind_card_hover(top_card, self.theme_mode)

        inner_top = ctk.CTkFrame(top_card, fg_color="transparent")
        inner_top.pack(fill="x", padx=18, pady=14)

        orb = GlassArtEngine.get_glass_orb(40, c('accent_violet'), self.theme_mode)
        ctk.CTkLabel(
            inner_top,
            text="🧠",
            image=orb,
            compound="center",
            font=ctk.CTkFont(size=18),
            width=40,
            height=40
        ).pack(side="left", padx=(0, 12))

        title_col = ctk.CTkFrame(inner_top, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text="AI Dosya Zekâsı Stüdyosu (Intelligence Center)",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=21, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Dosyaları içerik, metadata, boyut ve anlamsal etiket düzeyinde derinlemesine inceleyin.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        ctk.CTkButton(
            inner_top,
            text="🔬 Dosya Seç ve Analiz Et",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            height=36,
            corner_radius=9,
            command=self._select_and_analyze
        ).pack(side="right")

        # 2. Sonuç Alanı (Scrollable)
        self.result_container = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        self.result_container.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        try:
            self.result_container._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        if self.current_analysis:
            self._render_analysis(self.current_analysis[0], self.current_analysis[1])
        else:
            self._show_empty_state()

    def _show_empty_state(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.result_container.winfo_children():
            w.destroy()

        card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=16,
            border_width=1,
            border_color=c('border')
        )
        card.pack(fill="x", pady=20, padx=6)
        FluidAnimator.bind_card_hover(card, self.theme_mode)

        ctk.CTkLabel(
            card,
            text="🧠\n\nİncelemek istediğiniz dosyayı yukarıdan seçin veya doğrudan pencereye sürükleyin.\nAI File Intelligence motoru dosyanın adını, içeriğini, uzantısını ve teknik metadatasını analiz edecektir.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary'),
            justify="center"
        ).pack(pady=48, padx=24)

    def _select_and_analyze(self):
        f = filedialog.askopenfilename(title="Analiz Edilecek Dosyayı Seçin")
        if f:
            self.analyze_file(f)

    def analyze_file(self, file_path):
        if not os.path.exists(file_path):
            return

        target_base = self.app.cfg.get('target', '')
        res = AIFileIntelligence.analyze(file_path, target_base)
        self.current_analysis = (file_path, res)
        self._render_analysis(file_path, res)

    def _render_analysis(self, file_path, res):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.result_container.winfo_children():
            w.destroy()

        fname = os.path.basename(file_path)
        badge_txt, icon_ch, badge_fg, badge_bg = FluentTheme.file_badge_style(fname, self.theme_mode)

        # Üst Dosya Kimlik & Güven Skoru Cam Kartı
        summary_card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        summary_card.pack(fill="x", pady=(4, 12), padx=4)
        FluidAnimator.bind_card_hover(summary_card, self.theme_mode)

        inner_sum = ctk.CTkFrame(summary_card, fg_color="transparent")
        inner_sum.pack(fill="x", padx=18, pady=16)

        header_line = ctk.CTkFrame(inner_sum, fg_color="transparent")
        header_line.pack(fill="x")

        ctk.CTkLabel(
            header_line,
            text=f"{icon_ch} {badge_txt}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=badge_fg,
            fg_color=badge_bg,
            corner_radius=6,
            padx=8,
            pady=3
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header_line,
            text=fname,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        conf_pct = int(res.get('confidence', 0.9) * 100)
        conf_col = c('success') if conf_pct >= 85 else c('warning')
        ctk.CTkLabel(
            header_line,
            text=f"✨ AI Güven Skoru: %{conf_pct}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=conf_col,
            fg_color=c('success_bg') if conf_pct >= 85 else c('warning_bg'),
            corner_radius=6,
            padx=10,
            pady=3
        ).pack(side="right")

        pbar = ctk.CTkProgressBar(inner_sum, height=8, corner_radius=4, fg_color=c('bg_card_secondary'))
        pbar.pack(fill="x", pady=(10, 12))
        pbar.set(0.0)
        pbar.configure(progress_color=c('accent'))
        FluidAnimator.animate_progress(pbar, float(res.get('confidence', 0.9)), duration_ms=FluidAnimator.TIMING_COMPLEX, start_val=0.0)

        # 2 Sütunlu Bento Grid: Sol Sınıflandırma & Etiketler | Sağ Teknik Metadata
        bento = ctk.CTkFrame(self.result_container, fg_color="transparent")
        bento.pack(fill="x", pady=(0, 12), padx=4)
        bento.grid_columnconfigure(0, weight=1, uniform="ai_col")
        bento.grid_columnconfigure(1, weight=1, uniform="ai_col")

        # Sol Kart: Sınıflandırma ve Anlamsal Etiketler
        left_card = ctk.CTkFrame(bento, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        FluidAnimator.bind_card_hover(left_card, self.theme_mode)

        in_left = ctk.CTkFrame(left_card, fg_color="transparent")
        in_left.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(in_left, text="🎯 AI Sınıflandırma Rotası", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        info_rows = [
            ("Tespit Edilen Tür:", res.get('detected_type', '-')),
            ("Ana Kategori:", res.get('category', '-')),
            ("Alt Kategori:", res.get('subcategory', '-')),
            ("Hedef Konum:", res.get('target_rel_path', '-')),
            ("AI Gerekçesi:", res.get('reasoning', '-'))
        ]
        for label, val in info_rows:
            row = ctk.CTkFrame(in_left, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted'), width=125, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(val), font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_primary'), anchor="w", wraplength=240, justify="left").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(in_left, text="🏷️ Anlamsal Etiketler (Semantic Tags):", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('accent_violet_light')).pack(anchor="w", pady=(12, 6))

        tag_box = ctk.CTkFrame(in_left, fg_color="transparent")
        tag_box.pack(fill="x")
        for tag in res.get('tags', []):
            ctk.CTkLabel(
                tag_box,
                text=f" #{tag} ",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('bg_card_secondary'),
                text_color=c('accent_light'),
                corner_radius=8,
                padx=8,
                pady=3
            ).pack(side="left", padx=3, pady=2)

        # Sağ Kart: Teknik Dosya Metadata Bilgileri
        right_card = ctk.CTkFrame(bento, fg_color=c('bg_card'), corner_radius=14, border_width=1, border_color=c('border'))
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        FluidAnimator.bind_card_hover(right_card, self.theme_mode)

        in_right = ctk.CTkFrame(right_card, fg_color="transparent")
        in_right.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(in_right, text="📊 Teknik Dosya Metadatası", font=ctk.CTkFont(size=14, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 8))

        meta = res.get('metadata', {})
        for k, v in meta.items():
            if k == 'error':
                continue
            row = ctk.CTkFrame(in_right, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=str(k), font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted'), width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=11), text_color=c('text_secondary'), anchor="w").pack(side="left")

        # Alt Aksiyon Butonu
        ctk.CTkButton(
            self.result_container,
            text="⚡ Bu Dosyayı Şimdi Folders İçine Organize Et",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            height=40,
            corner_radius=10,
            command=lambda: self._execute_move(file_path)
        ).pack(fill="x", padx=4, pady=(4, 16))

    def _execute_move(self, file_path):
        target_base = self.app.cfg.get('target', '')
        res = organize_file(file_path, target_base)
        if res and res.get('status') == 'success':
            self.current_analysis = None
            self.app.handle_background_events([res])
            self._show_empty_state()
