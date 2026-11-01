"""
Configuration Manager (V2)
Manages application settings, monitored sources, desktop protection baseline,
Windows startup registry/shortcuts, and Fluent theme preferences.
"""

import os
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, 'config.json')

USER_PROFILE = os.path.expanduser('~')
DEFAULT_DESKTOP = os.path.join(USER_PROFILE, 'Desktop')
DEFAULT_DOWNLOADS = os.path.join(USER_PROFILE, 'Downloads')
DEFAULT_DOCUMENTS = os.path.join(USER_PROFILE, 'Documents')
DEFAULT_PICTURES = os.path.join(USER_PROFILE, 'Pictures')
DEFAULT_MUSIC = os.path.join(USER_PROFILE, 'Music')
DEFAULT_VIDEOS = os.path.join(USER_PROFILE, 'Videos')
DEFAULT_TARGET = os.path.join(DEFAULT_DESKTOP, 'Folders')

PINNED_FOLDERS = [
    {'id': 'desktop', 'name': 'Masaüstü', 'path': DEFAULT_DESKTOP, 'key': 'quick_desktop'},
    {'id': 'downloads', 'name': 'İndirilenler', 'path': DEFAULT_DOWNLOADS, 'key': 'quick_downloads'},
    {'id': 'documents', 'name': 'Belgeler', 'path': DEFAULT_DOCUMENTS, 'key': 'quick_documents'},
    {'id': 'pictures', 'name': 'Resimler', 'path': DEFAULT_PICTURES, 'key': 'quick_pictures'},
    {'id': 'music', 'name': 'Müzikler', 'path': DEFAULT_MUSIC, 'key': 'quick_music'},
    {'id': 'videos', 'name': 'Videolar', 'path': DEFAULT_VIDEOS, 'key': 'quick_videos'}
]

def get_desktop_current_items():
    """Masaüstünde şu an mevcut olan tüm dosya ve klasörlerin listesi."""
    if os.path.exists(DEFAULT_DESKTOP):
        return [f for f in os.listdir(DEFAULT_DESKTOP)]
    return []

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
    'check_interval': 4,
    'allow_new_categories': True,
    'start_with_windows': False,
    'minimize_to_tray_on_close': True,
    'theme_mode': 'dark', # 'dark', 'light', 'system'
    'notifications_enabled': True,
    'desktop_baseline': get_desktop_current_items()
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            # Masaüstü koruma listesini koru
            current_desktop = set(get_desktop_current_items())
            saved_baseline = set(cfg.get('desktop_baseline', []))
            cfg['desktop_baseline'] = list(saved_baseline | current_desktop)
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ayar kaydetme hatası: {e}")

def set_windows_startup(enable):
    """Windows Başlangıç klasörüne kısayol ekler veya kaldırır."""
    import sys
    startup_dir = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
    python_exe = sys.executable
    pythonw_candidate = python_exe.replace('python.exe', 'pythonw.exe')
    pythonw_path = pythonw_candidate if os.path.exists(pythonw_candidate) else python_exe
    app_script = os.path.join(APP_DIR, 'app.py')
    ico_path = os.path.join(APP_DIR, 'app_icon.ico')
    shortcut_path = os.path.join(startup_dir, 'AkilliKlasorDuzenleyici.lnk')

    if enable:
        try:
            import subprocess
            powershell_cmd = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{shortcut_path}');"
                f"$s.TargetPath='{pythonw_path}';"
                f"$s.Arguments='\"\"\"{app_script}\"\"\"';"
                f"$s.WorkingDirectory='{APP_DIR}';"
                f"$s.IconLocation='{ico_path},0';"
                f"$s.Save()"
            )
            subprocess.run(['powershell', '-Command', powershell_cmd], capture_output=True)
        except Exception as e:
            print(f"Başlangıç kısayolu oluşturulamadı: {e}")
    else:
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
            except Exception:
                pass
