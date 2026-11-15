"""
Windows 11 Fluent File Operations & Multi-Selection Engine (V2.1)
Provides reliable, non-blocking, and safe file management operations across all views:
- Open, Open With, Show in Explorer, Open Containing Folder
- Copy, Cut, Paste, Move To, Copy To, Copy File Path
- Safe Rename with extension preservation, character & conflict validation
- Differentiated Deletion:
  1. Move to Recycle Bin (Default, via Win32 SHFileOperationW with FOF_ALLOWUNDO)
  2. Permanent Delete (Always requires confirmation dialog, handles read-only/locked files)
- File & Folder Properties Dialog (Solid Fluent surface)
- Multi-Selection state management for batch context menu actions
"""

import os
import sys
import stat
import shutil
import ctypes
from ctypes import wintypes
import threading
import subprocess
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

from theme import FluentTheme
from animation import FluidAnimator, UIBridge
from config import save_config
from search_engine import SearchEngine


def format_size(size_bytes: int) -> str:
    return SearchEngine._format_bytes(size_bytes)


def get_file_category(filename: str) -> str:
    badge_txt, _, _, _ = FluentTheme.file_badge_style(filename, 'dark')
    return badge_txt


# ==============================================================================
# WIN32 RECYCLE BIN INTEROP (SHFileOperationW)
# ==============================================================================
FO_DELETE = 0x0003
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040
FOF_NOERRORUI = 0x0400

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class SHFILEOPSTRUCTW(ctypes.Structure):
    # Windows x64 uses natural alignment for SHFILEOPSTRUCTW (shellapi.h packs at 8 bytes on Win64, 1 byte on Win32)
    if ctypes.sizeof(ctypes.c_void_p) == 4:
        _pack_ = 1
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]


# ==============================================================================
# MULTI-SELECTION MANAGER
# ==============================================================================
class SelectionManager:
    """Tüm dosya görünümleri genelinde çoklu seçim (multi-selection) durumunu yönetir."""
    _selected = set()
    _widget_map = {}  # norm_path -> list of (widget, normal_bg_token, normal_border_token)

    @classmethod
    def _norm(cls, path: str) -> str:
        return os.path.normpath(path) if path else ""

    @classmethod
    def is_selected(cls, path: str) -> bool:
        return cls._norm(path) in cls._selected

    @classmethod
    def get_selected(cls) -> list:
        # Sadece hala mevcut olan yolları döndür
        valid = [p for p in list(cls._selected) if os.path.exists(p)]
        cls._selected = set(valid)
        return valid

    @classmethod
    def get_effective_paths(cls, clicked_path: str) -> list:
        """
        Sağ tıklanan öğe zaten seçili öğeler arasındaysa tüm seçili öğeleri döndürür.
        Değilse yalnızca sağ tıklanan öğeyi döndürür.
        """
        norm = cls._norm(clicked_path)
        selected = cls.get_selected()
        if norm in selected and len(selected) > 1:
            return selected
        return [norm] if norm else []

    @classmethod
    def register_widget(cls, path: str, widget, theme_mode: str = 'dark',
                        normal_bg_token: str = 'bg_card', normal_border_token: str = 'border'):
        if not path or not widget:
            return
        norm = cls._norm(path)
        entries = cls._widget_map.setdefault(norm, [])
        # Ölü widget referanslarını temizle
        alive = []
        for w, bgt, brt in entries:
            try:
                if w.winfo_exists():
                    alive.append((w, bgt, brt))
            except Exception:
                pass
        alive.append((widget, normal_bg_token, normal_border_token))
        cls._widget_map[norm] = alive

        if norm in cls._selected:
            cls._apply_visual(norm, True, theme_mode)

    @classmethod
    def _apply_visual(cls, norm_path: str, selected: bool, theme_mode: str = 'dark'):
        entries = cls._widget_map.get(norm_path, [])
        c = lambda token: FluentTheme.c(token, theme_mode)
        alive = []
        for w, bgt, brt in entries:
            try:
                if w.winfo_exists():
                    alive.append((w, bgt, brt))
                    if selected:
                        w.configure(fg_color=c('bg_card_active'), border_color=c('border_focus'))
                    else:
                        w.configure(fg_color=c(bgt), border_color=c(brt))
            except Exception:
                pass
        cls._widget_map[norm_path] = alive

    @classmethod
    def select(cls, path: str, theme_mode: str = 'dark'):
        norm = cls._norm(path)
        if not norm:
            return
        cls._selected.add(norm)
        cls._apply_visual(norm, True, theme_mode)

    @classmethod
    def deselect(cls, path: str, theme_mode: str = 'dark'):
        norm = cls._norm(path)
        cls._selected.discard(norm)
        cls._apply_visual(norm, False, theme_mode)

    @classmethod
    def toggle(cls, path: str, theme_mode: str = 'dark') -> bool:
        norm = cls._norm(path)
        if norm in cls._selected:
            cls.deselect(norm, theme_mode)
            return False
        else:
            cls.select(norm, theme_mode)
            return True

    @classmethod
    def clear(cls, theme_mode: str = 'dark'):
        old = list(cls._selected)
        cls._selected.clear()
        for norm in old:
            cls._apply_visual(norm, False, theme_mode)


