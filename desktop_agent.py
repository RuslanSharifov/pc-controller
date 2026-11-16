"""Windows tray-first launcher for PC Controller.

Run with: python desktop_agent.py
"""
from __future__ import annotations

import threading
import webbrowser
from io import BytesIO

import qrcode
import uvicorn
import webview
import pystray
from PIL import Image, ImageDraw

from app import app
from remote_access import PORT, get_pairing_info, install_remote_access

install_remote_access(app)


def run_server() -> None:
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


def tray_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), (30, 41, 59, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((5, 5, 59, 59), radius=13, fill=(37, 99, 235, 255))
    draw.text((13, 20), "PC", fill="white", stroke_width=1)
    return image


def show_pairing(icon, item) -> None:
    info = get_pairing_info()
    qr = qrcode.make(f"{info['url']}/static/connect.html?host={info['host']}&port={PORT}&code={info['pairing_code']}")
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    import base64
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
    body{{font-family:Segoe UI,sans-serif;background:#0f172a;color:#f8fafc;display:grid;place-items:center;height:100vh;margin:0}}
    main{{background:#1e293b;border:1px solid #334155;border-radius:18px;padding:24px;text-align:center;width:330px}}
    img{{width:210px;height:210px;background:white;padding:8px;border-radius:12px}}
    code{{display:block;font-size:28px;letter-spacing:7px;color:#4ade80;margin:14px}}
    small{{color:#94a3b8}}a{{color:#38bdf8}}
    </style></head><body><main><h2>PC Controller</h2>
    <p>Scan this QR code or enter the pairing code in your phone</p>
    <img src="data:image/png;base64,{encoded}"><code>{info['pairing_code']}</code>
    <small>{info['url']}</small><p><small>Only pair devices you trust. The code changes when the desktop agent restarts.</small></p>
    </main></body></html>"""
    webview.create_window("PC Controller · Pair device", html=html, width=410, height=560, resizable=False)
    webview.start()


def open_dashboard(icon, item) -> None:
    webbrowser.open(f"http://127.0.0.1:{PORT}")


def exit_app(icon, item) -> None:
    icon.stop()


if __name__ == "__main__":
    threading.Thread(target=run_server, name="pc-controller-api", daemon=True).start()
    tray = pystray.Icon(
        "PC Controller",
        tray_image(),
        "PC Controller",
        menu=pystray.Menu(
            pystray.MenuItem("Pair a device", show_pairing, default=True),
            pystray.MenuItem("Open dashboard", open_dashboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", exit_app),
        ),
    )
    tray.run()
