import customtkinter as ctk
from tkinter import messagebox
from theme import FluentTheme
from security_backup import SecurityBackupEngine
from animation import FluidAnimator
from notification_center import FluentContextMenu


class SecurityBackupView(ctk.CTkFrame):
    PAGE_SIZE = 20

    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode
        self._display_limit = self.PAGE_SIZE
        self._last_render_key = None

        self._build_ui()

    def on_page_show(self):
        cur_key = (SecurityBackupEngine.get_revision(), self._display_limit, self.theme_mode)
        if self._last_render_key == cur_key:
            return
        if hasattr(self, 'scroll') and self.scroll.winfo_exists():
            self._render_undo_list()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        self._last_render_key = None
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font

        # Başlık
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(10, 14))

        ctk.CTkLabel(
            title_box,
            text="Güvenlik, Yedekleme ve Geri Alma (Undo)",
            font=f(24, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Yapılan her dosya hareketini tek tıkla geri alın ve sistem güvenlik korumalarını yönetin",
            font=f(13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # 1. Kart: 1-Tık Geri Alma Eylemi
        undo_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        undo_card.pack(fill="x", padx=16, pady=(0, 12))
        FluidAnimator.bind_card_hover(undo_card, self.theme_mode)

        inner_u = ctk.CTkFrame(undo_card, fg_color="transparent")
        inner_u.pack(fill="x", padx=16, pady=12)

        u_text = ctk.CTkFrame(inner_u, fg_color="transparent")
        u_text.pack(side="left")

        ctk.CTkLabel(
            u_text,
            text="Hızlı Geri Alma (1-Click Undo):",
            font=f(14, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            u_text,
            text="Yanlışlıkla düzenlenen veya yeri değiştirilen son dosyayı anında eski yerine döndürün.",
            font=f(12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        ctk.CTkButton(
            inner_u,
            text="↩️ En Son İşlemi Geri Al",
            font=f(13, "bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=6,
            command=self._undo_last
        ).pack(side="right")

        # 2. Kart: Güvenlik Garantileri
        sec_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        sec_card.pack(fill="x", padx=16, pady=(0, 12))

        inner_sec = ctk.CTkFrame(sec_card, fg_color="transparent")
        inner_sec.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            inner_sec,
            text="🛡️ Aktif Sistem Güvenlik Korumaları:",
            font=f(13, "bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 6))

        guarantees = [
            ("✅ İndirme Koruması:", "Tarayıcınız dosya indirirken (.crdownload, .tmp, .part) dosyalar asla taşınmaz."),
            ("✅ Dosya Kilidi Testi:", "Başka bir programda açık olan veya yazılan dosyalar kilit açılana kadar bekletilir."),
            ("✅ Masaüstü Taban Koruması:", "Masaüstünüzde önceden var olan mevcut dosyalarınız asla klasörlere dağıtılmaz."),
            ("✅ İsim Çakışma Önleyici:", "Hedefte aynı isimde dosya varsa üzerine yazılmaz, (1), (2) şeklinde korunur.")
        ]

        for title, desc in guarantees:
            row = ctk.CTkFrame(inner_sec, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=title, font=f(11, "bold"), text_color=c('success'), width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=f(11), text_color=c('text_secondary'), anchor="w").pack(side="left")

        # 3. Geri Alınabilir İşlem Listesi
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            list_header,
            text="Geri Alınabilir Aktif İşlemler Defteri",
            font=f(13, "bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_undo_list()

    def _load_more(self):
        self._display_limit += self.PAGE_SIZE
        self._render_undo_list()

    def refresh(self):
        self._render_undo_list()

    def _render_undo_list(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        self._last_render_key = (SecurityBackupEngine.get_revision(), self._display_limit, self.theme_mode)

        FluidAnimator.cancel_chunk_render(self.scroll)
        for w in self.scroll.winfo_children():
            w.destroy()

        active_txs = SecurityBackupEngine.get_history(limit=150, active_only=True)

        if not active_txs:
            ctk.CTkLabel(
                self.scroll,
                text="Geri alınabilecek aktif dosya hareketi bulunmuyor.",
                font=f(13),
                text_color=c('text_muted')
            ).pack(pady=30)
            return

        total_cnt = len(active_txs)
        visible_slice = active_txs[:self._display_limit]

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
            card.pack_propagate(False)
            FluidAnimator.bind_card_hover(card, self.theme_mode)

            fname = tx.get('file_name', '')
            ctk.CTkLabel(
                card,
                text=f"📄 {fname if len(fname) <= 32 else fname[:29] + '...'}",
                font=f(12, "bold"),
                text_color=c('text_primary'),
                anchor="w"
            ).pack(side="left", padx=(12, 10), pady=8)

            ctk.CTkLabel(
                card,
                text=f"➔  {tx.get('category', '')}",
                font=f(11, "bold"),
                text_color=c('accent_light'),
                anchor="w"
            ).pack(side="left", padx=(0, 8), pady=8)

            ctk.CTkButton(
                card,
                text="↩️ Geri Al",
                font=f(11, "bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                width=84,
                height=26,
                corner_radius=6,
                command=lambda tid=tx['id']: self._undo_single(tid)
            ).pack(side="right", padx=12, pady=8)

            if tx.get('target_path'):
                FluentContextMenu.bind_to_widget(card, tx['target_path'], self.app, on_refresh=self.refresh)

        def _on_done():
            if total_cnt > self._display_limit and self.scroll.winfo_exists():
                ctk.CTkButton(
                    self.scroll,
                    text=f"Daha Fazla Göster (+{total_cnt - self._display_limit} işlem)",
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

    def _undo_single(self, tid):
        res = SecurityBackupEngine.undo_transaction(tid)
        if res['success']:
            messagebox.showinfo("Geri Alındı", res['message'])
            self._render_undo_list()
        else:
            messagebox.showerror("Hata", res['message'])

    def _undo_last(self):
        res = SecurityBackupEngine.undo_last()
        if res['success']:
            messagebox.showinfo("Geri Alındı", res['message'])
            self._render_undo_list()
        else:
            messagebox.showwarning("Bilgi", res['message'])
