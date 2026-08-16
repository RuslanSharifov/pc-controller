from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
import os
import base64
import ctypes
import subprocess
import psutil
import pyautogui
import screen_brightness_control as sbc

import comtypes
from pycaw.pycaw import AudioUtilities


# =========================================================
# WINDOWS MEDIA CONTROL (SAFE IMPORT WITH FOUNDATION)
# =========================================================
HAS_MEDIA_SDK = False

try:
    # Foundation modulunu öncədən import edirik
    import winrt.windows.foundation
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )
    from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
    HAS_MEDIA_SDK = True
except ModuleNotFoundError:
    try:
        import winsdk.windows.foundation
        from winsdk.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager as MediaManager,
        )
        from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions
        HAS_MEDIA_SDK = True
    except ModuleNotFoundError:
        HAS_MEDIA_SDK = False


# =========================================================
# DYNAMIC BASE DIRECTORY (FOR PYINSTALLER .EXE SUPPORT)
# =========================================================
    
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

# Tətbiqi və statik yolları yalnız 1 dəfə elan edirik
app = FastAPI(title="PC Remote Control", version="1.2.0")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

pyautogui.FAILSAFE = False


# =========================================================
# AUDIO
# =========================================================
def get_audio_interface():
    comtypes.CoInitialize()
    try:
        device = AudioUtilities.GetSpeakers()
        return device.EndpointVolume
    except Exception:
        comtypes.CoUninitialize()
        raise


def get_volume():
    volume = get_audio_interface()
    try:
        value = volume.GetMasterVolumeLevelScalar()
        muted = bool(volume.GetMute())
        return {"volume": round(value * 100), "muted": muted}
    finally:
        comtypes.CoUninitialize()


def set_volume(value: int):
    value = max(0, min(100, int(value)))
    volume = get_audio_interface()
    try:
        volume.SetMasterVolumeLevelScalar(value / 100.0, None)
        return {"volume": value, "muted": bool(volume.GetMute())}
    finally:
        comtypes.CoUninitialize()


# =========================================================
# BRIGHTNESS
# =========================================================
def get_brightness():
    try:
        values = sbc.get_brightness()
        return round(float(values[0])) if values else 50
    except Exception:
        return 50


def set_brightness_val(value: int):
    value = max(0, min(100, int(value)))
    try:
        sbc.set_brightness(value)
    except Exception:
        pass
    return value


# =========================================================
# MEDIA & COVER ART (SPOTIFY / WINDOWS MEDIA)
# =========================================================
async def get_thumbnail_base64(thumbnail_ref):
    if not thumbnail_ref:
        return None
    try:
        stream = await thumbnail_ref.open_read_async()
        size = stream.size
        if size == 0 or size > 5_000_000:  # 5MB-dan böyük şəkilləri ötür
            return None

        # winrt və ya winsdk üzərindən DataReader istifadəsi
        try:
            from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
        except ModuleNotFoundError:
            from winsdk.windows.storage.streams import DataReader, Buffer, InputStreamOptions

        buffer = Buffer(size)
        await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
        reader = DataReader.from_buffer(buffer)
        data = bytearray(size)
        reader.read_bytes(data)

        # Base64 string-ə çeviririk (HTML <img> tegində birbaşa göstərmək üçün)
        b64 = base64.b64encode(bytes(data)).decode("ascii")
        content_type = "image/png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        return f"data:{content_type};base64,{b64}"
    except Exception as e:
        print("Cover alarkən xəta:", e)
        return None


