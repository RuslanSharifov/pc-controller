# PC Controller

**PC Controller** is a Windows desktop agent with a local-network remote-control client for phones, tablets and other browsers. It is designed to work over the same private Wi-Fi/LAN without a cloud account.

> This branch introduces the LAN pairing and permission foundation. The native Android APK and signed installer are follow-up deliverables; they are not included in this source change yet.

## Current capabilities

- Windows tray-first desktop agent (notification area beside the clock)
- One-time six-digit pairing code and QR pairing page
- UDP LAN discovery beacon on port 9051
- Paired-device token authentication
- Desktop-managed permissions and device revocation
- Existing responsive dashboard for mobile browsers
- Media, volume and brightness controls
- Optional screen capture, mouse click and restricted keyboard input APIs
- Desktop shortcut and power controls remain disabled until explicitly enabled

## Run on Windows

Python 3.10+ is recommended.

```powershell
git clone https://github.com/RuslanSharifov/pc-controller.git
cd pc-controller
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python desktop_agent.py
```

The agent runs in the Windows notification area. Right-click its icon and select **Pair a device** to display the QR code and one-time code.

## Connect a phone

1. Connect the phone and PC to the same private Wi-Fi network.
2. On the PC, open the tray menu and choose **Pair a device**.
3. Scan the QR code. If scanning is unavailable, open `http://<PC-IP>:9050/static/connect.html` and enter the code.
4. After pairing, the phone opens the existing dashboard.

For local browser access on the PC, open `http://127.0.0.1:9050`.

## Desktop permissions

Open `http://127.0.0.1:9050/static/desktop.html` on the PC to:

- enable or disable media, volume and brightness controls;
- allow selected applications;
- separately enable desktop shortcuts, screen lock, screen viewing, mouse/keyboard input and power operations;
- revoke a previously paired device.

Only explicitly enabled remote actions are accepted by the API. New high-impact actions are disabled by default.

## Build and install on Windows

The GitHub Actions workflow builds both a portable executable and an Inno Setup installer.

For a local build:

```powershell
pip install -r requirements.txt
pyinstaller --noconfirm gui_launcher.spec
choco install innosetup --yes
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer/PCController.iss
```

Outputs:
- Portable app: `dist/PCController.exe`
- Installer: `dist/installer/PCController-Setup.exe`

The installer adds Start Menu shortcuts, optionally creates a desktop shortcut and can start the tray agent at Windows sign-in. Uninstall removes the application and its local pairing data. The installer is currently unsigned; Windows SmartScreen may show a warning until a code-signing certificate is configured.

## Network and security

- HTTP API: TCP 9050
- Discovery beacon: UDP 9051
- Allow the application through Windows Defender Firewall on **Private networks** only.
- Guest Wi-Fi isolation, VPNs and VLAN/client isolation can block discovery.
- The initial LAN transport uses HTTP. Do not expose it to the public internet or configure router port forwarding. TLS certificate provisioning and pinning are required before claiming encrypted transport.

See [docs/SECURITY_AND_PAIRING.md](docs/SECURITY_AND_PAIRING.md).

## Project structure

- `app.py` — existing FastAPI controls and Windows integrations
- `remote_access.py` — pairing, LAN discovery, permissions and remote input
- `desktop_agent.py` — Windows tray launcher
- `templates/` — shared remote dashboard
- `static/` — web client, connection page and desktop settings
- `desktop/README.md` — desktop agent notes
- `mobile/README.md` — mobile client notes

## License

MIT. See [LICENSE](LICENSE).
