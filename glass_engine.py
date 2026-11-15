"""
Windows 11 Premium Glass & Acrylic Compositor Engine (V2.1 — Corrected Transparency Architecture)
Provides:
1. Native Windows 10/11 DWM Acrylic & Mica Backdrop Integration via ctypes (dwmapi & user32):
   - Applies backdrop/caption/border styling ONLY to the top-level main application window.
   - NEVER sets global window alpha < 1.0 (WS_EX_LAYERED LWA_ALPHA), ensuring all child widgets,
     sidebar, cards, file lists, text, dialogs, and context menus remain 100% solid and readable.
2. Procedural Frosted Glass & Orb Renderer (PIL GaussianBlur + Specular Rim):
   - Memory-cached by active Tk root for zero frame-time overhead.
"""

import ctypes
from ctypes import wintypes
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENT_POLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


class WindowsGlassCompositor:
    """
    Windows 10/11 masaüstü pencere yöneticisi (DWM) üzerinden YALNIZCA ana pencere
    arka planına ve çerçevesine Acrylic/Mica görünümü uygular.
    Alt bileşenlerin (kartlar, dosya listeleri, metinler, menüler) şeffaflaşmasını
    önlemek için global pencere opaklığı (-alpha) her zaman 1.0 (tam katı/okunaklı) tutulur.
    """

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36
    DWMWA_SYSTEMBACKDROP_TYPE = 38

    DWMWCP_ROUND = 2
    DWMSBT_MAINWINDOW = 2       # Mica
    DWMSBT_TRANSIENTWINDOW = 3  # Acrylic
    DWMSBT_TABBEDWINDOW = 4     # Mica Alt

    WCA_ACCENT_POLICY = 19
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

    @classmethod
    def get_hwnd(cls, tk_widget) -> int:
        try:
            wid = tk_widget.winfo_id()
            parent = ctypes.windll.user32.GetParent(wid)
            return parent if parent else wid
        except Exception:
            return 0

    @classmethod
    def apply_glass_window(cls, root_window, theme_mode: str = 'dark', glass_opacity: float = 1.0):
        """
        Ana pencereye Windows 11 DWM Acrylic/Mica başlık/çerçeve özniteliklerini uygular.
        ÖNEMLİ KURAL: Alt bileşenlerin, kartların, metinlerin ve sağ-tık menülerinin
        şeffaflaşıp masaüstü duvar kağıdına karışmaması için global pencere -alpha
        değeri her zaman 1.0 olarak sabitlenir.
        """
        try:
            # Global widget ağacı şeffaflığını kesin olarak devre dışı bırak (her zaman 1.0 katı)
            root_window.attributes("-alpha", 1.0)
        except Exception:
            pass

        hwnd = cls.get_hwnd(root_window)
        if not hwnd:
            return False

        try:
            dwmapi = ctypes.windll.dwmapi
            user32 = ctypes.windll.user32

            # 1. Koyu/Açık Mod Başlık Çubuğu
            is_dark = 1 if theme_mode == 'dark' else 0
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(is_dark)),
                ctypes.sizeof(ctypes.c_int)
            )

            # 2. Windows 11 Yuvarlatılmış Köşeler (DWMWCP_ROUND)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(cls.DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )

            # 3. Başlık Çubuğu ve İnce Cam Kenarlık Rengi (COLORREF formatı: 0x00BBGGRR)
            if theme_mode == 'dark':
                caption_color = ctypes.c_uint(0x00120B07)
                border_color = ctypes.c_uint(0x0068422B)
            else:
                caption_color = ctypes.c_uint(0x00FAF0EA)
                border_color = ctypes.c_uint(0x00E8C69A)

            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_CAPTION_COLOR,
                ctypes.byref(caption_color),
                ctypes.sizeof(ctypes.c_uint)
            )
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_BORDER_COLOR,
                ctypes.byref(border_color),
                ctypes.sizeof(ctypes.c_uint)
            )

            # 4. Windows 11 DWM System Backdrop (Mica Alt / Acrylic yalnızca ana pencere çerçevesinde)
            backdrop_type = ctypes.c_int(cls.DWMSBT_MAINWINDOW)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(backdrop_type),
                ctypes.sizeof(ctypes.c_int)
            )

            # 5. Ana pencere arka planı için kontrollü DWM Acrylic katmanı
            alpha_byte = int(max(210, min(250, round(float(glass_opacity) * 245))))
            rgb_part = 0x120B07 if theme_mode == 'dark' else 0xFAF0EA
            gradient_abgr = (alpha_byte << 24) | rgb_part

            policy = ACCENT_POLICY()
            policy.AccentState = cls.ACCENT_ENABLE_ACRYLICBLURBEHIND
            policy.AccentFlags = 2
            policy.GradientColor = ctypes.c_uint(gradient_abgr)
            policy.AnimationId = 0

            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = cls.WCA_ACCENT_POLICY
            data.Data = ctypes.pointer(policy)
            data.SizeOfData = ctypes.sizeof(policy)

            user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
            return True
        except Exception:
            return False


