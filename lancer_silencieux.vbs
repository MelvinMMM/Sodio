Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
runScript = fso.BuildPath(scriptDir, "python\run.py")
pythonwExe = "C:\Users\melvi\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
If Not fso.FileExists(pythonwExe) Then
    pythonwExe = "pythonw.exe"
End If

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir
cmd = """" & pythonwExe & """ """ & runScript & """"
WshShell.Run cmd, 0, False
