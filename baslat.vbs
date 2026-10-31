Set WshShell = CreateObject("WScript.Shell")
strCurDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurDir
WshShell.Run """C:\Program Files\Python315\pythonw.exe"" """ & strCurDir & "\app.py""", 0, False
