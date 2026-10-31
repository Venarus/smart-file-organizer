import os
import subprocess

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
app_dir = r'C:\Users\senem\.gemini\antigravity\scratch\FolderOrganizerApp'
pythonw_path = r'C:\Program Files\Python315\pythonw.exe'

# 1. Eski kısayolları temizle
for f in os.listdir(desktop):
    if 'klas' in f.lower() or 'düzenleyici' in f.lower():
        try:
            os.remove(os.path.join(desktop, f))
            print(f"Eski kısayol silindi: {f}")
        except Exception:
            pass

# 2. PowerShell komutunu UTF-8 BOM ile yazıp çalıştır
ps_content = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = "{os.path.join(desktop, 'Akıllı Klasör Düzenleyici.lnk')}"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "{pythonw_path}"
$Shortcut.Arguments = '"{os.path.join(app_dir, 'app.py')}"'
$Shortcut.WorkingDirectory = "{app_dir}"
$Shortcut.IconLocation = "{os.path.join(app_dir, 'app_icon.ico')},0"
$Shortcut.Description = "Akıllı Klasör Düzenleyici - Arka Planda Otomasyon"
$Shortcut.Save()
Write-Host "BASARILI"
"""

ps_path = os.path.join(app_dir, 'run_create_sc.ps1')
with open(ps_path, 'w', encoding='utf-8-sig') as f:
    f.write(ps_content)

res = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_path], capture_output=True, text=True)
print("PowerShell çıktısı:", res.stdout.strip())
if res.stderr:
    print("PowerShell hatası:", res.stderr.strip())

if os.path.exists(ps_path):
    os.remove(ps_path)

# Kontrol et
created_files = [f for f in os.listdir(desktop) if 'klas' in f.lower() or 'düzenleyici' in f.lower()]
print(f"Masaüstünde oluşturulan kısayol: {created_files}")
