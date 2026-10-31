"""
Thumbnail Engine with Windows Shell & PIL Integration
Extracts high-fidelity thumbnails for Videos (.mp4, .mkv, .avi, .mov, etc.)
and Images (.png, .jpg, .webp, .gif, etc.) using Windows IShellItemImageFactory.
Includes fast memory & disk caching for sub-millisecond loads.
"""

import os
import sys
import ctypes
from ctypes import wintypes
import threading
from PIL import Image
import customtkinter as ctk

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
    _memory_cache = {}  # (path, width, height) -> CTkImage
    _lock = threading.Lock()

    SUPPORTED_VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.flv', '.m4v'}
    SUPPORTED_IMAGE = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico', '.tiff'}
    SUPPORTED_MEDIA = SUPPORTED_VIDEO | SUPPORTED_IMAGE

    @classmethod
    def is_media_file(cls, path):
        _, ext = os.path.splitext(path.lower())
        return ext in cls.SUPPORTED_MEDIA

    @classmethod
    def is_video(cls, path):
        _, ext = os.path.splitext(path.lower())
        return ext in cls.SUPPORTED_VIDEO

    @classmethod
    def get_thumbnail(cls, file_path, target_width=160, target_height=110):
        """
        Dosya için thumbnail döner (CTkImage).
        Varsa bellekten, yoksa Windows Shell veya PIL üzerinden üretir.
        """
        cache_key = (file_path, target_width, target_height)
        with cls._lock:
            if cache_key in cls._memory_cache:
                return cls._memory_cache[cache_key]

        img = cls._extract_shell_image(file_path, target_width, target_height)
        if not img:
            img = cls._extract_pil_image(file_path, target_width, target_height)

        if img:
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(target_width, target_height))
            with cls._lock:
                if len(cls._memory_cache) > 200:
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

            # Center on canvas
            canvas = Image.new('RGBA', (width, height), (30, 30, 30, 255))
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
                canvas = Image.new('RGBA', (width, height), (30, 30, 30, 255))
                offset_x = (width - img.width) // 2
                offset_y = (height - img.height) // 2
                canvas.paste(img, (offset_x, offset_y), img)
                return canvas
        except Exception:
            return None

import queue

class AsyncThumbnailLoader:
    _queue = queue.Queue()
    _worker_started = False
    _lock = threading.Lock()

    @classmethod
    def request_thumbnail(cls, file_path, width, height, callback):
        """Kuyruğa küçük resim isteği ekler ve tek bir arka plan thread'i ile sırayla işler."""
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
                img = ThumbnailEngine.get_thumbnail(file_path, width, height)
                if callback:
                    callback(img)
                cls._queue.task_done()
            except Exception:
                pass