# ==============================================================================
# FILE OPERATION MANAGER
# ==============================================================================
class FileOperationManager:
    """
    Tüm dosya ve klasör işlemlerini (Aç, Birlikte Aç, Kes/Kopyala/Yapıştır, Yeniden Adlandır,
    Geri Dönüşüm Kutusu'na Taşı, Kalıcı Sil, Özellikler, Favoriler) güvenli şekilde yürütür.
    """
    _clipboard = {'mode': None, 'paths': []}  # mode: 'copy' | 'cut' | None
    _active_modal = None

    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    INVALID_CHARS = set('<>:"/\\|?*')

    # ------------------------------------------------------------------
    # MODAL YÖNETİMİ
    # ------------------------------------------------------------------
    @classmethod
    def close_active_modal(cls):
        if cls._active_modal is not None:
            try:
                if cls._active_modal.winfo_exists():
                    cls._active_modal.destroy()
            except Exception:
                pass
            cls._active_modal = None

    @classmethod
    def _notify(cls, app, title: str, message: str, level: str = 'info'):
        if not app:
            return
        theme_mode = getattr(app, 'theme_mode', 'dark')
        try:
            FluidAnimator.show_toast(app, title, message, theme_mode=theme_mode, level=level)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # TEMEL AÇMA VE GEZGİN İŞLEMLERİ
    # ------------------------------------------------------------------
    @classmethod
    def open_item(cls, path: str, app=None) -> bool:
        if not path or not os.path.exists(path):
            cls._notify(app, "Dosya Bulunamadı", f"'{os.path.basename(path or '')}' artık mevcut değil.", level='error')
            return False
        try:
            os.startfile(os.path.normpath(path))
            return True
        except Exception as e:
            cls._notify(app, "Açma Hatası", str(e), level='error')
            return False

    @classmethod
    def open_with(cls, path: str, app=None) -> bool:
        if not path or not os.path.exists(path):
            cls._notify(app, "Dosya Bulunamadı", f"'{os.path.basename(path or '')}' bulunamadı.", level='error')
            return False
        try:
            norm = os.path.normpath(path)
            subprocess.Popen(['rundll32.exe', 'shell32.dll,OpenAs_RunDLL', norm])
            return True
        except Exception as e:
            cls._notify(app, "Birlikte Aç Hatası", str(e), level='error')
            return False

    @classmethod
    def reveal_in_explorer(cls, path: str, app=None) -> bool:
        if not path or not os.path.exists(path):
            cls._notify(app, "Konum Bulunamadı", f"'{os.path.basename(path or '')}' bulunamadı.", level='error')
            return False
        try:
            norm = os.path.normpath(path)
            if os.path.isfile(norm):
                subprocess.Popen(['explorer', '/select,', norm])
            else:
                os.startfile(norm)
            return True
        except Exception as e:
            cls._notify(app, "Gezgin Hatası", str(e), level='error')
            return False

    @classmethod
    def open_containing_folder(cls, path: str, app=None) -> bool:
        if not path:
            return False
        norm = os.path.normpath(path)
        parent = norm if os.path.isdir(norm) else os.path.dirname(norm)
        if not parent or not os.path.exists(parent):
            cls._notify(app, "Klasör Bulunamadı", "Üst klasör mevcut değil.", level='error')
            return False
        try:
            os.startfile(parent)
            return True
        except Exception as e:
            cls._notify(app, "Klasör Açma Hatası", str(e), level='error')
            return False

    @classmethod
    def copy_file_path(cls, paths, app=None) -> str:
        if isinstance(paths, str):
            paths = [paths]
        clean = [os.path.normpath(p) for p in paths if p]
        text = "\n".join(clean)
        if app and text:
            try:
                app.clipboard_clear()
                app.clipboard_append(text)
            except Exception:
                pass
            label = clean[0] if len(clean) == 1 else f"{len(clean)} dosya yolu kopyalandı"
            cls._notify(app, "Yol Panoya Kopyalandı", label, level='success')
        return text

    # ------------------------------------------------------------------
    # KOPYALA / KES / YAPIŞTIR / TAŞI
    # ------------------------------------------------------------------
    @classmethod
    def copy_items(cls, paths, app=None):
        if isinstance(paths, str):
            paths = [paths]
        valid = [os.path.normpath(p) for p in paths if p and os.path.exists(p)]
        if not valid:
            cls._notify(app, "Kopyalama Başarısız", "Seçili dosya bulunamadı.", level='warning')
            return False
        cls._clipboard = {'mode': 'copy', 'paths': valid}
        if app:
            try:
                app.clipboard_clear()
                app.clipboard_append("\n".join(valid))
            except Exception:
                pass
        msg = os.path.basename(valid[0]) if len(valid) == 1 else f"{len(valid)} öğe kopyalandı"
        cls._notify(app, "Panoya Kopyalandı", msg, level='info')
        return True

    @classmethod
    def cut_items(cls, paths, app=None):
        if isinstance(paths, str):
            paths = [paths]
        valid = [os.path.normpath(p) for p in paths if p and os.path.exists(p)]
        if not valid:
            cls._notify(app, "Kesme Başarısız", "Seçili dosya bulunamadı.", level='warning')
            return False
        cls._clipboard = {'mode': 'cut', 'paths': valid}
        msg = os.path.basename(valid[0]) if len(valid) == 1 else f"{len(valid)} öğe taşınmak üzere kesildi"
        cls._notify(app, "Kesildi", msg, level='info')
        return True

    @classmethod
    def has_clipboard(cls) -> bool:
        return bool(cls._clipboard.get('mode') and cls._clipboard.get('paths'))

    @classmethod
    def get_clipboard(cls) -> dict:
        return dict(cls._clipboard)

    @classmethod
    def _resolve_dest_collision(cls, dest_dir: str, basename: str) -> str:
        candidate = os.path.join(dest_dir, basename)
        if not os.path.exists(candidate):
            return candidate
        stem, ext = os.path.splitext(basename)
        idx = 1
        while True:
            new_name = f"{stem}_kopya_{idx}{ext}"
            cand = os.path.join(dest_dir, new_name)
            if not os.path.exists(cand):
                return cand
            idx += 1

    @classmethod
    def paste_items(cls, target_dir: str, app=None, on_refresh=None, synchronous: bool = False) -> dict:
        if not target_dir or not os.path.isdir(target_dir):
            cls._notify(app, "Yapıştırma Hatası", "Hedef klasör geçerli değil.", level='error')
            return {'succeeded': [], 'failed': [('target', 'Hedef klasör geçersiz')]}

        mode = cls._clipboard.get('mode')
        paths = list(cls._clipboard.get('paths') or [])
        if not mode or not paths:
            cls._notify(app, "Pano Boş", "Yapıştırılacak dosya bulunmuyor.", level='warning')
            return {'succeeded': [], 'failed': []}

        return cls._transfer_items(
            paths=paths,
            target_dir=target_dir,
            mode=mode,
            app=app,
            on_refresh=on_refresh,
            clear_clipboard_on_cut=True,
            synchronous=synchronous
        )

    @classmethod
    def _transfer_items(cls, paths: list, target_dir: str, mode: str, app=None,
                        on_refresh=None, clear_clipboard_on_cut: bool = False,
                        synchronous: bool = False) -> dict:
        results = {'succeeded': [], 'failed': []}
        norm_target = os.path.normpath(target_dir)

        def _worker():
            for src in paths:
                norm_src = os.path.normpath(src)
                if not os.path.exists(norm_src):
                    results['failed'].append((norm_src, "Dosya bulunamadı"))
                    continue
                base = os.path.basename(norm_src)
                try:
                    if mode == 'cut':
                        dest = os.path.join(norm_target, base)
                        if os.path.normcase(norm_src) == os.path.normcase(dest):
                            results['succeeded'].append(dest)
                            continue
                        if os.path.exists(dest):
                            dest = cls._resolve_dest_collision(norm_target, base)
                        shutil.move(norm_src, dest)
                        results['succeeded'].append(dest)
                    else:
                        dest = cls._resolve_dest_collision(norm_target, base)
                        if os.path.isdir(norm_src):
                            shutil.copytree(norm_src, dest)
                        else:
                            shutil.copy2(norm_src, dest)
                        results['succeeded'].append(dest)
                except Exception as e:
                    results['failed'].append((norm_src, str(e)))

            if mode == 'cut' and clear_clipboard_on_cut and results['succeeded']:
                cls._clipboard = {'mode': None, 'paths': []}

            def _finish_ui():
                ok_cnt = len(results['succeeded'])
                fail_cnt = len(results['failed'])
                verb = "taşındı" if mode == 'cut' else "kopyalandı"
                if ok_cnt and not fail_cnt:
                    cls._notify(app, "İşlem Tamamlandı", f"{ok_cnt} öğe başarıyla {verb}.", level='success')
                elif ok_cnt and fail_cnt:
                    cls._notify(app, "Kısmi Tamamlanma", f"{ok_cnt} öğe {verb}, {fail_cnt} başarısız.", level='warning')
                elif fail_cnt:
                    cls._notify(app, "İşlem Başarısız", results['failed'][0][1], level='error')
                if callable(on_refresh):
                    try:
                        on_refresh()
                    except Exception:
                        pass

            if synchronous:
                _finish_ui()
            else:
                UIBridge.post(_finish_ui)

        if synchronous:
            _worker()
        else:
            threading.Thread(target=_worker, daemon=True).start()
        return results

    @classmethod
    def move_to_dialog(cls, paths, app=None, on_refresh=None, target_dir: str = None, synchronous: bool = False):
        if isinstance(paths, str):
            paths = [paths]
        if target_dir is None:
            target_dir = filedialog.askdirectory(title="Taşınacak Hedef Klasörü Seçin")
        if not target_dir:
            return None
        return cls._transfer_items(paths, target_dir, mode='cut', app=app, on_refresh=on_refresh, synchronous=synchronous)

    @classmethod
    def copy_to_dialog(cls, paths, app=None, on_refresh=None, target_dir: str = None, synchronous: bool = False):
        if isinstance(paths, str):
            paths = [paths]
        if target_dir is None:
            target_dir = filedialog.askdirectory(title="Kopyalanacak Hedef Klasörü Seçin")
        if not target_dir:
            return None
        return cls._transfer_items(paths, target_dir, mode='copy', app=app, on_refresh=on_refresh, synchronous=synchronous)

    # ------------------------------------------------------------------
    # FAVORİLER
    # ------------------------------------------------------------------
    @classmethod
    def is_favorite(cls, path: str, app=None) -> bool:
        if not path or not app or not hasattr(app, 'cfg'):
            return False
        favs = app.cfg.get('favorites', [])
        norm = os.path.normcase(os.path.normpath(path))
        return any(os.path.normcase(os.path.normpath(f)) == norm for f in favs)

    @classmethod
    def toggle_favorite(cls, path: str, app=None, on_refresh=None) -> bool:
        if not path or not app or not hasattr(app, 'cfg'):
            return False
        norm = os.path.normpath(path)
        favs = list(app.cfg.get('favorites', []))
        norm_case = os.path.normcase(norm)
        existing = [f for f in favs if os.path.normcase(os.path.normpath(f)) == norm_case]
        if existing:
            for item in existing:
                favs.remove(item)
            app.cfg['favorites'] = favs
            save_config(app.cfg)
            cls._notify(app, "Favorilerden Çıkarıldı", os.path.basename(norm), level='info')
            added = False
        else:
            favs.append(norm)
            app.cfg['favorites'] = favs
            save_config(app.cfg)
            cls._notify(app, "Favorilere Eklendi", os.path.basename(norm), level='success')
            added = True
        if callable(on_refresh):
            try:
                on_refresh()
            except Exception:
                pass
        return added

    # ------------------------------------------------------------------
    # YENİDEN ADLANDIRMA (RENAME)
    # ------------------------------------------------------------------
    @classmethod
    def validate_new_name(cls, old_path: str, raw_new_name: str) -> tuple:
        """
        Yeni dosya/klasör adını doğrular.
        Dönüş: (is_valid: bool, final_new_path: str, error_message: str)
        - Varsayılan olarak dosya uzantısını korur (kullanıcı uzantı yazmadıysa eski uzantıyı ekler).
        - Geçersiz karakterleri (<>:"/\\|?*) ve Windows ayrılmış adlarını (CON, PRN vb.) reddeder.
        - Aynı klasördeki isim çakışmalarını tespit eder.
        """
        if not old_path:
            return False, "", "Geçersiz kaynak dosya yolu."
        norm_old = os.path.normpath(old_path)
        if not os.path.exists(norm_old):
            return False, "", "Kaynak dosya veya klasör artık mevcut değil."

        cleaned = (raw_new_name or "").strip()
        if not cleaned or cleaned in ('.', '..'):
            return False, "", "Dosya adı boş bırakılamaz."

        # Geçersiz karakter kontrolü
        if any(ch in cls.INVALID_CHARS or ord(ch) < 32 for ch in cleaned):
            return False, "", 'Dosya adı geçersiz karakterler içeremez (< > : " / \\ | ? *).'

        if cleaned.endswith('.') or cleaned.endswith(' '):
            return False, "", "Dosya adı nokta veya boşluk ile bitemez."

        is_dir = os.path.isdir(norm_old)
        old_base = os.path.basename(norm_old)
        _, old_ext = os.path.splitext(old_base)

        # Dosya ise ve kullanıcı uzantı belirtmediyse orijinal uzantıyı koru
        if not is_dir and old_ext:
            new_stem, new_ext = os.path.splitext(cleaned)
            if not new_ext:
                cleaned = f"{new_stem}{old_ext}"

        stem_check = os.path.splitext(cleaned)[0].upper()
        if stem_check in cls.RESERVED_NAMES or cleaned.upper() in cls.RESERVED_NAMES:
            return False, "", f"'{cleaned}' Windows tarafından ayrılmış bir sistem adıdır."

        parent_dir = os.path.dirname(norm_old)
        final_new_path = os.path.join(parent_dir, cleaned)

        # İsim çakışması kontrolü (büyük/küçük harf değişimi hariç başka bir dosya varsa reddet)
        if os.path.exists(final_new_path) and os.path.normcase(final_new_path) != os.path.normcase(norm_old):
            return False, final_new_path, f"'{cleaned}' adında bir öğe bu klasörde zaten mevcut."

        return True, final_new_path, ""

    @classmethod
    def execute_rename(cls, old_path: str, raw_new_name: str, app=None, on_refresh=None) -> tuple:
        """
        Doğrulama sonrası gerçek yeniden adlandırma işlemini gerçekleştirir.
        Dönüş: (success: bool, new_path: str, error_msg: str)
        """
        ok, new_path, err = cls.validate_new_name(old_path, raw_new_name)
        if not ok:
            cls._notify(app, "Yeniden Adlandırma Hatası", err, level='error')
            return False, "", err

        norm_old = os.path.normpath(old_path)
        if norm_old == new_path:
            return True, new_path, ""

        try:
            os.rename(norm_old, new_path)
        except PermissionError:
            msg = "Dosya başka bir program tarafından kullanılıyor veya erişim izni yok."
            cls._notify(app, "Yeniden Adlandırılamadı", msg, level='error')
            return False, "", msg
        except OSError as e:
            msg = f"Sistem hatası: {e.strerror or str(e)}"
            cls._notify(app, "Yeniden Adlandırılamadı", msg, level='error')
            return False, "", msg

        # Seçim listesini güncelle
        if SelectionManager.is_selected(norm_old):
            SelectionManager.deselect(norm_old)
            SelectionManager.select(new_path)

        cls._notify(
            app,
            "Yeniden Adlandırıldı",
            f"{os.path.basename(norm_old)} → {os.path.basename(new_path)}",
            level='success'
        )
        if callable(on_refresh):
            try:
                on_refresh()
            except Exception:
                pass
        return True, new_path, ""

    @classmethod
    def rename_item_dialog(cls, path: str, app=None, on_refresh=None):
        """
        Katı (solid) ve yüksek kontrastlı Windows 11 Fluent Yeniden Adlandırma penceresi açar.
        Dosya uzantısını varsayılan olarak korur ve anlık doğrulama yapar.
        """
        if not path or not os.path.exists(path):
            cls._notify(app, "Dosya Bulunamadı", "Yeniden adlandırılacak öğe mevcut değil.", level='error')
            return

        cls.close_active_modal()
        if not app:
            return

        theme_mode = getattr(app, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        norm_path = os.path.normpath(path)
        is_dir = os.path.isdir(norm_path)
        base_name = os.path.basename(norm_path)
        stem, ext = (base_name, "") if is_dir else os.path.splitext(base_name)

        modal = ctk.CTkFrame(
            app,
            fg_color=c('bg_elevated'),
            corner_radius=14,
            border_width=1,
            border_color=c('border_focus'),
            width=440,
            height=230
        )
        modal.pack_propagate(False)
        cls._active_modal = modal

        inner = ctk.CTkFrame(modal, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=18)

        # Başlık
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top,
            text="✏️  Yeniden Adlandır",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            top, text="✕", width=28, height=28, corner_radius=6,
            fg_color="transparent", hover_color=c('bg_card_hover'),
            text_color=c('text_secondary'), command=cls.close_active_modal
        ).pack(side="right")

        ctk.CTkLabel(
            inner,
            text=f"Mevcut: {base_name}",
            font=ctk.CTkFont(size=11),
            text_color=c('text_secondary'),
            anchor="w"
        ).pack(fill="x", pady=(6, 8))

        # Giriş satırı + Uzantı rozeti
        input_row = ctk.CTkFrame(inner, fg_color="transparent")
        input_row.pack(fill="x")

        entry = ctk.CTkEntry(
            input_row,
            height=38,
            corner_radius=8,
            fg_color=c('bg_input'),
            border_color=c('border_focus'),
            text_color=c('text_primary'),
            font=ctk.CTkFont(size=13)
        )
        entry.pack(side="left", fill="x", expand=True)
        entry.insert(0, stem)

        if ext:
            ext_badge = ctk.CTkLabel(
                input_row,
                text=ext,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=c('bg_card_secondary'),
                text_color=c('accent_light'),
                corner_radius=8,
                width=54,
                height=38
            )
            ext_badge.pack(side="left", padx=(8, 0))

        err_lbl = ctk.CTkLabel(
            inner,
            text="Dosya uzantısı otomatik olarak korunur.",
            font=ctk.CTkFont(size=11),
            text_color=c('text_muted'),
            anchor="w"
        )
        err_lbl.pack(fill="x", pady=(6, 10))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        def _submit(_event=None):
            raw_val = entry.get().strip()
            candidate = f"{raw_val}{ext}" if (ext and not raw_val.lower().endswith(ext.lower())) else raw_val
            ok, _, err_msg = cls.validate_new_name(norm_path, candidate)
            if not ok:
                err_lbl.configure(text=f"⚠️ {err_msg}", text_color=c('danger'))
                return
            cls.close_active_modal()
            cls.execute_rename(norm_path, candidate, app=app, on_refresh=on_refresh)

        ctk.CTkButton(
            btn_row,
            text="Vazgeç",
            width=100,
            height=34,
            corner_radius=8,
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            command=cls.close_active_modal
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Kaydet",
            width=110,
            height=34,
            corner_radius=8,
            fg_color=c('accent'),
            hover_color=c('accent_hover'),
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=_submit
        ).pack(side="right")

        entry.bind("<Return>", _submit)
        entry.bind("<Escape>", lambda _e: cls.close_active_modal())

        modal.place(relx=0.5, rely=0.5, anchor="center")
        modal.lift()
        try:
            entry.focus_set()
            entry.select_range(0, 'end')
        except Exception:
            pass

    # ------------------------------------------------------------------
    # SİLME İŞLEMLERİ: GERİ DÖNÜŞÜM KUTUSU (VARSAYILAN) & KALICI SİLME
    # ------------------------------------------------------------------
    @classmethod
    def is_file_locked(cls, path: str) -> bool:
        """
        Dosyanın başka bir işlem tarafından kilitli (in-use) olup olmadığını kontrol eder.
        Salt okunur (read-only) dosyalar kilitli sayılmaz, yalnızca paylaşım kilidi olanlar tespit edilir.
        """
        if not path or not os.path.isfile(path):
            return False
        try:
            # Windows CreateFileW ile paylaşım kontrolü (Silme/Yazma kilidi testi)
            kernel32 = ctypes.windll.kernel32
            FILE_SHARE_READ = 0x00000001
            DELETE_ACCESS = 0x00010000
            handle = kernel32.CreateFileW(
                os.path.normpath(path),
                DELETE_ACCESS,
                FILE_SHARE_READ,
                None,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL,
                None
            )
            if handle == INVALID_HANDLE_VALUE or handle == -1:
                err = kernel32.GetLastError()
                # ERROR_SHARING_VIOLATION = 32, ERROR_LOCK_VIOLATION = 33
                if err in (32, 33):
                    return True
                return False
            kernel32.CloseHandle(handle)
            return False
        except Exception:
            return False

    @classmethod
    def _send_to_recycle_bin_win32(cls, norm_path: str) -> tuple:
        """
        Win32 SHFileOperationW kullanarak dosyayı/klasörü Geri Dönüşüm Kutusu'na gönderir.
        Dönüş: (success: bool, error_reason: str)
        """
        if not os.path.exists(norm_path):
            return False, "Dosya veya klasör bulunamadı."

        if os.path.isfile(norm_path) and cls.is_file_locked(norm_path):
            return False, "Dosya şu anda başka bir uygulama tarafından kullanılıyor."

        # Salt okunur özelliği varsa Geri Dönüşüm Kutusu'na taşımadan önce kaldır
        try:
            attrs = os.stat(norm_path).st_mode
            if not (attrs & stat.S_IWRITE):
                os.chmod(norm_path, attrs | stat.S_IWRITE)
        except Exception:
            pass

        try:
            # SHFileOperationW çift null-terminated (\0\0) geniş karakter dizisi bekler
            buf = ctypes.create_unicode_buffer(norm_path + "\0\0")
            fileop = SHFILEOPSTRUCTW()
            fileop.hwnd = 0
            fileop.wFunc = FO_DELETE
            fileop.pFrom = ctypes.cast(buf, wintypes.LPCWSTR)
            fileop.pTo = None
            fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
            fileop.fAnyOperationsAborted = False
            fileop.hNameMappings = None
            fileop.lpszProgressTitle = None

            ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
            if ret != 0 or fileop.fAnyOperationsAborted:
                return False, f"Geri Dönüşüm Kutusu işlemi başarısız oldu (Kod: {ret})."

            # Dosyanın gerçekten silindiğini doğrula
            if os.path.exists(norm_path):
                return False, "Dosya Geri Dönüşüm Kutusu'na taşınamadı."
            return True, ""
        except Exception as e:
            return False, str(e)

    @classmethod
    def move_to_recycle_bin(cls, paths, app=None, on_refresh=None, synchronous: bool = False) -> dict:
        """
        Varsayılan Silme Davranışı: Seçili dosya veya klasörleri Geri Dönüşüm Kutusu'na taşır.
        Asla başarısız olan bir silme işlemini başarılı olarak bildirmez.
        """
        if isinstance(paths, str):
            paths = [paths]
        target_list = [os.path.normpath(p) for p in paths if p]
        results = {'succeeded': [], 'failed': []}

        if not target_list:
            cls._notify(app, "Silme Hatası", "Silinecek geçerli bir öğe seçilmedi.", level='warning')
            return results

        def _worker():
            for p in target_list:
                ok, reason = cls._send_to_recycle_bin_win32(p)
                if ok:
                    results['succeeded'].append(p)
                    SelectionManager.deselect(p)
                else:
                    results['failed'].append((p, reason))

            def _finish():
                ok_cnt = len(results['succeeded'])
                fail_cnt = len(results['failed'])
                if ok_cnt and not fail_cnt:
                    msg = (
                        f"'{os.path.basename(results['succeeded'][0])}' Geri Dönüşüm Kutusu'na taşındı."
                        if ok_cnt == 1 else f"{ok_cnt} öğe Geri Dönüşüm Kutusu'na taşındı."
                    )
                    cls._notify(app, "Geri Dönüşüm Kutusu'na Taşındı", msg, level='success')
                elif ok_cnt and fail_cnt:
                    cls._notify(
                        app,
                        "Kısmi Silme",
                        f"{ok_cnt} öğe taşındı, {fail_cnt} öğe silinemedi ({results['failed'][0][1]}).",
                        level='warning'
                    )
                else:
                    reason = results['failed'][0][1] if results['failed'] else "Bilinmeyen hata"
                    cls._notify(app, "Silme Başarısız", reason, level='error')

                if callable(on_refresh) and ok_cnt > 0:
                    try:
                        on_refresh()
                    except Exception:
                        pass

            if synchronous:
                _finish()
            else:
                UIBridge.post(_finish)

        if synchronous:
            _worker()
        else:
            threading.Thread(target=_worker, daemon=True).start()
        return results

    @classmethod
    def _delete_permanently_single(cls, norm_path: str) -> tuple:
        """Tek bir dosya veya klasörü kalıcı olarak siler ve gerçekten silindiğini doğrular."""
        if not os.path.exists(norm_path):
            return False, "Dosya veya klasör bulunamadı."

        if os.path.isfile(norm_path) and cls.is_file_locked(norm_path):
            return False, "Dosya şu anda başka bir program tarafından kullanılıyor."

        def _onerror(func, p, _exc_info):
            try:
                os.chmod(p, stat.S_IWRITE)
                func(p)
            except Exception:
                pass

        try:
            if os.path.isdir(norm_path) and not os.path.islink(norm_path):
                shutil.rmtree(norm_path, onerror=_onerror)
            else:
                try:
                    os.chmod(norm_path, stat.S_IWRITE)
                except Exception:
                    pass
                os.remove(norm_path)

            if os.path.exists(norm_path):
                return False, "Öğe diskten kaldırılamadı (Erişim engellendi)."
            return True, ""
        except PermissionError:
            return False, "Erişim izni reddedildi veya dosya kullanımda."
        except OSError as e:
            return False, e.strerror or str(e)

    @classmethod
    def execute_permanent_delete(cls, paths, app=None, on_refresh=None, synchronous: bool = False) -> dict:
        """Onay alındıktan sonra kalıcı silme işlemini yürütür."""
        if isinstance(paths, str):
            paths = [paths]
        target_list = [os.path.normpath(p) for p in paths if p]
        results = {'succeeded': [], 'failed': []}

        def _worker():
            for p in target_list:
                ok, reason = cls._delete_permanently_single(p)
                if ok:
                    results['succeeded'].append(p)
                    SelectionManager.deselect(p)
                else:
                    results['failed'].append((p, reason))

            def _finish():
                ok_cnt = len(results['succeeded'])
                fail_cnt = len(results['failed'])
                if ok_cnt and not fail_cnt:
                    msg = (
                        f"'{os.path.basename(results['succeeded'][0])}' kalıcı olarak silindi."
                        if ok_cnt == 1 else f"{ok_cnt} öğe kalıcı olarak silindi."
                    )
                    cls._notify(app, "Kalıcı Olarak Silindi", msg, level='success')
                elif ok_cnt and fail_cnt:
                    cls._notify(
                        app,
                        "Kısmi Kalıcı Silme",
                        f"{ok_cnt} silindi, {fail_cnt} başarısız ({results['failed'][0][1]}).",
                        level='warning'
                    )
                else:
                    reason = results['failed'][0][1] if results['failed'] else "Silme işlemi başarısız."
                    cls._notify(app, "Kalıcı Silme Başarısız", reason, level='error')

                if callable(on_refresh) and ok_cnt > 0:
                    try:
                        on_refresh()
                    except Exception:
                        pass

            if synchronous:
                _finish()
            else:
                UIBridge.post(_finish)

        if synchronous:
            _worker()
        else:
            threading.Thread(target=_worker, daemon=True).start()
        return results

    @classmethod
    def permanent_delete(cls, paths, app=None, on_refresh=None,
                         confirm_callback=None, synchronous: bool = False):
        """
        Kalıcı Silme (Permanent Delete).
        KURAL: Açık onay (confirmation) olmadan ASLA kalıcı silme yapmaz.
        - confirm_callback verildiyse (test veya özel onaycı) onu çağırır.
        - Aksi halde kullanıcıya etkilenen öğe sayısını gösteren katı Fluent onay penceresi açar.
        """
        if isinstance(paths, str):
            paths = [paths]
        valid = [os.path.normpath(p) for p in paths if p]
        if not valid:
            cls._notify(app, "Silme Hatası", "Silinecek geçerli bir öğe bulunamadı.", level='warning')
            return {'succeeded': [], 'failed': [], 'aborted': True}

        if callable(confirm_callback):
            confirmed = bool(confirm_callback(valid))
            if not confirmed:
                return {'succeeded': [], 'failed': [], 'aborted': True}
            return cls.execute_permanent_delete(valid, app=app, on_refresh=on_refresh, synchronous=synchronous)

        if not app:
            # UI olmadan ve confirm_callback olmadan asla kalıcı silme yapma!
            return {'succeeded': [], 'failed': [], 'aborted': True}

        cls.close_active_modal()
        theme_mode = getattr(app, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        count = len(valid)
        title_txt = "⚠️ Kalıcı Silme Onayı"
        if count == 1:
            name = os.path.basename(valid[0])
            desc_txt = (
                f"'{name}' öğesini kalıcı olarak silmek istediğinize emin misiniz?\n\n"
                "Bu işlem Geri Dönüşüm Kutusu'nu atlar ve GERİ ALINAMAZ."
            )
        else:
            desc_txt = (
                f"Seçili {count} öğeyi kalıcı olarak silmek istediğinize emin misiniz?\n\n"
                "Bu işlem Geri Dönüşüm Kutusu'nu atlar ve GERİ ALINAMAZ."
            )

        modal = ctk.CTkFrame(
            app,
            fg_color=c('bg_elevated'),
            corner_radius=14,
            border_width=1,
            border_color=c('danger'),
            width=450,
            height=225
        )
        modal.pack_propagate(False)
        cls._active_modal = modal

        inner = ctk.CTkFrame(modal, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=18)

        ctk.CTkLabel(
            inner,
            text=title_txt,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('danger'),
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            inner,
            text=desc_txt,
            font=ctk.CTkFont(size=12),
            text_color=c('text_primary'),
            justify="left",
            anchor="w",
            wraplength=400
        ).pack(fill="x", pady=(12, 16))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        def _confirm():
            cls.close_active_modal()
            cls.execute_permanent_delete(valid, app=app, on_refresh=on_refresh, synchronous=synchronous)

        def _recycle_instead():
            cls.close_active_modal()
            cls.move_to_recycle_bin(valid, app=app, on_refresh=on_refresh, synchronous=synchronous)

        ctk.CTkButton(
            btn_row,
            text="Vazgeç",
            width=90,
            height=34,
            corner_radius=8,
            fg_color=c('bg_card'),
            hover_color=c('bg_card_hover'),
            text_color=c('text_primary'),
            command=cls.close_active_modal
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="🗑️ Kalıcı Olarak Sil",
            width=145,
            height=34,
            corner_radius=8,
            fg_color=c('danger'),
            hover_color="#DC2626",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=_confirm
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="♻️ Geri Dönüşüm'e Taşı",
            width=150,
            height=34,
            corner_radius=8,
            fg_color=c('bg_card_secondary'),
            hover_color=c('bg_card_hover'),
            text_color=c('accent_light'),
            font=ctk.CTkFont(size=11, weight="bold"),
            command=_recycle_instead
        ).pack(side="left")

        modal.place(relx=0.5, rely=0.5, anchor="center")
        modal.lift()
        return {'pending_confirmation': True, 'count': count}

    # ------------------------------------------------------------------
    # ÖZELLİKLER (PROPERTIES / FILE DETAILS)
    # ------------------------------------------------------------------
    @classmethod
    def get_item_properties(cls, path: str) -> dict:
        norm = os.path.normpath(path) if path else ""
        if not norm or not os.path.exists(norm):
            return {'exists': False, 'path': norm}

        st = os.stat(norm)
        is_dir = os.path.isdir(norm)
        name = os.path.basename(norm) or norm
        _, ext = os.path.splitext(name)

        size_bytes = st.st_size
        item_count = None
        if is_dir:
            try:
                entries = list(os.scandir(norm))
                item_count = len(entries)
                size_bytes = sum(e.stat().st_size for e in entries if e.is_file())
            except Exception:
                item_count = 0

        return {
            'exists': True,
            'name': name,
            'path': norm,
            'parent': os.path.dirname(norm),
            'is_dir': is_dir,
            'extension': ext.lower() if not is_dir else "Klasör",
            'category': "Klasör" if is_dir else get_file_category(name),
            'size_bytes': size_bytes,
            'size_human': format_size(size_bytes),
            'item_count': item_count,
            'created': datetime.fromtimestamp(st.st_ctime).strftime('%d.%m.%Y %H:%M:%S'),
            'modified': datetime.fromtimestamp(st.st_mtime).strftime('%d.%m.%Y %H:%M:%S'),
            'accessed': datetime.fromtimestamp(st.st_atime).strftime('%d.%m.%Y %H:%M:%S'),
            'readonly': not bool(st.st_mode & stat.S_IWRITE),
        }

    @classmethod
    def show_properties_dialog(cls, path: str, app=None):
        info = cls.get_item_properties(path)
        if not info.get('exists'):
            cls._notify(app, "Özellikler Alınamadı", "Dosya veya klasör bulunamadı.", level='error')
            return None

        if not app:
            return info

        cls.close_active_modal()
        theme_mode = getattr(app, 'theme_mode', 'dark')
        c = lambda token: FluentTheme.c(token, theme_mode)

        modal = ctk.CTkFrame(
            app,
            fg_color=c('bg_elevated'),
            corner_radius=14,
            border_width=1,
            border_color=c('border_hover'),
            width=460,
            height=380
        )
        modal.pack_propagate(False)
        cls._active_modal = modal

        inner = ctk.CTkFrame(modal, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=18)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        icon = "📁" if info['is_dir'] else "📄"
        ctk.CTkLabel(
            top,
            text=f"{icon}  Öğe Özellikleri",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=c('text_primary')
        ).pack(side="left")

        ctk.CTkButton(
            top, text="✕", width=28, height=28, corner_radius=6,
            fg_color="transparent", hover_color=c('bg_card_hover'),
            text_color=c('text_secondary'), command=cls.close_active_modal
        ).pack(side="right")

        ctk.CTkFrame(inner, fg_color=c('border_subtle'), height=1).pack(fill="x", pady=(0, 10))

        rows = [
            ("Adı:", info['name']),
            ("Tür / Kategori:", f"{info['category']} ({info['extension']})"),
            ("Konum:", info['parent']),
            ("Boyut:", f"{info['size_human']} ({info['size_bytes']:,} bayt)".replace(',', '.')),
            ("Oluşturulma:", info['created']),
            ("Değiştirilme:", info['modified']),
            ("Son Erişim:", info['accessed']),
            ("Öznitelikler:", "Salt Okunur" if info['readonly'] else "Normal (Okuma/Yazma)"),
        ]
        if info['is_dir'] and info['item_count'] is not None:
            rows.insert(4, ("İçerik:", f"{info['item_count']} alt öğe"))

        for label_txt, val_txt in rows:
            r = ctk.CTkFrame(inner, fg_color="transparent", height=26)
            r.pack(fill="x", pady=2)
            r.pack_propagate(False)
            ctk.CTkLabel(
                r, text=label_txt, width=120, anchor="w",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=c('text_secondary')
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=str(val_txt)[:48] + ("..." if len(str(val_txt)) > 48 else ""),
                anchor="w", font=ctk.CTkFont(size=11), text_color=c('text_primary')
            ).pack(side="left", fill="x", expand=True)

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom", pady=(10, 0))

        ctk.CTkButton(
            btn_row, text="📋 Yolu Kopyala", width=125, height=32, corner_radius=8,
            fg_color=c('bg_card_secondary'), hover_color=c('bg_card_hover'),
            text_color=c('text_primary'), font=ctk.CTkFont(size=11),
            command=lambda: cls.copy_file_path(info['path'], app)
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="📍 Klasörde Göster", width=135, height=32, corner_radius=8,
            fg_color=c('bg_card_secondary'), hover_color=c('bg_card_hover'),
            text_color=c('text_primary'), font=ctk.CTkFont(size=11),
            command=lambda: (cls.close_active_modal(), cls.reveal_in_explorer(info['path'], app))
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row, text="Kapat", width=90, height=32, corner_radius=8,
            fg_color=c('accent'), hover_color=c('accent_hover'),
            text_color="#FFFFFF", font=ctk.CTkFont(size=11, weight="bold"),
            command=cls.close_active_modal
        ).pack(side="right")

        modal.place(relx=0.5, rely=0.5, anchor="center")
        modal.lift()
        return info
