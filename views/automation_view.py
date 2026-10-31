import os
import customtkinter as ctk
from tkinter import filedialog
from theme import FluentTheme
from config import (
    save_config,
    DEFAULT_DESKTOP,
    DEFAULT_DOWNLOADS,
    DEFAULT_DOCUMENTS,
    DEFAULT_PICTURES,
    DEFAULT_MUSIC,
    DEFAULT_VIDEOS
)

class AutomationView(ctk.CTkFrame):
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
            text="Otomasyon ve Arka Plan İzleme",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Giriş klasörlerini otomatik izleyin, yeni gelen dosyaları anında Folders'a yönlendirin",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # 1. Kart: İzleme Durumu ve Anahtar
        status_card = ctk.CTkFrame(
            scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        status_card.pack(fill="x", pady=(0, 12))

        inner_status = ctk.CTkFrame(status_card, fg_color="transparent")
        inner_status.pack(fill="x", padx=16, pady=16)

        left_stat = ctk.CTkFrame(inner_status, fg_color="transparent")
        left_stat.pack(side="left")

        is_active = self.app.cfg.get('auto_watch', True)
        self.status_title = ctk.CTkLabel(
            left_stat,
            text="🟢 Arka Plan İzlemesi Aktif" if is_active else "⏸️ Arka Plan İzlemesi Duraklatıldı",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('success') if is_active else c('warning')
        )
        self.status_title.pack(anchor="w")

        ctk.CTkLabel(
            left_stat,
            text="Yeni dosya geldiğinde indirme bitişi beklenir ve otomatik organize edilir.",
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        self.switch_watch = ctk.CTkSwitch(
            inner_status,
            text="Otomatik İzleme",
            font=ctk.CTkFont(size=13),
            command=self._toggle_watch
        )
        self.switch_watch.pack(side="right")
        if is_active:
            self.switch_watch.select()
        else:
            self.switch_watch.deselect()

        # 2. Kart: Giriş Klasörleri
        sources_card = ctk.CTkFrame(
            scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        sources_card.pack(fill="x", pady=(0, 12))

        inner_src = ctk.CTkFrame(sources_card, fg_color="transparent")
        inner_src.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(
            inner_src,
            text="İzlenen Giriş Klasörleri:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w", pady=(0, 8))

        active_sources = [os.path.normpath(s).lower() for s in self.app.cfg.get('sources', [])]

        # Windows 11 Sabitlenen Klasörler Checkboxları
        self.var_dt = ctk.BooleanVar(value=os.path.normpath(DEFAULT_DESKTOP).lower() in active_sources)
        cb_dt = ctk.CTkCheckBox(inner_src, text=f"🖥️ Masaüstü ({DEFAULT_DESKTOP}) — Sadece Yeni Gelenler (Koruma Aktif)", variable=self.var_dt, command=self._update_sources)
        cb_dt.pack(anchor="w", pady=4)

        self.var_dl = ctk.BooleanVar(value=os.path.normpath(DEFAULT_DOWNLOADS).lower() in active_sources)
        cb_dl = ctk.CTkCheckBox(inner_src, text=f"⬇️ İndirilenler ({DEFAULT_DOWNLOADS})", variable=self.var_dl, command=self._update_sources)
        cb_dl.pack(anchor="w", pady=4)

        self.var_doc = ctk.BooleanVar(value=os.path.normpath(DEFAULT_DOCUMENTS).lower() in active_sources)
        cb_doc = ctk.CTkCheckBox(inner_src, text=f"📄 Belgeler ({DEFAULT_DOCUMENTS})", variable=self.var_doc, command=self._update_sources)
        cb_doc.pack(anchor="w", pady=4)

        self.var_pic = ctk.BooleanVar(value=os.path.normpath(DEFAULT_PICTURES).lower() in active_sources)
        cb_pic = ctk.CTkCheckBox(inner_src, text=f"🖼️ Resimler ({DEFAULT_PICTURES})", variable=self.var_pic, command=self._update_sources)
        cb_pic.pack(anchor="w", pady=4)

        self.var_mus = ctk.BooleanVar(value=os.path.normpath(DEFAULT_MUSIC).lower() in active_sources)
        cb_mus = ctk.CTkCheckBox(inner_src, text=f"🎵 Müzikler ({DEFAULT_MUSIC})", variable=self.var_mus, command=self._update_sources)
        cb_mus.pack(anchor="w", pady=4)

        self.var_vid = ctk.BooleanVar(value=os.path.normpath(DEFAULT_VIDEOS).lower() in active_sources)
        cb_vid = ctk.CTkCheckBox(inner_src, text=f"🎬 Videolar ({DEFAULT_VIDEOS})", variable=self.var_vid, command=self._update_sources)
        cb_vid.pack(anchor="w", pady=4)

        # Özel klasörler
        standard_dirs = [DEFAULT_DESKTOP, DEFAULT_DOWNLOADS, DEFAULT_DOCUMENTS, DEFAULT_PICTURES, DEFAULT_MUSIC, DEFAULT_VIDEOS]
        standard_norms = [os.path.normpath(x).lower() for x in standard_dirs]
        custom_sources = [s for s in self.app.cfg.get('sources', []) if os.path.normpath(s).lower() not in standard_norms]
        if custom_sources:
            ctk.CTkLabel(inner_src, text="Özel Eklenen Klasörler:", font=ctk.CTkFont(size=12, weight="bold"), text_color=c('text_secondary')).pack(anchor="w", pady=(10, 4))
            for cs in custom_sources:
                cs_row = ctk.CTkFrame(inner_src, fg_color=c('bg_mica'), corner_radius=6)
                cs_row.pack(fill="x", pady=2)
                ctk.CTkLabel(cs_row, text=f"📁 {cs}", font=ctk.CTkFont(size=11), text_color=c('text_primary')).pack(side="left", padx=8, pady=4)
                ctk.CTkButton(
                    cs_row,
                    text="Kaldır",
                    font=ctk.CTkFont(size=10),
                    fg_color=c('danger_bg'),
                    hover_color=c('danger'),
                    width=50,
                    height=22,
                    corner_radius=4,
                    command=lambda p=cs: self._remove_custom_source(p)
                ).pack(side="right", padx=6)

        ctk.CTkButton(
            inner_src,
            text="+ Özel Klasör Ekle...",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            height=30,
            corner_radius=6,
            command=self._add_custom_folder
        ).pack(anchor="w", pady=(10, 0))

        # 3. Kart: Hedef Klasör ve Tarama Frekansı
        target_card = ctk.CTkFrame(
            scroll,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        target_card.pack(fill="x", pady=(0, 12))

        inner_tgt = ctk.CTkFrame(target_card, fg_color="transparent")
        inner_tgt.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner_tgt, text="Hedef Klasör:", font=ctk.CTkFont(size=13, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 4))

        tgt_row = ctk.CTkFrame(inner_tgt, fg_color="transparent")
        tgt_row.pack(fill="x", pady=(0, 12))

        self.tgt_lbl = ctk.CTkLabel(tgt_row, text=self.app.cfg.get('target', ''), font=ctk.CTkFont(size=12), text_color=c('accent_light'))
        self.tgt_lbl.pack(side="left")

        ctk.CTkButton(
            tgt_row,
            text="Değiştir",
            font=ctk.CTkFont(size=11),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            width=70,
            height=26,
            corner_radius=6,
            command=self._change_target
        ).pack(side="right")

        # Tarama Sıklığı
        ctk.CTkLabel(inner_tgt, text="Arka Plan Tarama Sıklığı:", font=ctk.CTkFont(size=13, weight="bold"), text_color=c('text_primary')).pack(anchor="w", pady=(0, 4))
        self.interval_menu = ctk.CTkOptionMenu(
            inner_tgt,
            values=["2 saniye", "4 saniye (Önerilen)", "10 saniye", "30 saniye"],
            width=160,
            height=28,
            corner_radius=6,
            command=self._on_interval_change
        )
        self.interval_menu.pack(anchor="w")
        curr_int = self.app.cfg.get('check_interval', 4)
        if curr_int == 2: self.interval_menu.set("2 saniye")
        elif curr_int == 10: self.interval_menu.set("10 saniye")
        elif curr_int == 30: self.interval_menu.set("30 saniye")
        else: self.interval_menu.set("4 saniye (Önerilen)")

    def _toggle_watch(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        is_on = bool(self.switch_watch.get())
        self.app.cfg['auto_watch'] = is_on
        save_config(self.app.cfg)
        self.status_title.configure(
            text="🟢 Arka Plan İzlemesi Aktif" if is_on else "⏸️ Arka Plan İzlemesi Duraklatıldı",
            text_color=c('success') if is_on else c('warning')
        )
        self.app.update_status_footer()

    def _update_sources(self):
        new_sources = []
        if self.var_dt.get(): new_sources.append(DEFAULT_DESKTOP)
        if self.var_dl.get(): new_sources.append(DEFAULT_DOWNLOADS)
        if self.var_doc.get(): new_sources.append(DEFAULT_DOCUMENTS)
        if self.var_pic.get(): new_sources.append(DEFAULT_PICTURES)
        if self.var_mus.get(): new_sources.append(DEFAULT_MUSIC)
        if self.var_vid.get(): new_sources.append(DEFAULT_VIDEOS)

        # Özel kaynakları koru
        standard_dirs = [DEFAULT_DESKTOP, DEFAULT_DOWNLOADS, DEFAULT_DOCUMENTS, DEFAULT_PICTURES, DEFAULT_MUSIC, DEFAULT_VIDEOS]
        standard_norms = [os.path.normpath(x).lower() for x in standard_dirs]
        for s in self.app.cfg.get('sources', []):
            norm_s = os.path.normpath(s).lower()
            if norm_s not in standard_norms:
                new_sources.append(s)

        self.app.cfg['sources'] = new_sources
        save_config(self.app.cfg)
        self.app.update_status_footer()

    def _add_custom_folder(self):
        f = filedialog.askdirectory(title="İzlenecek Özel Klasör Seç")
        if f:
            norm = os.path.normpath(f)
            sources = self.app.cfg.get('sources', [])
            if norm not in sources:
                sources.append(norm)
                self.app.cfg['sources'] = sources
                save_config(self.app.cfg)
                self._build_ui()
                self.app.update_status_footer()

    def _remove_custom_source(self, path):
        sources = self.app.cfg.get('sources', [])
        if path in sources:
            sources.remove(path)
            self.app.cfg['sources'] = sources
            save_config(self.app.cfg)
            self._build_ui()
            self.app.update_status_footer()

    def _change_target(self):
        f = filedialog.askdirectory(title="Hedef Klasör Seç (Folders)", initialdir=self.app.cfg.get('target', ''))
        if f:
            self.app.cfg['target'] = os.path.normpath(f)
            self.tgt_lbl.configure(text=self.app.cfg['target'])
            save_config(self.app.cfg)

    def _on_interval_change(self, val):
        sec = 4
        if "2" in val: sec = 2
        elif "10" in val: sec = 10
        elif "30" in val: sec = 30
        self.app.cfg['check_interval'] = sec
        save_config(self.app.cfg)
