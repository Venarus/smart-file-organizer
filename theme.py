"""
Windows 11 Fluent Glass Design System & Color Tokens (V2.1 — Corrected Solid Surface Hierarchy)
Transparency Rules:
- Main Application Window Background (bg_primary): Deep Acrylic/Mica base (#070B12 / #E6EEF8)
- Sidebar (bg_secondary): Semi-opaque solid distinguishable surface (#10192B / #DCE6F4)
- Main Content Area (bg_mica): Controlled, readable workspace surface (#0B121E / #F1F5FA)
- Cards & File Rows (bg_card / bg_card_secondary): Solid, high-contrast surfaces (#16233A / #1E2F4D)
- Dialogs & Context Menus (bg_elevated): Opaque, high-contrast elevated surface (#1B2B46 / #FFFFFF)
"""

import tkinter as tk
import customtkinter as ctk


class FluentTheme:
    _font_cache = {}

    @classmethod
    def font(cls, size: int = 12, weight: str = "normal", family: str = None) -> ctk.CTkFont:
        """
        Paylaşımlı CTkFont önbelleği (Aktif Tk root örneğine duyarlı).
        Her bileşen için yeni Tcl font nesnesi ve ScalingTracker geri çağırımı
        oluşturulmasını önleyerek sayfa geçişlerini ve bellek kullanımını optimize eder.
        """
        root_id = id(tk._default_root)
        key = (root_id, family or "default", int(size), str(weight))
        cached = cls._font_cache.get(key)
        if cached is not None:
            return cached
        if family:
            f = ctk.CTkFont(family=family, size=size, weight=weight)
        else:
            f = ctk.CTkFont(size=size, weight=weight)
        cls._font_cache[key] = f
        return f

    # Midnight Obsidian Theme (Windows 11 Acrylic Window + Solid Readable Surfaces)
    DARK = {
        'bg_primary': '#070B12',         # Ana Pencere Tabanı (DWM Acrylic / Mica Arka Planı)
        'bg_mica': '#0B121E',            # Ana Çalışma Alanı Kontrollü Okunaklı Zemin
        'bg_secondary': '#10192B',       # Yarı-Opak Katı Kenar Çubuğu (Sidebar) ve Üst Bar
        'bg_card': '#16233A',            # Katı ve Yüksek Kontrastlı Kart & Dosya Satırı Yüzeyi
        'bg_card_secondary': '#1E2F4D',  # İkincil Katı Kart Katmanı (Alt Satırlar / Çipler)
        'bg_elevated': '#1B2B46',        # Tam Okunaklı Bağlam Menüsü (Context Menu) / Diyalog Yüzeyi
        'bg_card_hover': '#24385A',      # Belirgin Satır / Kart Hover Yüzeyi
        'bg_card_active': '#29436E',     # Seçili / Aktif Dosya Satırı Yüzeyi
        'bg_input': '#0E1726',           # Belirgin Giriş Kutusu (Input Field) Arka Planı
        'border': '#293F66',             # Net Kart ve Satır Kenarlığı (1px)
        'border_subtle': '#1F3150',      # Tablo ve Satır Ayırıcı Kenarlık
        'border_hover': '#38BDF8',       # Hover Durumunda Parlayan Buz Mavisi Kenarlık
        'border_focus': '#60A5FA',       # Odak (Focus) ve Seçim Kenarlığı
        'accent': '#0EA5E9',             # Ana Vurgu (Cool Sky Cyan-Blue)
        'accent_hover': '#38BDF8',       # Parlak Cyan Hover
        'accent_pressed': '#0284C7',     # Basılı Durum
        'accent_light': '#7DD3FC',       # Buz Mavisi İkon ve Vurgu Metni
        'accent_bg': '#132A4A',          # Vurgu Rozet Arka Planı
        'accent_violet': '#8B5CF6',      # İkincil Vurgu (Electric Violet)
        'accent_violet_light': '#C4B5FD',# Yumuşak Lavanta / Mor Vurgu
        'accent_subtle': '#173054',      # Seçili Vurgu Arka Planı
        'nav_indicator': '#38BDF8',      # Sol Aktif Menü Neon-Cyan Çubuğu
        'text_primary': '#F8FAFC',       # Kristal Beyazı Yüksek Kontrastlı Ana Metin
        'text_secondary': '#CBD5E1',     # Açık Gümüş Okunaklı İkincil Metin
        'text_muted': '#94A3B8',         # Alt Bilgi / Meta Veri Metni (Yüksek Okunabilirlik)
        'text_disabled': '#64748B',      # Devre Dışı Metin
        'success': '#34D399',            # Zümrüt Yeşili
        'success_bg': '#0F332F',
        'warning': '#FBBF24',            # Kehribar Sarısı
        'warning_bg': '#332814',
        'danger': '#FB7185',             # Yakut Kırmızısı
        'danger_bg': '#3B1829',
        'error': '#F43F5E',              # Kritik İşlem / Silme
        'info': '#38BDF8',               # Bilgi Mavisi
        'info_bg': '#132E4C',
        'skeleton_base': '#18263F',      # İskelet Yükleme Tabanı
        'skeleton_highlight': '#263B61', # İskelet Yükleme Işıltısı
        'quick_access_bg': '#1A2A46',    # Hızlı Erişim Katı Çip Yüzeyi
        'quick_access_hover': '#253B61'
    }

    # Crystal Daylight Theme (Windows 11 Light Mode with Solid Cards)
    LIGHT = {
        'bg_primary': '#E6EEF8',         # Ana Pencere Tabanı
        'bg_mica': '#F1F5FA',            # Ana Çalışma Alanı Kontrollü Zemin
        'bg_secondary': '#DCE6F4',       # Yarı-Opak Katı Sidebar ve Üst Bar
        'bg_card': '#FFFFFF',            # Katı Beyaz Kart & Dosya Satırı Yüzeyi
        'bg_card_secondary': '#F4F7FB',  # İkincil Katı Kart Katmanı
        'bg_elevated': '#FFFFFF',        # Tam Okunaklı Bağlam Menüsü / Diyalog Yüzeyi
        'bg_card_hover': '#EDF4FF',      # Belirgin Kart Hover Yüzeyi
        'bg_card_active': '#DBEAFE',     # Seçili Dosya Satırı Yüzeyi
        'bg_input': '#FFFFFF',           # Giriş Kutusu
        'border': '#C4D4EB',             # Net Kart ve Satır Kenarlığı
        'border_subtle': '#D8E3F2',      # Düşük Kontrastlı Ayırıcı
        'border_hover': '#0284C7',       # Hover Kenarlığı
        'border_focus': '#0284C7',       # Odak Kenarlığı
        'accent': '#0284C7',             # Cool Cyan-Blue Accent
        'accent_hover': '#0EA5E9',       # Accent Hover
        'accent_pressed': '#0369A1',     # Accent Basılı
        'accent_light': '#0369A1',       # Vurgu Metni / İkonu
        'accent_bg': '#E0F2FE',          # Vurgu Rozet Arka Planı
        'accent_violet': '#7C3AED',      # İkincil Mor Vurgu
        'accent_violet_light': '#6D28D9',# Koyu Lavanta
        'accent_subtle': '#E0F2FE',      # Seçili Arka Plan
        'nav_indicator': '#0284C7',      # Sol Aktif Menü Çubuğu
        'text_primary': '#0F172A',       # Derin Arduvaz Ana Metin
        'text_secondary': '#334155',     # İkincil Metin
        'text_muted': '#475569',         # Alt Bilgi Metni
        'text_disabled': '#94A3B8',      # Devre Dışı Metin
        'success': '#059669',
        'success_bg': '#D1FAE5',
        'warning': '#D97706',
        'warning_bg': '#FEF3C7',
        'danger': '#E11D48',
        'danger_bg': '#FFE4E6',
        'error': '#E11D48',
        'info': '#0284C7',
        'info_bg': '#E0F2FE',
        'skeleton_base': '#E2E8F0',
        'skeleton_highlight': '#F1F5F9',
        'quick_access_bg': '#FFFFFF',
        'quick_access_hover': '#E0F2FE'
    }

    @classmethod
    def get_colors(cls, mode='dark'):
        if mode == 'light':
            return cls.LIGHT
        return cls.DARK

    @classmethod
    def apply_appearance(cls, mode='dark'):
        if mode == 'system':
            ctk.set_appearance_mode("System")
        elif mode == 'light':
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    @classmethod
    def c(cls, token_name, current_mode='dark'):
        """Belirtilen mod için renk kodunu döndürür."""
        palette = cls.LIGHT if current_mode == 'light' else cls.DARK
        return palette.get(token_name, '#0EA5E9')

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """#RRGGBB kodunu (R, G, B) tuple değerine dönüştürür."""
        h = hex_color.lstrip('#')
        if len(h) == 3:
            h = ''.join(ch * 2 for ch in h)
        if len(h) != 6:
            return (14, 165, 233)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return (14, 165, 233)

    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """(R, G, B) tuple değerini #RRGGBB koduna dönüştürür."""
        r = max(0, min(255, int(round(rgb[0]))))
        g = max(0, min(255, int(round(rgb[1]))))
        b = max(0, min(255, int(round(rgb[2]))))
        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def interpolate_color(cls, start_hex: str, end_hex: str, t: float) -> str:
        """
        İki renk arasında t (0.0 -> 1.0) oranında doğrusal RGB interpolasyonu yapar.
        """
        t = max(0.0, min(1.0, float(t)))
        r1, g1, b1 = cls.hex_to_rgb(start_hex)
        r2, g2, b2 = cls.hex_to_rgb(end_hex)
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        return cls.rgb_to_hex((r, g, b))

    @classmethod
    def file_badge_style(cls, filename: str, mode: str = 'dark') -> tuple:
        """
        Dosya uzantısına göre (Rozet Metni, İkon, Metin Rengi, Katı Arka Plan Rengi) döndürür.
        """
        lower = (filename or "").lower()
        c = lambda tok: cls.c(tok, mode)
        if lower.endswith(('.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt')):
            return ("DOC", "📄", c('accent_light'), c('info_bg'))
        if lower.endswith(('.xls', '.xlsx', '.csv')):
            return ("XLS", "📊", c('success'), c('success_bg'))
        if lower.endswith(('.ppt', '.pptx')):
            return ("PPT", "📽️", c('warning'), c('warning_bg'))
        if lower.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.svg')):
            return ("IMG", "🖼️", c('accent_violet_light'), '#261C4A' if mode == 'dark' else '#EDE9FE')
        if lower.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
            return ("VID", "🎬", c('danger'), c('danger_bg'))
        if lower.endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
            return ("AUD", "🎵", c('warning'), c('warning_bg'))
        if lower.endswith(('.zip', '.rar', '.7z', '.tar', '.gz')):
            return ("ARC", "🗄️", c('warning'), c('warning_bg'))
        if lower.endswith(('.py', '.js', '.ts', '.cpp', '.c', '.cs', '.html', '.css', '.json', '.ino')):
            return ("CODE", "💻", c('success'), c('success_bg'))
        if lower.endswith(('.exe', '.msi', '.bat')):
            return ("APP", "⚙️", c('accent_light'), c('info_bg'))
        if lower.endswith('.lnk'):
            return ("LNK", "🔗", c('text_secondary'), c('bg_card_secondary'))
        return ("FILE", "📄", c('text_secondary'), c('bg_card_secondary'))
