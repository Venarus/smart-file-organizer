"""
Windows 11 Fluent Glass Pinned Folder Explorer (V2.1 — Premium Glass Edition)
Displays Desktop, Downloads, Documents, Pictures, Music, and Videos
with real-time file listing, native shell icons, file-type glass badges,
live folder search filter, baseline protection shield, right-click context menu,
and 1-click intelligent organization into Desktop/Folders.
"""

import os
import threading
from datetime import datetime
import customtkinter as ctk

from theme import FluentTheme
from thumbnail_engine import ThumbnailEngine
from organizer import organize_file
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu
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
        'desc': 'Masaüstü çalışma alanı. Önceden var olan kısayol ve klasörleriniz kilitlidir ve korunur.'
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
    PAGE_SIZE = 80

    def __init__(self, master, app_controller, folder_id='documents'):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.folder_id = folder_id
        self.meta = FOLDER_META.get(folder_id, FOLDER_META['documents'])
        self.folder_path = self.meta['path']
        self.theme_mode = self.app.theme_mode
        self._display_limit = self.PAGE_SIZE
        self._filter_query = ""

        self._folder_icon = None
        self._load_icon()

        self._build_ui()

    def _load_icon(self):
        try:
            pil_img = ThumbnailEngine._extract_shell_image(self.folder_path, 36, 36)
            if pil_img:
                self._folder_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(34, 34))
        except Exception:
            self._folder_icon = None

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def on_page_show(self):
        self._display_limit = self.PAGE_SIZE
        self._refresh_content()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

        # 1. Üst Buzlu Cam Klasör Başlık Kartı
        header_card = ctk.CTkFrame(
            self,
            fg_color=c('bg_card'),
            corner_radius=14,
            border_width=1,
            border_color=c('border')
        )
        header_card.pack(fill="x", padx=12, pady=(6, 10))
        FluidAnimator.bind_card_hover(header_card, self.theme_mode)

        header = ctk.CTkFrame(header_card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=14)

        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left")

        if self._folder_icon:
            lbl_ic = ctk.CTkLabel(left_box, text="", image=self._folder_icon)
            lbl_ic.pack(side="left", padx=(0, 12))
        else:
            lbl_ic = ctk.CTkLabel(left_box, text="📁", font=ctk.CTkFont(size=28))
            lbl_ic.pack(side="left", padx=(0, 12))

        title_inner = ctk.CTkFrame(left_box, fg_color="transparent")
        title_inner.pack(side="left")

        top_title_row = ctk.CTkFrame(title_inner, fg_color="transparent")
        top_title_row.pack(anchor="w")

        ctk.CTkLabel(
            top_title_row,
            text=f"{self.meta['name']} 📌",
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=21, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        is_monitored = any(os.path.normpath(s).lower() == os.path.normpath(self.folder_path).lower() for s in self.app.cfg.get('sources', []))
        status_txt = "🟢 CANLI İZLENİYOR" if is_monitored else "⚪ İZLEME DIŞI"
        status_clr = c('success') if is_monitored else c('text_muted')
        status_bg = c('success_bg') if is_monitored else c('bg_card_secondary')

        ctk.CTkLabel(
            top_title_row,
            text=status_txt,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=status_clr,
            fg_color=status_bg,
            corner_radius=5,
            padx=8,
            pady=2
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            title_inner,
            text=f"{self.meta['desc']}  •  📍 {self.folder_path}",
            font=ctk.CTkFont(size=11),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        # Sağ Aksiyon Butonları
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        self.btn_organize_now = ctk.CTkButton(
            btn_box,
            text="⚡ Folders'a Organize Et",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._organize_folder_items
        )
        self.btn_organize_now.pack(side="right", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📂 Gezginde Aç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            height=34,
            corner_radius=8,
            command=lambda: os.startfile(self.folder_path) if os.path.exists(self.folder_path) else None
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_box,
            text="🔄",
            width=36,
            font=ctk.CTkFont(size=13),
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            border_width=1,
            border_color=c('border'),
            height=34,
            corner_radius=8,
            command=self._refresh_content
        ).pack(side="right", padx=4)

        # 2. Masaüstü Koruma Kalkanı & Klasör İçi Filtre Çubuğu
        sub_bar = ctk.CTkFrame(self, fg_color="transparent")
        sub_bar.pack(fill="x", padx=12, pady=(0, 8))

        self.filter_entry = ctk.CTkEntry(
            sub_bar,
            placeholder_text=f"🔍 {self.meta['name']} içinde dosya filtrele...",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_input'),
            border_color=c('border'),
            text_color=c('text_primary'),
            width=280,
            height=32,
            corner_radius=8
        )
        self.filter_entry.pack(side="left")
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)
        FluidAnimator.bind_input_focus(self.filter_entry, self.theme_mode)

        if self.meta.get('is_desktop'):
            baseline_count = len(self.app.cfg.get('desktop_baseline', []))
            ctk.CTkLabel(
                sub_bar,
                text=f"🛡️ Masaüstü Koruma Kalkanı Aktif: Mevcut {baseline_count} kısayol/klasör kilitli",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=c('success'),
                fg_color=c('success_bg'),
                corner_radius=7,
                padx=12,
                pady=4
            ).pack(side="right")
        else:
            ctk.CTkLabel(
                sub_bar,
                text="💡 İpucu: Hızlı bağlam menüsü için herhangi bir dosya satırına sağ tıklayın",
                font=ctk.CTkFont(size=11),
                text_color=c('text_muted')
            ).pack(side="right")

        # 3. İçerik Alanı
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        try:
            self.scroll._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        self._render_files()

    def _on_filter_change(self, _event=None):
        self._filter_query = self.filter_entry.get().strip().lower()
        self._refresh_content()

    def _refresh_content(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._render_files()

    def _load_more(self):
        self._display_limit += self.PAGE_SIZE
        self._refresh_content()

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

        organizable_files = []
        protected_items = []

        for item in items:
            if item.lower() in ignored_names or item.startswith('.'):
                continue
            if self._filter_query and self._filter_query not in item.lower():
                continue
            item_path = os.path.join(self.folder_path, item)
            is_file = os.path.isfile(item_path)

            if self.meta.get('is_desktop') and item in baseline:
                protected_items.append((item, item_path, is_file, True))
            elif is_file:
                organizable_files.append((item, item_path, is_file, False))
            else:
                protected_items.append((item, item_path, is_file, False))

        if organizable_files:
            sec_header = ctk.CTkFrame(self.scroll, fg_color="transparent")
            sec_header.pack(fill="x", pady=(4, 6))

            ctk.CTkLabel(
                sec_header,
                text=f"⚡ Organize Edilecek Yeni Dosyalar ({len(organizable_files)})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=c('accent_light')
            ).pack(side="left")

            for name, path, is_file, _ in organizable_files[:self._display_limit]:
                self._create_file_row(self.scroll, name, path, is_file, can_organize=True, c=c)
        else:
            empty_box = ctk.CTkFrame(
                self.scroll,
                fg_color=c('bg_card'),
                corner_radius=12,
                border_width=1,
                border_color=c('border')
            )
            empty_box.pack(fill="x", pady=(4, 12))

            ctk.CTkLabel(
                empty_box,
                text=f"✨ {self.meta['name']} klasöründe bekleyen dağınık dosya yok!\nOtomatik izleme aktif: Bu klasöre gelen yeni dosyalar anında Desktop/Folders klasörüne organize edilir.",
                font=ctk.CTkFont(size=12),
                text_color=c('text_secondary'),
                justify="center"
            ).pack(padx=20, pady=16)

        if protected_items:
            sec_prot = ctk.CTkFrame(self.scroll, fg_color="transparent")
            sec_prot.pack(fill="x", pady=(10, 6))

            title = "🛡️ Korunan Masaüstü Öğeleri" if self.meta.get('is_desktop') else "📁 Mevcut Alt Klasörler ve Öğeler"
            ctk.CTkLabel(
                sec_prot,
                text=f"{title} ({len(protected_items)})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=c('text_secondary')
            ).pack(side="left")

            for name, path, is_file, is_base in protected_items[:self._display_limit]:
                self._create_file_row(self.scroll, name, path, is_file, can_organize=False, is_baseline=is_base, c=c)

        total_items = len(organizable_files) + len(protected_items)
        if total_items > self._display_limit:
            ctk.CTkButton(
                self.scroll,
                text=f"Daha Fazla Göster (+{total_items - self._display_limit} öğe)",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=c('bg_card'),
                hover_color=c('bg_card_hover'),
                text_color=c('accent_light'),
                height=34,
                corner_radius=8,
                command=self._load_more
            ).pack(pady=10)

    def _create_file_row(self, parent, name, path, is_file, can_organize, is_baseline=False, c=None):
        row = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        row.pack(fill="x", pady=2)
        FluidAnimator.bind_card_hover(row, self.theme_mode)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=7)

        if is_file:
            badge_txt, icon_char, badge_fg, badge_bg = FluentTheme.file_badge_style(name, self.theme_mode)
        else:
            badge_txt, icon_char, badge_fg, badge_bg = ("DIR", "📁", c('accent_light'), c('accent_subtle'))

        ctk.CTkLabel(
            inner,
            text=f"{icon_char} {badge_txt}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=badge_fg,
            fg_color=badge_bg,
            corner_radius=6,
            width=54,
            padx=6,
            pady=3
        ).pack(side="left", padx=(0, 10))

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

        extra_menu = []
        if can_organize:
            extra_menu.append(("⚡  Folders'a Organize Et", lambda p=path: self._organize_single(p)))
            ctk.CTkButton(
                inner,
                text="⚡ Organize Et",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('accent'),
                hover_color=c('accent_hover'),
                text_color="#FFFFFF",
                width=104,
                height=28,
                corner_radius=7,
                command=lambda p=path: self._organize_single(p)
            ).pack(side="right")
        elif is_baseline:
            ctk.CTkLabel(
                inner,
                text="🛡️ Kilitli",
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
                text="📂 Aç",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=c('bg_card_secondary'),
                hover_color=c('bg_card_hover'),
                text_color=c('text_primary'),
                border_width=1,
                border_color=c('border'),
                width=58,
                height=26,
                corner_radius=7,
                command=lambda p=path: os.startfile(p) if os.path.exists(p) else None
            ).pack(side="right")

        FluentContextMenu.bind_to_widget(row, path, self.app, extra_actions=extra_menu)

    def _organize_single(self, file_path):
        target = self.app.cfg.get('target', DEFAULT_TARGET)
        allow_new = self.app.cfg.get('allow_new_categories', True)
        res = organize_file(file_path, target, allow_new)
        if res and res.get('status') == 'success':
            self._refresh_content()
            self.app.handle_background_events([res])

    def _organize_folder_items(self):
        target = self.app.cfg.get('target', DEFAULT_TARGET)
        allow_new = self.app.cfg.get('allow_new_categories', True)
        baseline = set(self.app.cfg.get('desktop_baseline', [])) if self.meta.get('is_desktop') else set()

        self.btn_organize_now.configure(state="disabled", text="⏳ Organize Ediliyor...")

        def run_thread():
            events = []
            if os.path.exists(self.folder_path):
                for item in os.listdir(self.folder_path):
                    if self.meta.get('is_desktop') and item in baseline:
                        continue
                    item_path = os.path.join(self.folder_path, item)
                    if os.path.isfile(item_path):
                        res = organize_file(item_path, target, allow_new)
                        if res and res.get('status') == 'success':
                            events.append(res)

            def _done():
                try:
                    if self.winfo_exists():
                        self.btn_organize_now.configure(state="normal", text="⚡ Folders'a Organize Et")
                        self._refresh_content()
                    if events:
                        self.app.handle_background_events(events)
                    else:
                        FluidAnimator.show_toast(
                            self.app,
                            f"{self.meta['name']} Klasörü",
                            "Organize edilecek yeni bir dosya bulunamadı.",
                            theme_mode=self.theme_mode,
                            duration_ms=2200,
                            level='info'
                        )
                except Exception:
                    pass

            UIBridge.post(_done)

        threading.Thread(target=run_thread, daemon=True).start()
