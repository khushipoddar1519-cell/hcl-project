"""FastAPI Application Server for Hotel Analytics.

Run directly:
    python server.py
or with uvicorn:
    uvicorn server:app --reload --port 8000
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.api import router as api_router
from modules import config

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Hotel Analytics API",
    description="Full-stack Hotel Revenue Management & Cancellation-Risk Prediction System",
    version="2.0.0"
)

# CORS middleware for development and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API endpoints
app.include_router(api_router)

# Mount frontend static directory if exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
def serve_favicon():
    fav_file = FRONTEND_DIR / "favicon.svg"
    if fav_file.exists():
        return FileResponse(str(fav_file), media_type="image/svg+xml")
    return Response(status_code=404)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "app": config.APP_NAME,
        "tagline": config.APP_TAGLINE,
        "version": "2.0.0"
    }

@app.get("/", tags=["Frontend"])
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "Hotel Analytics Backend API is running. Access interactive documentation at /docs",
        "docs_url": "/docs"
    }

import os
import socket
import time
import threading
import webbrowser

def is_port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True

def select_port(preferred: int = 8000) -> int:
    env_port = os.environ.get("PORT")
    if env_port:
        return int(env_port)
    
    if not is_port_busy(preferred):
        return preferred
    
    print(f"⚠️ Port {preferred} is currently occupied by another process.")
    for candidate in range(preferred + 1, preferred + 10):
        if not is_port_busy(candidate):
            print(f"🔄 Automatically routing to available port {candidate}...")
            return candidate
    return preferred

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_browser_delayed(url: str, delay: float = 0.8):
    def _target():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_target, daemon=True).start()

@app.get("/api/system/network-info", tags=["System"])
def network_info():
    ip = get_local_ip()
    port = int(os.environ.get("PORT", 8000))
    return {
        "local_ip": ip,
        "port": port,
        "localhost_url": f"http://localhost:{port}",
        "network_url": f"http://{ip}:{port}"
    }

if __name__ == "__main__":
    port = select_port(8000)
    host = os.environ.get("HOST", "127.0.0.1")
    url = f"http://localhost:{port}"

    print("=" * 65)
    print("🏨 Hotel Analytics Web Dashboard Running")
    print("=" * 65)
    print(f"👉 Direct URL:       {url}")
    print(f"📖 Swagger API Docs: {url}/docs")
    print(f"🩺 Health Check:     {url}/health")
    print("=" * 65)

    if os.environ.get("AUTO_OPEN_BROWSER", "1") == "1":
        open_browser_delayed(url, delay=0.8)

    uvicorn.run("server:app", host=host, port=port, reload=False)


