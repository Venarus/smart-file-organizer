import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from storage_analyzer import StorageAnalyzer

class MyFilesView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self.stat_labels = {}
        self._is_loading = False

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def on_page_show(self):
        """Sayfa açıldığında önbellek durumuna göre istatistikleri kontrol eder."""
        target_base = self.app.cfg.get('target', '')
        if target_base in StorageAnalyzer._cache:
            self._apply_cached_stats(StorageAnalyzer._cache[target_base].get('category_map', {}))

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.stat_labels.clear()

        # Başlık ve Hızlı Aç Barı
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Dosyalarım (Folders Gezgini)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Masaüstünüzdeki Folders klasörünün güncel yapısı ve kategorileri",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="📂 Ana Klasörü Aç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self.app.open_target_folder
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_box,
            text="🔄 Yenile",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=self._refresh_data
        ).pack(side="right", padx=4)

        # Windows 11 Hızlı Erişim Ribbon (Masaüstü, İndirilenler, Belgeler, Resimler, Müzikler, Videolar, Folders)
        qa_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        qa_card.pack(fill="x", padx=16, pady=(0, 10))

        qa_inner = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_inner.pack(fill="x", padx=14, pady=10)

        qa_top = ctk.CTkFrame(qa_inner, fg_color="transparent")
        qa_top.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            qa_top,
            text="📌 Hızlı Erişim (Windows 11 Sabitlenen Klasörler)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        user_home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        quick_folders = [
            ("🖥️ Masaüstü", os.path.join(user_home, "Desktop")),
            ("📥 İndirilenler", os.path.join(user_home, "Downloads")),
            ("📑 Belgeler", os.path.join(user_home, "Documents")),
            ("🖼️ Resimler", os.path.join(user_home, "Pictures")),
            ("🎵 Müzikler", os.path.join(user_home, "Music")),
            ("🎬 Videolar", os.path.join(user_home, "Videos")),
            ("📁 Folders", self.app.cfg.get('target', ''))
        ]

        qa_chips_box = ctk.CTkFrame(qa_inner, fg_color="transparent")
        qa_chips_box.pack(fill="x")

        for label_text, target_path in quick_folders:
            btn_chip = ctk.CTkButton(
                qa_chips_box,
                text=f"{label_text} 📌",
                font=ctk.CTkFont(size=11),
                fg_color=c('quick_access_bg'),
                hover_color=c('quick_access_hover'),
                text_color=c('text_primary'),
                border_width=1,
                border_color=c('border_subtle'),
                height=30,
                corner_radius=6,
                command=lambda p=target_path: os.startfile(p) if os.path.exists(p) else None
            )
            btn_chip.pack(side="left", padx=(0, 6), pady=2)

        # Bilgi Breadcrumb Barı
        target_base = self.app.cfg.get('target', '')
        cached_info = StorageAnalyzer._cache.get(target_base)
        summary_text = f"📍 Konum: {target_base}"
        if cached_info:
            summary_text += f"   •   {cached_info.get('total_files', 0):,} Dosya   •   {cached_info.get('total_size_human', '0 B')}".replace(',', '.')

        info_bar = ctk.CTkFrame(self, fg_color="transparent")
        info_bar.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(
            info_bar,
            text=summary_text,
            font=ctk.CTkFont(size=11),
            text_color=c('accent_light')
        ).pack(side="left")

        # Kategori Kartları (Scrollable Container — Katı Mica Arka Planı yırtılmaları önler)
        scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        target_base = self.app.cfg.get('target', '')
        if not os.path.exists(target_base):
            ctk.CTkLabel(
                scroll,
                text="Hedef klasör bulunamadı.",
                font=ctk.CTkFont(size=14),
                text_color=c('danger')
            ).pack(pady=40)
            return

        category_icons = {
            '01_elektronik': '⚡',
            '02_oyunlar': '🎮',
            '03_yazılım': '💻',
            '04_medya': '🎨',
            '05_belgeler': '📑',
            '06_programlar': '📦',
            '07_kısayollar': '🔗',
            '08_3d': '🧊',
            '09_yazı': '🔤',
            '10_arşivler': '🗄️',
            '11_teknik': '📐'
        }

        try:
            entries = sorted(os.listdir(target_base))
        except Exception:
            entries = []

        is_cached = target_base in StorageAnalyzer._cache
        category_map = StorageAnalyzer._cache[target_base].get('category_map', {}) if is_cached else {}

        has_categories = False
        for entry in entries:
            entry_path = os.path.join(target_base, entry)
            if os.path.isdir(entry_path):
                has_categories = True
                stats = category_map.get(entry, None)
                self._create_category_card(scroll, entry, entry_path, stats, category_icons, c)

        if not has_categories:
            ctk.CTkLabel(
                scroll,
                text="Henüz Folders klasöründe bir kategori bulunmuyor.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=40)

        # Eğer önbellekte henüz yoksa arka planda hesaplat
        if not is_cached and not self._is_loading:
            self._is_loading = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

    def _async_load_stats(self, target_base):
        try:
            data = StorageAnalyzer.analyze_folder(target_base)
            cmap = data.get('category_map', {})
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._apply_cached_stats(cmap))
            except Exception:
                pass
        except Exception:
            pass
        finally:
            self._is_loading = False

    def _apply_cached_stats(self, cmap):
        for cat_name, lbl in self.stat_labels.items():
            if cat_name in cmap:
                st = cmap[cat_name]
                lbl.configure(text=f"📊 {st['count']:,} dosya  •  {st['size_human']} ({st['percentage']}%)".replace(',', '.'))

    def _refresh_data(self):
        StorageAnalyzer.invalidate_cache()
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    def _create_category_card(self, parent, cat_name, cat_path, stats, icon_map, c):
        try:
            sub_items = os.listdir(cat_path)
            sub_dirs = [d for d in sub_items if os.path.isdir(os.path.join(cat_path, d))]
        except Exception:
            sub_dirs = []

        if stats:
            info_text = f"📊 {stats['count']:,} dosya  •  {stats['size_human']} ({stats['percentage']}%)  •  {len(sub_dirs)} alt klasör".replace(',', '.')
        else:
            info_text = f"📊 Hesaplanıyor...  •  {len(sub_dirs)} alt klasör"

        # İkon eşleme
        cat_icon = '📁'
        lower_cat = cat_name.lower()
        for k, ic in icon_map.items():
            if lower_cat.startswith(k):
                cat_icon = ic
                break

        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        left_box = ctk.CTkFrame(inner, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True)

        header_row = ctk.CTkFrame(left_box, fg_color="transparent")
        header_row.pack(anchor="w")

        ctk.CTkLabel(
            header_row,
            text=cat_icon,
            font=ctk.CTkFont(size=20)
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header_row,
            text=cat_name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        lbl_info = ctk.CTkLabel(
            left_box,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=c('accent_light')
        )
        lbl_info.pack(anchor="w", pady=(4, 6))
        self.stat_labels[cat_name] = lbl_info

        if sub_dirs:
            pills_frame = ctk.CTkFrame(left_box, fg_color="transparent")
            pills_frame.pack(anchor="w")
            for sub in sub_dirs[:6]:
                pill = ctk.CTkLabel(
                    pills_frame,
                    text=f"📁 {sub}",
                    font=ctk.CTkFont(size=10),
                    text_color=c('text_muted'),
                    fg_color=c('bg_secondary'),
                    corner_radius=4,
                    padx=6,
                    pady=2
                )
                pill.pack(side="left", padx=2, pady=2)
            if len(sub_dirs) > 6:
                ctk.CTkLabel(
                    pills_frame,
                    text=f"+{len(sub_dirs)-6} daha",
                    font=ctk.CTkFont(size=10),
                    text_color=c('text_muted')
                ).pack(side="left", padx=4)

        if "medya" in cat_name.lower() or "video" in cat_name.lower():
            btn_gal = ctk.CTkButton(
                inner,
                text="🎬 Önizle",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                text_color="#FFFFFF",
                width=80,
                height=32,
                corner_radius=6,
                command=lambda: self.app.navigate_to('media')
            )
            btn_gal.pack(side="right", padx=(4, 0))

        btn_open = ctk.CTkButton(
            inner,
            text="Aç",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            width=65,
            height=32,
            corner_radius=6,
            command=lambda p=cat_path: os.startfile(p) if os.path.exists(p) else None
        )
        btn_open.pack(side="right")
