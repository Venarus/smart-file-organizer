import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from search_engine import SearchEngine
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu


class SemanticSearchView(ctk.CTkFrame):
    MAX_DISPLAY_RESULTS = 60

    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.results = []
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
        title_box.pack(fill="x", padx=16, pady=(10, 12))

        ctk.CTkLabel(
            title_box,
            text="Anlamsal ve Akıllı Arama",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Folders ve izlenen klasörlerdeki dosyaları filtrelerle hızlıca bulun (Sağ tık ile hızlı menü)",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Filtre Kartı
        filter_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        filter_card.pack(fill="x", padx=16, pady=(0, 12))
        FluidAnimator.bind_card_hover(filter_card, self.theme_mode)

        # Satır 1: Arama kutusu ve Ara butonu
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 8))

        self.query_entry = ctk.CTkEntry(
            row1,
            placeholder_text="Dosya adı, kelime, etiket veya kategori ara...",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=6,
            fg_color=c('bg_input'),
            border_color=c('border'),
            text_color=c('text_primary')
        )
        self.query_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.query_entry.bind("<Return>", lambda e: self.perform_search())
        FluidAnimator.bind_input_focus(self.query_entry, self.theme_mode)
        # Alias for global search compatibility
        self.search_entry = self.query_entry

        btn_search = ctk.CTkButton(
            row1,
            text="🔍 Ara",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            width=90,
            height=36,
            corner_radius=6,
            command=self.perform_search
        )
        btn_search.pack(side="right")

        # Satır 2: Filtre Seçenekleri
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(row2, text="Kategori:", font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted')).pack(side="left", padx=(0, 4))
        self.cat_menu = ctk.CTkOptionMenu(
            row2,
            values=["Tümü", "Elektronik", "Oyunlar", "Yazılım", "Medya", "Belgeler", "Programlar", "3D", "Arşivler"],
            width=110,
            height=28,
            corner_radius=6,
            fg_color=c('bg_secondary'),
            button_color=c('bg_card_hover'),
            text_color=c('text_primary')
        )
        self.cat_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row2, text="Uzantı:", font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted')).pack(side="left", padx=(0, 4))
        self.ext_menu = ctk.CTkOptionMenu(
            row2,
            values=["Tümü", ".pdf", ".png", ".jpg", ".mp4", ".py", ".exe", ".zip", ".ino", ".pdsprj"],
            width=95,
            height=28,
            corner_radius=6,
            fg_color=c('bg_secondary'),
            button_color=c('bg_card_hover'),
            text_color=c('text_primary')
        )
        self.ext_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row2, text="Tarih:", font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted')).pack(side="left", padx=(0, 4))
        self.date_menu = ctk.CTkOptionMenu(
            row2,
            values=["Tümü", "Bugün", "Bu Hafta", "Bu Ay"],
            width=95,
            height=28,
            corner_radius=6,
            fg_color=c('bg_secondary'),
            button_color=c('bg_card_hover'),
            text_color=c('text_primary')
        )
        self.date_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row2, text="Boyut:", font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_muted')).pack(side="left", padx=(0, 4))
        self.size_menu = ctk.CTkOptionMenu(
            row2,
            values=["Tümü", "< 1 MB", "1 MB - 50 MB", "> 50 MB"],
            width=110,
            height=28,
            corner_radius=6,
            fg_color=c('bg_secondary'),
            button_color=c('bg_card_hover'),
            text_color=c('text_primary')
        )
        self.size_menu.pack(side="left")

        # Sonuç Başlık Barı
        res_header = ctk.CTkFrame(self, fg_color="transparent")
        res_header.pack(fill="x", padx=16, pady=(0, 6))

        self.res_count_lbl = ctk.CTkLabel(
            res_header,
            text="Arama sonuçları",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        )
        self.res_count_lbl.pack(side="left")

        # Sonuçlar Listesi
        self.results_scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.results_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.results_scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        ctk.CTkLabel(
            self.results_scroll,
            text="🔎\n\nDosya adı veya anahtar kelime yazıp 'Ara' butonuna tıklayın.\nFiltreleri kullanarak aramanızı daraltabilirsiniz.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_muted'),
            justify="center"
        ).pack(pady=40)

    def set_query_and_search(self, q):
        self.query_entry.delete(0, "end")
        self.query_entry.insert(0, q)
        self.perform_search()

    def execute_search(self):
        self.perform_search()

    def perform_search(self):
        q = self.query_entry.get().strip()
        cat = self.cat_menu.get()
        ext = self.ext_menu.get()
        date_f = self.date_menu.get()
        size_f = self.size_menu.get()

        target_base = self.app.cfg.get('target', '')

        for w in self.results_scroll.winfo_children():
            w.destroy()

        self.res_count_lbl.configure(text="🔍 Aranıyor... Lütfen bekleyin...")
        FluidAnimator.create_skeleton(self.results_scroll, rows=4, row_height=52, theme_mode=self.theme_mode)

        def _worker():
            res = SearchEngine.search(
                base_folder=target_base,
                query=q,
                category=cat,
                extension=ext,
                date_filter=date_f,
                size_filter=size_f
            )
            UIBridge.post(lambda: self._display_results(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _analyze_with_ai(self, path):
        self.app.navigate_to('ai')
        if self.app.current_view and hasattr(self.app.current_view, 'analyze_file'):
            self.app.current_view.analyze_file(path)

    def _display_results(self, results):
        try:
            if not self.results_scroll.winfo_exists():
                return
        except Exception:
            return

        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.results = results

        for w in self.results_scroll.winfo_children():
            w.destroy()

        total_cnt = len(self.results)
        if total_cnt > self.MAX_DISPLAY_RESULTS:
            self.res_count_lbl.configure(text=f"Arama Sonuçları (Toplam {total_cnt} dosya bulundu, ilk {self.MAX_DISPLAY_RESULTS} listeleniyor)")
        else:
            self.res_count_lbl.configure(text=f"Arama Sonuçları ({total_cnt} dosya bulundu)")

        if not self.results:
            ctk.CTkLabel(
                self.results_scroll,
                text="Arama kriterlerine uygun dosya bulunamadı.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=40)
            return

        display_items = self.results[:self.MAX_DISPLAY_RESULTS]
        for item in display_items:
            row = ctk.CTkFrame(
                self.results_scroll,
                fg_color=c('bg_card'),
                corner_radius=8,
                border_width=1,
                border_color=c('border')
            )
            row.pack(fill="x", pady=3)
            FluidAnimator.bind_card_hover(row, self.theme_mode)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            badge_txt, icon_ch, badge_fg, badge_bg = FluentTheme.file_badge_style(item['name'], self.theme_mode)
            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(anchor="w")

            ctk.CTkLabel(
                title_row,
                text=f"{icon_ch} {badge_txt}",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=5,
                padx=6,
                pady=2
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                title_row,
                text=item['name'],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=c('text_primary'),
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                left,
                text=f"📂 {item['rel_path']}  •  {item['size_human']}  •  {item['modified']}",
                font=ctk.CTkFont(size=10),
                text_color=c('text_muted'),
                anchor="w"
            ).pack(anchor="w")

            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            ctk.CTkButton(
                right,
                text="Aç",
                font=ctk.CTkFont(size=11),
                fg_color=c('bg_card_hover'),
                hover_color=c('bg_card_active'),
                text_color=c('text_primary'),
                width=50,
                height=26,
                corner_radius=4,
                command=lambda p=item['path']: SearchEngine.open_file(p)
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                right,
                text="Klasörde Göster",
                font=ctk.CTkFont(size=11),
                fg_color=c('bg_card_hover'),
                hover_color=c('bg_card_active'),
                text_color=c('text_primary'),
                width=90,
                height=26,
                corner_radius=4,
                command=lambda p=item['path']: SearchEngine.reveal_in_explorer(p)
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                right,
                text="Yapay Zeka Analiz",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                text_color="#FFFFFF",
                width=110,
                height=26,
                corner_radius=4,
                command=lambda p=item['path']: self._analyze_with_ai(p)
            ).pack(side="left", padx=4)

            FluentContextMenu.bind_to_widget(row, item['path'], self.app)
