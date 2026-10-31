import os
import pystray
from PIL import Image, ImageDraw

def create_tray_icon_image():
    """Sistem tepsisi için modern, şık bir klasör/düzenleme simgesi çizer."""
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Klasör arka planı (Modern Mavi-Teal gradyan hissi)
    # Sekme
    draw.rounded_rectangle((6, 12, 30, 26), radius=4, fill=(59, 130, 246, 255))
    # Ana gövde
    draw.rounded_rectangle((6, 20, 58, 56), radius=6, fill=(37, 99, 235, 255))
    # Ön cep
    draw.rounded_rectangle((10, 28, 54, 52), radius=4, fill=(96, 165, 250, 255))

    # Ortaya düzenleme / yıldız simgesi
    draw.line((32, 33, 32, 47), fill=(255, 255, 255, 255), width=3)
    draw.line((25, 40, 39, 40), fill=(255, 255, 255, 255), width=3)

    return image

class SystemTrayApp:
    def __init__(self, on_show_window, on_organize_now, on_toggle_watch, on_open_folder, on_exit_app):
        self.on_show_window = on_show_window
        self.on_organize_now = on_organize_now
        self.on_toggle_watch = on_toggle_watch
        self.on_open_folder = on_open_folder
        self.on_exit_app = on_exit_app

        self.icon_image = create_tray_icon_image()
        self.tray_icon = None

    def _create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("📌 Uygulamayı Aç", lambda: self.on_show_window()),
            pystray.MenuItem("⚡ Şimdi Düzenle", lambda: self.on_organize_now()),
            pystray.MenuItem("📂 Folders Klasörünü Aç", lambda: self.on_open_folder()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Çıkış", lambda: self.on_exit_app())
        )

    def start(self):
        menu = self._create_menu()
        self.tray_icon = pystray.Icon(
            "KlasorDuzenleyici",
            self.icon_image,
            "Akıllı Klasör Düzenleyici (Arka Planda)",
            menu
        )
        self.tray_icon.run_detached()

    def stop(self):
        if self.tray_icon:
            self.tray_icon.stop()
