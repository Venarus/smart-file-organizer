"""
Visual Asset Generator for Smart File Organizer V2 GitHub Repository
Renders high-resolution Windows 11 Fluent Design banners, architecture diagrams,
and UI mockups using PIL and native Windows Segoe UI typography.
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
os.makedirs(ASSETS_DIR, exist_ok=True)

FONTS_DIR = os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'Fonts')

def get_font(name="segoeui.ttf", size=14):
    path = os.path.join(FONTS_DIR, name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

# -------------------------------------------------------------------------
# 1. BANNER (1280x420)
# -------------------------------------------------------------------------
def create_banner():
    w, h = 1280, 420
    im = Image.new("RGBA", (w, h), "#181818")
    draw = ImageDraw.Draw(im)

    # Ambient gradient glow
    for i in range(120):
        alpha = int(25 * (1 - i / 120))
        r = 300 + i * 2
        draw.ellipse([w//2 - r, -100 - r//3, w//2 + r, 200 + r//2], fill=(0, 120, 212, alpha))
        draw.ellipse([w - 200 - r//2, 100 - r//3, w - 200 + r//2, 350 + r//3], fill=(16, 185, 129, alpha // 2))

    # Inner Container Card
    draw_rounded_rect(draw, [40, 30, w - 40, h - 30], radius=16, fill="#202020", outline="#383838", width=1)

    # Accent Top Highlight Line
    draw.line([(60, 30), (w - 60, 30)], fill="#0078D4", width=3)

    # Badge: Windows 11 Fluent Design
    draw_rounded_rect(draw, [70, 60, 340, 92], radius=16, fill="#003E6B", outline="#0078D4", width=1)
    f_badge = get_font("segoeuib.ttf", 13)
    draw.text((90, 68), "⚡ WINDOWS 11 FLUENT DESIGN V2", font=f_badge, fill="#4CC2FF")

    # App Title
    f_title = get_font("segoeuib.ttf", 38)
    draw.text((70, 110), "Smart File Organizer", font=f_title, fill="#FFFFFF")

    # Subtitle
    f_sub = get_font("segoeui.ttf", 18)
    draw.text((70, 165), "AI-Driven Autonomous File Intelligence & Real-Time Background Organization", font=f_sub, fill="#D0D0D0")

    # Descriptions
    f_desc = get_font("segoeui.ttf", 14)
    desc_txt = (
        "Integrated Windows 11 Quick Access (Desktop, Downloads, Documents, Pictures, Music, Videos)\n"
        "NTFS MTime Zero-Lag Monitoring  •  Multi-Factor AI Categorization  •  1-Click Undo Security Rollback"
    )
    draw.text((70, 205), desc_txt, font=f_desc, fill="#A0A0A0")

    # Bottom Pill Badges
    badges = [
        ("🟢 Zero CPU Background Watcher", "#10B981", "#064E3B"),
        ("🛡️ Desktop Baseline Protection", "#0078D4", "#003E6B"),
        ("🚀 Single-Instance IPC Activation", "#8B5CF6", "#3B0764"),
        ("⚡ 60 FPS Mica Fluent UI", "#F59E0B", "#78350F")
    ]
    bx = 70
    f_pills = get_font("segoeuib.ttf", 12)
    for txt, stroke, bg in badges:
        bw = int(draw.textlength(txt, font=f_pills)) + 24
        draw_rounded_rect(draw, [bx, 310, bx + bw, 345], radius=17, fill=bg, outline=stroke, width=1)
        draw.text((bx + 12, 319), txt, font=f_pills, fill="#FFFFFF")
        bx += bw + 14

    # Right side visual card (Quick Access Preview)
    rx, ry, rw, rh = w - 420, 65, 340, 275
    draw_rounded_rect(draw, [rx, ry, rx + rw, ry + rh], radius=12, fill="#262626", outline="#3A3A3A", width=1)
    f_head = get_font("segoeuib.ttf", 12)
    draw.text((rx + 16, ry + 14), "SABİTLENENLER (HIZLI ERİŞİM) 📌", font=f_head, fill="#8E8E8E")

    pinned_items = [
        ("🖥️  Masaüstü", "#262626"),
        ("⬇️  İndirilenler", "#262626"),
        ("📄  Belgeler", "#333333"), # Active selected state!
        ("🖼️  Resimler", "#262626"),
        ("🎵  Müzikler", "#262626"),
        ("🎬  Videolar", "#262626")
    ]
    f_item = get_font("segoeui.ttf", 13)
    iy = ry + 42
    for label, bg_color in pinned_items:
        draw_rounded_rect(draw, [rx + 10, iy, rx + rw - 10, iy + 32], radius=6, fill=bg_color, outline=None)
        draw.text((rx + 20, iy + 6), label, font=f_item, fill="#FFFFFF" if bg_color != "#262626" else "#D0D0D0")
        draw.text((rx + rw - 35, iy + 7), "📌", font=f_item, fill="#707070")
        iy += 36

    im.convert("RGB").save(os.path.join(ASSETS_DIR, "banner.png"), quality=95)
    print("Created: banner.png")

# -------------------------------------------------------------------------
# 2. ARCHITECTURE DIAGRAM (1200x680)
# -------------------------------------------------------------------------
def create_architecture():
    w, h = 1200, 680
    im = Image.new("RGBA", (w, h), "#1C1C1C")
    draw = ImageDraw.Draw(im)

    # Title Header
    f_t = get_font("segoeuib.ttf", 26)
    draw.text((50, 30), "Smart File Organizer V2 — System Architecture", font=f_t, fill="#FFFFFF")
    f_s = get_font("segoeui.ttf", 14)
    draw.text((50, 70), "Event-driven asynchronous file processing pipeline with multi-factor AI classification", font=f_s, fill="#8E8E8E")

    # Column 1: SOURCES
    c1_x, c1_y, c1_w, c1_h = 50, 120, 240, 510
    draw_rounded_rect(draw, [c1_x, c1_y, c1_x + c1_w, c1_y + c1_h], radius=12, fill="#242424", outline="#363636", width=1)
    f_col = get_font("segoeuib.ttf", 15)
    draw.text((c1_x + 18, c1_y + 16), "1. INPUT SOURCES", font=f_col, fill="#4CC2FF")

    sources = [
        ("Desktop (Masaüstü)", "Baseline Protection Active", "#0078D4"),
        ("Downloads (İndirilenler)", "Auto Browser Downloads", "#10B981"),
        ("Documents (Belgeler)", "Office & Text Records", "#0078D4"),
        ("Pictures (Resimler)", "Photos, Wallpapers", "#38BDF8"),
        ("Music (Müzikler)", "Audio, Podcasts", "#F59E0B"),
        ("Videos (Videolar)", "Recordings, Clips", "#A855F7"),
        ("Drag & Drop Zone", "Manual File/Folder Drop", "#EC4899"),
    ]
    f_s1 = get_font("segoeuib.ttf", 12)
    f_s2 = get_font("segoeui.ttf", 10)
    sy = c1_y + 55
    for title, desc, clr in sources:
        draw_rounded_rect(draw, [c1_x + 12, sy, c1_x + c1_w - 12, sy + 54], radius=8, fill="#2C2C2C", outline=clr, width=1)
        draw.text((c1_x + 22, sy + 8), title, font=f_s1, fill="#FFFFFF")
        draw.text((c1_x + 22, sy + 28), desc, font=f_s2, fill="#A0A0A0")
        sy += 64

    # Column 2: WATCHER & IPC ENGINE
    c2_x, c2_y, c2_w, c2_h = 330, 120, 260, 510
    draw_rounded_rect(draw, [c2_x, c2_y, c2_x + c2_w, c2_y + c2_h], radius=12, fill="#242424", outline="#363636", width=1)
    draw.text((c2_x + 18, c2_y + 16), "2. WATCHER & IPC", font=f_col, fill="#10B981")

    modules2 = [
        ("Background Watcher", "NTFS mtime Directory Caching\nZero CPU idle poll cycle", "#10B981"),
        ("Download Lock Detector", "Checks incomplete ext & locks\nSleep-free size stability test", "#F59E0B"),
        ("Single-Instance IPC", "TCP Localhost Port 49285\nBrings hidden tray to front", "#8B5CF6"),
        ("Desktop Protection", "Hardened baseline filter\nPrevents moving user shortcuts", "#0078D4")
    ]
    sy2 = c2_y + 55
    for title, desc, clr in modules2:
        draw_rounded_rect(draw, [c2_x + 12, sy2, c2_x + c2_w - 12, sy2 + 96], radius=8, fill="#2C2C2C", outline=clr, width=1)
        draw.text((c2_x + 22, sy2 + 10), title, font=f_s1, fill="#FFFFFF")
        draw.text((c2_x + 22, sy2 + 34), desc, font=f_s2, fill="#A0A0A0")
        sy2 += 110

    # Column 3: AI INTELLIGENCE ENGINE
    c3_x, c3_y, c3_w, c3_h = 630, 120, 260, 510
    draw_rounded_rect(draw, [c3_x, c3_y, c3_x + c3_w, c3_y + c3_h], radius=12, fill="#242424", outline="#363636", width=1)
    draw.text((c3_x + 18, c3_y + 16), "3. AI INTELLIGENCE", font=f_col, fill="#A855F7")

    modules3 = [
        ("Multi-Factor Analyzer", "Extension, File Name & Stem\nCreation & MTime Metadata", "#A855F7"),
        ("15 Category Classification", "School, Programming, Media,\nCAD/3D, Installers, Archive", "#EC4899"),
        ("Smart Subcategories", "School/HW, Wallpapers, Code\nElectronics/Proteus, Audio", "#38BDF8"),
        ("Semantic Tagging Engine", "Auto tags (PDF, Work, Project)\nFast multi-tag search index", "#10B981")
    ]
    sy3 = c3_y + 55
    for title, desc, clr in modules3:
        draw_rounded_rect(draw, [c3_x + 12, sy3, c3_x + c3_w - 12, sy3 + 96], radius=8, fill="#2C2C2C", outline=clr, width=1)
        draw.text((c3_x + 22, sy3 + 10), title, font=f_s1, fill="#FFFFFF")
        draw.text((c3_x + 22, sy3 + 34), desc, font=f_s2, fill="#A0A0A0")
        sy3 += 110

    # Column 4: TARGET & SECURITY
    c4_x, c4_y, c4_w, c4_h = 930, 120, 220, 510
    draw_rounded_rect(draw, [c4_x, c4_y, c4_x + c4_w, c4_y + c4_h], radius=12, fill="#242424", outline="#363636", width=1)
    draw.text((c4_x + 18, c4_y + 16), "4. STORAGE & UNDO", font=f_col, fill="#F59E0B")

    modules4 = [
        ("Folders Root", "Desktop/Folders target\n52,000+ files organized", "#0078D4"),
        ("Collision Resolver", "Automatic (1), (2) naming\nZero data overwrite risk", "#10B981"),
        ("Security Ledger", "Audit transaction log\nInstant 1-Click Rollback", "#F59E0B"),
        ("Storage Analyzer", "Real-time disk statistics\nCategory size distribution", "#A855F7")
    ]
    sy4 = c4_y + 55
    for title, desc, clr in modules4:
        draw_rounded_rect(draw, [c4_x + 12, sy4, c4_x + c4_w - 12, sy4 + 96], radius=8, fill="#2C2C2C", outline=clr, width=1)
        draw.text((c4_x + 22, sy4 + 10), title, font=f_s1, fill="#FFFFFF")
        draw.text((c4_x + 22, sy4 + 34), desc, font=f_s2, fill="#A0A0A0")
        sy4 += 110

    # Draw Connecting Arrows
    f_arr = get_font("segoeuib.ttf", 22)
    draw.text((300, 360), "➔", font=f_arr, fill="#505050")
    draw.text((600, 360), "➔", font=f_arr, fill="#505050")
    draw.text((900, 360), "➔", font=f_arr, fill="#505050")

    im.convert("RGB").save(os.path.join(ASSETS_DIR, "architecture_diagram.png"), quality=95)
    print("Created: architecture_diagram.png")

# -------------------------------------------------------------------------
# 3. DASHBOARD OVERVIEW MOCKUP (1100x650)
# -------------------------------------------------------------------------
def create_dashboard_mockup():
    w, h = 1100, 650
    im = Image.new("RGBA", (w, h), "#202020")
    draw = ImageDraw.Draw(im)

    # Window Chrome / Header
    draw_rounded_rect(draw, [20, 20, w - 20, h - 20], radius=14, fill="#202020", outline="#333333", width=1)

    # Header Bar
    draw_rounded_rect(draw, [35, 35, w - 35, 85], radius=8, fill="#262626", outline="#303030", width=1)
    f_app = get_font("segoeuib.ttf", 15)
    draw.text((50, 48), "📂  Smart File Organizer V2", font=f_app, fill="#FFFFFF")

    # Search Bar
    draw_rounded_rect(draw, [280, 44, 720, 76], radius=6, fill="#1C1C1C", outline="#383838", width=1)
    f_srch = get_font("segoeui.ttf", 12)
    draw.text((295, 52), "🔍  Dosya, kategori veya etiket ara... (Enter)", font=f_srch, fill="#7E7E7E")

    # Header Buttons
    draw_rounded_rect(draw, [740, 44, 850, 76], radius=6, fill="#0078D4", outline=None)
    draw.text((755, 52), "⚡ Şimdi Tara", font=f_app, fill="#FFFFFF")

    draw_rounded_rect(draw, [860, 44, 955, 76], radius=6, fill="#303030", outline=None)
    draw.text((875, 52), "📂 Folders", font=f_app, fill="#D0D0D0")

    # Sidebar (Left)
    sb_w = 230
    draw_rounded_rect(draw, [35, 95, 35 + sb_w, h - 35], radius=10, fill="#1C1C1C", outline="#303030", width=1)

    f_sec = get_font("segoeuib.ttf", 10)
    draw.text((50, 110), "SABİTLENENLER 📌", font=f_sec, fill="#7E7E7E")

    sidebar_rows = [
        ("🖥️  Masaüstü", False),
        ("⬇️  İndirilenler", False),
        ("📄  Belgeler", True), # Selected
        ("🖼️  Resimler", False),
        ("🎵  Müzikler", False),
        ("🎬  Videolar", False),
    ]
    f_sb = get_font("segoeui.ttf", 12)
    y_btn = 132
    for name, selected in sidebar_rows:
        if selected:
            draw_rounded_rect(draw, [45, y_btn, 35 + sb_w - 10, y_btn + 30], radius=6, fill="#2E2E2E", outline=None)
            draw.text((55, y_btn + 6), name, font=f_sb, fill="#4CC2FF")
        else:
            draw.text((55, y_btn + 6), name, font=f_sb, fill="#D0D0D0")
        draw.text((35 + sb_w - 32, y_btn + 6), "📌", font=f_sb, fill="#666666")
        y_btn += 34

    draw.line([(50, y_btn + 6), (35 + sb_w - 20, y_btn + 6)], fill="#2E2E2E", width=1)
    y_btn += 16
    draw.text((50, y_btn), "UYGULAMA MENÜSÜ", font=f_sec, fill="#7E7E7E")
    y_btn += 18
    nav_rows = ["🏠  Genel Bakış", "📂  Folders Gezgini", "🎬  Medya & Galeri", "🧠  AI Zekâsı", "🔄  Otomasyon", "🛡️  Güvenlik & Yedek"]
    for name in nav_rows:
        draw.text((55, y_btn + 4), name, font=f_sb, fill="#A8A8A8")
        y_btn += 28

    # Main Content Area
    cx = 35 + sb_w + 15
    cw = w - 35 - cx
    draw.text((cx, 105), "Genel Bakış", font=get_font("segoeuib.ttf", 22), fill="#FFFFFF")
    draw_rounded_rect(draw, [cx + 140, 110, cx + 270, 134], radius=10, fill="#064E3B", outline="#10B981")
    draw.text((cx + 152, 114), "● Sistem Hazır & Aktif", font=get_font("segoeuib.ttf", 10), fill="#10B981")

    # 4 Stat Cards
    card_w = (cw - 30) // 4
    card_y = 150
    stat_data = [
        ("📁 Toplam Dosya", "52.559", "Folders klasöründe"),
        ("💾 Kaplanan Alan", "27,8 GB", "Düzenlenmiş veri"),
        ("⚡ Son İşlem", "Tamamlandı", "0 saniye önce"),
        ("🟢 İzlenen Klasör", "6 Adet", "Masaüstü, İndirilenler...")
    ]
    f_c1 = get_font("segoeuib.ttf", 11)
    f_c2 = get_font("segoeuib.ttf", 18)
    f_c3 = get_font("segoeui.ttf", 10)
    for idx, (t, val, sub) in enumerate(stat_data):
        bx = cx + idx * (card_w + 10)
        draw_rounded_rect(draw, [bx, card_y, bx + card_w, card_y + 90], radius=8, fill="#282828", outline="#363636", width=1)
        draw.text((bx + 12, card_y + 10), t, font=f_c1, fill="#A0A0A0")
        draw.text((bx + 12, card_y + 32), val, font=f_c2, fill="#4CC2FF" if idx==0 else "#FFFFFF")
        draw.text((bx + 12, card_y + 64), sub, font=f_c3, fill="#707070")

    # Quick Access Ribbon
    qa_y = 255
    draw_rounded_rect(draw, [cx, qa_y, cx + cw, qa_y + 85], radius=10, fill="#262626", outline="#333333", width=1)
    draw.text((cx + 16, qa_y + 12), "📌 Hızlı Erişim (Windows 11 Sabitlenen Klasörler)", font=get_font("segoeuib.ttf", 12), fill="#FFFFFF")
    q_chips = ["🖥️ Masaüstü 📌", "📥 İndirilenler 📌", "📑 Belgeler 📌", "🖼️ Resimler 📌", "🎵 Müzikler 📌", "🎬 Videolar 📌"]
    qx = cx + 16
    for chip in q_chips:
        cw_c = int(draw.textlength(chip, font=f_sb)) + 20
        draw_rounded_rect(draw, [qx, qa_y + 40, qx + cw_c, qa_y + 70], radius=6, fill="#2F2F2F", outline="#3E3E3E")
        draw.text((qx + 10, qa_y + 47), chip, font=f_sb, fill="#D0D0D0")
        qx += cw_c + 8

    # Drag & Drop Zone Card
    dz_y = 355
    draw_rounded_rect(draw, [cx, dz_y, cx + cw, dz_y + 115], radius=10, fill="#262626", outline="#0078D4", width=1)
    draw.text((cx + 25, dz_y + 22), "📥  Dosyaları veya Klasörleri Buraya Sürükleyip Bırakın", font=get_font("segoeuib.ttf", 14), fill="#FFFFFF")
    draw.text((cx + 25, dz_y + 50), "AI motoru içerik, dosya türü ve metadata analizini otomatik yaparak Folders klasörüne organize eder.", font=f_sb, fill="#A0A0A0")
    draw_rounded_rect(draw, [cx + cw - 140, dz_y + 40, cx + cw - 20, dz_y + 78], radius=6, fill="#0078D4", outline=None)
    draw.text((cx + cw - 125, dz_y + 50), "📄 Dosya Seç", font=get_font("segoeuib.ttf", 12), fill="#FFFFFF")

    # Categories Bar
    cat_y = 485
    draw_rounded_rect(draw, [cx, cat_y, cx + cw, h - 35], radius=10, fill="#242424", outline="#333333", width=1)
    draw.text((cx + 16, cat_y + 14), "Aktif Kategoriler (Desktop/Folders)", font=get_font("segoeuib.ttf", 12), fill="#FFFFFF")
    cats = ["⚡ 01_Elektronik", "💻 03_Yazılım", "🎨 04_Medya", "📑 05_Belgeler", "📦 06_Programlar", "🗄️ 10_Arşivler"]
    cx_item = cx + 16
    for c in cats:
        cw_i = int(draw.textlength(c, font=f_sb)) + 18
        draw_rounded_rect(draw, [cx_item, cat_y + 44, cx_item + cw_i, cat_y + 74], radius=6, fill="#2E2E2E", outline=None)
        draw.text((cx_item + 9, cat_y + 51), c, font=f_sb, fill="#E0E0E0")
        cx_item += cw_i + 8

    im.convert("RGB").save(os.path.join(ASSETS_DIR, "dashboard_overview.png"), quality=95)
    print("Created: dashboard_overview.png")

if __name__ == "__main__":
    create_banner()
    create_architecture()
    create_dashboard_mockup()
    print("All visual assets generated successfully!")
