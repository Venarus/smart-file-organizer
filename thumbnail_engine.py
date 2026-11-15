"""
Thumbnail Engine with Windows Shell & PIL Integration (V2.1 Stability Upgrade)
Extracts high-fidelity thumbnails for Videos (.mp4, .mkv, .avi, .mov, etc.)
and Images (.png, .jpg, .jpeg, .webp, .gif, etc.) using Windows IShellItemImageFactory.
Includes:
- Fast memory caching keyed by Tk root instance
- Locked-aspect-ratio (width x height) placeholder CTkImage generation so cards never
  resize or shift layout when thumbnails finish loading
- Thread-safe UIBridge dispatch so widget updates never run on the background thread
"""

import os
import sys
import ctypes
from ctypes import wintypes
import threading
import queue
import tkinter as tk
from PIL import Image, ImageDraw
import customtkinter as ctk
from animation import UIBridge

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, '.thumbnail_cache')

ole32 = ctypes.windll.ole32
shell32 = ctypes.windll.shell32
gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32

try:
    ole32.CoInitialize(None)
except Exception:
    pass


class SIZE(ctypes.Structure):
    _fields_ = [('cx', wintypes.LONG), ('cy', wintypes.LONG)]


class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', wintypes.DWORD),
        ('Data2', wintypes.WORD),
        ('Data3', wintypes.WORD),
        ('Data4', wintypes.BYTE * 8)
    ]


# IID_IShellItemImageFactory: {bcc18b79-ba16-442f-80c4-8a59c30c463b}
IID_IShellItemImageFactory = GUID(
    0xbcc18b79, 0xba16, 0x442f,
    (wintypes.BYTE * 8)(0x80, 0xc4, 0x8a, 0x59, 0xc3, 0x0c, 0x46, 0x3b)
)


class BITMAP(ctypes.Structure):
    _fields_ = [
        ('bmType', wintypes.LONG),
        ('bmWidth', wintypes.LONG),
        ('bmHeight', wintypes.LONG),
        ('bmWidthBytes', wintypes.LONG),
        ('bmPlanes', wintypes.WORD),
        ('bmBitsPixel', wintypes.WORD),
        ('bmBits', ctypes.c_void_p)
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD)
    ]


