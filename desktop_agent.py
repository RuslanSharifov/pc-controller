"""Windows tray-first launcher for PC Controller.

Run with: python desktop_agent.py
"""
from __future__ import annotations

import threading
import webbrowser
from io import BytesIO

import qrcode
import uvicorn
import pystray
from PIL import Image, ImageDraw

from app import app
from fastapi import HTTPException, Request
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
    webbrowser.open(f"http://127.0.0.1:{PORT}/static/desktop.html")


@app.get("/api/local/qr")
async def local_pairing_qr(request: Request):
    if not request.client or request.client.host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=403, detail="Local desktop access required")
    import base64
    import qrcode
    from io import BytesIO
    info = get_pairing_info()
    target = f"{info['url']}/static/connect.html?host={info['host']}&port={PORT}&code={info['pairing_code']}"
    image = qrcode.make(target)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"image": "data:image/png;base64," + encoded}


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
