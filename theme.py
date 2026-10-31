"""
Windows 11 Fluent Design System Theme & Style Definitions
Provides centralized color tokens, font configurations, and styling helpers
for both Dark and Light themes matching Microsoft Windows 11 aesthetics.
"""

class FluentTheme:
    # --- DARK THEME (Windows 11 Settings / File Explorer Dark) ---
    DARK = {
        'bg_mica': '#202020',           # Ana Mica arka plan
        'bg_sidebar': '#1C1C1C',        # Sabit gezinme paneli arka planı (derinlikli)
        'bg_secondary': '#262626',      # İkincil katman / alt bar
        'bg_card': '#2B2B2B',           # Kart yüzeyi (Fluent card)
        'bg_card_hover': '#333333',     # Kart hover
        'bg_card_active': '#3C3C3C',    # Kart seçili / aktif
        'bg_input': '#242424',          # Arama ve girdi kutuları
        'border': '#383838',            # Düşük kontrastlı Windows 11 kenarlık
        'border_subtle': '#2F2F2F',     # Çok hafif kenarlık
        'border_focus': '#0078D4',      # Odaklanmış kenarlık
        'accent': '#0078D4',            # Windows 11 Mavi Accent
        'accent_hover': '#1A88D8',      # Accent Hover
        'accent_light': '#4CC2FF',      # Açık mavi vurgu (koyu temada metin için)
        'accent_bg': '#003E6B',         # Accent arka planı
        'text_primary': '#FFFFFF',      # Birincil metin (beyaz)
        'text_secondary': '#D0D0D0',    # İkincil metin (açık gri)
        'text_muted': '#8E8E8E',        # Sönük metin
        'success': '#10B981',           # Başarılı / Aktif yeşil
        'success_bg': '#064E3B',        # Başarılı arka plan
        'warning': '#F59E0B',           # Uyarı turuncu
        'warning_bg': '#78350F',        # Uyarı arka plan
        'danger': '#EF4444',            # Hata / Tehlike kırmızı
        'danger_bg': '#7F1D1D',         # Tehlike arka plan
        'sidebar_active': '#2E2E2E',    # Sidebar aktif sekme
        'sidebar_hover': '#262626',     # Sidebar hover
        'section_header': '#767676',    # Kategori başlığı (küçük gri)
        'pill_bg': '#262626',           # Durum etiketi arka planı
        'quick_access_bg': '#262626',   # Hızlı erişim kartı arka planı
        'quick_access_hover': '#323232',# Hızlı erişim kartı hover
    }

    # --- LIGHT THEME (Windows 11 Settings / File Explorer Light) ---
    LIGHT = {
        'bg_mica': '#F3F3F3',           # Ana Mica arka plan
        'bg_sidebar': '#F8F8F8',        # Sabit gezinme paneli arka planı
        'bg_secondary': '#EAEAEA',      # İkincil katman / alt bar
        'bg_card': '#FFFFFF',           # Kart yüzeyi
        'bg_card_hover': '#F5F5F5',     # Kart hover
        'bg_card_active': '#EBEBEB',    # Kart seçili / aktif
        'bg_input': '#FFFFFF',          # Arama ve girdi kutuları
        'border': '#E5E5E5',            # Düşük kontrastlı açık gri kenarlık
        'border_subtle': '#EEEEEE',     # Çok hafif kenarlık
        'border_focus': '#0078D4',      # Odaklanmış kenarlık
        'accent': '#0078D4',            # Windows 11 Mavi Accent
        'accent_hover': '#006CBE',      # Accent Hover
        'accent_light': '#0078D4',      # Vurgu
        'accent_bg': '#E0EEF9',         # Accent arka planı
        'text_primary': '#1A1A1A',      # Birincil metin
        'text_secondary': '#5A5A5A',    # İkincil metin
        'text_muted': '#7A7A7A',        # Sönük metin
        'success': '#059669',           # Başarılı yeşil
        'success_bg': '#D1FAE5',        # Başarılı arka plan
        'warning': '#D97706',           # Uyarı
        'warning_bg': '#FEF3C7',        # Uyarı arka plan
        'danger': '#DC2626',            # Hata
        'danger_bg': '#FEE2E2',         # Hata arka plan
        'sidebar_active': '#EAEAEA',    # Sidebar aktif sekme
        'sidebar_hover': '#F2F2F2',     # Sidebar hover
        'section_header': '#8C8C8C',    # Kategori başlığı
        'pill_bg': '#EAEAEA',           # Durum etiketi arka planı
        'quick_access_bg': '#FFFFFF',   # Hızlı erişim kartı arka planı
        'quick_access_hover': '#F0F0F0',# Hızlı erişim kartı hover
    }

    # Font tanımları (Windows 11 yerel yazı tipleri)
    FONTS = {
        'family_title': 'Segoe UI Variable Display',
        'family_body': 'Segoe UI Variable Text',
        'family_mono': 'Consolas',
        'fallback': 'Segoe UI'
    }

    @classmethod
    def get_palette(cls, theme_mode='dark'):
        mode = theme_mode.lower()
        if mode == 'light':
            return cls.LIGHT
        return cls.DARK

    @classmethod
    def c(cls, token, theme_mode='dark'):
        """Belirtilen tasarım belirtecinin (token) rengini döner."""
        palette = cls.get_palette(theme_mode)
        return palette.get(token, palette.get('accent'))
