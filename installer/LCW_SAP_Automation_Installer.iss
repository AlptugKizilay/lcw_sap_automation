; Inno Setup Kurulum Senaryosu
; LCW SAP Otomasyonu v1.0.0

#define MyAppName "LCW SAP Otomasyonu"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LCWaikiki"
#define MyAppExeName "LCW_SAP_Automation.exe"

[Setup]
AppId={{C789A5F0-8632-4E49-A672-881275C66C3E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\LCW_SAP_Automation
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Yönetici (Admin) yetkisi gerektirmeden kullanıcı seviyesinde kurulum (Per-User)
PrivilegesRequired=lowest
OutputDir=..\dist_setup
OutputBaseFilename=LCW_SAP_Automation_Setup_v1.0.0
SetupIconFile=..\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\app_icon.ico

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller ile derlenmiş dist/LCW_SAP_Automation klasöründeki tüm dosyalar
Source: "..\dist\LCW_SAP_Automation\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

