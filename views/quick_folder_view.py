"""
Windows 11 Fluent Pinned Folder View (Hızlı Erişim Klasör Görünümü)
Displays Desktop, Downloads, Documents, Pictures, Music, and Videos
with real-time file listing, native icons, baseline protection status,
and 1-click intelligent organization into Desktop/Folders.
"""

import os
import sys
import threading
from datetime import datetime
import customtkinter as ctk

from theme import FluentTheme
from thumbnail_engine import ThumbnailEngine
from organizer import organize_file
from config import (
    DEFAULT_DESKTOP,
    DEFAULT_DOWNLOADS,
    DEFAULT_DOCUMENTS,
    DEFAULT_PICTURES,
    DEFAULT_MUSIC,
    DEFAULT_VIDEOS,
    DEFAULT_TARGET
)

FOLDER_META = {
    'desktop': {
        'name': 'Masaüstü',
        'path': DEFAULT_DESKTOP,
        'is_desktop': True,
        'desc': 'Masaüstü çalışma alanı. Önceden var olan kısayol ve klasörleriniz korunur.'
    },
    'downloads': {
        'name': 'İndirilenler',
        'path': DEFAULT_DOWNLOADS,
        'is_desktop': False,
        'desc': 'İnternet tarayıcılarından ve uygulamalardan indirilen dosyaların varsayılan konumu.'
    },
    'documents': {
        'name': 'Belgeler',
        'path': DEFAULT_DOCUMENTS,
        'is_desktop': False,
        'desc': 'Kişisel ve iş belgeleriniz, ofis dosyalarınız ve kayıtlarınız.'
    },
    'pictures': {
        'name': 'Resimler',
        'path': DEFAULT_PICTURES,
        'is_desktop': False,
        'desc': 'Fotoğraflarınız, ekran görüntüleri ve görsel medya koleksiyonunuz.'
    },
    'music': {
        'name': 'Müzikler',
        'path': DEFAULT_MUSIC,
        'is_desktop': False,
        'desc': 'Ses kayıtları, şarkılar ve ses dosyalarınız.'
    },
    'videos': {
        'name': 'Videolar',
        'path': DEFAULT_VIDEOS,
        'is_desktop': False,
        'desc': 'Video kayıtları, ekran videoları ve film klipleri.'
    }
}

