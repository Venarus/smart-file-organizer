$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$AppDir = "C:\Users\senem\.gemini\antigravity\scratch\FolderOrganizerApp"
$ShortcutPath = Join-Path $DesktopPath "Akıllı Klasör Düzenleyici.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Program Files\Python315\pythonw.exe"
$Shortcut.Arguments = "`"$AppDir\app.py`""
$Shortcut.WorkingDirectory = $AppDir
$Shortcut.IconLocation = "$AppDir\app_icon.ico,0"
$Shortcut.Description = "Akıllı Klasör Düzenleyici - Arka Planda Otomasyon"
$Shortcut.Save()

Write-Host "Kısayol oluşturuldu: $ShortcutPath"