async def get_media_info():
    if not HAS_MEDIA_SDK:
        return {
            "title": "No media",
            "artist": "Offline",
            "album": "",
            "is_playing": False,
            "has_media": False,
            "cover": None,
        }

    try:
        sessions = await MediaManager.request_async()
        if not sessions:
            return {"title": "No media", "artist": "Offline", "album": "", "is_playing": False, "has_media": False, "cover": None}

        current = sessions.get_current_session()
        if not current:
            all_sessions = sessions.get_sessions()
            if all_sessions:
                current = all_sessions[0]

        if current:
            info = await current.try_get_media_properties_async()
            playback = current.get_playback_info()

            # Albom şəklini alırıq
            cover_b64 = None
            if hasattr(info, "thumbnail") and info.thumbnail:
                cover_b64 = await get_thumbnail_base64(info.thumbnail)

            return {
                "title": info.title or "Mahnı Adı Yoxdur",
                "artist": info.artist or "Məlum Olmayan İfaçı",
                "album": getattr(info, "album_title", "") or "",
                "is_playing": (playback.playback_status == 4) if playback else False,
                "has_media": True,
                "cover": cover_b64,  # HTML <img> src parametri üçün base64 data URL
            }
    except Exception as e:
        print("Media error:", e)

    return {
        "title": "No media",
        "artist": "Offline",
        "album": "",
        "is_playing": False,
        "has_media": False,
        "cover": None,
    }


async def get_media_info():
    if not HAS_MEDIA_SDK:
        return {
            "title": "Media SDK Yoxdur",
            "artist": "Offline",
            "album": "",
            "is_playing": False,
            "has_media": False,
            "cover": None,
        }

    try:
        sessions = await MediaManager.request_async()
        if not sessions:
            return {"title": "No media", "artist": "Offline", "album": "", "is_playing": False, "has_media": False, "cover": None}

        # 1. Aktiv (hazırda oxunan) sessiyanı al
        current = sessions.get_current_session()
        
        # 2. Əgər get_current_session() None qaytararsa, bütün aktiv sessiyaları yoxla (Spotify fallback)
        if not current:
            all_sessions = sessions.get_sessions()
            if all_sessions:
                # Ən son aktiv olan və ya oxutma statusu olan sessiyanı seç
                current = all_sessions[0]

        if current:
            info = await current.try_get_media_properties_async()
            playback = current.get_playback_info()

            cover = None
            if hasattr(info, "thumbnail") and info.thumbnail:
                cover = await get_thumbnail_base64(info.thumbnail)

            # Playback status: 4 = Playing, 3 = Paused
            is_playing = (playback.playback_status == 4) if playback else False

            return {
                "title": info.title or "Mahnı Adı Yoxdur",
                "artist": info.artist or "Məlum Olmayan İfaçı",
                "album": getattr(info, "album_title", "") or "",
                "is_playing": is_playing,
                "has_media": True,
                "cover": cover,
            }
            
    except Exception as e:
        print("Media error detal:", e)

    return {
        "title": "No media",
        "artist": "Offline",
        "album": "",
        "is_playing": False,
        "has_media": False,
        "cover": None,
    }


async def get_media_info():
    if not HAS_MEDIA_SDK:
        return {
            "title": "Spotify / Media Controller",
            "artist": "Active System",
            "album": "",
            "is_playing": False,
            "has_media": False,
            "cover": None,
        }

    try:
        sessions = await MediaManager.request_async()
        current = sessions.get_current_session()
        if current:
            info = await current.try_get_media_properties_async()
            playback = current.get_playback_info()
            return {
                "title": info.title or "No Track",
                "artist": info.artist or "Unknown",
                "album": getattr(info, "album_title", "") or "",
                "is_playing": playback.playback_status == 4,
                "has_media": True,
                "cover": None,
            }
    except Exception as e:
        print("Media error:", e)

    return {
        "title": "No media",
        "artist": "Offline",
        "album": "",
        "is_playing": False,
        "has_media": False,
        "cover": None,
    }


# =========================================================
# HOME
# =========================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

# =========================================================
# STATUS
# =========================================================
@app.get("/api/status")
async def status():
    battery = psutil.sensors_battery()
    audio = {"volume": 0, "muted": False}
    try:
        audio = get_volume()
    except Exception:
        pass

    media = await get_media_info()

    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "battery": battery.percent if battery else None,
        "plugged": battery.power_plugged if battery else False,
        "volume": audio["volume"],
        "muted": audio["muted"],
        "brightness": get_brightness(),
        "media": media,
    }


