"""
Windows 11 Fluent Notification Center & Universal Context Menu System (V2.1)
Provides:
- NotificationCenter: Centralized notification store with unread badge tracking,
  deduplication, and an interactive Windows 11 Flyout drawer.
- FluentContextMenu: Solid, high-contrast Windows 11 right-click context menu for files
  and folders across all views, with full file management actions, keyboard navigation,
  multi-selection batch support, and screen-edge collision handling.
"""

import os
import subprocess
from datetime import datetime
import customtkinter as ctk
from theme import FluentTheme
from animation import FluidAnimator
from file_ops import FileOperationManager, SelectionManager


class NotificationCenter:
    _items = []
    _max_items = 60
    _active_flyout = None

    @classmethod
    def add(cls, title: str, message: str, level: str = 'info'):
        entry = {
            'id': len(cls._items) + 1,
            'title': title,
            'message': message,
            'level': level,
            'time': datetime.now().strftime('%H:%M:%S'),
            'read': False
        }
        cls._items.insert(0, entry)
        if len(cls._items) > cls._max_items:
            cls._items = cls._items[:cls._max_items]

    @classmethod
    def get_all(cls):
        return list(cls._items)

    @classmethod
    def get_unread_count(cls) -> int:
        return sum(1 for item in cls._items if not item.get('read', False))

    @classmethod
    def mark_all_read(cls):
        for item in cls._items:
            item['read'] = True

    @classmethod
    def clear(cls):
        cls._items.clear()

    @classmethod
    def toggle_flyout(cls, app_window):
        """Üst bardaki 🔔 Bildirim Merkezi panelini açar veya kapatır."""
        if cls._active_flyout is not None:
            try:
                if cls._active_flyout.winfo_exists():
                    cls._active_flyout.destroy()
                    cls._active_flyout = None
                    return
            except Exception:
                cls._active_flyout = None

        cls.mark_all_read()
        if hasattr(app_window, 'update_notification_badge'):
            app_window.update_notification_badge()

        theme_mode = getattr(app_window, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        flyout = ctk.CTkFrame(
            app_window,
            fg_color=c('bg_elevated'),
            corner_radius=12,
            border_width=1,
            border_color=c('border_hover'),
            width=360,
            height=420
        )
        flyout.pack_propagate(False)
        cls._active_flyout = flyout

        header = ctk.CTkFrame(flyout, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="🔔 Bildirim Merkezi",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        btn_close = ctk.CTkButton(
            header,
            text="✕",
            width=26,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=c('bg_card_hover'),
            text_color=c('text_secondary'),
            command=lambda: cls.close_flyout()
        )
        btn_close.pack(side="right")

        btn_clear = ctk.CTkButton(
            header,
            text="Temizle",
            width=60,
            height=24,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_secondary'),
            command=lambda: _clear_and_refresh()
        )
        btn_clear.pack(side="right", padx=6)

        ctk.CTkFrame(flyout, fg_color=c('border_subtle'), height=1).pack(fill="x", padx=12)

        scroll = ctk.CTkScrollableFrame(flyout, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        def _render_items():
            for w in scroll.winfo_children():
                w.destroy()

            items = cls.get_all()
            if not items:
                ctk.CTkLabel(
                    scroll,
                    text="📭\n\nYeni bildirim bulunmuyor.\nArka plan işlemleri ve sistem bildirimleri burada listelenir.",
                    font=ctk.CTkFont(size=12),
                    text_color=c('text_muted'),
                    justify="center"
                ).pack(pady=60, padx=16)
                return

            level_icons = {
                'success': ('✅', c('success')),
                'warning': ('⚠️', c('warning')),
                'error': ('❌', c('danger')),
                'info': ('✨', c('accent_light'))
            }

            for item in items:
                ic, col = level_icons.get(item.get('level', 'info'), level_icons['info'])
                card = ctk.CTkFrame(
                    scroll,
                    fg_color=c('bg_card'),
                    corner_radius=8,
                    border_width=1,
                    border_color=c('border_subtle')
                )
                card.pack(fill="x", pady=3)
                FluidAnimator.bind_card_hover(card, theme_mode)

                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=8)

                top_r = ctk.CTkFrame(inner, fg_color="transparent")
                top_r.pack(fill="x")

                ctk.CTkLabel(
                    top_r,
                    text=f"{ic} {item['title']}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=col
                ).pack(side="left")

                ctk.CTkLabel(
                    top_r,
                    text=item['time'],
                    font=ctk.CTkFont(size=10),
                    text_color=c('text_muted')
                ).pack(side="right")

                ctk.CTkLabel(
                    inner,
                    text=item['message'],
                    font=ctk.CTkFont(size=11),
                    text_color=c('text_primary'),
                    anchor="w",
                    justify="left",
                    wraplength=290
                ).pack(anchor="w", pady=(3, 0))

        def _clear_and_refresh():
            cls.clear()
            if hasattr(app_window, 'update_notification_badge'):
                app_window.update_notification_badge()
            _render_items()

        _render_items()

        flyout.place(relx=0.985, y=60, anchor="ne")
        FluidAnimator.fade_in_surface(
            flyout,
            c('bg_secondary'),
            c('bg_elevated'),
            duration_ms=FluidAnimator.TIMING_MODAL
        )

    @classmethod
    def close_flyout(cls):
        if cls._active_flyout is not None:
            try:
                if cls._active_flyout.winfo_exists():
                    cls._active_flyout.destroy()
            except Exception:
                pass
            cls._active_flyout = None


class FluentContextMenu:
    """
    Windows 11 Fluent Sağ-Tık Bağlam Menüsü (Universal Context Menu).
    - Katı (solid) yüksek kontrastlı yüzey ('bg_elevated')
    - Tüm alt bileşenler için derin (recursive) ve ata-tabanlı (ancestor) sağ-tık yakalama
    - Tekil ve çoklu seçim (batch) işlemleri
    - Klavye navigasyonu (Yukarı/Aşağı ok, Enter, Escape)
    - Ekran kenarı taşma koruması (Screen-edge collision handling)
    """
    _active_menu = None
    _menu_buttons = []
    _focused_idx = -1
    _last_open_ts = 0.0

    @classmethod
    def close_active(cls):
        cls._menu_buttons = []
        cls._focused_idx = -1
        if cls._active_menu is not None:
            try:
                if cls._active_menu.winfo_exists():
                    cls._active_menu.destroy()
            except Exception:
                pass
            cls._active_menu = None

    @classmethod
    def _bind_recursive(cls, widget, right_click_fn, ctrl_click_fn):
        try:
            widget.bind("<Button-3>", right_click_fn, add="+")
            widget.bind("<Control-Button-1>", ctrl_click_fn, add="+")
            for child in widget.winfo_children():
                cls._bind_recursive(child, right_click_fn, ctrl_click_fn)
        except Exception:
            pass

    @classmethod
    def bind_to_widget(cls, widget, file_path: str, app_controller,
                       extra_actions=None, on_refresh=None,
                       normal_bg_token: str = 'bg_card', normal_border_token: str = 'border'):
        """
        Bir dosya veya klasör kartına sağ-tık (<Button-3>) menüsü ve Ctrl+Sol-Tık çoklu seçim bağlar.
        Kartın kendisine veya içindeki herhangi bir küçük resim, ikon, rozet ya da metne
        sağ tıklandığında menü güvenilir şekilde açılır.
        """
        if not widget or not file_path:
            return

        theme_mode = getattr(app_controller, 'theme_mode', 'dark')
        SelectionManager.register_widget(
            file_path, widget, theme_mode=theme_mode,
            normal_bg_token=normal_bg_token, normal_border_token=normal_border_token
        )

        ctx_payload = {
            'file_path': file_path,
            'app': app_controller,
            'extra_actions': extra_actions,
            'on_refresh': on_refresh,
        }
        try:
            widget._ctx_data = ctx_payload
        except Exception:
            pass

        def _on_right_click(event):
            cls.show(
                event,
                file_path=file_path,
                app_controller=app_controller,
                extra_actions=extra_actions,
                on_refresh=on_refresh
            )
            return "break"

        def _on_ctrl_click(_event):
            SelectionManager.toggle(file_path, theme_mode=getattr(app_controller, 'theme_mode', 'dark'))
            return "break"

        cls._bind_recursive(widget, _on_right_click, _on_ctrl_click)

    @classmethod
    def handle_global_right_click(cls, event, app_controller) -> bool:
        """
        Kök pencere (root) düzeyinde sağ-tık yedek yakalayıcısı.
        Eğer sağ tıklanan alt bileşen (ör. sonradan eklenen küçük resim veya iç canvas)
        doğrudan bind edilmemişse bile, ata (master) zincirinde `_ctx_data` arayarak menüyü açar.
        """
        w = getattr(event, 'widget', None)
        visited = 0
        while w is not None and visited < 16:
            visited += 1
            ctx = getattr(w, '_ctx_data', None)
            if isinstance(ctx, dict) and ctx.get('file_path'):
                cls.show(
                    event,
                    file_path=ctx['file_path'],
                    app_controller=ctx.get('app') or app_controller,
                    extra_actions=ctx.get('extra_actions'),
                    on_refresh=ctx.get('on_refresh')
                )
                return True
            w = getattr(w, 'master', None)
        return False

    @classmethod
    def _resolve_refresh_fn(cls, app_controller, on_refresh=None):
        if callable(on_refresh):
            return on_refresh
        view = getattr(app_controller, 'current_view', None)
        if view is not None:
            for attr in ('refresh', '_start_async_scan', '_load_folder_async', 'load_files'):
                fn = getattr(view, attr, None)
                if callable(fn):
                    return fn
        return None

    @classmethod
    def show(cls, event, file_path: str, app_controller, extra_actions=None, on_refresh=None):
        import time
        now = time.perf_counter()
        # Aynı sağ-tık olayının hem alt bileşenden hem üst bileşenden 25 ms içinde çift tetiklenmesini önle
        if (now - cls._last_open_ts) < 0.025 and cls._active_menu is not None:
            return
        cls._last_open_ts = now

        cls.close_active()
        if not app_controller or not file_path:
            return

        theme_mode = getattr(app_controller, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)
        refresh_fn = cls._resolve_refresh_fn(app_controller, on_refresh)

        norm_path = os.path.normpath(file_path)
        effective_paths = SelectionManager.get_effective_paths(norm_path)
        is_multi = len(effective_paths) > 1
        exists = os.path.exists(norm_path)
        is_dir = os.path.isdir(norm_path)
        is_file = os.path.isfile(norm_path)
        target_paste_dir = norm_path if is_dir else os.path.dirname(norm_path)

        menu_width = 248
        menu = ctk.CTkFrame(
            app_controller,
            fg_color=c('bg_elevated'),
            corner_radius=10,
            border_width=1,
            border_color=c('border_hover'),
            width=menu_width
        )
        cls._active_menu = menu

        inner = ctk.CTkFrame(menu, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=6, pady=6)

        # Başlık satırı
        if is_multi:
            header_txt = f"📚  {len(effective_paths)} Öğe Seçili"
        else:
            name = os.path.basename(norm_path) or norm_path
            ic = "📁" if is_dir else "📄"
            header_txt = f"{ic}  {name[:26]}" + ("..." if len(name) > 26 else "")

        ctk.CTkLabel(
            inner,
            text=header_txt,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('accent_light'),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(2, 4))

        def _add_separator():
            ctk.CTkFrame(inner, fg_color=c('border_subtle'), height=1).pack(fill="x", padx=4, pady=3)

        _add_separator()

        # Menü öğesi tanımları: (label, command, text_color_token_or_None)
        menu_specs = []

        # --- GRUP 1: TEMEL AÇMA VE KONUM İŞLEMLERİ ---
        if not is_multi and exists:
            menu_specs.append(("📂  Aç", lambda: FileOperationManager.open_item(norm_path, app_controller), None))
            if is_file:
                menu_specs.append(("🚀  Birlikte Aç...", lambda: FileOperationManager.open_with(norm_path, app_controller), None))
            menu_specs.append(("📍  Dosya Gezgininde Göster", lambda: FileOperationManager.reveal_in_explorer(norm_path, app_controller), None))
            menu_specs.append(("📁  Bulunduğu Klasörü Aç", lambda: FileOperationManager.open_containing_folder(norm_path, app_controller), None))
            menu_specs.append(("__SEP__", None, None))

        # --- GRUP 2: PANO & ORGANİZASYON ---
        if exists:
            lbl_copy = f"📋  Kopyala ({len(effective_paths)})" if is_multi else "📋  Kopyala"
            lbl_cut = f"✂️  Kes ({len(effective_paths)})" if is_multi else "✂️  Kes"
            menu_specs.append((lbl_copy, lambda: FileOperationManager.copy_items(effective_paths, app_controller), None))
            menu_specs.append((lbl_cut, lambda: FileOperationManager.cut_items(effective_paths, app_controller), None))

        if FileOperationManager.has_clipboard() and target_paste_dir and os.path.isdir(target_paste_dir):
            clip_cnt = len(FileOperationManager.get_clipboard().get('paths', []))
            menu_specs.append((
                f"📥  Buraya Yapıştır ({clip_cnt})",
                lambda: FileOperationManager.paste_items(target_paste_dir, app_controller, on_refresh=refresh_fn),
                'accent_light'
            ))

        if exists:
            menu_specs.append(("📦  Şuraya Taşı...", lambda: FileOperationManager.move_to_dialog(effective_paths, app_controller, on_refresh=refresh_fn), None))
            menu_specs.append(("📑  Şuraya Kopyala...", lambda: FileOperationManager.copy_to_dialog(effective_paths, app_controller, on_refresh=refresh_fn), None))

            if not is_multi:
                is_fav = FileOperationManager.is_favorite(norm_path, app_controller)
                fav_lbl = "⭐  Favorilerden Çıkar" if is_fav else "⭐  Favorilere Ekle"
                menu_specs.append((fav_lbl, lambda: FileOperationManager.toggle_favorite(norm_path, app_controller, on_refresh=refresh_fn), None))

                if is_file:
                    menu_specs.append(("🧠  AI Zekâsı ile İncele", lambda: cls._analyze_in_ai(norm_path, app_controller), None))

        if extra_actions:
            for ext_label, ext_cmd in extra_actions:
                menu_specs.append((ext_label, ext_cmd, None))

        menu_specs.append(("__SEP__", None, None))

        # --- GRUP 3: DÜZENLEME & SİLME (GERİ DÖNÜŞÜM KUTUSU VS KALICI SİLME) ---
        if exists:
            if not is_multi:
                menu_specs.append(("✏️  Yeniden Adlandır", lambda: FileOperationManager.rename_item_dialog(norm_path, app_controller, on_refresh=refresh_fn), None))

            recycle_lbl = f"♻️  Geri Dönüşüm Kutusu'na Taşı ({len(effective_paths)})" if is_multi else "♻️  Geri Dönüşüm Kutusu'na Taşı"
            perm_lbl = f"🗑️  Kalıcı Olarak Sil ({len(effective_paths)})..." if is_multi else "🗑️  Kalıcı Olarak Sil..."

            menu_specs.append((
                recycle_lbl,
                lambda: FileOperationManager.move_to_recycle_bin(effective_paths, app_controller, on_refresh=refresh_fn),
                None
            ))
            menu_specs.append((
                perm_lbl,
                lambda: FileOperationManager.permanent_delete(effective_paths, app_controller, on_refresh=refresh_fn),
                'danger'
            ))
            menu_specs.append(("__SEP__", None, None))

        # --- GRUP 4: SEÇİM, YOL KOPYALAMA, YENİLE & ÖZELLİKLER ---
        is_cur_sel = SelectionManager.is_selected(norm_path)
        sel_lbl = "⬜  Seçimi Kaldır" if is_cur_sel else "☑️  Seç"
        menu_specs.append((sel_lbl, lambda: SelectionManager.toggle(norm_path, theme_mode=theme_mode), None))
        if len(SelectionManager.get_selected()) > 1:
            menu_specs.append((
                f"🧹  Tüm Seçimleri Temizle ({len(SelectionManager.get_selected())})",
                lambda: SelectionManager.clear(theme_mode=theme_mode),
                None
            ))

        menu_specs.append(("🔗  Dosya Yolunu Kopyala", lambda: FileOperationManager.copy_file_path(effective_paths, app_controller), None))

        if callable(refresh_fn):
            menu_specs.append(("🔄  Görünümü Yenile", refresh_fn, None))

        if not is_multi and exists:
            menu_specs.append(("ℹ️  Özellikler", lambda: FileOperationManager.show_properties_dialog(norm_path, app_controller), None))

        # Butonları oluştur
        cls._menu_buttons = []
        last_was_sep = True
        for label, cmd, color_token in menu_specs:
            if label == "__SEP__":
                if not last_was_sep:
                    _add_separator()
                    last_was_sep = True
                continue
            last_was_sep = False
            txt_col = c(color_token) if color_token else c('text_primary')
            btn = ctk.CTkButton(
                inner,
                text=label,
                anchor="w",
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=c('bg_card_hover'),
                text_color=txt_col,
                command=lambda fn=cmd: (cls.close_active(), fn())
            )
            btn.pack(fill="x", pady=1)
            cls._menu_buttons.append((btn, cmd))

        # Ekran kenarı çarpışma kontrolü (Screen-Edge Collision Handling)
        try:
            menu.update_idletasks()
            req_h = max(220, inner.winfo_reqheight() + 16)
            req_w = menu_width
            rx = event.x_root - app_controller.winfo_rootx()
            ry = event.y_root - app_controller.winfo_rooty()
            win_w = max(400, app_controller.winfo_width())
            win_h = max(400, app_controller.winfo_height())
            x = max(8, min(rx, win_w - req_w - 12))
            y = max(8, min(ry, win_h - req_h - 12))
            menu.place(x=x, y=y)
            menu.lift()
        except Exception:
            menu.place(relx=0.5, rely=0.5, anchor="center")

    @classmethod
    def navigate_keyboard(cls, direction: int):
        """Yukarı (-1) veya Aşağı (+1) ok tuşu ile bağlam menüsü öğeleri arasında gezinir."""
        if not cls._active_menu or not cls._menu_buttons:
            return
        try:
            if not cls._active_menu.winfo_exists():
                return
        except Exception:
            return

        count = len(cls._menu_buttons)
        cls._focused_idx = (cls._focused_idx + direction) % count
        c_hover = FluentTheme.c('bg_card_hover', 'dark')
        for idx, (btn, _) in enumerate(cls._menu_buttons):
            try:
                btn.configure(fg_color=c_hover if idx == cls._focused_idx else "transparent")
            except Exception:
                pass

    @classmethod
    def activate_focused(cls) -> bool:
        """Enter tuşu ile seçili menü öğesini çalıştırır."""
        if not cls._active_menu or not cls._menu_buttons:
            return False
        if 0 <= cls._focused_idx < len(cls._menu_buttons):
            _, cmd = cls._menu_buttons[cls._focused_idx]
            cls.close_active()
            if callable(cmd):
                cmd()
            return True
        return False

    @staticmethod
    def _open_item(path: str):
        FileOperationManager.open_item(path)

    @staticmethod
    def _reveal_in_explorer(path: str):
        FileOperationManager.reveal_in_explorer(path)

    @staticmethod
    def _analyze_in_ai(path: str, app_controller):
        try:
            app_controller.navigate_to('ai')
            view = getattr(app_controller, 'current_view', None)
            if view and hasattr(view, 'analyze_file'):
                view.analyze_file(path)
        except Exception:
            pass

    @staticmethod
    def _copy_path(path: str, app_controller):
        FileOperationManager.copy_file_path(path, app_controller)
