Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
venvPythonw = currentDir & "\venv\Scripts\pythonw.exe"

If fso.FileExists(venvPythonw) Then
    WshShell.Run """" & venvPythonw & """ """ & currentDir & "\main.py""", 0, False
Else
    WshShell.Run "pythonw """ & currentDir & "\main.py""", 0, False
End If
