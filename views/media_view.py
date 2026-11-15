"""
Media & Video Gallery View with High-Fidelity Thumbnails & Locked-Geometry Grid (V2.1)
Features:
- Live thumbnails for Videos (.mp4, .mkv, .avi, etc.) and Images (.png, .jpg, .gif)
- Locked 176px card geometry + 160x100 CTkImage placeholder so asynchronous thumbnail
  loads NEVER cause layout shifts or row jumping during vertical scrolling
- Universal right-click context menu on every part of every media card
- Scroll position preservation across refreshes (rename, delete, move)
"""

import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from thumbnail_engine import ThumbnailEngine, AsyncThumbnailLoader
from search_engine import SearchEngine
from animation import FluidAnimator, UIBridge
from notification_center import FluentContextMenu


class MediaGalleryView(ctk.CTkFrame):
    PAGE_SIZE = 18
    CARD_HEIGHT = 178
    THUMB_W = 160
    THUMB_H = 100

    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.current_filter = "Tümü"
        self.all_media_files = []
        self._display_limit = self.PAGE_SIZE
        self._is_loading = False
        self._last_dir_sig = None

        self._build_ui()
        self._load_media_async()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        self._last_dir_sig = None
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
        self._load_media_async()

    def on_page_show(self):
        # Eğer medya listesi boşsa veya hedef klasör değiştiyse yükle
        if not self.all_media_files and not self._is_loading:
            self._load_media_async()

    def refresh(self):
        """Dosya silme, yeniden adlandırma veya taşıma sonrasında kaydırma konumunu koruyarak yeniler."""
        saved_y = 0.0
        try:
            saved_y = self.scroll_area._parent_canvas.yview()[0]
        except Exception:
            pass
        self._load_media_async(preserve_scroll=saved_y)

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font

        # 1. Başlık ve Aksiyon Barı
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text="Medya & Video Galerisi",
            font=f(24, "bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text="Küçük Resim Önizlemeli",
            font=f(10, "bold"),
            text_color=c('accent_light'),
            fg_color=c('accent_bg'),
            corner_radius=10,
            padx=8,
            pady=2
        ).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            title_box,
            text="Videoları ve görselleri sabit geometrili önizleme kartları ve tam sağ-tık menüsüyle yönetin",
            font=f(13),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        # Sağ: Klasörü Aç & Yenile
        right_acts = ctk.CTkFrame(header, fg_color="transparent")
        right_acts.pack(side="right")

        ctk.CTkButton(
            right_acts,
            text="📂 Medya Klasörünü Aç",
            font=f(12, "bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self._open_media_folder
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            right_acts,
            text="🔄 Yenile",
            font=f(12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=self.refresh
        ).pack(side="right", padx=4)

        # 2. Filtre Barı (Tümü, Videolar, Fotoğraflar, GIF'ler)
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=16, pady=(0, 10))

        filters = [
            ("Tümü", "Tümü"),
            ("Videolar 🎬", "video"),
            ("Görseller 🖼️", "image"),
            ("GIF Animasyonlar ✨", "gif")
        ]

        self.filter_buttons = {}
        for f_label, f_key in filters:
            is_active = (f_key == self.current_filter)
            bg = c('accent') if is_active else c('bg_card')
            text_c = "#FFFFFF" if is_active else c('text_primary')
            btn = ctk.CTkButton(
                filter_bar,
                text=f_label,
                font=f(11, "bold" if is_active else "normal"),
                fg_color=bg,
                hover_color=c('accent_hover'),
                text_color=text_c,
                height=30,
                corner_radius=8,
                command=lambda k=f_key: self._set_filter(k)
            )
            btn.pack(side="left", padx=(0, 6))
            self.filter_buttons[f_key] = btn

        self.lbl_count_info = ctk.CTkLabel(
            filter_bar,
            text="Taranıyor...",
            font=f(11),
            text_color=c('text_muted')
        )
        self.lbl_count_info.pack(side="right", padx=6)

        # 3. Sabit Geometrili Kart Izgarası (Katı bg_mica Arka Planı yırtılmaları önler)
        self.scroll_area = ctk.CTkScrollableFrame(
            self,
            fg_color=c('bg_mica'),
            scrollbar_button_color=c('border'),
            scrollbar_button_hover_color=c('accent')
        )
        self.scroll_area.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll_area._parent_canvas.configure(yscrollincrement=12)
        except Exception:
            pass

        # 3 sütunlu eşit genişlikli grid yapılandırması
        self.scroll_area.grid_columnconfigure((0, 1, 2), weight=1, uniform="media_col")

    def _set_filter(self, filter_key):
        if filter_key == self.current_filter:
            return
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        self.current_filter = filter_key
        self._display_limit = self.PAGE_SIZE
        AsyncThumbnailLoader.clear_pending()
        for k, btn in self.filter_buttons.items():
            if k == filter_key:
                btn.configure(fg_color=c('accent'), text_color="#FFFFFF", font=f(11, "bold"))
            else:
                btn.configure(fg_color=c('bg_card'), text_color=c('text_primary'), font=f(11, "normal"))
        self._render_grid()

    def _load_more(self):
        saved_y = 0.0
        try:
            saved_y = self.scroll_area._parent_canvas.yview()[0]
        except Exception:
            pass
        self._display_limit += self.PAGE_SIZE
        self._render_grid(preserve_scroll=saved_y)

    def _open_media_folder(self):
        target_base = self.app.cfg.get('target', '')
        media_path = os.path.join(target_base, "04_Medya ve Tasarım")
        if os.path.exists(media_path):
            os.startfile(media_path)
        else:
            self.app.open_target_folder()

    def _load_media_async(self, preserve_scroll: float = None):
        if self._is_loading:
            return
        self._is_loading = True
        target_base = self.app.cfg.get('target', '')

        def worker():
            files = []
            seen_paths = set()
            search_dirs = [
                os.path.join(target_base, "04_Medya ve Tasarım"),
                os.path.join(target_base, "Medya ve Videolar"),
                os.path.join(os.environ.get('USERPROFILE', ''), "Pictures"),
                os.path.join(os.environ.get('USERPROFILE', ''), "Videos")
            ]

            for sdir in search_dirs:
                if os.path.exists(sdir):
                    for root, dirs, fnames in os.walk(sdir):
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        for fn in fnames:
                            fp = os.path.normpath(os.path.join(root, fn))
                            norm_key = os.path.normcase(fp)
                            if norm_key in seen_paths:
                                continue
                            if ThumbnailEngine.is_media_file(fp):
                                try:
                                    st = os.stat(fp)
                                    seen_paths.add(norm_key)
                                    files.append({
                                        'name': fn,
                                        'path': fp,
                                        'is_video': ThumbnailEngine.is_video(fp),
                                        'is_gif': fn.lower().endswith('.gif'),
                                        'size_bytes': st.st_size,
                                        'size_human': SearchEngine._format_bytes(st.st_size),
                                        'mtime': st.st_mtime
                                    })
                                except Exception:
                                    pass
                        if len(files) >= 120:
                            break
                if len(files) >= 120:
                    break

            files.sort(key=lambda x: x['mtime'], reverse=True)
            self.all_media_files = files
            self._is_loading = False
            UIBridge.post(lambda: self._render_grid(preserve_scroll=preserve_scroll))

        threading.Thread(target=worker, daemon=True).start()

    def _render_grid(self, preserve_scroll: float = None):
        try:
            if not self.scroll_area.winfo_exists():
                return
        except Exception:
            return

        c = lambda token: FluentTheme.c(token, self.theme_mode)
        f = FluentTheme.font
        FluidAnimator.cancel_chunk_render(self.scroll_area)
        for w in self.scroll_area.winfo_children():
            w.destroy()

        # Mevcut olmayan (silinmiş) dosyaları listeden temizle
        self.all_media_files = [x for x in self.all_media_files if os.path.exists(x['path'])]

        # Filtreleme
        if self.current_filter == "video":
            items = [x for x in self.all_media_files if x['is_video']]
        elif self.current_filter == "image":
            items = [x for x in self.all_media_files if not x['is_video'] and not x['is_gif']]
        elif self.current_filter == "gif":
            items = [x for x in self.all_media_files if x['is_gif']]
        else:
            items = self.all_media_files

        self.lbl_count_info.configure(text=f"{len(items)} Medya Dosyası")

        if not items:
            ctk.CTkLabel(
                self.scroll_area,
                text="Bu filtreye uygun medya dosyası bulunamadı.\nFolders içerisine video veya fotoğraf ekleyebilirsiniz.",
                font=f(13),
                text_color=c('text_muted'),
                justify="center"
            ).grid(row=0, column=0, columnspan=3, pady=60)
            return

        total_items = len(items)
        max_items = items[:self._display_limit]

        def _render_one(item, idx):
            r = idx // 3
            col = idx % 3
            self._create_media_card(self.scroll_area, item, r, col, c, f)

        def _on_done():
            try:
                if not self.scroll_area.winfo_exists():
                    return
                if total_items > self._display_limit:
                    next_row = (len(max_items) // 3) + 1
                    ctk.CTkButton(
                        self.scroll_area,
                        text=f"Daha Fazla Göster (+{total_items - self._display_limit} medya)",
                        font=f(12, "bold"),
                        fg_color=c('bg_card'),
                        hover_color=c('bg_card_hover'),
                        text_color=c('accent_light'),
                        height=34,
                        corner_radius=8,
                        command=self._load_more
                    ).grid(row=next_row, column=0, columnspan=3, pady=12)
                if preserve_scroll is not None and preserve_scroll > 0:
                    self.scroll_area.update_idletasks()
                    self.scroll_area._parent_canvas.yview_moveto(preserve_scroll)
            except Exception:
                pass

        FluidAnimator.render_chunked(
            self.scroll_area,
            max_items,
            _render_one,
            initial_batch=9,
            chunk_size=6,
            interval_ms=8,
            on_complete=_on_done
        )

    def _create_media_card(self, parent, item, r, col, c, f):
        """
        Sabit yüksekliğe (CARD_HEIGHT = 178px) ve kilitli pack_propagate(False) geometrisine sahip medya kartı.
        Küçük resim yüklenmeden önce ve yüklendikten sonra boyut 1 piksel bile değişmez.
        """
        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border'),
            height=self.CARD_HEIGHT
        )
        card.grid(row=r, column=col, padx=5, pady=5, sticky="nsew")
        card.pack_propagate(False)

        # Üst Küçük Resim (Thumbnail) Alanı — Sabit 110px yükseklik
        thumb_frame = ctk.CTkFrame(card, fg_color=c('bg_secondary'), height=108, corner_radius=8)
        thumb_frame.pack(fill="x", padx=6, pady=(6, 4))
        thumb_frame.pack_propagate(False)

        # Sabit boyutlu (160x100) CTkImage yer tutucu (metin modu yerine görüntü moduyla başlar!)
        placeholder_img = ThumbnailEngine.get_placeholder(
            target_width=self.THUMB_W,
            target_height=self.THUMB_H,
            is_video=item['is_video'],
            theme_mode=self.theme_mode
        )
        lbl_thumb = ctk.CTkLabel(
            thumb_frame,
            text="",
            image=placeholder_img,
            width=self.THUMB_W,
            height=self.THUMB_H
        )
        lbl_thumb.place(relx=0.5, rely=0.5, anchor="center")

        # Eğer video ise üzerinde oynatma simgesi rozeti
        if item['is_video']:
            badge = ctk.CTkLabel(
                thumb_frame,
                text="▶ Video",
                font=f(9, "bold"),
                text_color="#FFFFFF",
                fg_color="#111827",
                corner_radius=4,
                padx=6,
                pady=1
            )
            badge.place(relx=0.06, rely=0.14, anchor="w")

        # Dosya Başlığı (Sabit tek satır kesme ile sütun genişlemesini önler)
        raw_name = item['name']
        disp_name = raw_name if len(raw_name) <= 28 else raw_name[:25] + "..."
        name_lbl = ctk.CTkLabel(
            card,
            text=disp_name,
            font=f(11, "bold"),
            text_color=c('text_primary'),
            anchor="w",
            height=20
        )
        name_lbl.pack(fill="x", padx=10, pady=(0, 2))

        # Alt Satır: Boyut & Aksiyon Butonları
        info_row = ctk.CTkFrame(card, fg_color="transparent", height=28)
        info_row.pack(fill="x", padx=10, pady=(0, 6))
        info_row.pack_propagate(False)

        ctk.CTkLabel(
            info_row,
            text=f"💾 {item['size_human']}",
            font=f(10),
            text_color=c('text_muted')
        ).pack(side="left")

        btn_open = ctk.CTkButton(
            info_row,
            text="Oynat" if item['is_video'] else "Aç",
            font=f(10, "bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            width=50,
            height=24,
            corner_radius=6,
            command=lambda p=item['path']: os.startfile(p) if os.path.exists(p) else None
        )
        btn_open.pack(side="right", padx=(4, 0))

        btn_loc = ctk.CTkButton(
            info_row,
            text="📁",
            font=f(11),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            width=28,
            height=24,
            corner_radius=6,
            command=lambda p=item['path']: SearchEngine.reveal_in_explorer(p)
        )
        btn_loc.pack(side="right")

        # Küçük resmi arka planda yükle (UIBridge üzerinden güvenli şekilde sadece image referansını değiştirir)
        def on_thumb_ready(img):
            if img is not None:
                try:
                    if card.winfo_exists() and lbl_thumb.winfo_exists():
                        lbl_thumb.configure(image=img)
                except Exception:
                    pass

        AsyncThumbnailLoader.request_thumbnail(item['path'], self.THUMB_W, self.THUMB_H, on_thumb_ready)

        # Hover ve tüm alt bileşenleri kapsayan Sağ-Tık Bağlam Menüsü (en sonda bağlanır!)
        FluidAnimator.bind_card_hover(card, self.theme_mode)
        FluentContextMenu.bind_to_widget(
            card,
            item['path'],
            self.app,
            on_refresh=self.refresh
        )
