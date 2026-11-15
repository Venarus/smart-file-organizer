"""
Windows 11 Premium Glass & Acrylic Compositor Engine (V2.1 Premium Glass Edition)
Provides:
1. Native Windows 10/11 DWM Acrylic & Mica Backdrop Integration via ctypes (dwmapi & user32):
   - DWMWA_SYSTEMBACKDROP_TYPE (Acrylic / Mica Alt)
   - SetWindowCompositionAttribute (ACCENT_ENABLE_ACRYLICBLURBEHIND)
   - DWMWA_BORDER_COLOR & DWMWA_CAPTION_COLOR (Subtle glass rim & midnight caption)
   - Genuine window translucency (-alpha compositor blending) so desktop wallpaper subtly shines through.
2. Procedural Frosted Glass & Aurora Light Renderer (PIL GaussianBlur + Specular Rim):
   - Renders genuine blurred glass hero banners, glowing icon orbs, and frosted surface headers
   - Memory-cached for zero frame-time overhead.
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
    Windows 10/11 masaüstü pencere yöneticisi (DWM) üzerinden gerçek
    Acrylic/Mica yarı-saydamlık, yuvarlatılmış köşe ve cam kenarlık efektlerini uygular.
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
            tk_widget.update_idletasks()
            wid = tk_widget.winfo_id()
            parent = ctypes.windll.user32.GetParent(wid)
            return parent if parent else wid
        except Exception:
            return 0

    @classmethod
    def apply_glass_window(cls, root_window, theme_mode: str = 'dark', glass_opacity: float = 0.95):
        """
        Ana pencereye Windows 11 DWM Acrylic/Mica arka planı, cam kenarlığı
        ve gerçek pencere yarı-saydamlığı (-alpha) uygular.
        """
        glass_opacity = max(0.82, min(1.0, float(glass_opacity)))

        # 1. Gerçek Pencere Yarı-Saydamlığı (Masaüstü duvar kağıdının cam yüzeyden hafifçe görünmesini sağlar)
        try:
            root_window.attributes("-alpha", glass_opacity)
        except Exception:
            pass

        hwnd = cls.get_hwnd(root_window)
        if not hwnd:
            return False

        try:
            dwmapi = ctypes.windll.dwmapi
            user32 = ctypes.windll.user32

            # 2. Koyu/Açık Mod Başlık Çubuğu
            is_dark = 1 if theme_mode == 'dark' else 0
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(is_dark)),
                ctypes.sizeof(ctypes.c_int)
            )

            # 3. Windows 11 Yuvarlatılmış Köşeler (DWMWCP_ROUND)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(cls.DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )

            # 4. Başlık Çubuğu ve İnce Cam Kenarlık Rengi (COLORREF formatı: 0x00BBGGRR)
            if theme_mode == 'dark':
                # Deep Midnight (#090D16 -> R=0x09, G=0x0D, B=0x16 -> 0x00160D09)
                caption_color = ctypes.c_uint(0x00160D09)
                # Subtle Cool Cyan-Blue Glass Rim (#284B78 -> R=0x28, G=0x4B, B=0x78 -> 0x00784B28)
                border_color = ctypes.c_uint(0x00784B28)
            else:
                # Crystal Light (#EEF2F9 -> R=0xEE, G=0xF2, B=0xF9 -> 0x00F9F2EE)
                caption_color = ctypes.c_uint(0x00F9F2EE)
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

            # 5. Windows 11 DWM System Backdrop (Acrylic = 3)
            backdrop_type = ctypes.c_int(cls.DWMSBT_TRANSIENTWINDOW)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                cls.DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(backdrop_type),
                ctypes.sizeof(ctypes.c_int)
            )

            # 6. Windows Compositor Acrylic Blur Behind (SetWindowCompositionAttribute)
            # AABBGGRR formatında yarı saydam gece mavisi/obsidyen katman
            gradient_abgr = 0xCC180E09 if theme_mode == 'dark' else 0xCCF9F2EE
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
    Gerçek PIL Gaussian Blur, yarı-saydam katmanlama (RGBA alpha compositing)
    ve üst kenar ışık kırılması (specular highlight) kullanarak
    Windows 11 Fluent Cam (Glassmorphism) yüzey dokuları üretir.
    """
    _cache = {}

    @classmethod
    def get_hero_banner(cls, width: int = 900, height: int = 128, theme_mode: str = 'dark', variant: str = 'aurora') -> ctk.CTkImage:
        """
        Dashboard ve ana ekranlar için yumuşak bulanıklaştırılmış (Gaussian Blur)
        Aurora Cam (Cyan + Elektrik Moru + Gece Mavisi) arka plan görüntüsü üretir.
        """
        key = (id(tk._default_root), "hero", width, height, theme_mode, variant)
        if key in cls._cache:
            return cls._cache[key]

        # Hızlı işlem için yarı çözünürlükte çizip bulanıklaştır, sonra hedef boyuta ölçekle
        w_low = max(120, width // 3)
        h_low = max(40, height // 2)

        if theme_mode == 'dark':
            base_rgba = (13, 19, 34, 255)
            bloom_cyan = (14, 165, 233, 115)     # #0EA5E9
            bloom_violet = (139, 92, 246, 105)   # #8B5CF6
            bloom_indigo = (56, 189, 248, 80)    # #38BDF8
            rim_top = (255, 255, 255, 55)
            rim_border = (56, 189, 248, 65)
        else:
            base_rgba = (238, 244, 253, 255)
            bloom_cyan = (14, 165, 233, 65)
            bloom_violet = (139, 92, 246, 55)
            bloom_indigo = (59, 130, 246, 50)
            rim_top = (255, 255, 255, 190)
            rim_border = (14, 165, 233, 75)

        img = Image.new("RGBA", (w_low, h_low), base_rgba)
        overlay = Image.new("RGBA", (w_low, h_low), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Aurora ışık küreleri
        draw.ellipse((-w_low * 0.1, -h_low * 0.6, w_low * 0.55, h_low * 1.4), fill=bloom_cyan)
        draw.ellipse((w_low * 0.35, -h_low * 0.5, w_low * 0.95, h_low * 1.5), fill=bloom_violet)
        draw.ellipse((w_low * 0.65, h_low * 0.1, w_low * 1.15, h_low * 1.6), fill=bloom_indigo)

        # Diyagonal cam yansıması (Specular glass sheen)
        draw.polygon(
            [
                (int(w_low * 0.15), 0),
                (int(w_low * 0.38), 0),
                (int(w_low * 0.22), h_low),
                (int(w_low * 0.02), h_low),
            ],
            fill=(255, 255, 255, 22 if theme_mode == 'dark' else 90)
        )

        blurred = overlay.filter(ImageFilter.GaussianBlur(radius=18))
        combined = Image.alpha_composite(img, blurred)
        full_img = combined.resize((width, height), Image.Resampling.BICUBIC)

        # Üst 1px cam parlaklığı (Specular top edge)
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
        """İstatistik ve kategori kartları için parlak yarı-saydam cam küre (orb) arka planı üretir."""
        key = (id(tk._default_root), "orb", size, color_hex, theme_mode)
        if key in cls._cache:
            return cls._cache[key]

        scale = 2
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        h = color_hex.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

        fill_alpha = 52 if theme_mode == 'dark' else 38
        rim_alpha = 140 if theme_mode == 'dark' else 110

        d.rounded_rectangle(
            (2, 2, s - 3, s - 3),
            radius=int(s * 0.28),
            fill=(r, g, b, fill_alpha),
            outline=(r, g, b, rim_alpha),
            width=2
        )
        # Üst parlama noktası
        d.line([(int(s * 0.25), 4), (int(s * 0.75), 4)], fill=(255, 255, 255, 110), width=2)

        final_img = img.resize((size, size), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(size, size))
        cls._cache[key] = ctk_img
        return ctk_img