# =========================================================
# VOLUME
# =========================================================
@app.post("/api/volume/up")
def volume_up():
    curr = get_volume()["volume"]
    return set_volume(curr + 5)


@app.post("/api/volume/down")
def volume_down():
    curr = get_volume()["volume"]
    return set_volume(curr - 5)


@app.post("/api/volume/set")
def volume_set(data: dict):
    return set_volume(data.get("volume", 50))


@app.post("/api/volume/toggle")
def volume_toggle():
    vol = get_audio_interface()
    try:
        curr = bool(vol.GetMute())
        vol.SetMute(not curr, None)
        return {
            "muted": not curr,
            "volume": round(vol.GetMasterVolumeLevelScalar() * 100),
        }
    finally:
        comtypes.CoUninitialize()


# =========================================================
# BRIGHTNESS
# =========================================================
@app.post("/api/brightness/up")
def brightness_up():
    curr = get_brightness()
    return {"brightness": set_brightness_val(curr + 10)}


@app.post("/api/brightness/down")
def brightness_down():
    curr = get_brightness()
    return {"brightness": set_brightness_val(curr - 10)}


@app.post("/api/brightness/set")
def brightness_set(data: dict):
    return {"brightness": set_brightness_val(data.get("brightness", 50))}


# =========================================================
# MEDIA CONTROLS
# =========================================================
@app.post("/api/media/playpause")
def media_playpause():
    pyautogui.press("playpause")
    return {"ok": True}


@app.post("/api/media/next")
def media_next():
    pyautogui.press("nexttrack")
    return {"ok": True}


@app.post("/api/media/prev")
def media_prev():
    pyautogui.press("prevtrack")
    return {"ok": True}


# =========================================================
# LOCK + SHORTCUTS
# =========================================================
@app.post("/api/lock")
def lock_screen():
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception:
        os.system("rundll32.exe user32.dll,LockWorkStation")
    return {"ok": True}


@app.post("/api/showdesktop")
def show_desktop():
    pyautogui.hotkey("win", "d")
    return {"ok": True}


@app.post("/api/alttab")
def alt_tab():
    pyautogui.hotkey("alt", "tab")
    return {"ok": True}


@app.post("/api/closewindow")
def close_window():
    pyautogui.hotkey("alt", "f4")
    return {"ok": True}


# =========================================================
# APPLICATIONS
# =========================================================
APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "vscode": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs": r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe",
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    "explorer": "explorer.exe",
}


@app.post("/api/open/{appname}")
def open_app(appname: str):
    appname = appname.lower().strip()

    if appname == "settings":
        subprocess.Popen("start ms-settings:", shell=True)
        return {"ok": True}
    if appname == "windows":
        pyautogui.press("win")
        return {"ok": True}

    if appname in APPS:
        path = APPS[appname]
        try:
            if appname in ("cmd", "powershell"):
                subprocess.Popen(path, creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif appname == "explorer":
                subprocess.Popen(path)
            else:
                if os.path.exists(path):
                    subprocess.Popen([path])
                else:
                    if appname == "chrome":
                        subprocess.Popen("start chrome", shell=True)
                    elif appname == "vscode":
                        subprocess.Popen("code", shell=True)
                    elif appname == "spotify":
                        subprocess.Popen("start spotify:", shell=True)
                    elif appname == "vs":
                        subprocess.Popen("start devenv", shell=True)
                    else:
                        return {"ok": False, "error": "Not found"}
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "Unknown app"}


# =========================================================
# POWER
# =========================================================
@app.post("/api/system/shutdown")
def shutdown():
    subprocess.Popen("shutdown /s /t 0", shell=True)
    return {"ok": True}


@app.post("/api/system/restart")
def restart():
    subprocess.Popen("shutdown /r /t 0", shell=True)
    return {"ok": True}


@app.post("/api/system/sleep")
def sleep():
    subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
