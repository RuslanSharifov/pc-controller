import sys
import os
import socket
import threading
import time
import base64
import uvicorn
from io import BytesIO
import qrcode
import webview

# Import FastAPI app instance
from app import app

def get_local_ip():
    """Finds the local IPv4 address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_qr_base64(url):
    """Converts QR code to Base64 image"""
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def run_server():
    """Runs Uvicorn server in a single thread"""
    uvicorn.run(app, host="0.0.0.0", port=9050, log_level="error")

if __name__ == '__main__':
    # 1. Start server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    local_ip = get_local_ip()
    phone_url = f"http://{local_ip}:9050"
    qr_base64 = generate_qr_base64(phone_url)

    # 2. HTML UI (English & Updated Buttons)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
                user-select: none;
            }}
            .card {{
                background: #1e293b;
                padding: 25px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                border: 1px solid #334155;
                width: 320px;
            }}
            h2 {{ color: #38bdf8; margin-top: 0; margin-bottom: 5px; font-size: 22px; }}
            p {{ color: #94a3b8; font-size: 13px; margin-bottom: 18px; }}
            .qr-container {{
                background: white;
                padding: 10px;
                border-radius: 12px;
                display: inline-block;
            }}
            img {{ display: block; border-radius: 8px; }}
            .url-box {{
                margin-top: 15px;
                background: #0f172a;
                padding: 8px 12px;
                border-radius: 8px;
                font-family: monospace;
                color: #4ade80;
                font-size: 15px;
                border: 1px solid #1e293b;
                word-break: break-all;
            }}
            .actions {{
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }}
            .btn {{
                flex: 1;
                background: #0284c7;
                color: white;
                border: none;
                padding: 10px 12px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                font-size: 13px;
                transition: 0.2s;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{ background: #0369a1; }}
            .btn-github {{
                background: #334155;
                color: #f8fafc;
            }}
            .btn-github:hover {{ background: #475569; }}
            .footer {{ margin-top: 18px; font-size: 11px; color: #64748b; letter-spacing: 0.5px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>PC Remote Control</h2>
            <p>Scan the QR code with your phone:</p>
            <div class="qr-container">
                <img src="data:image/png;base64,{qr_base64}" width="200" height="200" />
            </div>
            <div class="url-box">{phone_url}</div>
            
            <div class="actions">
                <button class="btn" onclick="window.location.href='http://127.0.0.1:9050'">Open Panel</button>
                <a class="btn btn-github" href="https://github.com/RuslanSharifov/pc-controller.git" target="_blank">GitHub Repo</a>
            </div>

            <div class="footer">DEVELOPED BY Ruslan</div>
        </div>
    </body>
    </html>
    """

    # 3. Create GUI window
    webview.create_window(
        'PC Remote Control - Launcher',
        html=html_content,
        width=450,
        height=580,
        resizable=False
    )
    webview.start()
    sys.exit()