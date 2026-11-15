import os
import sys
import json
import ctypes
import winreg

APP_NAME = "FolderOrganizerApp"
APP_VERSION = "2.1.0"

# Uygulama çalışma dizini (PyInstaller EXE veya Script uyumlu)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "config.json")

# Kullanıcı klasörleri (Windows 11 Hızlı Erişim / Sabitlenen Klasörler)
USER_HOME = os.path.expanduser('~')
DEFAULT_DESKTOP = os.path.join(USER_HOME, 'Desktop')
DEFAULT_DOWNLOADS = os.path.join(USER_HOME, 'Downloads')
DEFAULT_DOCUMENTS = os.path.join(USER_HOME, 'Documents')
DEFAULT_PICTURES = os.path.join(USER_HOME, 'Pictures')
DEFAULT_MUSIC = os.path.join(USER_HOME, 'Music')
DEFAULT_VIDEOS = os.path.join(USER_HOME, 'Videos')
DEFAULT_TARGET = os.path.join(DEFAULT_DESKTOP, 'Folders')

# Tüm Windows 11 Sabitlenen (Pinned) Klasörler
PINNED_USER_FOLDERS = [
    DEFAULT_DESKTOP,
    DEFAULT_DOWNLOADS,
    DEFAULT_DOCUMENTS,
    DEFAULT_PICTURES,
    DEFAULT_MUSIC,
    DEFAULT_VIDEOS,
]

DEFAULT_CONFIG = {
    'sources': [
        DEFAULT_DESKTOP,
        DEFAULT_DOWNLOADS,
        DEFAULT_DOCUMENTS,
        DEFAULT_PICTURES,
        DEFAULT_MUSIC,
        DEFAULT_VIDEOS
    ],
    'target': DEFAULT_TARGET,
    'auto_watch': True,
    'run_on_startup': False,
    'check_interval': 4,
    'theme': 'dark',                  # 'dark', 'light', 'system'
    'glass_opacity': 0.95,            # 0.85 - 1.00 Pencere Acrylic/Cam şeffaflığı
    'animation_mode': 'full',         # 'full', 'reduced', 'disabled'
    'respect_system_motion': True,    # Windows erişilebilirlik azaltılmış hareket ayarını izle
    'notifications': True,
    'sound_effects': False,
    'deep_content_analysis': True,
    'protect_existing_desktop': True, # Masaüstündeki önceden var olan dosyaları koru
    'desktop_baseline': [],           # Korunan masaüstü öğelerinin listesi
    'baseline_initialized': False,
    'allow_new_categories': True,     # Gerektiğinde yeni kategori/alt kategori oluştur
    'custom_rules': []                # Kullanıcının özel anahtar kelime -> kategori kuralları
}


def get_desktop_snapshot():
    """Masaüstünde şu an bulunan dosya ve klasörlerin isim listesini alır."""
    try:
        if os.path.exists(DEFAULT_DESKTOP):
            return os.listdir(DEFAULT_DESKTOP)
    except Exception:
        pass
    return []


def get_system_reduced_motion() -> bool:
    """
    Windows işletim sisteminin 'Animasyon efektlerini göster' (SPI_GETCLIENTAREAANIMATION = 0x1042)
    erişilebilirlik ayarını kontrol eder. Kullanıcı animasyonları kapattıysa True döner.
    """
    try:
        SPI_GETCLIENTAREAANIMATION = 0x1042
        enabled = ctypes.c_int(1)
        res = ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(enabled), 0
        )
        if res != 0:
            return not bool(enabled.value)
    except Exception:
        pass
    return False


def get_effective_animation_mode(cfg=None) -> str:
    """
    Kullanıcı tercihi ve Windows erişilebilirlik ayarlarına göre
    etkin animasyon modunu ('full', 'reduced', 'disabled') döndürür.
    """
    if cfg is None:
        cfg = load_config()
    mode = cfg.get('animation_mode', 'full')
    if mode not in ('full', 'reduced', 'disabled'):
        mode = 'full'

    if mode == 'disabled':
        return 'disabled'

    if cfg.get('respect_system_motion', True) and get_system_reduced_motion():
        return 'reduced'

    return mode


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cfg.update(data)
        except Exception:
            pass

    # Masaüstü koruma listesi henüz oluşturulmadıysa mevcut masaüstünü kaydet
    if not cfg.get('baseline_initialized', False):
        cfg['desktop_baseline'] = get_desktop_snapshot()
        cfg['baseline_initialized'] = True
        save_config(cfg)

    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Yapılandırma kaydetme hatası: {e}")


def refresh_desktop_baseline(cfg):
    """Mevcut masaüstü durumunu güvenli taban çizgisi olarak yeniler."""
    cfg['desktop_baseline'] = get_desktop_snapshot()
    cfg['baseline_initialized'] = True
    save_config(cfg)
    return len(cfg['desktop_baseline'])


def set_startup(enable=True):
    """Windows başlangıcında (Registry Run) çalışmayı açar veya kapatır."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        if getattr(sys, 'frozen', False):
            cmd = f'"{sys.executable}" --minimized'
        else:
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw):
                pythonw = sys.executable
            main_script = os.path.join(APP_DIR, "main.py")
            cmd = f'"{pythonw}" "{main_script}" --minimized'

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Başlangıç ayarı hatası: {e}")
        return False
