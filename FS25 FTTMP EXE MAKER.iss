[Setup]
AppName=FS25 Fill Type Texture Maker Python
AppVersion=0.1 ALPHA
DefaultDirName=C:\diffusemakerPython
DefaultGroupName=FS25 Fill Type Texture Maker Python
UninstallDisplayIcon={app}\FS25FTTMP.ico
OutputDir=.
OutputBaseFilename=FS25_FillTypeTextureMaker_Installer
SetupIconFile=FS25FTTMP.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "generate_all_texture_types.py"; DestDir: "{app}"
Source: "launch_texture_tool.bat"; DestDir: "{app}"
Source: "install_requirements.bat"; DestDir: "{app}"
Source: "README_FS25_Texture_Tool.txt"; DestDir: "{app}"
Source: "python-3.11.8-amd64.exe"; DestDir: "{app}"
Source: "FS25FTTMP.ico"; DestDir: "{app}"
Source: "giantsTextureTool\\*"; DestDir: "{app}\\giantsTextureTool"; Flags: recursesubdirs
Source: "gims\\*"; DestDir: "{app}\\gims"; Flags: recursesubdirs
Source: "input\\*"; DestDir: "{app}\\input"; Flags: ignoreversion
Source: "output\\*"; DestDir: "{app}\\output"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\\FS25 Fill Type Texture Maker Python"; Filename: "{app}"; IconFilename: "{app}\\FS25FTTMP.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a shortcut to the texture tool folder on the Desktop"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Install Python silently if not present
Filename: "{app}\\python-3.11.8-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"; StatusMsg: "Installing Python..."; Check: NeedsPython

; Delete Python installer after it's used
Filename: "cmd.exe"; Parameters: "/c del /q ""{app}\\python-3.11.8-amd64.exe"""; Flags: runhidden; Check: NeedsPython


[UninstallRun]
Filename: "cmd.exe"; Parameters: "/c echo ATTENTION: The installation process also installed Python if it was not already present on your PC. && choice /M ""Would you like to uninstall Python as well?"" && IF ERRORLEVEL 2 exit && python -m pip uninstall -y pillow numpy opencv-python && rmdir /S /Q C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python"
; RunOnceId not used by design to always allow uninstall prompt

[Code]
function NeedsPython: Boolean;
begin
  Result := not FileExists(ExpandConstant('{app}\\python.exe'));
end;
