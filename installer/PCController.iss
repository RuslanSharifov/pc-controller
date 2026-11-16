#define MyAppName "PC Controller"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Ruslan Sharifov"
#define MyAppExeName "PCController.exe"

[Setup]
AppId={{D5E0B5A4-9E5D-4B7C-95B2-3ABCE77A21B0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PC Controller
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=PCController-Setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "autostart"; Description: "Start PC Controller when I sign in to Windows"; Flags: unchecked
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\PCController.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PC Controller"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\PC Controller"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\PC Controller"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart


[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PC Controller"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\PCController"