class QuickFolderView(ctk.CTkFrame):
    def __init__(self, master, app_controller, folder_id='documents'):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.folder_id = folder_id
        self.meta = FOLDER_META.get(folder_id, FOLDER_META['documents'])
        self.folder_path = self.meta['path']
        self.theme_mode = self.app.theme_mode

        self._folder_icon = None
        self._load_icon()

        self._build_ui()

    def _load_icon(self):
        try:
            pil_img = ThumbnailEngine._extract_shell_image(self.folder_path, 32, 32)
            if pil_img:
                self._folder_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
        except Exception:
            self._folder_icon = None

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def on_page_show(self):
        self._refresh_content()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # Üst Başlık ve Aksiyon Çubuğu
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 10))

        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left")

        # Klasör İkonu
        if self._folder_icon:
            lbl_ic = ctk.CTkLabel(left_box, text="", image=self._folder_icon)
            lbl_ic.pack(side="left", padx=(0, 10))
        else:
            lbl_ic = ctk.CTkLabel(left_box, text="📁", font=ctk.CTkFont(size=26))
            lbl_ic.pack(side="left", padx=(0, 10))

        title_inner = ctk.CTkFrame(left_box, fg_color="transparent")
        title_inner.pack(side="left")

        ctk.CTkLabel(
            title_inner,
            text=f"{self.meta['name']} 📌",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=c('text_primary')
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_inner,
            text=self.meta['desc'],
            font=ctk.CTkFont(size=12),
            text_color=c('text_secondary')
        ).pack(anchor="w")

        # Sağ Aksiyon Butonları
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        self.btn_organize_now = ctk.CTkButton(
            btn_box,
            text="⚡ Folders'a Organize Et",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self._organize_folder_items
        )
        self.btn_organize_now.pack(side="right", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📂 Gezginde Aç",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=lambda: os.startfile(self.folder_path) if os.path.exists(self.folder_path) else None
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_box,
            text="🔄 Yenile",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=self._refresh_content
        ).pack(side="right", padx=4)

        # Masaüstü Koruma Bilgi Kartı (Sadece Masaüstü için)
        if self.meta.get('is_desktop'):
            protect_card = ctk.CTkFrame(
                self,
                fg_color=c('bg_card'),
                corner_radius=8,
                border_width=1,
                border_color=c('border')
            )
            protect_card.pack(fill="x", padx=16, pady=(0, 8))

            p_inner = ctk.CTkFrame(protect_card, fg_color="transparent")
            p_inner.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(
                p_inner,
                text="🛡️ Masaüstü Koruma Modu Aktif",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=c('success')
            ).pack(side="left")

            baseline_count = len(self.app.cfg.get('desktop_baseline', []))
            ctk.CTkLabel(
                p_inner,
                text=f"— Önceden mevcut olan {baseline_count} öğe (kısayollar, uygulamalar) kilitlidir. Yalnızca yeni indirilen veya kaydedilen dosyalar organize edilir.",
                font=ctk.CTkFont(size=11),
                text_color=c('text_secondary')
            ).pack(side="left", padx=8)

        # Bilgi Barı (Konum ve Durum)
        info_bar = ctk.CTkFrame(self, fg_color="transparent")
        info_bar.pack(fill="x", padx=16, pady=(0, 6))

        is_monitored = any(os.path.normpath(s).lower() == os.path.normpath(self.folder_path).lower() for s in self.app.cfg.get('sources', []))
        status_txt = "🟢 Arka Planda Otomatik İzleniyor" if is_monitored else "⚪ İzleme Dışı"
        status_clr = c('success') if is_monitored else c('text_muted')

        ctk.CTkLabel(
            info_bar,
            text=f"📍 {self.folder_path}",
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        ).pack(side="left")

        ctk.CTkLabel(
            info_bar,
            text=f"•   {status_txt}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_clr
        ).pack(side="left", padx=8)

        # İçerik Alanı (Scrollable Frame - Solid Mica Background)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_files()

    def _refresh_content(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._render_files()

    def _render_files(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        if not os.path.exists(self.folder_path):
            ctk.CTkLabel(
                self.scroll,
                text="Klasör bulunamadı veya erişilemez durumda.",
                font=ctk.CTkFont(size=13),
                text_color=c('danger')
            ).pack(pady=40)
            return

        try:
            items = os.listdir(self.folder_path)
        except Exception as e:
            ctk.CTkLabel(
                self.scroll,
                text=f"Klasör okuma hatası: {e}",
                font=ctk.CTkFont(size=13),
                text_color=c('danger')
            ).pack(pady=40)
            return

        baseline = set(self.app.cfg.get('desktop_baseline', [])) if self.meta.get('is_desktop') else set()
        ignored_names = {'desktop.ini', 'thumbs.db', '.ds_store'}

        # Dosyaları ve klasörleri sınıflandır
        organizable_files = []
        protected_items = []

        for item in items:
            if item.lower() in ignored_names or item.startswith('.'):
                continue
            item_path = os.path.join(self.folder_path, item)
            is_file = os.path.isfile(item_path)

            if self.meta.get('is_desktop') and item in baseline:
                protected_items.append((item, item_path, is_file, True))
            elif is_file:
                organizable_files.append((item, item_path, is_file, False))
            else:
                protected_items.append((item, item_path, is_file, False))

        # 1. Organize Edilmeye Hazır Dosyalar Bölümü
        if organizable_files:
            sec_header = ctk.CTkFrame(self.scroll, fg_color="transparent")
            sec_header.pack(fill="x", pady=(4, 6))

            ctk.CTkLabel(
                sec_header,
                text=f"⚡ Organize Edilecek Dosyalar ({len(organizable_files)})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=c('accent_light')
            ).pack(side="left")

            ctk.CTkLabel(
                sec_header,
                text="Bu dosyalar Folders klasörüne taşınabilir",
                font=ctk.CTkFont(size=11),
                text_color=c('text_secondary')
            ).pack(side="left", padx=8)

            for name, path, is_file, _ in organizable_files:
                self._create_file_row(self.scroll, name, path, is_file, can_organize=True, c=c)
        else:
            empty_box = ctk.CTkFrame(self.scroll, fg_color=c('bg_card'), corner_radius=10, border_width=1, border_color=c('border_subtle'))
            empty_box.pack(fill="x", pady=(4, 12))

            ctk.CTkLabel(
                empty_box,
                text=f"✨ {self.meta['name']} klasörü düzenli ve tertemiz!\nOtomatik izleme aktif: Bu klasöre gelen yeni dosyalar anında Desktop/Folders klasörüne organize edilir.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_secondary'),
                justify="center"
            ).pack(padx=20, pady=16)

        # 2. Korunan veya Sabit Öğeler Bölümü (Masaüstü kısayolları veya alt klasörler)
        if protected_items:
            sec_prot = ctk.CTkFrame(self.scroll, fg_color="transparent")
            sec_prot.pack(fill="x", pady=(12, 6))

            title = "🛡️ Korunan Masaüstü Öğeleri" if self.meta.get('is_desktop') else "📁 Mevcut Klasörler ve Öğeler"
            ctk.CTkLabel(
                sec_prot,
                text=f"{title} ({len(protected_items)})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=c('text_secondary')
            ).pack(side="left")

            for name, path, is_file, is_base in protected_items:
                self._create_file_row(self.scroll, name, path, is_file, can_organize=False, is_baseline=is_base, c=c)

    def _create_file_row(self, parent, name, path, is_file, can_organize, is_baseline=False, c=None):
        row = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=8,
            border_width=1,
            border_color=c('border')
        )
        row.pack(fill="x", pady=2)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)

        icon_char = "📄" if is_file else "📁"
        _, ext = os.path.splitext(name.lower())
        if ext in ['.png', '.jpg', '.jpeg', '.webp']: icon_char = "🖼️"
        elif ext in ['.mp4', '.mkv', '.avi', '.mov']: icon_char = "🎬"
        elif ext in ['.mp3', '.wav', '.flac']: icon_char = "🎵"
        elif ext in ['.zip', '.rar', '.7z']: icon_char = "🗄️"
        elif ext in ['.exe', '.msi']: icon_char = "⚙️"
        elif ext in ['.lnk']: icon_char = "🔗"

        ctk.CTkLabel(
            inner,
            text=icon_char,
            font=ctk.CTkFont(size=15)
        ).pack(side="left", padx=(0, 8))

        # İsim ve Detay
        info_box = ctk.CTkFrame(inner, fg_color="transparent")
        info_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info_box,
            text=name,
            font=ctk.CTkFont(size=12, weight="bold" if can_organize else "normal"),
            text_color=c('text_primary'),
            anchor="w"
        ).pack(anchor="w")

        try:
            stat = os.stat(path)
            size_kb = stat.st_size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            mod_str = datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')
            detail = f"{size_str}  •  {mod_str}" if is_file else f"Klasör  •  {mod_str}"
        except Exception:
            detail = "Bilinmeyen boyut"

        ctk.CTkLabel(
            info_box,
            text=detail,
            font=ctk.CTkFont(size=10),
            text_color=c('text_muted'),
            anchor="w"
        ).pack(anchor="w")

        # Rozet / Aksiyon Butonu
        if can_organize:
            ctk.CTkButton(
                inner,
                text="⚡ Organize Et",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                width=100,
                height=28,
                corner_radius=6,
                command=lambda p=path: self._organize_single(p)
            ).pack(side="right")
        elif is_baseline:
            ctk.CTkLabel(
                inner,
                text="🛡️ Korunuyor",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=c('success'),
                fg_color=c('success_bg'),
                corner_radius=6,
                padx=8,
                pady=2
            ).pack(side="right")
        else:
            ctk.CTkButton(
                inner,
                text="Aç",
                font=ctk.CTkFont(size=11),
                fg_color=c('bg_input'),
                hover_color=c('bg_card_hover'),
                text_color=c('text_primary'),
                width=50,
                height=26,
                corner_radius=6,
                command=lambda p=path: os.startfile(p) if os.path.exists(p) else None
            ).pack(side="right")

    def _organize_single(self, file_path):
        target = self.app.cfg.get('target', DEFAULT_TARGET)
        allow_new = self.app.cfg.get('allow_new_categories', True)
        res = organize_file(file_path, target, allow_new)
        if res and res.get('status') == 'success':
            self._refresh_content()
            self.app._periodic_status_update()

    def _organize_folder_items(self):
        target = self.app.cfg.get('target', DEFAULT_TARGET)
        allow_new = self.app.cfg.get('allow_new_categories', True)
        baseline = set(self.app.cfg.get('desktop_baseline', [])) if self.meta.get('is_desktop') else set()

        def run_thread():
            count = 0
            if os.path.exists(self.folder_path):
                for item in os.listdir(self.folder_path):
                    if self.meta.get('is_desktop') and item in baseline:
                        continue
                    item_path = os.path.join(self.folder_path, item)
                    if os.path.isfile(item_path):
                        res = organize_file(item_path, target, allow_new)
                        if res and res.get('status') == 'success':
                            count += 1
            if self.winfo_exists():
                self.after(0, self._refresh_content)
                self.after(0, self.app._periodic_status_update)

        threading.Thread(target=run_thread, daemon=True).start()
