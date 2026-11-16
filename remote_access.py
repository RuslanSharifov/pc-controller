"""LAN pairing, device authentication, permissions and remote input for PC Controller.

The pairing code is shown only in the local desktop UI. Paired devices receive a
random bearer token; only its SHA-256 digest is persisted on disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse


PORT = int(os.environ.get("PC_CONTROLLER_PORT", "9050"))
DISCOVERY_PORT = 9051
SERVICE_NAME = "pc-controller"
DEFAULT_PERMISSIONS: dict[str, Any] = {
    "status": True,
    "media": True,
    "volume": True,
    "brightness": True,
    "apps": [],
    "desktop_shortcuts": False,
    "system_shortcuts": False,
    "screen_view": False,
    "remote_input": False,
    "power": False,
}


def _data_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    path = Path(root) / "PCController"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = _data_dir()
DEVICES_FILE = DATA_DIR / "paired_devices.json"
PERMISSIONS_FILE = DATA_DIR / "permissions.json"
_LOCK = threading.RLock()
_PAIRING_CODE = f"{secrets.randbelow(1_000_000):06d}"
_DEVICES: dict[str, dict[str, Any]] = {}
_PERMISSIONS: dict[str, Any] = {}
_FAILED_PAIRS: dict[str, list[float]] = {}


def _load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def _save_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


_DEVICES = _load_json(DEVICES_FILE, {})
_PERMISSIONS = {**DEFAULT_PERMISSIONS, **_load_json(PERMISSIONS_FILE, {})}
if not isinstance(_DEVICES, dict):
    _DEVICES = {}
if not isinstance(_PERMISSIONS.get("apps"), list):
    _PERMISSIONS["apps"] = []


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _is_loopback(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost"}


def _local_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def get_pairing_info() -> dict[str, str]:
    ip = _local_ip()
    return {
        "device_name": socket.gethostname(),
        "host": ip,
        "url": f"http://{ip}:{PORT}",
        "pairing_code": _PAIRING_CODE,
        "discovery_port": str(DISCOVERY_PORT),
    }


def get_public_capabilities() -> dict[str, Any]:
    with _LOCK:
        return {
            "apps": list(_PERMISSIONS.get("apps", [])),
            "permissions": {key: bool(value) for key, value in _PERMISSIONS.items() if key != "apps"},
        }


def _permission_for(path: str) -> tuple[str | None, str | None]:
    if path in {"/api/status", "/api/capabilities"}:
        return "status", None
    if path.startswith("/api/media/"):
        return "media", None
    if path.startswith("/api/volume/"):
        return "volume", None
    if path.startswith("/api/brightness/"):
        return "brightness", None
    if path.startswith("/api/open/"):
        return "apps", path.rsplit("/", 1)[-1].lower()
    if path in {"/api/lock"}:
        return "system_shortcuts", None
    if path in {"/api/showdesktop", "/api/alttab", "/api/closewindow"}:
        return "desktop_shortcuts", None
    if path.startswith("/api/system/"):
        return "power", None
    if path == "/api/remote/screenshot":
        return "screen_view", None
    if path.startswith("/api/remote/"):
        return "remote_input", None
    return None, None


def install_remote_access(app) -> None:
    """Install pairing endpoints and enforce permissions on all remote API calls."""

    @app.middleware("http")
    async def remote_auth_middleware(request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        if path in {"/api/pair", "/api/pair/info"}:
            return await call_next(request)

        if path.startswith("/api/local/") and not _is_loopback(request):
            return JSONResponse({"detail": "Local desktop access required"}, status_code=403)

        if path.startswith("/api/local/"):
            return await call_next(request)

        if _is_loopback(request):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        with _LOCK:
            device = _DEVICES.get(_digest(token)) if token else None
            permission, app_id = _permission_for(path)
            allowed = bool(device and permission and _PERMISSIONS.get(permission, False))
            if allowed and permission == "apps":
                allowed = app_id in _PERMISSIONS.get("apps", [])
        if not device:
            return JSONResponse({"detail": "Pair this device before controlling the PC"}, status_code=401)
        if not allowed:
            return JSONResponse({"detail": "This action is disabled in desktop permissions"}, status_code=403)
        return await call_next(request)

    @app.get("/api/capabilities")
    async def capabilities():
        return get_public_capabilities()

    @app.get("/api/pair/info")
    async def pair_info(request: Request):
        if not _is_loopback(request):
            raise HTTPException(status_code=403, detail="Open pairing details on the PC")
        return get_pairing_info()

    @app.post("/api/pair")
    async def pair_device(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        attempts = [t for t in _FAILED_PAIRS.get(ip, []) if now - t < 60]
        _FAILED_PAIRS[ip] = attempts
        if len(attempts) >= 8:
            raise HTTPException(status_code=429, detail="Too many pairing attempts. Try again in one minute.")
        body = await request.json()
        code = str(body.get("code", "")).strip()
        name = str(body.get("device_name", "Mobile device")).strip()[:64] or "Mobile device"
        if not secrets.compare_digest(code, _PAIRING_CODE):
            attempts.append(now)
            _FAILED_PAIRS[ip] = attempts
            raise HTTPException(status_code=401, detail="Incorrect pairing code")
        token = secrets.token_urlsafe(32)
        device_id = str(uuid.uuid4())
        record = {
            "id": device_id,
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        with _LOCK:
            _DEVICES[_digest(token)] = record
            _save_json(DEVICES_FILE, _DEVICES)
        return {"token": token, "device": record}

    @app.get("/api/local/info")
    async def local_info(request: Request):
        if not _is_loopback(request):
            raise HTTPException(status_code=403, detail="Local desktop access required")
        return {**get_pairing_info(), "permissions": _PERMISSIONS}

    @app.get("/api/local/devices")
    async def local_devices(request: Request):
        if not _is_loopback(request):
            raise HTTPException(status_code=403, detail="Local desktop access required")
        with _LOCK:
            return {"devices": list(_DEVICES.values())}

    @app.delete("/api/local/devices/{device_id}")
    async def revoke_device(device_id: str, request: Request):
        if not _is_loopback(request):
            raise HTTPException(status_code=403, detail="Local desktop access required")
        with _LOCK:
            key = next((k for k, v in _DEVICES.items() if v.get("id") == device_id), None)
            if key:
                _DEVICES.pop(key, None)
                _save_json(DEVICES_FILE, _DEVICES)
        return {"ok": True}

    @app.put("/api/local/permissions")
    async def save_permissions(request: Request):
        if not _is_loopback(request):
            raise HTTPException(status_code=403, detail="Local desktop access required")
        incoming = await request.json()
        updated = dict(DEFAULT_PERMISSIONS)
        for key in DEFAULT_PERMISSIONS:
            if key in incoming:
                updated[key] = incoming[key]
        updated["apps"] = sorted({str(x).lower() for x in updated["apps"] if str(x).isidentifier()})
        with _LOCK:
            _PERMISSIONS.clear()
            _PERMISSIONS.update(updated)
            _save_json(PERMISSIONS_FILE, _PERMISSIONS)
        return {"permissions": _PERMISSIONS}

    @app.get("/api/remote/screenshot")
    async def remote_screenshot():
        import base64
        from io import BytesIO
        import pyautogui
        image = pyautogui.screenshot()
        image.thumbnail((1600, 900))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=65, optimize=True)
        return {"image": "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")}

    @app.post("/api/remote/click")
    async def remote_click(request: Request):
        import pyautogui
        body = await request.json()
        width, height = pyautogui.size()
        x = max(0, min(width - 1, int(body.get("x", 0))))
        y = max(0, min(height - 1, int(body.get("y", 0))))
        button = body.get("button", "left")
        if button not in {"left", "right", "middle"}:
            raise HTTPException(status_code=400, detail="Unsupported mouse button")
        pyautogui.click(x=x, y=y, button=button)
        return {"ok": True}

    @app.post("/api/remote/key")
    async def remote_key(request: Request):
        import pyautogui
        body = await request.json()
        key = str(body.get("key", "")).lower()
        allowed_keys = {
            "enter", "esc", "tab", "space", "backspace", "delete",
            "up", "down", "left", "right", "home", "end", "pageup",
            "pagedown", "playpause", "nexttrack", "prevtrack", "volumeup",
            "volumedown", "volumemute",
        }
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail="Key is not allowed")
        pyautogui.press(key)
        return {"ok": True}

    def discovery_beacon() -> None:
        payload = json.dumps({
            "service": SERVICE_NAME,
            "version": 1,
            "device_name": socket.gethostname(),
            "port": PORT,
        }).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            try:
                sock.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
            except OSError:
                pass
            time.sleep(3)

    threading.Thread(target=discovery_beacon, name="pc-controller-discovery", daemon=True).start()
