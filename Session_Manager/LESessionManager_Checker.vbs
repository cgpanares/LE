Dim Arg, file, args, shell, exec_command
Set Arg = WScript.Arguments

file = Arg(0)
args = Arg(1)

Function FileExists(FilePath)
	Set fso = CreateObject("Scripting.FileSystemObject")
	If fso.FileExists(FilePath) Then
		FileExists=CBool(1)
	Else
		FileExists=CBool(0)
	End If
End Function

If FileExists("<path_to_app_directory>\config.yaml") Then
	exec_command = "<path_to_app_directory>\" & file
Else
	exec_command = "<path_to_app_directory>\" & file & " -t " & args
End If

Set shell = CreateObject("WScript.Shell")
shell.Run exec_command,0