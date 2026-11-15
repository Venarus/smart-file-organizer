import customtkinter as ctk
from theme import FluentTheme
from security_backup import SecurityBackupEngine
from animation import FluidAnimator
from notification_center import FluentContextMenu


class ActivityView(ctk.CTkFrame):
    PAGE_SIZE = 24

    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.current_filter = "Tümü"
        self._display_limit = self.PAGE_SIZE
        self._last_render_key = None
        self._filter_btns = {}
        self._build_ui()

    def on_page_show(self):
        cur_key = (SecurityBackupEngine.get_revision(), self.current_filter, self._display_limit, self.theme_mode)
        if self._last_render_key == cur_key:
            return
        if hasattr(self, 'scroll') and self.scroll.winfo_exists():
            self._render_list()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        self._last_render_key = None
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        self._filter_btns.clear()

        # Başlık
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(10, 14))

        ctk.CTkLabel(
            title_box,
            text="Aktivite Merkezi (Activity Center)",
            font=f(24, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Arka plan izleyicisi ve manuel yapılan tüm dosya taşıma işlemlerinin kayıtları",
            font=f(13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Filtre ve Aksiyon Barı
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 10))

        btn_box = ctk.CTkFrame(bar, fg_color="transparent")
        btn_box.pack(side="left")

        for f_name in ["Tümü", "Aktif", "Geri Alınan"]:
            is_act = (f_name == self.current_filter)
            bg = c('accent') if is_act else c('bg_card')
            btn = ctk.CTkButton(
                btn_box,
                text=f_name,
                font=f(12, "bold" if is_act else "normal"),
                fg_color=bg,
                hover_color=c('accent_hover'),
                text_color="#FFFFFF" if is_act else c('text_primary'),
                width=85,
                height=30,
                corner_radius=6,
                command=lambda fn=f_name: self._set_filter(fn)
            )
            btn.pack(side="left", padx=2)
            self._filter_btns[f_name] = btn

        ctk.CTkButton(
            bar,
            text="Geçmişi Sıfırla",
            font=f(11, "bold"),
            fg_color=c('danger_bg'),
            hover_color=c('danger'),
            text_color=c('text_primary'),
            width=105,
            height=30,
            corner_radius=6,
            command=self._clear_history
        ).pack(side="right")

        # Liste Alanı
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_list()

    def _set_filter(self, f_name):
        if f_name == self.current_filter:
            return
        self.current_filter = f_name
        self._display_limit = self.PAGE_SIZE
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        for name, btn in self._filter_btns.items():
            is_act = (name == f_name)
            btn.configure(
                fg_color=c('accent') if is_act else c('bg_card'),
                text_color="#FFFFFF" if is_act else c('text_primary'),
                font=f(12, "bold" if is_act else "normal")
            )
        self._render_list()

    def _load_more(self):
        self._display_limit += self.PAGE_SIZE
        self._render_list()

    def _render_list(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        self._last_render_key = (SecurityBackupEngine.get_revision(), self.current_filter, self._display_limit, self.theme_mode)

        FluidAnimator.cancel_chunk_render(self.scroll)
        for w in self.scroll.winfo_children():
            w.destroy()

        history = SecurityBackupEngine.get_history(limit=200)

        if self.current_filter == "Aktif":
            history = [tx for tx in history if tx.get('status') == 'active']
        elif self.current_filter == "Geri Alınan":
            history = [tx for tx in history if tx.get('status') == 'undone']

        if not history:
            ctk.CTkLabel(
                self.scroll,
                text="Bu filtreye uygun kayıtlı işlem bulunmuyor.",
                font=f(13),
                text_color=c('text_muted')
            ).pack(pady=40)
            return

        total_cnt = len(history)
        visible_slice = history[:self._display_limit]

        def _render_item(tx, _idx):
            card = ctk.CTkFrame(
                self.scroll,
                fg_color=c('bg_card'),
                corner_radius=9,
                border_width=1,
                border_color=c('border'),
                height=44
            )
            card.pack(fill="x", pady=2)
            FluidAnimator.bind_card_hover(card, self.theme_mode)

            is_undone = tx.get('status') == 'undone'
            status_badge = "↩️ Geri Alındı" if is_undone else "✅ Taşındı"
            status_color = c('warning') if is_undone else c('success')

            ctk.CTkLabel(
                card,
                text=status_badge,
                font=f(11, "bold"),
                text_color=status_color,
                width=95,
                anchor="w"
            ).pack(side="left", padx=(12, 8), pady=8)

            fname = tx.get('file_name', '')
            ctk.CTkLabel(
                card,
                text=fname if len(fname) <= 36 else fname[:33] + "...",
                font=f(12, "bold"),
                text_color=c('text_primary'),
                anchor="w"
            ).pack(side="left", padx=(0, 12), pady=8)

            ctk.CTkLabel(
                card,
                text=f"➔  {tx.get('category', '')}",
                font=f(11, "bold"),
                text_color=c('accent_light'),
                anchor="w"
            ).pack(side="left", padx=(0, 10), pady=8)

            ctk.CTkLabel(
                card,
                text=f"🕒 {tx.get('timestamp', '')}",
                font=f(10),
                text_color=c('text_muted')
            ).pack(side="right", padx=12, pady=8)

            if tx.get('target_path'):
                FluentContextMenu.bind_to_widget(card, tx['target_path'], self.app)

        def _on_done():
            if total_cnt > self._display_limit and self.scroll.winfo_exists():
                ctk.CTkButton(
                    self.scroll,
                    text=f"Daha Fazla Göster (+{total_cnt - self._display_limit} kayıt)",
                    font=f(12, "bold"),
                    fg_color=c('bg_card'),
                    hover_color=c('bg_card_hover'),
                    text_color=c('accent_light'),
                    height=32,
                    corner_radius=8,
                    command=self._load_more
                ).pack(pady=8)

        FluidAnimator.render_chunked(
            self.scroll,
            visible_slice,
            _render_item,
            initial_batch=6,
            chunk_size=8,
            interval_ms=8,
            on_complete=_on_done
        )

    def _clear_history(self):
        SecurityBackupEngine.clear_history()
        self._render_list()
