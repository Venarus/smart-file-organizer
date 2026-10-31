import os
import customtkinter as ctk
from theme import FluentTheme
from security_backup import SecurityBackupEngine

class ActivityView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.current_filter = "Tümü"
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
            text="Aktivite Merkezi (Activity Center)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Arka plan izleyicisi ve manuel yapılan tüm dosya taşıma işlemlerinin kayıtları",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Filtre ve Aksiyon Barı
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 10))

        # Filtre butonları
        btn_box = ctk.CTkFrame(bar, fg_color="transparent")
        btn_box.pack(side="left")

        for f_name in ["Tümü", "Aktif", "Geri Alınan"]:
            bg = c('accent') if f_name == self.current_filter else c('bg_card')
            ctk.CTkButton(
                btn_box,
                text=f_name,
                font=ctk.CTkFont(size=12),
                fg_color=bg,
                hover_color=c('accent_hover'),
                text_color=c('text_primary'),
                width=75,
                height=30,
                corner_radius=6,
                command=lambda fn=f_name: self._set_filter(fn)
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            bar,
            text="Geçmişi Sıfırla",
            font=ctk.CTkFont(size=11),
            fg_color=c('danger_bg'),
            hover_color=c('danger'),
            width=95,
            height=30,
            corner_radius=6,
            command=self._clear_history
        ).pack(side="right")

        # Liste Alanı (Katı Mica Arka Planı yırtılmaları önler)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_list()

    def _set_filter(self, f_name):
        self.current_filter = f_name
        self._build_ui()

    def _render_list(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll.winfo_children():
            w.destroy()

        history = SecurityBackupEngine.get_history(limit=40)

        if self.current_filter == "Aktif":
            history = [tx for tx in history if tx.get('status') == 'active']
        elif self.current_filter == "Geri Alınan":
            history = [tx for tx in history if tx.get('status') == 'undone']

        if not history:
            ctk.CTkLabel(
                self.scroll,
                text="Bu filtreye uygun kayıtlı işlem bulunmuyor.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=40)
            return

        for tx in history:
            card = ctk.CTkFrame(
                self.scroll,
                fg_color=c('bg_card'),
                corner_radius=8,
                border_width=1,
                border_color=c('border')
            )
            card.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            is_undone = tx.get('status') == 'undone'
            status_badge = "↩️ [Geri Alındı]" if is_undone else "✅ [Taşındı]"
            status_color = c('warning') if is_undone else c('success')

            header = ctk.CTkFrame(left, fg_color="transparent")
            header.pack(anchor="w")

            ctk.CTkLabel(header, text=status_badge, font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(header, text=tx.get('file_name', ''), font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_primary')).pack(side="left")

            details = f"🕒 {tx.get('timestamp')}  •  Kategori: {tx.get('category')}  •  Hedef: {tx.get('target_path')}"
            ctk.CTkLabel(left, text=details, font=ctk.CTkFont(size=10), text_color=c('text_muted')).pack(anchor="w", pady=(2, 0))

    def _clear_history(self):
        SecurityBackupEngine.clear_history()
        self._render_list()
