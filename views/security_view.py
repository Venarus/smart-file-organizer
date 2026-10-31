import os
import customtkinter as ctk
from tkinter import messagebox
from theme import FluentTheme
from security_backup import SecurityBackupEngine

class SecurityBackupView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

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
            text="Güvenlik, Yedekleme ve Geri Alma (Undo)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Yapılan her dosya hareketini tek tıkla geri alın ve sistem güvenlik korumalarını yönetin",
            font=ctk.CTkFont(size=13),
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
        undo_card.pack(fill="x", padx=16, pady=(0, 14))

        inner_u = ctk.CTkFrame(undo_card, fg_color="transparent")
        inner_u.pack(fill="x", padx=16, pady=14)

        u_text = ctk.CTkFrame(inner_u, fg_color="transparent")
        u_text.pack(side="left")

        ctk.CTkLabel(
            u_text,
            text="Hızlı Geri Alma (1-Click Undo):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            u_text,
            text="Yanlışlıkla düzenlenen veya yeri değiştirilen son dosyayı anında eski yerine döndürün.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        ctk.CTkButton(
            inner_u,
            text="↩️ En Son İşlemi Geri Al",
            font=ctk.CTkFont(size=13, weight="bold"),
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
        sec_card.pack(fill="x", padx=16, pady=(0, 14))

        inner_sec = ctk.CTkFrame(sec_card, fg_color="transparent")
        inner_sec.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner_sec,
            text="🛡️ Aktif Sistem Güvenlik Korumaları:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        guarantees = [
            ("✅ İndirme Koruması:", "Tarayıcınız dosya indirirken (.crdownload, .tmp, .part) dosyalar asla taşınmaz."),
            ("✅ Dosya Kilidi Testi:", "Başka bir programda açık olan veya yazılan dosyalar kilit açılana kadar bekletilir."),
            ("✅ Masaüstü Taban Koruması:", "Masaüstünüzde önceden var olan mevcut dosyalarınız asla klasörlere dağıtılmaz."),
            ("✅ İsim Çakışma Önleyici:", "Hedefte aynı isimde dosya varsa üzerine yazılmaz, (1), (2) şeklinde korunur.")
        ]

        for title, desc in guarantees:
            row = ctk.CTkFrame(inner_sec, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=c('success'), width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=11), text_color=c('text_secondary'), anchor="w").pack(side="left")

        # 3. Geri Alınabilir İşlem Listesi
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            list_header,
            text="Geri Alınabilir Aktif İşlemler Defteri",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_undo_list()

    def _render_undo_list(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll.winfo_children():
            w.destroy()

        active_txs = SecurityBackupEngine.get_history(limit=50, active_only=True)

        if not active_txs:
            ctk.CTkLabel(
                self.scroll,
                text="Geri alınabilecek aktif dosya hareketi bulunmuyor.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=30)
            return

        for tx in active_txs:
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

            ctk.CTkLabel(
                left,
                text=f"📄 {tx['file_name']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=c('text_primary')
            ).pack(anchor="w")

            detail_str = f"Eski Konum: {tx['original_path']}  ➔  Yeni Konum: {tx['target_path']}"
            ctk.CTkLabel(
                left,
                text=detail_str,
                font=ctk.CTkFont(size=10),
                text_color=c('text_muted')
            ).pack(anchor="w", pady=(2, 0))

            ctk.CTkButton(
                inner,
                text="↩️ Geri Al",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                width=80,
                height=26,
                corner_radius=6,
                command=lambda tid=tx['id']: self._undo_single(tid)
            ).pack(side="right")

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
