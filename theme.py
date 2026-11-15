"""
Windows 11 Fluent Design System Theme & Color Tokens (V2.1)
Provides centralized design tokens, dark/light mode switching, surface hierarchy,
subtle borders, elevation states, and color interpolation utilities.
"""

import customtkinter as ctk


class FluentTheme:
    # Dark Theme Tokens (Windows 11 Settings / Explorer / Store inspired)
    DARK = {
        'bg_primary': '#1C1C1C',        # Ana pencere tabanı (Mica Base)
        'bg_mica': '#202020',           # Ana içerik arka planı
        'bg_secondary': '#252525',      # Sidebar ve Üst Başlık yüzeyi
        'bg_card': '#2B2B2B',           # Kart yüzeyi (Fluent Layer 1)
        'bg_card_secondary': '#323232', # İkincil kart yüzeyi (Fluent Layer 2)
        'bg_elevated': '#363636',       # Yükseltilmiş yüzey (Modal / Flyout / Palette)
        'bg_card_hover': '#353535',     # Kart üzerine gelindiğinde
        'bg_card_active': '#3E3E3E',    # Aktif / Seçili kart veya menü
        'bg_input': '#242424',          # Giriş alanları / Arama kutusu
        'border': '#383838',            # İnce kenarlık (Subtle stroke)
        'border_subtle': '#2F2F2F',     # Çok düşük kontrastlı ayırıcı
        'border_hover': '#4E4E4E',      # Üzerine gelindiğinde kenarlık
        'border_focus': '#60CDFF',      # Odak (Focus) kenarlığı
        'accent': '#0078D4',            # Windows 11 Ana Mavi Accent
        'accent_hover': '#1984D8',      # Accent Hover
        'accent_pressed': '#006CBE',    # Accent Basılı
        'accent_light': '#60CDFF',      # Açık Mavi (İkonlar ve vurgular)
        'accent_subtle': '#1E3A52',     # Yumuşak mavi seçili arka plan
        'nav_indicator': '#60CDFF',     # Sol aktif menü dikey vurgu çubuğu
        'text_primary': '#FFFFFF',      # Ana metin
        'text_secondary': '#C5C5C5',    # İkincil açıklama metni
        'text_muted': '#8A8A8A',        # Pasif / Alt bilgi metni
        'text_disabled': '#5E5E5E',     # Devre dışı metin
        'success': '#6CCB5F',           # Başarılı (Windows Security Yeşili)
        'success_bg': '#1E3320',
        'warning': '#FCE100',           # Uyarı
        'warning_bg': '#3A3415',
        'danger': '#FF99A4',            # Hata / Silme
        'danger_bg': '#3D1E22',
        'error': '#F44336',             # Kritik Hata Butonu
        'info': '#60CDFF',              # Bilgi
        'info_bg': '#192E3D',
        'skeleton_base': '#292929',     # İskelet yükleme tabanı
        'skeleton_highlight': '#383838',# İskelet yükleme parlaması
        'quick_access_bg': '#262626',   # Hızlı Erişim çip arka planı
        'quick_access_hover': '#333333'
    }

    # Light Theme Tokens
    LIGHT = {
        'bg_primary': '#F3F3F3',        # Ana pencere tabanı (Mica Light)
        'bg_mica': '#F3F3F3',           # Ana içerik arka planı
        'bg_secondary': '#EBEBEB',      # Sidebar ve Üst Başlık yüzeyi
        'bg_card': '#FFFFFF',           # Kart yüzeyi (Fluent Layer 1)
        'bg_card_secondary': '#F6F6F6', # İkincil kart yüzeyi (Fluent Layer 2)
        'bg_elevated': '#FFFFFF',       # Yükseltilmiş yüzey (Modal / Flyout / Palette)
        'bg_card_hover': '#F9F9F9',     # Kart üzerine gelindiğinde
        'bg_card_active': '#E5E5E5',    # Aktif / Seçili kart veya menü
        'bg_input': '#FFFFFF',          # Giriş alanları
        'border': '#E0E0E0',            # İnce kenarlık
        'border_subtle': '#EAEAEA',     # Çok düşük kontrastlı ayırıcı
        'border_hover': '#BDBDBD',      # Üzerine gelindiğinde kenarlık
        'border_focus': '#0067C0',      # Odak (Focus) kenarlığı
        'accent': '#0067C0',            # Windows 11 Light Mavi Accent
        'accent_hover': '#1975C5',      # Accent Hover
        'accent_pressed': '#005BA1',    # Accent Basılı
        'accent_light': '#005FB8',      # Vurgu metni / ikonu
        'accent_subtle': '#E1F0FF',     # Yumuşak mavi seçili arka plan
        'nav_indicator': '#0067C0',     # Sol aktif menü dikey vurgu çubuğu
        'text_primary': '#1A1A1A',      # Ana metin
        'text_secondary': '#5C5C5C',    # İkincil açıklama metni
        'text_muted': '#868686',        # Pasif / Alt bilgi metni
        'text_disabled': '#A8A8A8',     # Devre dışı metin
        'success': '#0F7B0F',           # Başarılı
        'success_bg': '#E6F4E6',
        'warning': '#9D5D00',           # Uyarı
        'warning_bg': '#FFF8E6',
        'danger': '#C42B1C',            # Hata / Silme
        'danger_bg': '#FDE7E9',
        'error': '#D32F2F',             # Kritik Hata Butonu
        'info': '#0067C0',              # Bilgi
        'info_bg': '#E8F3FC',
        'skeleton_base': '#E6E6E6',     # İskelet yükleme tabanı
        'skeleton_highlight': '#F5F5F5',# İskelet yükleme parlaması
        'quick_access_bg': '#FFFFFF',   # Hızlı Erişim çip arka planı
        'quick_access_hover': '#F0F0F0'
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
        return palette.get(token_name, '#0078D4')

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """#RRGGBB kodunu (R, G, B) tuple değerine dönüştürür."""
        h = hex_color.lstrip('#')
        if len(h) == 3:
            h = ''.join(ch * 2 for ch in h)
        if len(h) != 6:
            return (0, 120, 212)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return (0, 120, 212)

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
        CustomTkinter bileşenlerinde yumuşak geçiş (fade / hover / focus) için kullanılır.
        """
        t = max(0.0, min(1.0, float(t)))
        r1, g1, b1 = cls.hex_to_rgb(start_hex)
        r2, g2, b2 = cls.hex_to_rgb(end_hex)
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        return cls.rgb_to_hex((r, g, b))
