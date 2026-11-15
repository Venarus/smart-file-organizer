"""
Windows 11 Fluent Glass Design System & Color Tokens (V2.1 — Premium Glass Edition)
Provides:
- Deep Midnight Obsidian Glass (DARK) and Crystal Daylight Glass (LIGHT) palettes
- Cool Cyan-Blue (#0EA5E9 / #38BDF8) & Electric Violet (#8B5CF6 / #A78BFA) dual-accent system
- Translucent surface hierarchy (Layer 0 Base -> Layer 1 Frosted Card -> Layer 2 Elevated Glass)
- Specular border tokens and RGB color interpolation utilities.
"""

import customtkinter as ctk


class FluentTheme:
    # Midnight Obsidian Glass Theme (Windows 11 Acrylic & High-End Glassmorphism)
    DARK = {
        'bg_primary': '#090D16',         # Derin Gece Obsidyen Tabanı (Acrylic Base)
        'bg_mica': '#0C1220',            # Ana Çalışma Alanı Cam Tuvali
        'bg_secondary': '#0E1628',       # Yarı-Saydam Sidebar ve Üst Komut Barı
        'bg_card': '#131D33',            # Buzlu Cam Kart Yüzeyi (Glass Layer 1)
        'bg_card_secondary': '#18243E',  # İkincil Cam Katmanı (Glass Layer 2)
        'bg_elevated': '#1B2845',        # Yükseltilmiş Cam Yüzeyi (Modal / Flyout / Menü)
        'bg_card_hover': '#1E2E4F',      # Aydınlatılmış Cam Hover Yüzeyi
        'bg_card_active': '#233862',     # Seçili / Aktif Cam Yüzeyi
        'bg_input': '#0D1526',           # Çukur Cam Giriş Kutusu (Input Well)
        'border': '#233554',             # İnce Yarı-Saydam Cam Kenarlığı (1px Specular)
        'border_subtle': '#18263F',      # Düşük Kontrastlı Cam Ayırıcı
        'border_hover': '#38BDF8',       # Hover Durumunda Parlayan Buz Mavisi Kenarlık
        'border_focus': '#60A5FA',       # Odak (Focus) Işık Kenarlığı
        'accent': '#0EA5E9',             # Ana Cam Vurgusu (Cool Sky Cyan-Blue)
        'accent_hover': '#38BDF8',       # Parlak Cyan Hover
        'accent_pressed': '#0284C7',     # Basılı Durum
        'accent_light': '#7DD3FC',       # Buz Mavisi İkon ve Vurgu Metni
        'accent_violet': '#8B5CF6',      # İkincil Vurgu (Electric Violet)
        'accent_violet_light': '#C4B5FD',# Yumuşak Lavanta / Mor Vurgu
        'accent_subtle': '#152C4F',      # Yarı-Saydam Seçili Vurgu Arka Planı
        'nav_indicator': '#38BDF8',      # Sol Aktif Menü Neon-Cyan Çubuğu
        'text_primary': '#F8FAFC',       # Yumuşak Kristal Beyazı Ana Metin
        'text_secondary': '#94A3B8',     # Buzlu Gümüş İkincil Metin
        'text_muted': '#64748B',         # Pasif / Alt Bilgi Metni
        'text_disabled': '#475569',      # Devre Dışı Metin
        'success': '#34D399',            # Zümrüt Cam Yeşili
        'success_bg': '#0D2E2B',
        'warning': '#FBBF24',            # Kehribar Cam Sarısı
        'warning_bg': '#2E2412',
        'danger': '#FB7185',             # Yakut Cam Pembesi / Kırmızısı
        'danger_bg': '#331524',
        'error': '#F43F5E',              # Kritik İşlem / Silme
        'info': '#38BDF8',               # Bilgi Mavisi
        'info_bg': '#102A45',
        'skeleton_base': '#152038',      # İskelet Yükleme Tabanı
        'skeleton_highlight': '#24365C', # İskelet Yükleme Işıltısı
        'quick_access_bg': '#15223B',    # Hızlı Erişim Cam Çip Yüzeyi
        'quick_access_hover': '#213459'
    }

    # Crystal Daylight Glass Theme
    LIGHT = {
        'bg_primary': '#EAF0FA',         # Kristal Gün Işığı Tabanı
        'bg_mica': '#F1F5FC',            # Ana Çalışma Alanı Tuvali
        'bg_secondary': '#E4ECF8',       # Yarı-Saydam Sidebar ve Üst Bar
        'bg_card': '#FFFFFF',            # Kristal Beyaz Cam Kart (Glass Layer 1)
        'bg_card_secondary': '#F4F7FC',  # İkincil Cam Katmanı (Glass Layer 2)
        'bg_elevated': '#FFFFFF',        # Yükseltilmiş Modal / Flyout
        'bg_card_hover': '#F8FAFF',      # Kart Hover Yüzeyi
        'bg_card_active': '#DBEAFE',     # Seçili Cam Yüzeyi
        'bg_input': '#FFFFFF',           # Giriş Kutusu
        'border': '#CBD8EE',             # İnce Kristal Kenarlık
        'border_subtle': '#DEE7F5',      # Düşük Kontrastlı Ayırıcı
        'border_hover': '#0EA5E9',       # Hover Kenarlığı
        'border_focus': '#0284C7',       # Odak Kenarlığı
        'accent': '#0284C7',             # Cool Cyan-Blue Accent
        'accent_hover': '#0EA5E9',       # Accent Hover
        'accent_pressed': '#0369A1',     # Accent Basılı
        'accent_light': '#0369A1',       # Vurgu Metni / İkonu
        'accent_violet': '#7C3AED',      # İkincil Mor Vurgu
        'accent_violet_light': '#6D28D9',# Koyu Lavanta
        'accent_subtle': '#E0F2FE',      # Seçili Arka Plan
        'nav_indicator': '#0284C7',      # Sol Aktif Menü Çubuğu
        'text_primary': '#0F172A',       # Derin Arduvaz Ana Metin
        'text_secondary': '#475569',     # İkincil Metin
        'text_muted': '#64748B',         # Alt Bilgi Metni
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
        CustomTkinter cam bileşenlerinde pürüzsüz aydınlanma ve geçiş için kullanılır.
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
        Dosya uzantısına göre (Rozet Metni, İkon, Metin Rengi, Cam Arka Plan Rengi) döndürür.
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
            return ("IMG", "🖼️", c('accent_violet_light'), '#231B42' if mode == 'dark' else '#EDE9FE')
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
