"""
Windows 11 Fluent Notification Center & Contextual Menu System (V2.1)
Provides:
- NotificationCenter: Centralized notification store with unread badge tracking,
  deduplication, and an interactive Windows 11 Flyout drawer.
- FluentContextMenu: Modern Windows 11 right-click context menu for files and folders.
"""

import os
import subprocess
from datetime import datetime
import customtkinter as ctk
from theme import FluentTheme
from animation import FluidAnimator


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

        # Üst Başlık
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

        # Konumlandır ve yumuşak giriş uygula
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
    Windows 11 Fluent Sağ-Tık Bağlam Menüsü (Context Menu).
    Dosya ve klasör satırlarına sağ tıklandığında hızlı aksiyonlar sunar.
    """
    _active_menu = None

    @classmethod
    def close_active(cls):
        if cls._active_menu is not None:
            try:
                if cls._active_menu.winfo_exists():
                    cls._active_menu.destroy()
            except Exception:
                pass
            cls._active_menu = None

    @classmethod
    def bind_to_widget(cls, widget, file_path: str, app_controller, extra_actions=None):
        """Bir dosya veya klasör kartına sağ-tık (<Button-3>) menüsü bağlar."""
        if not widget:
            return

        def _on_right_click(event):
            cls.show(event, file_path, app_controller, extra_actions=extra_actions)

        try:
            widget.bind("<Button-3>", _on_right_click, add="+")
            for child in widget.winfo_children():
                child.bind("<Button-3>", _on_right_click, add="+")
        except Exception:
            pass

    @classmethod
    def show(cls, event, file_path: str, app_controller, extra_actions=None):
        cls.close_active()
        if not app_controller or not file_path:
            return

        theme_mode = getattr(app_controller, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        menu = ctk.CTkFrame(
            app_controller,
            fg_color=c('bg_elevated'),
            corner_radius=10,
            border_width=1,
            border_color=c('border_hover'),
            width=215
        )
        cls._active_menu = menu

        inner = ctk.CTkFrame(menu, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=6, pady=6)

        name = os.path.basename(file_path) or file_path
        ctk.CTkLabel(
            inner,
            text=f"📄 {name[:24]}" + ("..." if len(name) > 24 else ""),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=c('accent_light'),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(2, 4))

        ctk.CTkFrame(inner, fg_color=c('border_subtle'), height=1).pack(fill="x", padx=4, pady=3)

        actions = [
            ("📂  Aç", lambda: cls._open_item(file_path)),
            ("📍  Klasörde Göster", lambda: cls._reveal_in_explorer(file_path)),
        ]

        if os.path.isfile(file_path):
            actions.append(("🧠  AI Zekâsı ile İncele", lambda: cls._analyze_in_ai(file_path, app_controller)))

        if extra_actions:
            actions.extend(extra_actions)

        actions.append(("📋  Yolu Panoya Kopyala", lambda: cls._copy_path(file_path, app_controller)))

        for label, cmd in actions:
            btn = ctk.CTkButton(
                inner,
                text=label,
                anchor="w",
                height=30,
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=c('bg_card_hover'),
                text_color=c('text_primary'),
                command=lambda fn=cmd: (cls.close_active(), fn())
            )
            btn.pack(fill="x", pady=1)

        # Fare koordinatlarına göre yerleştir
        try:
            rx = event.x_root - app_controller.winfo_rootx()
            ry = event.y_root - app_controller.winfo_rooty()
            win_w = app_controller.winfo_width()
            win_h = app_controller.winfo_height()
            x = max(10, min(rx, win_w - 230))
            y = max(10, min(ry, win_h - 210))
            menu.place(x=x, y=y)
            menu.lift()
        except Exception:
            menu.place(relx=0.5, rely=0.5, anchor="center")

    @staticmethod
    def _open_item(path: str):
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception:
                pass

    @staticmethod
    def _reveal_in_explorer(path: str):
        if not os.path.exists(path):
            return
        try:
            norm = os.path.normpath(path)
            if os.path.isfile(norm):
                subprocess.Popen(['explorer', '/select,', norm])
            else:
                os.startfile(norm)
        except Exception:
            pass

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
        try:
            app_controller.clipboard_clear()
            app_controller.clipboard_append(path)
            FluidAnimator.show_toast(
                app_controller,
                "Panoya Kopyalandı",
                path,
                theme_mode=getattr(app_controller, 'theme_mode', 'dark'),
                duration_ms=2200,
                level='success'
            )
        except Exception:
            pass
