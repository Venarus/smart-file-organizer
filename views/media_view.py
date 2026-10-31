"""
Media & Video Gallery View with High-Fidelity Thumbnails & Fluid Grid (V2)
Features:
- Live thumbnails for Videos (.mp4, .mkv, .avi, etc.) and Images (.png, .jpg, .gif)
- Play button badge overlays on videos
- Instant filter tabs (Tümü, Videolar, Fotoğraflar, GIF'ler)
- Smooth Linux/Fluent style card hover animations
- Direct playback & Reveal in Explorer actions
"""

import os
import threading
import customtkinter as ctk
from theme import FluentTheme
from thumbnail_engine import ThumbnailEngine, AsyncThumbnailLoader
from search_engine import SearchEngine
from animation import FluidAnimator

class MediaGalleryView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self.theme_mode = self.app.theme_mode

        self.current_filter = "Tümü"
        self.all_media_files = []
        self._is_loading = False

        self._build_ui()
        self._load_media_async()

    def update_theme(self, theme_mode):
        self.theme_mode = theme_mode
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
        self._load_media_async()

    def _build_ui(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)

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
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text="Küçük Resim Önizlemeli",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c('accent_light'),
            fg_color=c('accent_bg'),
            corner_radius=10,
            padx=8,
            pady=2
        ).pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            title_box,
            text="Folders klasörünüzdeki videoları ve görselleri akıcı önizleme kartlarıyla keşfedin",
            font=ctk.CTkFont(size=13),
            text_color=c('text_secondary')
        ).pack(anchor="w", pady=(2, 0))

        # Sağ: Klasörü Aç & Yenile
        right_acts = ctk.CTkFrame(header, fg_color="transparent")
        right_acts.pack(side="right")

        ctk.CTkButton(
            right_acts,
            text="📂 Medya Klasörünü Aç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            height=34,
            corner_radius=8,
            command=self._open_media_folder
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            right_acts,
            text="🔄 Yenile",
            font=ctk.CTkFont(size=12),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            height=34,
            corner_radius=8,
            command=self._load_media_async
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
                font=ctk.CTkFont(size=11, weight="bold" if is_active else "normal"),
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
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted')
        )
        self.lbl_count_info.pack(side="right", padx=6)

        # 3. Akıcı Kart Izgarası (Scrollable Grid — Katı Mica Arka Planı yırtılmaları önler)
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color=c('bg_mica'))
        self.scroll_area.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        try:
            self.scroll_area._parent_canvas.configure(yscrollincrement=4)
        except Exception:
            pass

        # 3 sütunlu grid yapılandırması
        self.scroll_area.grid_columnconfigure((0, 1, 2), weight=1, uniform="media_col")

    def _set_filter(self, filter_key):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        self.current_filter = filter_key
        for k, btn in self.filter_buttons.items():
            if k == filter_key:
                btn.configure(fg_color=c('accent'), text_color="#FFFFFF", font=ctk.CTkFont(size=11, weight="bold"))
            else:
                btn.configure(fg_color=c('bg_card'), text_color=c('text_primary'), font=ctk.CTkFont(size=11, weight="normal"))
        self._render_grid()

    def _open_media_folder(self):
        target_base = self.app.cfg.get('target', '')
        media_path = os.path.join(target_base, "04_Medya ve Tasarım")
        if os.path.exists(media_path):
            os.startfile(media_path)
        else:
            self.app.open_target_folder()

    def _load_media_async(self):
        if self._is_loading:
            return
        self._is_loading = True
        target_base = self.app.cfg.get('target', '')

        def worker():
            files = []
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
                            fp = os.path.join(root, fn)
                            if ThumbnailEngine.is_media_file(fp):
                                try:
                                    st = os.stat(fp)
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
            try:
                if self.winfo_exists():
                    self.after(0, self._render_grid)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _render_grid(self):
        c = lambda token: FluentTheme.c(token, self.theme_mode)
        for w in self.scroll_area.winfo_children():
            w.destroy()

        # Filtreleme
        if self.current_filter == "video":
            items = [f for f in self.all_media_files if f['is_video']]
        elif self.current_filter == "image":
            items = [f for f in self.all_media_files if not f['is_video'] and not f['is_gif']]
        elif self.current_filter == "gif":
            items = [f for f in self.all_media_files if f['is_gif']]
        else:
            items = self.all_media_files

        self.lbl_count_info.configure(text=f"{len(items)} Medya Dosyası")

        if not items:
            ctk.CTkLabel(
                self.scroll_area,
                text="Bu filtreye uygun medya dosyası bulunamadı.\nFolders içerisine video veya fotoğraf ekleyebilirsiniz.",
                font=ctk.CTkFont(size=13),
                text_color=c('text_muted'),
                justify="center"
            ).grid(row=0, column=0, columnspan=3, pady=60)
            return

        # Grid oluşturma (3 Sütun)
        max_items = items[:48]  # İlk 48 ögeyi hızlıca çiz
        for idx, item in enumerate(max_items):
            r = idx // 3
            col = idx % 3
            self._create_media_card(self.scroll_area, item, r, col, c)

    def _create_media_card(self, parent, item, r, col, c):
        card = ctk.CTkFrame(
            parent,
            fg_color=c('bg_card'),
            corner_radius=10,
            border_width=1,
            border_color=c('border')
        )
        card.grid(row=r, column=col, padx=5, pady=5, sticky="nsew")

        # Üst Küçük Resim (Thumbnail) Alanı
        thumb_frame = ctk.CTkFrame(card, fg_color=c('bg_secondary'), height=110, corner_radius=8)
        thumb_frame.pack(fill="x", padx=6, pady=6)
        thumb_frame.pack_propagate(False)

        # Küçük resim yer tutucusu
        lbl_thumb = ctk.CTkLabel(thumb_frame, text="🎬" if item['is_video'] else "🖼️", font=ctk.CTkFont(size=28))
        lbl_thumb.place(relx=0.5, rely=0.5, anchor="center")

        # Eğer video ise üzerinde oynatma simgesi rozeti
        if item['is_video']:
            badge = ctk.CTkLabel(
                thumb_frame,
                text="▶ Video",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#FFFFFF",
                fg_color="#1A1A1A",
                corner_radius=4,
                padx=6,
                pady=1
            )
            badge.place(relx=0.08, rely=0.15, anchor="w")

        # Sıralı arka plan kuyruğuyla küçük resim yükleme (CPU ve GDI kilitlenmesini önler)
        def on_thumb_ready(img):
            if img:
                try:
                    if card.winfo_exists() and lbl_thumb.winfo_exists():
                        self.after(0, lambda: lbl_thumb.configure(image=img, text=""))
                except Exception:
                    pass

        AsyncThumbnailLoader.request_thumbnail(item['path'], 160, 100, on_thumb_ready)

        # Dosya Başlığı
        name_lbl = ctk.CTkLabel(
            card,
            text=item['name'],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('text_primary'),
            anchor="w"
        )
        name_lbl.pack(fill="x", padx=10, pady=(2, 0))

        # Alt Satır: Boyut & Aksiyon Butonları
        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=10, pady=(2, 6))

        ctk.CTkLabel(
            info_row,
            text=f"💾 {item['size_human']}",
            font=ctk.CTkFont(size=10),
            text_color=c('text_muted')
        ).pack(side="left")

        btn_open = ctk.CTkButton(
            info_row,
            text="Oynat" if item['is_video'] else "Aç",
            font=ctk.CTkFont(size=10, weight="bold"),
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
            font=ctk.CTkFont(size=11),
            fg_color=c('bg_card_hover'),
            hover_color=c('bg_card_active'),
            text_color=c('text_primary'),
            width=28,
            height=24,
            corner_radius=6,
            command=lambda p=item['path']: SearchEngine.reveal_in_explorer(p)
        )
        btn_loc.pack(side="right")
