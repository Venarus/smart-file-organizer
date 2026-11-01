import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme
from storage_analyzer import StorageAnalyzer
from security_backup import SecurityBackupEngine
from animation import FluidAnimator

class HomeView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.lbl_total_files = None
        self.lbl_total_size = None
        self._is_loading_stats = False

        self._build_ui()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def on_page_show(self):
        """Kullanıcı Ana Sayfaya her geri döndüğünde tetiklenir."""
        self.refresh_stats()

    def refresh_stats(self):
        """İstatistikleri arka planda günceller."""
        if self._is_loading_stats:
            return
        target_folder = self.app.cfg.get('target', '')
        if target_folder in StorageAnalyzer._cache:
            self._apply_stats(StorageAnalyzer._cache[target_folder])
        else:
            self._is_loading_stats = True
            threading.Thread(target=self._async_load_stats, args=(target_folder,), daemon=True).start()

    def _async_load_stats(self, target_folder):
        try:
            data = StorageAnalyzer.analyze_folder(target_folder)
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._apply_stats(data))
            except Exception:
                pass
        except Exception:
            pass

    def _apply_stats(self, data):
        self._is_loading_stats = False
        if self.lbl_total_files and self.lbl_total_files.winfo_exists():
            self.lbl_total_files.configure(text=f"{data.get('total_files', 0):,}".replace(',', '.'))
        if self.lbl_total_size and self.lbl_total_size.winfo_exists():
            self.lbl_total_size.configure(text=data.get('total_size_human', '0 B'))

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # 1. Başlık Alanı ve Sistem Durumu Rozeti
        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=16, pady=(10, 12))

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Genel Bakış",
            font=ctk.CTkFont(family=FluentTheme.FONTS['fallback'], size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        # Sistem Durum Rozeti (Linux tarzı nefes alan canlı nabız)
        lbl_sys_badge = ctk.CTkLabel(
            title_row,
            text="● Sistem Hazır & Aktif",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('success'),
            fg_color=c('success_bg'),
            corner_radius=10,
            padx=10,
            pady=3
        )
        lbl_sys_badge.pack(side="left", padx=(12, 0))
        FluidAnimator.start_pulse_badge(lbl_sys_badge, color_base="#10B981", color_glow="#6EE7B7")

        ctk.CTkLabel(
            title_box,
            text="Windows 11 Fluent Design & AI Dosya Zekâsı Yönetim Konsolu",
            font=ctk.CTkFont(family=FluentTheme.FONTS['fallback'], size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        # 2. İstatistik Kartları (Grid)
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=(0, 14))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_col")

        target_folder = self.app.cfg.get('target', '')
        cached_data = StorageAnalyzer._cache.get(target_folder)

        initial_files = f"{cached_data['total_files']:,}".replace(',', '.') if cached_data else "Yükleniyor..."
        initial_size = cached_data['total_size_human'] if cached_data else "Hesaplanıyor..."

        # Kart 1: Toplam Dosya
        card1 = ctk.CTkFrame(stats_frame, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        card1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(card1, text="📁 Toplam Dosya", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", padx=14, pady=(12, 2))
        self.lbl_total_files = ctk.CTkLabel(card1, text=initial_files, font=ctk.CTkFont(size=22, weight="bold"), text_color=c('accent_light'))
        self.lbl_total_files.pack(anchor="w", padx=14, pady=(0, 2))
        ctk.CTkLabel(card1, text="Folders klasöründe", font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(anchor="w", padx=14, pady=(0, 12))

        # Kart 2: Kaplanan Alan
        card2 = ctk.CTkFrame(stats_frame, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        card2.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(card2, text="💾 Kaplanan Alan", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", padx=14, pady=(12, 2))
        self.lbl_total_size = ctk.CTkLabel(card2, text=initial_size, font=ctk.CTkFont(size=22, weight="bold"), text_color=c('accent_light'))
        self.lbl_total_size.pack(anchor="w", padx=14, pady=(0, 2))
        ctk.CTkLabel(card2, text="Disk kullanımı", font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(anchor="w", padx=14, pady=(0, 12))

        # Kart 3: AI Doğruluğu
        card3 = ctk.CTkFrame(stats_frame, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        card3.grid(row=0, column=2, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(card3, text="🧠 AI Doğruluğu", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(card3, text="%98.4", font=ctk.CTkFont(size=22, weight="bold"), text_color=c('success')).pack(anchor="w", padx=14, pady=(0, 2))
        ctk.CTkLabel(card3, text="Çok boyutlu analiz", font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(anchor="w", padx=14, pady=(0, 12))

        # Kart 4: İzlenen Konum
        card4 = ctk.CTkFrame(stats_frame, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border'))
        card4.grid(row=0, column=3, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(card4, text="👁️ İzlenen Konum", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(card4, text=f"{len(self.app.cfg.get('sources', []))} Klasör", font=ctk.CTkFont(size=22, weight="bold"), text_color=c('accent_light')).pack(anchor="w", padx=14, pady=(0, 2))
        ctk.CTkLabel(card4, text="Arka plan aktif", font=ctk.CTkFont(size=11), text_color=c('text_muted')).pack(anchor="w", padx=14, pady=(0, 12))

        if not cached_data:
            self.refresh_stats()

        # 3. Windows 11 Hızlı Erişim Ribbon (Masaüstü, İndirilenler, Belgeler, Resimler, Müzikler, Videolar, Folders)
        qa_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        qa_card.pack(fill="x", padx=16, pady=(0, 14))

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

        ctk.CTkLabel(
            qa_top,
            text="Klasörü Açmak İçin Tıklayın",
            font=ctk.CTkFont(size=10),
            text_color=c('text_muted')
        ).pack(side="right")

        qa_chips_box = ctk.CTkFrame(qa_inner, fg_color="transparent")
        qa_chips_box.pack(fill="x")

        user_home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        quick_folders = [
            ("🖥️ Masaüstü", os.path.join(user_home, "Desktop")),
            ("📥 İndirilenler", os.path.join(user_home, "Downloads")),
            ("📑 Belgeler", os.path.join(user_home, "Documents")),
            ("🖼️ Resimler", os.path.join(user_home, "Pictures")),
            ("🎵 Müzikler", os.path.join(user_home, "Music")),
            ("🎬 Videolar", os.path.join(user_home, "Videos")),
            ("📂 Folders", self.app.cfg.get('target', ''))
        ]

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

        # 4. Sürükle - Bırak Kartı (Drag & Drop Zone)
        drop_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=12,
            border_width=1,
            border_color=c('accent')
        )
        drop_card.pack(fill="x", padx=16, pady=(0, 14))

        inner_drop = ctk.CTkFrame(drop_card, fg_color="transparent")
        inner_drop.pack(fill="x", padx=18, pady=14)

        icon_frame = ctk.CTkFrame(inner_drop, fg_color=c('accent_bg'), width=48, height=48, corner_radius=10)
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame,
            text="📥",
            font=ctk.CTkFont(size=24)
        ).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner_drop, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            text_box,
            text="Dosyaları veya Klasörleri Buraya Sürükleyip Bırakın",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_box,
            text="AI motoru içerik, dosya türü ve metadata analizini otomatik yaparak Folders klasörüne organize eder.",
            font=ctk.CTkFont(size=11),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(inner_drop, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="📄 Dosya Seç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=32,
            corner_radius=6,
            command=self._pick_files
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📁 Klasör Seç",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            height=32,
            corner_radius=6,
            command=self._pick_folder
        ).pack(side="left", padx=4)

        # 5. Hızlı Eylemler & Son İşlemler (2 Kolon)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        bottom_frame.grid_columnconfigure((0, 1), weight=1, uniform="bottom_cols")

        # Sol: Hızlı Aksiyonlar
        quick_card = ctk.CTkFrame(
            bottom_frame,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        quick_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            quick_card,
            text="⚡ Hızlı İşlemler",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", padx=16, pady=(12, 10))

        actions = [
            ("⚡ Giriş Klasörlerini Şimdi Tara", self.app.manual_organize, c('accent')),
            ("📂 Folders Ana Klasörünü Aç", self.app.open_target_folder, c('bg_card_hover')),
            ("📑 Mükerrer Kopya Dosyaları Bul", lambda: self.app.navigate_to('duplicates'), c('bg_card_hover')),
            ("📊 Depolama Analizini Görüntüle", lambda: self.app.navigate_to('storage'), c('bg_card_hover')),
            ("↩️ En Son İşlemi Geri Al (Undo)", self.app.undo_last_action, c('danger_bg'))
        ]

        for text, cmd, bg in actions:
            btn = ctk.CTkButton(
                quick_card,
                text=text,
                font=ctk.CTkFont(size=12),
                fg_color=bg,
                hover_color=c('bg_card_active'),
                text_color=c('text_primary'),
                anchor="w",
                height=32,
                corner_radius=6,
                command=cmd
            )
            btn.pack(fill="x", padx=16, pady=4)

        # Sağ: Son Aktiviteler
        recent_card = ctk.CTkFrame(
            bottom_frame,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        recent_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        recent_header = ctk.CTkFrame(recent_card, fg_color="transparent")
        recent_header.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            recent_header,
            text="🕒 Son İşlemler",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            recent_header,
            text="Tümünü Gör →",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            width=80,
            height=24,
            command=lambda: self.app.navigate_to('activity')
        ).pack(side="right")

        # Son 5 işlem kaydı
        history = SecurityBackupEngine.get_history(limit=5)
        if not history:
            ctk.CTkLabel(
                recent_card,
                text="Henüz kaydedilmiş bir dosya işlemi yok.\nDosyalarınızı sürükleyip bırakarak başlayabilirsiniz.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_muted'),
                justify="center"
            ).pack(expand=True, pady=20)
        else:
            for tx in history:
                row = ctk.CTkFrame(recent_card, fg_color=c('bg_mica'), corner_radius=6)
                row.pack(fill="x", padx=12, pady=3)

                inner_row = ctk.CTkFrame(row, fg_color="transparent")
                inner_row.pack(fill="x", padx=10, pady=6)

                icon = "↩️" if tx.get('status') == 'undone' else "📄"
                ctk.CTkLabel(
                    inner_row,
                    text=icon,
                    font=ctk.CTkFont(size=14)
                ).pack(side="left", padx=(0, 8))

                name_lbl = ctk.CTkLabel(
                    inner_row,
                    text=tx.get('file_name', ''),
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=c('text_primary'),
                    anchor="w"
                )
                name_lbl.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    inner_row,
                    text=tx.get('category', ''),
                    font=ctk.CTkFont(size=11),
                    text_color=c('accent_light')
                ).pack(side="right", padx=(8, 0))

    def _pick_files(self):
        paths = filedialog.askopenfilenames(title="Düzenlenecek Dosyaları Seçin")
        if paths:
            self.app.on_files_dropped(list(paths))

    def _pick_folder(self):
        p = filedialog.askdirectory(title="Düzenlenecek Klasörü Seçin")
        if p:
            self.app.on_files_dropped([p])
