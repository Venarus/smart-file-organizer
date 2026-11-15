"""
Modern Glass File & Category Explorer (Folders Gezgini) (V2.1 — Premium Glass Edition)
Features:
- Switchable Bento Glass Grid (2-column) and Detailed Glass List views
- Glowing Glass Orbs per category + animated storage utilization progress bars
- Windows 11 Pinned Folders Quick-Jump Glass Ribbon
- Translucent right-click context menu & smooth hover border illumination
"""

import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from glass_engine import GlassArtEngine
from storage_analyzer import StorageAnalyzer
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu


class MyFilesView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self.view_layout = "grid"  # 'grid' veya 'list'
        self.stat_labels = {}
        self._is_loading = False

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def on_page_show(self):
        target_base = self.app.cfg.get('target', '')
        if target_base in StorageAnalyzer._cache:
            self._apply_cached_stats(StorageAnalyzer._cache[target_base].get('category_map', {}))

    def _toggle_layout(self, val):
        new_mode = "list" if "Liste" in val else "grid"
        if new_mode != self.view_layout:
            self.view_layout = new_mode
            for w in self.winfo_children():
                w.destroy()
            self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.stat_labels.clear()

        # 1. Üst Cam Başlık Kartı
        header_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        header_card.pack(fill="x", padx=12, pady=(6, 10))
        FluidAnimator.bind_card_hover(header_card, self.theme_mode)

        header = ctk.CTkFrame(header_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=14)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Folders Cam Gezgini (My Files)",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=22, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        target_base = self.app.cfg.get('target', '')
        cached_info = StorageAnalyzer._cache.get(target_base)
        sub_txt = f"📍 {target_base}"
        if cached_info:
            sub_txt += f"   •   {cached_info.get('total_files', 0):,} Dosya   •   {cached_info.get('total_size_human', '0 B')}".replace(',', '.')

        ctk.CTkLabel(
            title_box,
            text=sub_txt,
            font=ctk.CTkFont(size=11),
            text_color=c('accent_light')
        ).pack(anchor="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        self.layout_seg = ctk.CTkSegmentedButton(
            btn_box,
            values=["⊞ Bento Grid", "☰ Liste"],
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            selected_color=c('accent'),
            selected_hover_color=c('accent_hover'),
            unselected_color=c('bg_card_secondary'),
            unselected_hover_color=c('bg_card_hover'),
            command=self._toggle_layout
        )
        self.layout_seg.pack(side="left", padx=6)
        self.layout_seg.set("☰ Liste" if self.view_layout == "list" else "⊞ Bento Grid")

        ctk.CTkButton(
            btn_box,
            text="🔄 Yenile",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            height=32,
            width=85,
            corner_radius=8,
            command=self._refresh_data
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📂 Gezginde Aç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            height=32,
            width=120,
            corner_radius=8,
            command=self.app.open_target_folder
        ).pack(side="left", padx=4)

        # 2. Windows 11 Sabitlenen Klasörler Cam Şeridi
        qa_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('border')
        )
        qa_card.pack(fill="x", padx=12, pady=(0, 10))
        FluidAnimator.bind_card_hover(qa_card, self.theme_mode)

        qa_inner = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_inner.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            qa_inner,
            text="📌 Sabitlenen Klasörler:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('text_secondary')
        ).pack(side="left", padx=(0, 10))

        pinned_routes = [
            ("🖥️ Masaüstü", 'qf_desktop'),
            ("📥 İndirilenler", 'qf_downloads'),
            ("📑 Belgeler", 'qf_documents'),
            ("🖼️ Resimler", 'qf_pictures'),
            ("🎵 Müzikler", 'qf_music'),
            ("🎬 Videolar", 'qf_videos'),
        ]
        for label_text, route_id in pinned_routes:
            ctk.CTkButton(
                qa_inner,
                text=f"{label_text} 📌",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('quick_access_bg'),
                hover_color=c('quick_access_hover'),
                text_color=c('text_primary'),
                border_width=1,
                border_color=c('border_subtle'),
                height=28,
                corner_radius=7,
                command=lambda rid=route_id: self.app.navigate_to(rid)
            ).pack(side="left", padx=3)

        # 3. Kategori Kartları Tuvali
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        try:
            scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        if not os.path.exists(target_base):
            ctk.CTkLabel(
                scroll,
                text="Hedef Folders klasörü bulunamadı.",
                font=ctk.CTkFont(size=14),
                text_color=c('danger')
            ).pack(pady=40)
            return

        category_meta = {
            '01_elektronik': ('⚡', '#38BDF8'),
            '02_oyunlar': ('🎮', '#8B5CF6'),
            '03_yazılım': ('💻', '#10B981'),
            '04_medya': ('🎨', '#F43F5E'),
            '05_belgeler': ('📑', '#0EA5E9'),
            '06_programlar': ('📦', '#F59E0B'),
            '07_kısayollar': ('🔗', '#94A3B8'),
            '08_3d': ('🧊', '#A855F7'),
            '09_yazı': ('🔤', '#EC4899'),
            '10_arşivler': ('🗄️', '#EAB308'),
            '11_teknik': ('📐', '#06B6D4')
        }

        try:
            entries = sorted(os.listdir(target_base))
        except Exception:
            entries = []

        is_cached = target_base in StorageAnalyzer._cache
        category_map = StorageAnalyzer._cache[target_base].get('category_map', {}) if is_cached else {}

        dir_entries = []
        for entry in entries:
            entry_path = os.path.join(target_base, entry)
            if os.path.isdir(entry_path) and not entry.startswith('.'):
                dir_entries.append((entry, entry_path))

        if not dir_entries:
            ctk.CTkLabel(
                scroll,
                text="✨ Henüz Folders klasöründe bir kategori bulunmuyor.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=40)
        elif self.view_layout == "grid":
            grid_holder = ctk.CTkFrame(scroll, fg_color="transparent")
            grid_holder.pack(fill="both", expand=True)
            grid_holder.grid_columnconfigure(0, weight=1, uniform="cat_col")
            grid_holder.grid_columnconfigure(1, weight=1, uniform="cat_col")
            for idx, (entry, entry_path) in enumerate(dir_entries):
                stats = category_map.get(entry, None)
                card = self._create_category_card(grid_holder, entry, entry_path, stats, category_meta, c)
                card.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=5, pady=5)
        else:
            for entry, entry_path in dir_entries:
                stats = category_map.get(entry, None)
                card = self._create_category_card(scroll, entry, entry_path, stats, category_meta, c)
                card.pack(fill="x", pady=5, padx=4)

        if not is_cached and not self._is_loading:
            self._is_loading = True
            threading.Thread(target=self._async_load_stats, args=(target_base,), daemon=True).start()

    def _async_load_stats(self, target_base):
        try:
            data = StorageAnalyzer.analyze_folder(target_base)
            cmap = data.get('category_map', {})
            UIBridge.post(lambda: self._apply_cached_stats(cmap))
        except Exception:
            pass
        finally:
            self._is_loading = False

    def _apply_cached_stats(self, cmap):
        for cat_name, (lbl, pbar) in self.stat_labels.items():
            if cat_name in cmap:
                try:
                    st = cmap[cat_name]
                    if lbl.winfo_exists():
                        lbl.configure(text=f"{st['count']:,} dosya  •  {st['size_human']} (%{st['percentage']})".replace(',', '.'))
                    if pbar and pbar.winfo_exists():
                        ratio = max(0.03, min(1.0, float(st.get('percentage', 0)) / 100.0))
                        FluidAnimator.animate_progress(pbar, ratio, duration_ms=FluidAnimator.TIMING_COMPLEX)
                except Exception:
                    pass

    def _refresh_data(self):
        StorageAnalyzer.invalidate_cache()
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()

    def _create_category_card(self, parent, cat_name, cat_path, stats, meta_map, c):
        try:
            sub_items = os.listdir(cat_path)
            sub_dirs = [d for d in sub_items if os.path.isdir(os.path.join(cat_path, d))]
        except Exception:
            sub_dirs = []

        if stats:
            info_text = f"{stats['count']:,} dosya  •  {stats['size_human']} (%{stats['percentage']})".replace(',', '.')
            pct_ratio = max(0.03, min(1.0, float(stats.get('percentage', 0)) / 100.0))
        else:
            info_text = f"Hesaplanıyor...  •  {len(sub_dirs)} alt klasör"
            pct_ratio = 0.04

        cat_icon, orb_col = ('📁', c('accent'))
        lower_cat = cat_name.lower()
        for k, (ic, col) in meta_map.items():
            if lower_cat.startswith(k):
                cat_icon, orb_col = ic, col
                break

        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=13,
            border_width=1,
            border_color=c('border')
        )
        FluidAnimator.bind_card_hover(card, self.theme_mode)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        orb_img = GlassArtEngine.get_glass_orb(38, orb_col, self.theme_mode)
        ctk.CTkLabel(
            top_row,
            text=cat_icon,
            image=orb_img,
            compound="center",
            font=ctk.CTkFont(size=17),
            width=38,
            height=38
        ).pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text=cat_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary'),
            anchor="w"
        ).pack(anchor="w")

        lbl_info = ctk.CTkLabel(
            title_col,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color=c('accent_light'),
            anchor="w"
        )
        lbl_info.pack(anchor="w")

        btn_open = ctk.CTkButton(
            top_row,
            text="📂 Aç",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            width=64,
            height=28,
            corner_radius=7,
            command=lambda p=cat_path: os.startfile(p) if os.path.exists(p) else None
        )
        btn_open.pack(side="right", padx=(4, 0))

        if "medya" in lower_cat or "video" in lower_cat:
            ctk.CTkButton(
                top_row,
                text="🎬 Galeri",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                text_color="#FFFFFF",
                width=74,
                height=28,
                corner_radius=7,
                command=lambda: self.app.navigate_to('media')
            ).pack(side="right")

        pbar = ctk.CTkProgressBar(inner, height=5, corner_radius=3, fg_color=c('bg_card_secondary'))
        pbar.pack(fill="x", pady=(10, 6))
        pbar.set(pct_ratio)
        pbar.configure(progress_color=orb_col)
        self.stat_labels[cat_name] = (lbl_info, pbar)

        if sub_dirs:
            pills_frame = ctk.CTkFrame(inner, fg_color="transparent")
            pills_frame.pack(anchor="w", fill="x")
            for sub in sub_dirs[:5]:
                sub_p = os.path.join(cat_path, sub)
                pill = ctk.CTkButton(
                    pills_frame,
                    text=f"📁 {sub}",
                    font=ctk.CTkFont(size=10),
                    text_color=c('text_secondary'),
                    fg_color=c('bg_card_secondary'),
                    hover_color=c('bg_card_hover'),
                    height=22,
                    width=60,
                    corner_radius=5,
                    command=lambda sp=sub_p: os.startfile(sp) if os.path.exists(sp) else None
                )
                pill.pack(side="left", padx=(0, 4), pady=1)
            if len(sub_dirs) > 5:
                ctk.CTkLabel(
                    pills_frame,
                    text=f"+{len(sub_dirs)-5}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=c('text_muted')
                ).pack(side="left", padx=4)

        FluentContextMenu.bind_to_widget(card, cat_path, self.app)
        return card