class ThumbnailEngine:
    _memory_cache = {}       # (root_id, path, width, height) -> CTkImage
    _pil_cache = {}          # (path, width, height) -> PIL.Image
    _placeholder_cache = {}  # (root_id, width, height, is_video, theme_mode) -> CTkImage
    _lock = threading.Lock()

    SUPPORTED_VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.flv', '.m4v'}
    SUPPORTED_IMAGE = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.tiff'}
    SUPPORTED_MEDIA = SUPPORTED_VIDEO | SUPPORTED_IMAGE

    @classmethod
    def _root_id(cls) -> int:
        return id(tk._default_root) if tk._default_root is not None else 0

    @classmethod
    def is_media_file(cls, path):
        _, ext = os.path.splitext(path.lower())
        return ext in cls.SUPPORTED_MEDIA

    @classmethod
    def is_video(cls, path):
        _, ext = os.path.splitext(path.lower())
        return ext in cls.SUPPORTED_VIDEO

    @classmethod
    def get_placeholder(cls, target_width=160, target_height=100, is_video=False, theme_mode='dark'):
        """
        Sabit boyutlu (target_width x target_height) yer tutucu CTkImage döndürür.
        Küçük resim yüklenmeden önce ve yüklendikten sonra bileşen boyutunun birebir aynı
        kalmasını sağlayarak kaydırma (scroll) sırasında kart kaymalarını %100 önler.
        """
        rid = cls._root_id()
        key = (rid, target_width, target_height, bool(is_video), theme_mode)
        with cls._lock:
            if key in cls._placeholder_cache:
                return cls._placeholder_cache[key]

        bg_rgb = (15, 23, 42, 255) if theme_mode == 'dark' else (226, 232, 240, 255)
        fg_rgb = (59, 130, 246, 180) if is_video else (148, 163, 184, 150)

        canvas = Image.new('RGBA', (target_width, target_height), bg_rgb)
        draw = ImageDraw.Draw(canvas)
        cx, cy = target_width // 2, target_height // 2

        if is_video:
            # Ortada şık oynat (play) üçgeni ve çerçevesi
            r = 18
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fg_rgb, width=2)
            draw.polygon([(cx - 5, cy - 8), (cx - 5, cy + 8), (cx + 9, cy)], fill=fg_rgb)
        else:
            # Ortada minimal görsel çerçevesi ikonu
            w2, h2 = 18, 14
            draw.rectangle((cx - w2, cy - h2, cx + w2, cy + h2), outline=fg_rgb, width=2)
            draw.polygon([(cx - 12, cy + 10), (cx - 3, cy - 2), (cx + 4, cy + 6), (cx + 9, cy + 1), (cx + 14, cy + 10)], fill=fg_rgb)

        ctk_img = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(target_width, target_height))
        with cls._lock:
            cls._placeholder_cache[key] = ctk_img
        return ctk_img

    @classmethod
    def get_Cached_Sync(cls, file_path, target_width=160, target_height=100):
        """Bellekte hazır varsa anında CTkImage döndürür, yoksa None döner (UI thread için sıfır bloklama)."""
        rid = cls._root_id()
        cache_key = (rid, file_path, target_width, target_height)
        with cls._lock:
            if cache_key in cls._memory_cache:
                return cls._memory_cache[cache_key]
            pil_key = (file_path, target_width, target_height)
            pil_img = cls._pil_cache.get(pil_key)
        if pil_img is not None:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(target_width, target_height))
            with cls._lock:
                cls._memory_cache[cache_key] = ctk_img
            return ctk_img
        return None

    @classmethod
    def extract_pil_thumbnail(cls, file_path, target_width=160, target_height=100):
        """Arka plan iş parçacığında güvenli çalışır (Tk nesnesi oluşturmaz, yalnızca PIL Image üretir)."""
        pil_key = (file_path, target_width, target_height)
        with cls._lock:
            if pil_key in cls._pil_cache:
                return cls._pil_cache[pil_key]

        img = cls._extract_shell_image(file_path, target_width, target_height)
        if not img:
            img = cls._extract_pil_image(file_path, target_width, target_height)

        if img:
            with cls._lock:
                if len(cls._pil_cache) > 300:
                    cls._pil_cache.clear()
                cls._pil_cache[pil_key] = img
        return img

    @classmethod
    def get_thumbnail(cls, file_path, target_width=160, target_height=110):
        """
        Dosya için thumbnail döner (CTkImage).
        Varsa bellekten, yoksa Windows Shell veya PIL üzerinden üretir.
        """
        cached = cls.get_Cached_Sync(file_path, target_width, target_height)
        if cached is not None:
            return cached

        img = cls.extract_pil_thumbnail(file_path, target_width, target_height)
        if img:
            rid = cls._root_id()
            cache_key = (rid, file_path, target_width, target_height)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(target_width, target_height))
            with cls._lock:
                if len(cls._memory_cache) > 300:
                    cls._memory_cache.clear()
                cls._memory_cache[cache_key] = ctk_img
            return ctk_img

        return None

    @classmethod
    def _extract_shell_image(cls, file_path, width, height):
        if not os.path.exists(file_path):
            return None
        try:
            p_factory = ctypes.c_void_p()
            hr = shell32.SHCreateItemFromParsingName(
                file_path, None,
                ctypes.byref(IID_IShellItemImageFactory),
                ctypes.byref(p_factory)
            )
            if hr != 0 or not p_factory:
                return None

            vtable = ctypes.cast(p_factory, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            GetImage_proto = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, SIZE, ctypes.c_ulong, ctypes.POINTER(wintypes.HBITMAP)
            )
            GetImage = GetImage_proto(vtable[3])

            size = SIZE(width * 2, height * 2)  # High DPI supersampling
            hbitmap = wintypes.HBITMAP()
            hr_img = GetImage(p_factory, size, 0x00, ctypes.byref(hbitmap))

            if hr_img != 0 or not hbitmap:
                Release_proto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
                Release_proto(vtable[2])(p_factory)
                return None

            bmp = BITMAP()
            gdi32.GetObjectW(hbitmap, ctypes.sizeof(bmp), ctypes.byref(bmp))

            hdc = user32.GetDC(0)
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = bmp.bmWidth
            bmi.biHeight = -bmp.bmHeight  # Top-down DIB
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0

            buf_size = bmp.bmWidth * bmp.bmHeight * 4
            buffer = (ctypes.c_char * buf_size)()
            gdi32.GetDIBits(hdc, hbitmap, 0, bmp.bmHeight, buffer, ctypes.byref(bmi), 0)

            user32.ReleaseDC(0, hdc)
            gdi32.DeleteObject(hbitmap)

            Release_proto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
            Release_proto(vtable[2])(p_factory)

            raw_img = Image.frombuffer('RGBA', (bmp.bmWidth, bmp.bmHeight), buffer, 'raw', 'BGRA', 0, 1)
            raw_img.thumbnail((width, height), Image.Resampling.LANCZOS)

            canvas = Image.new('RGBA', (width, height), (15, 23, 42, 255))
            offset_x = (width - raw_img.width) // 2
            offset_y = (height - raw_img.height) // 2
            canvas.paste(raw_img, (offset_x, offset_y), raw_img if raw_img.mode == 'RGBA' else None)
            return canvas
        except Exception:
            return None

    @classmethod
    def _extract_pil_image(cls, file_path, width, height):
        try:
            with Image.open(file_path) as img:
                img = img.convert('RGBA')
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                canvas = Image.new('RGBA', (width, height), (15, 23, 42, 255))
                offset_x = (width - img.width) // 2
                offset_y = (height - img.height) // 2
                canvas.paste(img, (offset_x, offset_y), img)
                return canvas
        except Exception:
            return None


