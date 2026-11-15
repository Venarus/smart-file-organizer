import os
import threading
import customtkinter as ctk
from datetime import datetime
from theme import FluentTheme
from storage_analyzer import StorageAnalyzer
from security_backup import SecurityBackupEngine
from animation import FluidAnimator, UIBridge


class HomeView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self._is_loading_stats = False
        self._prev_files = 0
        self._prev_cats = 0
        self._prev_today = 0

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    @staticmethod
    def _get_activity_summary():
        history = SecurityBackupEngine.get_history(limit=500, active_only=True)
        today_prefix = datetime.now().strftime('%Y-%m-%d')
        today_cnt = sum(1 for tx in history if str(tx.get('timestamp', '')).startswith(today_prefix))
        return {'today': today_cnt, 'total': len(history)}

    def on_page_show(self):
        """Sayfa tekrar görünür olduğunda tüm bileşenleri silmeden sayaçları ve son işlemleri günceller."""
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        summary = self._get_activity_summary()
        new_today = summary.get('today', 0)

        if hasattr(self, 'lbl_today_actions') and self.lbl_today_actions.winfo_exists():
            FluidAnimator.animate_counter(
                self.lbl_today_actions,
                self._prev_today,
                new_today,
                duration_ms=FluidAnimator.TIMING_COMPLEX
            )
            self._prev_today = new_today

        target_base = self.app.cfg.get('target', '')
        cached_storage = StorageAnalyzer._cache.get(target_base)
        if cached_storage:
            self._apply_storage_stats(cached_storage)
        elif not self._is_loading_stats:
            self._is_loading_stats = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

        if hasattr(self, 'recent_container') and self.recent_container.winfo_exists():
            self._populate_recent_list(c)

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # Kaydırılabilir Ana Konteyner (Solid Mica Arka Planı ile pürüzsüz kaydırma)
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('text_muted')
        )
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(6, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # 1. Üst Karşılama & Özet Başlığı
        header_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(4, 14))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Genel Bakış",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=26, weight="bold"),
            text_color=c('text_primary')
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="AI Dosya Zekâsı Sistemi aktif ve klasörlerinizi gerçek zamanlı koruyor.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=c('text_secondary')
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # 2. İstatistik Kartları (4'lü Fluent Grid)
        stats_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats_grid.pack(fill="x", pady=(0, 18))
        for i in range(4):
            stats_grid.grid_columnconfigure(i, weight=1, uniform="stat")

        target_base = self.app.cfg.get('target', '')
        summary = self._get_activity_summary()
        cached_storage = StorageAnalyzer._cache.get(target_base)

        init_files = cached_storage.get('total_files', 0) if cached_storage else 0
        init_size = cached_storage.get('total_size_human', 'Hesaplanıyor...') if cached_storage else "Hesaplanıyor..."
        init_cats = len(cached_storage.get('categories', [])) if cached_storage else 0
        init_today = summary.get('today', 0)

        self.lbl_total_files = self._create_stat_card(stats_grid, 0, "📂", "Toplam Dosya", "0", "Folders içinde korunan", c)
        self.lbl_total_size = self._create_stat_card(stats_grid, 1, "💾", "Toplam Boyut", init_size, "Optimize edilen alan", c)
        self.lbl_categories = self._create_stat_card(stats_grid, 2, "🏷️", "Aktif Kategori", "0", "Akıllı sınıflandırma", c)
        self.lbl_today_actions = self._create_stat_card(stats_grid, 3, "⚡", "Bugün Düzenlenen", "0", f"Toplam: {summary.get('total', 0)} işlem", c)

        # Sayaçları akıcı şekilde hedef değerlere yükselt
        FluidAnimator.animate_counter(self.lbl_total_files, 0, init_files, duration_ms=FluidAnimator.TIMING_COMPLEX)
        FluidAnimator.animate_counter(self.lbl_categories, 0, init_cats, duration_ms=FluidAnimator.TIMING_COMPLEX)
        FluidAnimator.animate_counter(self.lbl_today_actions, 0, init_today, duration_ms=FluidAnimator.TIMING_COMPLEX)
        self._prev_files = init_files
        self._prev_cats = init_cats
        self._prev_today = init_today

        # 3. Windows 11 Sabitlenen Klasörler (Hızlı Erişim Çipleri)
        qa_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        qa_card.pack(fill="x", pady=(0, 18))
        FluidAnimator.bind_card_hover(qa_card, self.theme_mode)

        qa_inner = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            qa_inner,
            text="📌 Windows 11 Sabitlenen Klasörler (Uygulama İçi Görünüm)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        chips_row = ctk.CTkFrame(qa_inner, fg_color="transparent")
        chips_row.pack(fill="x")

        pinned_nav = [
            ("🖥️ Masaüstü 📌", 'qf_desktop'),
            ("📥 İndirilenler 📌", 'qf_downloads'),
            ("📑 Belgeler 📌", 'qf_documents'),
            ("🖼️ Resimler 📌", 'qf_pictures'),
            ("🎵 Müzikler 📌", 'qf_music'),
            ("🎬 Videolar 📌", 'qf_videos'),
            ("📁 Folders Ana Klasör", 'files')
        ]
        for label_txt, nav_id in pinned_nav:
            ctk.CTkButton(
                chips_row,
                text=label_txt,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('quick_access_bg'),
                hover_color=c('quick_access_hover'),
                text_color=c('text_primary'),
                border_width=1,
                border_color=c('border_subtle'),
                height=32,
                corner_radius=7,
                command=lambda nid=nav_id: self.app.navigate_to(nid)
            ).pack(side="left", padx=(0, 6), pady=2)

        # 4. Sürükle & Bırak Akıllı Alanı (Quick Drop Zone) + Hızlı Eylemler
        mid_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mid_frame.pack(fill="x", pady=(0, 18))
        mid_frame.grid_columnconfigure(0, weight=3)
        mid_frame.grid_columnconfigure(1, weight=2)

        # Sol: Sürükle-Bırak Kartı
        self.drop_card = ctk.CTkFrame(
            mid_frame,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=2,
            border_color=c('accent')
        )
        self.drop_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        FluidAnimator.bind_card_hover(
            self.drop_card,
            self.theme_mode,
            normal_border_token='accent',
            hover_border_token='accent_light'
        )

        drop_inner = ctk.CTkFrame(self.drop_card, fg_color="transparent")
        drop_inner.pack(expand=True, fill="both", padx=24, pady=24)

        ctk.CTkLabel(
            drop_inner,
            text="📥 Dosyaları Buraya Sürükleyin ve Bırakın",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c('accent_light')
        ).pack(pady=(6, 4))

        ctk.CTkLabel(
            drop_inner,
            text="Pencerenin herhangi bir yerine bıraktığınız dosya ve klasörler\nAI File Intelligence motoru tarafından analiz edilerek ilgili kategoriye taşınır.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary'),
            justify="center"
        ).pack(pady=(0, 14))

        btn_row = ctk.CTkFrame(drop_inner, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row,
            text="⚡ Şimdi Tüm Klasörleri Tara",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            corner_radius=8,
            height=36,
            command=self.app.trigger_manual_scan
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="📂 Folders Klasörünü Aç",
            font=ctk.CTkFont(size=13),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            corner_radius=8,
            height=36,
            command=self.app.open_target_folder
        ).pack(side="left", padx=6)

        # Sağ: Hızlı Araçlar Kartı
        quick_card = ctk.CTkFrame(
            mid_frame,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        quick_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        FluidAnimator.bind_card_hover(quick_card, self.theme_mode)

        q_inner = ctk.CTkFrame(quick_card, fg_color="transparent")
        q_inner.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            q_inner,
            text="Hızlı Zekâ Araçları",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 10))

        self._create_quick_btn(q_inner, "🔍 Akıllı Anlamsal Arama", lambda: self.app.navigate_to('search'), c)
        self._create_quick_btn(q_inner, "📑 Kopya Dosyaları Temizle", lambda: self.app.navigate_to('duplicates'), c)
        self._create_quick_btn(q_inner, "📊 Depolama Dağılımını Gör", lambda: self.app.navigate_to('storage'), c)
        self._create_quick_btn(q_inner, "↩️ Son İşlemleri Geri Al (Undo)", lambda: self.app.navigate_to('security'), c)

        # 5. Son Organizasyon Hareketleri
        recent_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        recent_card.pack(fill="x", pady=(0, 10))

        r_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        r_header.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            r_header,
            text="Son Düzenlenen Dosyalar",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            r_header,
            text="Tümünü Gör →",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            width=90,
            height=28,
            command=lambda: self.app.navigate_to('activity')
        ).pack(side="right")

        self.recent_container = ctk.CTkFrame(recent_card, fg_color="transparent")
        self.recent_container.pack(fill="x", padx=18, pady=(0, 14))

        self._populate_recent_list(c)

        # Arka planda istatistikleri hesapla (UI kilitlenmesini önler)
        if not cached_storage and not self._is_loading_stats:
            self._is_loading_stats = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

    def _async_load_stats(self, target_base):
        try:
            data = StorageAnalyzer.analyze_folder(target_base)
            UIBridge.post(lambda: self._apply_storage_stats(data))
        except Exception:
            pass
        finally:
            self._is_loading_stats = False

    def _apply_storage_stats(self, data):
        try:
            new_files = data.get('total_files', 0)
            new_cats = len(data.get('categories', []))
            if hasattr(self, 'lbl_total_files') and self.lbl_total_files.winfo_exists():
                FluidAnimator.animate_counter(
                    self.lbl_total_files,
                    self._prev_files,
                    new_files,
                    duration_ms=FluidAnimator.TIMING_COMPLEX
                )
                self._prev_files = new_files
            if hasattr(self, 'lbl_total_size') and self.lbl_total_size.winfo_exists():
                self.lbl_total_size.configure(text=data.get('total_size_human', '0 B'))
            if hasattr(self, 'lbl_categories') and self.lbl_categories.winfo_exists():
                FluidAnimator.animate_counter(
                    self.lbl_categories,
                    self._prev_cats,
                    new_cats,
                    duration_ms=FluidAnimator.TIMING_COMPLEX
                )
                self._prev_cats = new_cats
        except Exception:
            pass

    def _create_stat_card(self, parent, col, icon, title, value, subtitle, c):
        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        FluidAnimator.bind_card_hover(card, self.theme_mode)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(
            top,
            text=icon,
            font=ctk.CTkFont(size=20)
        ).pack(side="left")

        ctk.CTkLabel(
            top,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=c('text_secondary')
        ).pack(side="left", padx=8)

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=c('text_primary')
        )
        val_lbl.pack(anchor="w", pady=(8, 2))

        ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        ).pack(anchor="w")
        return val_lbl

    def _create_quick_btn(self, parent, text, cmd, c):
        btn = ctk.CTkButton(
            parent,
            text=text,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=cmd
        )
        btn.pack(fill="x", pady=3)

    def _populate_recent_list(self, c):
        for w in self.recent_container.winfo_children():
            w.destroy()

        logs = SecurityBackupEngine.get_history(limit=6, active_only=True)
        if not logs:
            ctk.CTkLabel(
                self.recent_container,
                text="Henüz kaydedilmiş bir dosya organizasyon işlemi bulunmuyor.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_muted')
            ).pack(pady=14)
            return

        for entry in logs:
            row = ctk.CTkFrame(
                self.recent_container,
                fg_color=c('bg_card_secondary'),
                corner_radius=8,
                border_width=1,
                border_color=c('border_subtle')
            )
            row.pack(fill="x", pady=3)
            FluidAnimator.bind_card_hover(
                row,
                self.theme_mode,
                normal_bg_token='bg_card_secondary',
                hover_bg_token='bg_card_hover',
                normal_border_token='border_subtle',
                hover_border_token='border_hover'
            )

            ctk.CTkLabel(
                row,
                text="📄 " + entry.get('file_name', 'Bilinmeyen'),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=c('text_primary')
            ).pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(
                row,
                text=f"➔  {entry.get('category', '')} / {entry.get('subcategory', '')}",
                font=ctk.CTkFont(size=12),
                text_color=c('accent_light')
            ).pack(side="left", padx=8)

            conf = int(float(entry.get('confidence', 0.9)) * 100)
            ctk.CTkLabel(
                row,
                text=f"AI %{conf}  •  {entry.get('timestamp', '')}",
                font=ctk.CTkFont(size=11),
                text_color=c('text_muted')
            ).pack(side="right", padx=12)
