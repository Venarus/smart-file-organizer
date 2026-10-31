import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from storage_analyzer import StorageAnalyzer
from search_engine import SearchEngine

class StorageView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self._is_loading = False

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # Başlık ve Yenile Butonu
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 14))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Depolama ve Boyut Analizcisi",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Folders klasörünün disk alanı kullanımını ve en büyük dosyaları görselleştirin",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="🔄 Yeniden Tara",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=6,
            command=self._force_refresh
        ).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        target_base = self.app.cfg.get('target', '')
        if not os.path.exists(target_base):
            ctk.CTkLabel(self.scroll, text="Hedef klasör bulunamadı.", font=ctk.CTkFont(size=14), text_color=c('danger')).pack(pady=40)
            return

        if target_base in StorageAnalyzer._cache:
            self._render_storage_content(StorageAnalyzer._cache[target_base])
        else:
            self._render_loading_state()
            if not self._is_loading:
                self._is_loading = True
                threading.Thread(target=self._async_load, args=(target_base,), daemon=True).start()

    def _render_loading_state(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.scroll,
            text="⏳\n\nDepolama dağılımı ve büyük dosyalar arka planda hesaplanıyor...\nLütfen bekleyin.",
            font=ctk.CTkFont(size=14),
            text_color=c('text_muted'),
            justify="center"
        ).pack(pady=60)

    def _async_load(self, target_base):
        try:
            data = StorageAnalyzer.analyze_folder(target_base)
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._render_storage_content(data))
            except Exception:
                pass
        except Exception:
            pass
        finally:
            self._is_loading = False

    def _render_storage_content(self, data):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll.winfo_children():
            w.destroy()

        # 1. Metrik Kartları
        m_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        m_frame.pack(fill="x", pady=(0, 14))
        m_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="m_col")

        metrics = [
            ("💾 Toplam Kaplanan Alan", data['total_size_human'], c('accent_light')),
            ("📄 Toplam Dosya Sayısı", f"{data['total_files']:,}".replace(',', '.') + " Adet", c('text_primary')),
            ("📁 Toplam Klasör Sayısı", f"{data['total_dirs']} Adet", c('text_primary'))
        ]

        for i, (label, val, col) in enumerate(metrics):
            card = ctk.CTkFrame(m_frame, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=20, weight="bold"), text_color=col).pack(anchor="w", padx=14, pady=(0, 12))

        # 2. Kategori Dağılım Çubukları
        cat_card = ctk.CTkFrame(self.scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        cat_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            cat_card,
            text="📊 Kategorilere Göre Disk Kullanımı",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", padx=16, pady=(12, 10))

        for cat in data.get('categories', []):
            c_row = ctk.CTkFrame(cat_card, fg_color="transparent")
            c_row.pack(fill="x", padx=16, pady=4)

            header = ctk.CTkFrame(c_row, fg_color="transparent")
            header.pack(fill="x")
            ctk.CTkLabel(header, text=cat['name'], font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_primary')).pack(side="left")
            ctk.CTkLabel(header, text=f"{cat['size_human']}  (%{cat['percentage']})  •  {cat['count']:,} dosya".replace(',', '.'), font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(side="right")

            pb = ctk.CTkProgressBar(c_row, height=6, corner_radius=3)
            pb.pack(fill="x", pady=(2, 6))
            pb.set(cat['percentage'] / 100.0)
            pb.configure(progress_color=c('accent'))

        ctk.CTkFrame(cat_card, fg_color="transparent", height=8).pack()

        # 3. En Büyük 10 Dosya
        large_card = ctk.CTkFrame(self.scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        large_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            large_card,
            text="🐘 En Çok Yer Kaplayan İlk 10 Dosya",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", padx=16, pady=(12, 8))

        for item in data.get('largest_files', []):
            row = ctk.CTkFrame(large_card, fg_color=c('bg_mica'), corner_radius=6)
            row.pack(fill="x", padx=14, pady=3)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=6)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(left, text=item['name'], font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_primary')).pack(anchor="w")
            ctk.CTkLabel(left, text=f"[{item['category']}] • {item['size_human']}", font=ctk.CTkFont(size=10), text_color=c('accent_light')).pack(anchor="w")

            ctk.CTkButton(
                inner,
                text="Klasörde Göster",
                font=ctk.CTkFont(size=11),
                fg_color=c('bg_card_hover'),
                hover_color=c('bg_card_active'),
                text_color=c('text_primary'),
                width=100,
                height=26,
                corner_radius=6,
                command=lambda p=item['path']: SearchEngine.reveal_in_explorer(p)
            ).pack(side="right")

        ctk.CTkFrame(large_card, fg_color="transparent", height=8).pack()

    def _force_refresh(self):
        StorageAnalyzer.invalidate_cache()
        self._build_ui()
