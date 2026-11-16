# Windows Desktop Agent

The desktop agent is the Windows-side host for PC Controller. It runs the FastAPI control service in the background and exposes a tray icon beside the Windows clock.

## Development

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python desktop_agent.py
```

Tray actions:
- **Pair a device** — opens the one-time pairing QR code and code.
- **Open dashboard** — opens the local dashboard.
- **Exit** — stops the tray agent.

Desktop permissions are managed at `http://127.0.0.1:9050/static/desktop.html`.

## Packaging

The PyInstaller spec is `gui_launcher.spec` and builds the tray-first `desktop_agent.py` entry point. The Inno Setup script at `installer/PCController.iss` creates a per-user installer with optional sign-in startup and clean uninstall. The current installer is unsigned.