class GlassArtEngine:
    """
    PIL Gaussian Blur ve üst kenar ışık kırılması (specular highlight) kullanarak
    Windows 11 Fluent yüzey dokuları ve ikon küreleri üretir.
    """
    _cache = {}

    @classmethod
    def get_hero_banner(cls, width: int = 900, height: int = 128, theme_mode: str = 'dark', variant: str = 'aurora') -> ctk.CTkImage:
        key = (id(tk._default_root), "hero", width, height, theme_mode, variant)
        if key in cls._cache:
            return cls._cache[key]

        w_low = max(120, width // 3)
        h_low = max(40, height // 2)

        if theme_mode == 'dark':
            base_rgba = (20, 31, 52, 255)
            bloom_cyan = (14, 165, 233, 95)
            bloom_violet = (139, 92, 246, 85)
            bloom_indigo = (56, 189, 248, 70)
            rim_top = (255, 255, 255, 55)
            rim_border = (56, 189, 248, 75)
        else:
            base_rgba = (255, 255, 255, 255)
            bloom_cyan = (14, 165, 233, 45)
            bloom_violet = (139, 92, 246, 40)
            bloom_indigo = (59, 130, 246, 35)
            rim_top = (255, 255, 255, 220)
            rim_border = (14, 165, 233, 85)

        img = Image.new("RGBA", (w_low, h_low), base_rgba)
        overlay = Image.new("RGBA", (w_low, h_low), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        draw.ellipse((-w_low * 0.1, -h_low * 0.6, w_low * 0.55, h_low * 1.4), fill=bloom_cyan)
        draw.ellipse((w_low * 0.35, -h_low * 0.5, w_low * 0.95, h_low * 1.5), fill=bloom_violet)
        draw.ellipse((w_low * 0.65, h_low * 0.1, w_low * 1.15, h_low * 1.6), fill=bloom_indigo)

        blurred = overlay.filter(ImageFilter.GaussianBlur(radius=18))
        combined = Image.alpha_composite(img, blurred)
        full_img = combined.resize((width, height), Image.Resampling.BICUBIC)

        final_draw = ImageDraw.Draw(full_img)
        final_draw.line([(2, 1), (width - 3, 1)], fill=rim_top, width=1)
        final_draw.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=14,
            outline=rim_border,
            width=1
        )

        ctk_img = ctk.CTkImage(light_image=full_img, dark_image=full_img, size=(width, height))
        cls._cache[key] = ctk_img
        return ctk_img

    @classmethod
    def get_glass_orb(cls, size: int = 42, color_hex: str = "#38BDF8", theme_mode: str = 'dark') -> ctk.CTkImage:
        """İstatistik ve kategori kartları için katı/okunaklı parlak küre arka planı üretir."""
        key = (id(tk._default_root), "orb", size, color_hex, theme_mode)
        if key in cls._cache:
            return cls._cache[key]

        scale = 2
        s = size * scale
        base_rgb = (22, 34, 56, 255) if theme_mode == 'dark' else (241, 245, 249, 255)
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        h = color_hex.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        # Katı ve okunaklı zemin üzerine vurgu rengi
        blended_r = int(base_rgb[0] * 0.72 + r * 0.28)
        blended_g = int(base_rgb[1] * 0.72 + g * 0.28)
        blended_b = int(base_rgb[2] * 0.72 + b * 0.28)

        d.rounded_rectangle(
            (2, 2, s - 3, s - 3),
            radius=int(s * 0.28),
            fill=(blended_r, blended_g, blended_b, 255),
            outline=(r, g, b, 210),
            width=2
        )
        d.line([(int(s * 0.25), 4), (int(s * 0.75), 4)], fill=(255, 255, 255, 130), width=2)

        final_img = img.resize((size, size), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(size, size))
        cls._cache[key] = ctk_img
        return ctk_img
