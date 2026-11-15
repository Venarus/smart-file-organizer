import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme
from organizer import organize_file
from animation import FluidAnimator, UIBridge


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
            text="Manuel dosya ve klasörleri sürükleyip bırakarak veya seçerek Folders içerisine organize edin",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Büyük Sürükle-Bırak Alanı
        self.drop_area = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=16,
            border_width=2,
            border_color=c('accent')
        )
        self.drop_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        FluidAnimator.bind_card_hover(
            self.drop_area,
            self.theme_mode,
            normal_border_token='accent',
            hover_border_token='accent_light'
        )

        center_box = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.46, anchor="center")

        ctk.CTkLabel(
            center_box,
            text="📥",
            font=ctk.CTkFont(size=54)
        ).pack(pady=(0, 10))

        self.lbl_drop_title = ctk.CTkLabel(
            center_box,
            text="Dosyaları veya Klasörleri Buraya Bırakın",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=c('text_primary')
        )
        self.lbl_drop_title.pack(pady=(0, 6))

        self.lbl_drop_sub = ctk.CTkLabel(
            center_box,
            text="İster tek tek, ister yüzlerce dosyayı aynı anda sürükleyin.\nAI Zekâsı dosyalarınızı analiz edip Folders klasöründeki doğru yerlerine taşır.",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary'),
            justify="center"
        )
        self.lbl_drop_sub.pack(pady=(0, 16))

        self.progress_bar = ctk.CTkProgressBar(center_box, width=320, height=8, corner_radius=4)
        self.progress_bar.set(0.0)
        self.progress_bar.configure(progress_color=c('accent'))
        self.progress_bar.pack(pady=(0, 16))

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
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
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

    def _process_items_with_progress(self, raw_paths):
        target_base = self.app.cfg.get('target', '')
        allow_new = self.app.cfg.get('allow_new_categories', True)

        def _worker():
            file_list = []
            for p in raw_paths:
                if os.path.isfile(p):
                    file_list.append(p)
                elif os.path.isdir(p):
                    try:
                        for item in os.listdir(p):
                            ip = os.path.join(p, item)
                            if os.path.isfile(ip):
                                file_list.append(ip)
                    except Exception:
                        pass

            total = len(file_list)
            if total == 0:
                UIBridge.post(lambda: FluidAnimator.show_toast(
                    self.app,
                    "Bilgi",
                    "Seçilen konumda organize edilecek uygun dosya bulunamadı.",
                    theme_mode=self.theme_mode,
                    level='warning'
                ))
                return

            events = []
            for idx, fp in enumerate(file_list, 1):
                ev = organize_file(fp, target_base, allow_new)
                if ev and ev.get('status') == 'success':
                    events.append(ev)
                ratio = idx / float(total)
                UIBridge.post(lambda r=ratio, i=idx, t=total: self._update_progress_ui(r, i, t))

            def _finish():
                try:
                    if self.winfo_exists():
                        self.lbl_drop_title.configure(text=f"✅ {len(events)} Dosya Başarıyla Organize Edildi!")
                        FluidAnimator.animate_progress(self.progress_bar, 1.0, duration_ms=180)
                    if events:
                        self.app.handle_background_events(events)
                except Exception:
                    pass

            UIBridge.post(_finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress_ui(self, ratio, current_idx, total_cnt):
        try:
            if self.winfo_exists():
                self.progress_bar.set(ratio)
                self.lbl_drop_title.configure(text=f"⚡ Organize Ediliyor ({current_idx}/{total_cnt})...")
        except Exception:
            pass

    def _pick_files(self):
        files = filedialog.askopenfilenames(title="Düzenlenecek Dosyaları Seçin")
        if files:
            self._process_items_with_progress(list(files))

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Düzenlenecek Klasörü Seçin")
        if folder:
            self._process_items_with_progress([folder])
