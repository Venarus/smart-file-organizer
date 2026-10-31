import os
import threading
import customtkinter as ctk
from tkinter import messagebox
from theme import FluentTheme
from duplicate_manager import DuplicateManager

class DuplicateView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.dup_data = None
        self._is_scanning = False
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
            text="Mükerrer Dosya Yöneticisi (Duplicate Manager)",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Aynı içeriğe sahip kopya dosyaları SHA-256 doğrulukla bulun ve disk alanı kazanın",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Tarama ve İstatistik Kartı
        top_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        top_card.pack(fill="x", padx=16, pady=(0, 14))

        inner_top = ctk.CTkFrame(top_card, fg_color="transparent")
        inner_top.pack(fill="x", padx=16, pady=14)

        info_box = ctk.CTkFrame(inner_top, fg_color="transparent")
        info_box.pack(side="left", fill="x", expand=True)

        self.lbl_stats = ctk.CTkLabel(
            info_box,
            text="Tarama bekleniyor...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        )
        self.lbl_stats.pack(anchor="w")

        self.lbl_wasted = ctk.CTkLabel(
            info_box,
            text="Folders klasöründeki gereksiz kopyaları tespit etmek için taramayı başlatın.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_muted')
        )
        self.lbl_wasted.pack(anchor="w")

        # Filtre ve Tarama Butonları
        actions_box = ctk.CTkFrame(inner_top, fg_color="transparent")
        actions_box.pack(side="right")

        target_base = self.app.cfg.get('target', '')
        subdirs = ["Tüm Folders"]
        if os.path.exists(target_base):
            for d in os.listdir(target_base):
                if os.path.isdir(os.path.join(target_base, d)) and not d.startswith('.'):
                    subdirs.append(d)

        self.folder_combo = ctk.CTkComboBox(
            actions_box,
            values=subdirs,
            width=200,
            height=34,
            corner_radius=6,
            fg_color=c('bg_card_secondary'),
            border_color=c('border'),
            text_color=c('text_primary'),
            button_color=c('accent'),
            button_hover_color=c('accent_hover'),
            dropdown_fg_color=c('bg_card'),
            dropdown_text_color=c('text_primary')
        )
        self.folder_combo.set("Tüm Folders")
        self.folder_combo.pack(side="left", padx=(0, 10))

        self.btn_scan = ctk.CTkButton(
            actions_box,
            text="🔍 Mükerrerleri Tara",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=6,
            command=self.start_scan_thread
        )
        self.btn_scan.pack(side="left")

        # Sonuçlar Alanı
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        if self.dup_data:
            self._render_results()
        else:
            ctk.CTkLabel(
                self.scroll,
                text="📑\n\nMükerrer kopya analizi yapmak için 'Mükerrerleri Tara' butonuna tıklayın.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted'),
                justify="center"
            ).pack(pady=40)

    def start_scan_thread(self):
        if self._is_scanning:
            return

        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self._is_scanning = True
        self.btn_scan.configure(state="disabled", text="⏳ Taranıyor...")
        self.lbl_stats.configure(text="Klasör taranıyor...", text_color=c('accent'))
        self.lbl_wasted.configure(text="Dosya boyutları ve parmak izleri kontrol ediliyor...")

        # Seçili hedefi belirle
        target_base = self.app.cfg.get('target', '')
        selected = self.folder_combo.get()
        if selected != "Tüm Folders":
            target_path = os.path.join(target_base, selected)
        else:
            target_path = target_base

        def progress_cb(msg):
            self.after(0, lambda: self.lbl_wasted.configure(text=msg))

        def worker():
            try:
                res = DuplicateManager.scan_directory(target_path, progress_callback=progress_cb)
            except Exception as e:
                res = {'total_duplicates': 0, 'total_groups': 0, 'wasted_bytes': 0, 'wasted_human': '0 B', 'groups': [], 'error': str(e)}
            self.after(0, lambda: self._on_scan_completed(res))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_completed(self, data):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self._is_scanning = False
        self.btn_scan.configure(state="normal", text="🔍 Mükerrerleri Tara")
        self.dup_data = data

        if 'error' in data:
            self.lbl_stats.configure(text="❌ Tarama Hatası", text_color=c('error'))
            self.lbl_wasted.configure(text=str(data['error']))
            return

        dup_cnt = self.dup_data.get('total_duplicates', 0)
        wasted_str = self.dup_data.get('wasted_human', '0 B')

        if dup_cnt > 0:
            self.lbl_stats.configure(
                text=f"⚠️ {dup_cnt} adet mükerrer kopya dosya tespit edildi!",
                text_color=c('warning')
            )
            self.lbl_wasted.configure(
                text=f"Gereksiz kaplanan disk alanı: {wasted_str} ({self.dup_data.get('total_scanned', 0)} dosya incelendi)",
                text_color=c('text_secondary')
            )
        else:
            self.lbl_stats.configure(
                text="✅ Tebrikler! Hiç mükerrer kopya dosya bulunamadı.",
                text_color=c('success')
            )
            self.lbl_wasted.configure(
                text=f"Toplam {self.dup_data.get('total_scanned', 0)} dosya incelendi, hepsi tekil.",
                text_color=c('text_muted')
            )

        self._render_results()

    def _render_results(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll.winfo_children():
            w.destroy()

        groups = self.dup_data.get('groups', [])
        if not groups:
            ctk.CTkLabel(
                self.scroll,
                text="Hiç kopya dosya bulunmuyor. Klasörünüz tertemiz!",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted')
            ).pack(pady=40)
            return

        for grp in groups:
            group_card = ctk.CTkFrame(
                self.scroll,
                fg_color=c('bg_card'),
                corner_radius=10,
                border_width=1,
                border_color=c('border')
            )
            group_card.pack(fill="x", pady=6)

            header = ctk.CTkFrame(group_card, fg_color="transparent")
            header.pack(fill="x", padx=14, pady=(10, 6))

            ctk.CTkLabel(
                header,
                text=f"📄 {grp['file_name']}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=c('text_primary')
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=f"Boyut: {grp['size_human']} | {len(grp['files'])} Kopya | İsraf: {grp['wasted_human']}",
                font=ctk.CTkFont(size=12),
                text_color=c('accent')
            ).pack(side="right")

            # Dosya listesi
            for idx, item in enumerate(grp['files']):
                is_original = (idx == 0)
                row = ctk.CTkFrame(group_card, fg_color=c('bg_card_secondary'), corner_radius=6)
                row.pack(fill="x", padx=14, pady=3)

                prefix = "👑 [ASIL]" if is_original else "📋 [KOPYA]"
                badge_col = c('success') if is_original else c('warning')

                ctk.CTkLabel(
                    row,
                    text=prefix,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=badge_col,
                    width=70
                ).pack(side="left", padx=(10, 6), pady=6)

                ctk.CTkLabel(
                    row,
                    text=item['path'],
                    font=ctk.CTkFont(size=12),
                    text_color=c('text_primary'),
                    anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=6, pady=6)

                ctk.CTkLabel(
                    row,
                    text=item['modified'],
                    font=ctk.CTkFont(size=11),
                    text_color=c('text_muted')
                ).pack(side="left", padx=8)

                if not is_original:
                    btn_del = ctk.CTkButton(
                        row,
                        text="Sil",
                        font=ctk.CTkFont(size=11, weight="bold"),
                        fg_color=c('error'),
                        hover_color=c('accent_hover'),
                        width=50,
                        height=26,
                        corner_radius=4,
                        command=lambda p=item['path'], g=grp: self._delete_copy(p, g)
                    )
                    btn_del.pack(side="right", padx=(6, 10), pady=4)
                else:
                    ctk.CTkLabel(
                        row,
                        text="Korunuyor",
                        font=ctk.CTkFont(size=11),
                        text_color=c('text_muted'),
                        width=60
                    ).pack(side="right", padx=(6, 10))

            ctk.CTkFrame(group_card, fg_color="transparent", height=6).pack()

    def _delete_copy(self, file_path, group):
        if not messagebox.askyesno("Kopya Dosya Silme Onayı", f"Bu kopya dosyayı silmek istediğinizden emin misiniz?\n\n{file_path}"):
            return

        ok, msg = DuplicateManager.delete_file(file_path)
        if ok:
            messagebox.showinfo("Başarılı", "Kopya dosya başarıyla silindi.")
            # Listeyi güncelle
            group['files'] = [f for f in group['files'] if f['path'] != file_path]
            if len(group['files']) <= 1:
                self.dup_data['groups'] = [g for g in self.dup_data['groups'] if g['hash'] != group['hash']]
            self._render_results()
        else:
            messagebox.showerror("Hata", f"Dosya silinemedi:\n{msg}")