class AsyncThumbnailLoader:
    _queue = queue.Queue()
    _worker_started = False
    _lock = threading.Lock()

    @classmethod
    def clear_pending(cls):
        """Sayfa veya filtre değiştiğinde kuyrukta bekleyen eski küçük resim isteklerini temizler."""
        try:
            while not cls._queue.empty():
                cls._queue.get_nowait()
                cls._queue.task_done()
        except Exception:
            pass

    @classmethod
    def request_thumbnail(cls, file_path, width, height, callback):
        """
        Kuyruğa küçük resim isteği ekler.
        Önbellekte varsa senkron olarak hemen döndürür; yoksa arka planda PIL Image üretir
        ve CTkImage oluşturma + widget güncellemesini UIBridge üzerinden ana UI thread'de yapar.
        """
        cached = ThumbnailEngine.get_Cached_Sync(file_path, width, height)
        if cached is not None:
            if callable(callback):
                callback(cached)
            return

        cls._ensure_worker()
        cls._queue.put((file_path, width, height, callback))

    @classmethod
    def _ensure_worker(cls):
        with cls._lock:
            if not cls._worker_started:
                cls._worker_started = True
                threading.Thread(target=cls._worker_loop, daemon=True).start()

    @classmethod
    def _worker_loop(cls):
        try:
            ole32.CoInitialize(None)
        except Exception:
            pass

        while True:
            try:
                file_path, width, height, callback = cls._queue.get()
                pil_img = ThumbnailEngine.extract_pil_thumbnail(file_path, width, height)
                if callback:
                    def _deliver(p=file_path, w=width, h=height, img=pil_img, cb=callback):
                        try:
                            if img is not None:
                                rid = ThumbnailEngine._root_id()
                                key = (rid, p, w, h)
                                with ThumbnailEngine._lock:
                                    ctk_img = ThumbnailEngine._memory_cache.get(key)
                                    if ctk_img is None:
                                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
                                        ThumbnailEngine._memory_cache[key] = ctk_img
                                cb(ctk_img)
                            else:
                                cb(None)
                        except Exception:
                            pass
                    UIBridge.post(_deliver)
                cls._queue.task_done()
            except Exception:
                pass
