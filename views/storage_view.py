import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from storage_analyzer import StorageAnalyzer
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu


class StorageView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self._is_loading = False
        self._rendered_storage_id = None

        self._build_ui()

    def on_page_show(self):
        target_base = self.app.cfg.get('target', '')
        cached = StorageAnalyzer._cache.get(target_base)
        if cached is not None and id(cached) != self._rendered_storage_id:
            self._render_data(cached)

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        self._rendered_storage_id = None
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font

        # Başlık ve Yenile Barı
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 14))

        left_t = ctk.CTkFrame(header, fg_color="transparent")
        left_t.pack(side="left")

        ctk.CTkLabel(
            left_t,
            text="Depolama Alanı Analizi (Storage Analyzer)",
            font=f(24, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_t,
            text="Folders içerisindeki kategorilerin disk kullanım dağılımı ve en büyük dosyalar",
            font=f(13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="🔄 Yeniden Hesapla",
            font=f(12, "bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self._force_refresh
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        target_base = self.app.cfg.get('target', '')
        if target_base in StorageAnalyzer._cache:
            self._render_data(StorageAnalyzer._cache[target_base])
        else:
            self._start_async_analysis(force=False)

    def _force_refresh(self):
        StorageAnalyzer.invalidate_cache()
        self._rendered_storage_id = None
        self._start_async_analysis(force=True)

    def refresh(self):
        self._force_refresh()

    def _start_async_analysis(self, force=False):
        if self._is_loading:
            return
        self._is_loading = True
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font

        FluidAnimator.cancel_chunk_render(self.scroll)
        for w in self.scroll.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.scroll,
            text="⏳ Depolama dağılımı arka planda analiz ediliyor...",
            font=f(13, "bold"),
            text_color=c('accent_light')
        ).pack(anchor="w", pady=(10, 4))

        FluidAnimator.create_skeleton(self.scroll, rows=4, row_height=56, theme_mode=self.theme_mode)

        target_base = self.app.cfg.get('target', '')

        def worker():
            data = StorageAnalyzer.analyze_folder(target_base, force_refresh=force)
            self._is_loading = False
            UIBridge.post(lambda: self._render_data(data))

        threading.Thread(target=worker, daemon=True).start()

    def _render_data(self, data):
        try:
            if not self.scroll.winfo_exists():
                return
        except Exception:
            return

        self._rendered_storage_id = id(data)
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        FluidAnimator.cancel_chunk_render(self.scroll)
        for w in self.scroll.winfo_children():
            w.destroy()

        # 1. Özet Kartı
        top_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        top_card.pack(fill="x", pady=(0, 12))
        FluidAnimator.bind_card_hover(top_card, self.theme_mode)

        inner_top = ctk.CTkFrame(top_card, fg_color="transparent")
        inner_top.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            inner_top,
            text=f"💾 Toplam Kullanılan Alan: {data['total_size_human']}",
            font=f(18, "bold"),
            text_color=c('accent_light')
        ).pack(side="left")

        ctk.CTkLabel(
            inner_top,
            text=f"Toplam Dosya Sayısı: {data['total_files']:,}".replace(',', '.'),
            font=f(14, "bold"),
            text_color=c('text_primary')
        ).pack(side="right")

        # 2. Kategori Dağılım Çubukları
        cat_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        cat_card.pack(fill="x", pady=(0, 12))

        inner_cat = ctk.CTkFrame(cat_card, fg_color="transparent")
        inner_cat.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            inner_cat,
            text="📊 Kategorilere Göre Alan Dağılımı",
            font=f(15, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        for cat in data.get('categories', []):
            top_r = ctk.CTkFrame(inner_cat, fg_color="transparent")
            top_r.pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(
                top_r,
                text=f"📁 {cat['name']} ({cat['count']:,} dosya)".replace(',', '.'),
                font=f(12, "bold"),
                text_color=c('text_primary')
            ).pack(side="left")

            ctk.CTkLabel(
                top_r,
                text=f"{cat['size_human']}  (%{cat['percentage']})",
                font=f(12),
                text_color=c('accent_light')
            ).pack(side="right")

            pbar = ctk.CTkProgressBar(inner_cat, height=7, corner_radius=4)
            pbar.pack(fill="x", pady=(3, 4))
            target_ratio = max(0.02, min(1.0, cat['percentage'] / 100.0))
            pbar.set(target_ratio)
            pbar.configure(progress_color=c('accent'))

        # 3. En Büyük 15 Dosya
        large_card = ctk.CTkFrame(
            self.scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        large_card.pack(fill="x", pady=(0, 10))

        inner_l = ctk.CTkFrame(large_card, fg_color="transparent")
        inner_l.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            inner_l,
            text="🐘 En Çok Yer Kaplayan Dosyalar (Top 15 — Sağ Tık ile Hızlı Menü)",
            font=f(15, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        largest_items = list(enumerate(data.get('largest_files', [])[:15], 1))

        def _render_large_item(pair, _i):
            idx, lf = pair
            f_row = ctk.CTkFrame(
                inner_l,
                fg_color=c('bg_card_secondary'),
                corner_radius=6,
                border_width=1,
                border_color=c('border_subtle'),
                height=38
            )
            f_row.pack(fill="x", pady=2)
            f_row.pack_propagate(False)
            FluidAnimator.bind_card_hover(
                f_row,
                self.theme_mode,
                normal_bg_token='bg_card_secondary',
                hover_bg_token='bg_card_hover',
                normal_border_token='border_subtle',
                hover_border_token='border_hover'
            )

            ctk.CTkLabel(
                f_row,
                text=f"#{idx}  {lf['name']}",
                font=f(12, "bold"),
                text_color=c('text_primary')
            ).pack(side="left", padx=12, pady=6)

            ctk.CTkLabel(
                f_row,
                text=f"[{lf['category']}]",
                font=f(11),
                text_color=c('text_muted')
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                f_row,
                text="Aç",
                width=50,
                height=24,
                corner_radius=4,
                font=f(11),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                command=lambda p=lf['path']: os.startfile(p) if os.path.exists(p) else None
            ).pack(side="right", padx=10)

            ctk.CTkLabel(
                f_row,
                text=lf['size_human'],
                font=f(12, "bold"),
                text_color=c('warning')
            ).pack(side="right", padx=10)

            FluentContextMenu.bind_to_widget(
                f_row,
                lf['path'],
                self.app,
                on_refresh=self.refresh,
                normal_bg_token='bg_card_secondary',
                normal_border_token='border_subtle'
            )

        FluidAnimator.render_chunked(
            inner_l,
            largest_items,
            _render_large_item,
            initial_batch=4,
            chunk_size=5,
            interval_ms=8
        )
