import os
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme

class SmartOrgView(ctk.CTkFrame):
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
            text="Akıllı Düzenleme (Smart Organization)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Manuel dosya ve klasörleri sürükleyip bırakarak Folders içerisine organize edin",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Büyük Sürükle-Bırak Alanı
        drop_area = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=16,
            border_width=2,
            border_color=c('accent')
        )
        drop_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        center_box = ctk.CTkFrame(drop_area, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            center_box,
            text="📥",
            font=ctk.CTkFont(size=56)
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            center_box,
            text="Dosyaları veya Klasörleri Buraya Bırakın",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=c('text_primary')
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            center_box,
            text="İster tek tek, ister yüzlerce dosyayı aynı anda sürükleyin.\nAI Zekâsı dosyalarınızı analiz edip Folders klasöründeki doğru yerlerine taşır.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary'),
            justify="center"
        ).pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(center_box, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row,
            text="📄 Dosya(lar) Seç",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=38,
            corner_radius=8,
            command=self._pick_files
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row,
            text="📁 Klasör Seç",
            font=ctk.CTkFont(size=13),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            height=38,
            corner_radius=8,
            command=self._pick_folder
        ).pack(side="left", padx=8)

        # Alt Bilgi Çubuğu
        footer = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        footer.pack(fill="x", padx=16, pady=(0, 10))

        inner_f = ctk.CTkFrame(footer, fg_color="transparent")
        inner_f.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(
            inner_f,
            text="💡 İpucu: Masaüstünüzdeki mevcut dosyalarınız bu işlemlerden asla etkilenmez ve güvenle korunur.",
            font=ctk.CTkFont(size=12),
            text_color=c('accent_light')
        ).pack(side="left")

        ctk.CTkButton(
            inner_f,
            text="📂 Folders'ı Aç",
            font=ctk.CTkFont(size=11),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            height=28,
            corner_radius=6,
            command=self.app.open_target_folder
        ).pack(side="right")

    def _pick_files(self):
        files = filedialog.askopenfilenames(title="Düzenlenecek Dosyaları Seçin")
        if files:
            self.app.on_files_dropped(list(files))

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Düzenlenecek Klasörü Seçin")
        if folder:
            self.app.on_files_dropped([folder])
