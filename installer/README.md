# Windows installer

This layer packages the PyInstaller-built `dist/PCController.exe` using Inno Setup.

## Build

```powershell
pyinstaller --noconfirm gui_launcher.spec
choco install innosetup --yes
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer/PCController.iss
```

Output: `dist/installer/PCController-Setup.exe`.

The per-user installer can add a Start Menu shortcut, optionally create a desktop shortcut and optionally register the tray agent to start at sign-in. Uninstall removes the installed application and its local paired-device/permissions data. The installer is not code-signed yet.
