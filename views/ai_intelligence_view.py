import os
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme
from intelligence import AIFileIntelligence
from organizer import organize_file

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

        # Başlık
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(10, 14))

        ctk.CTkLabel(
            title_box,
            text="AI Dosya Zekâsı (Intelligence Center)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Dosyaları derinlemesine analiz edin; içerik, metadata ve anlamsal ilişkileri inceleyin.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Dosya Seçim & Analiz Butonu
        select_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        select_card.pack(fill="x", padx=16, pady=(0, 16))

        inner_sel = ctk.CTkFrame(select_card, fg_color="transparent")
        inner_sel.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner_sel,
            text="🔬 İncelemek İstediğiniz Dosyayı Seçin:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            inner_sel,
            text="Dosya Seç ve Analiz Et",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=32,
            corner_radius=6,
            command=self._select_and_analyze
        ).pack(side="right")

        # Sonuç Alanı (Scrollable)
        self.result_container = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.result_container.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.result_container._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # Başlangıç Boş Durum Bilgisi
        self._show_empty_state()

    def _show_empty_state(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.result_container.winfo_children():
            w.destroy()

        card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        card.pack(fill="x", pady=20)

        ctk.CTkLabel(
            card,
            text="🧠\n\nYukarıdan bir dosya seçin veya pencereye sürükleyin.\nAI Zekâsı dosyanın adını, içeriğini, uzantısını, boyutunu ve metadata verilerini tarayacaktır.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_muted'),
            justify="center"
        ).pack(pady=40)

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

        # 1. Kart: Özet & Güven Skoru
        summary_card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        summary_card.pack(fill="x", pady=(0, 12))

        inner_sum = ctk.CTkFrame(summary_card, fg_color="transparent")
        inner_sum.pack(fill="x", padx=16, pady=16)

        header_line = ctk.CTkFrame(inner_sum, fg_color="transparent")
        header_line.pack(fill="x")

        ctk.CTkLabel(
            header_line,
            text=f"📄 {os.path.basename(file_path)}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        conf_pct = int(res['confidence'] * 100)
        ctk.CTkLabel(
            header_line,
            text=f"AI Güven Oranı: %{conf_pct}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('success') if conf_pct >= 85 else c('warning')
        ).pack(side="right")

        # İlerleme çubuğu
        pbar = ctk.CTkProgressBar(inner_sum, height=8, corner_radius=4)
        pbar.pack(fill="x", pady=(8, 12))
        pbar.set(res['confidence'])
        pbar.configure(progress_color=c('accent'))

        # Bilgi Satırları
        info_rows = [
            ("Tespit Edilen Tür:", res.get('detected_type', '-')),
            ("Ana Kategori:", res.get('category', '-')),
            ("Alt Kategori:", res.get('subcategory', '-')),
            ("Hedef Yol:", res.get('target_rel_path', '-')),
            ("AI Gerekçesi:", res.get('reasoning', '-'))
        ]

        for label, val in info_rows:
            row = ctk.CTkFrame(inner_sum, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary'), width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=12), text_color=c('text_primary'), anchor="w").pack(side="left", fill="x", expand=True)

        # 2. Kart: Anlamsal Etiketler (Tags)
        tags_card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        tags_card.pack(fill="x", pady=(0, 12))

        inner_tags = ctk.CTkFrame(tags_card, fg_color="transparent")
        inner_tags.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner_tags,
            text="🏷️ Çıkarılan Anlamsal Etiketler:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        tag_box = ctk.CTkFrame(inner_tags, fg_color="transparent")
        tag_box.pack(fill="x")

        for tag in res.get('tags', []):
            pill = ctk.CTkLabel(
                tag_box,
                text=f" #{tag} ",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('bg_mica'),
                text_color=c('accent_light'),
                corner_radius=12,
                padx=8,
                pady=4
            )
            pill.pack(side="left", padx=4, pady=2)

        # 3. Kart: Metadata Ayrıntıları
        meta_card = ctk.CTkFrame(
            self.result_container,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        meta_card.pack(fill="x", pady=(0, 12))

        inner_meta = ctk.CTkFrame(meta_card, fg_color="transparent")
        inner_meta.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner_meta,
            text="📊 Teknik Dosya Metadata Bilgileri:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 6))

        meta = res.get('metadata', {})
        for k, v in meta.items():
            if k == 'error': continue
            row = ctk.CTkFrame(inner_meta, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=str(k), font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted'), width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=11), text_color=c('text_secondary'), anchor="w").pack(side="left")

        # Aksiyon: Hemen Taşı
        ctk.CTkButton(
            self.result_container,
            text="⚡ Bu Dosyayı Şimdi Folders İçine Düzenle",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=36,
            corner_radius=8,
            command=lambda: self._execute_move(file_path)
        ).pack(fill="x", pady=(4, 16))

    def _execute_move(self, file_path):
        target_base = self.app.cfg.get('target', '')
        res = organize_file(file_path, target_base)
        if res and res.get('status') == 'success':
            self.app.handle_background_events([res])
            self._show_empty_state()
