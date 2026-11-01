"""Hotel Analytics Unified Master Launcher.

Usage:
    python start.py            # Starts FastAPI Server & Modern Web Frontend (http://localhost:8000)
    python start.py --all      # Starts both FastAPI and Streamlit concurrently
    python start.py --streamlit# Starts the Streamlit dashboard only
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"

if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

import socket
import re
import time

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_public_tunnel(port=8000):
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        url = None
        for _ in range(40):
            line = proc.stderr.readline()
            if not line:
                break
            match = re.search(r"https://([a-zA-Z0-9-]+)\.trycloudflare\.com", line)
            if match and match.group(1) != "api":
                url = match.group(0)
                break
        return proc, url
    except Exception:
        return None, None

def run_server(public=False, network=False):
    env = os.environ.copy()
    if network:
        env["HOST"] = "0.0.0.0"

    if public:
        print("🌐 Starting server with Global Public Link for mobile & other devices...")
        server_proc = subprocess.Popen([str(VENV_PYTHON), "server.py"], env=env)
        time.sleep(1.5)
        tunnel_proc, tunnel_url = start_public_tunnel(8000)

        print("=" * 68)
        print("🏨 Hotel Analytics Platform (Public Access Mode)")
        print("=" * 68)
        if tunnel_url:
            print("🌍 GLOBAL PUBLIC LINK (Opens on ANY phone, tablet, or computer):")
            print(f"   👉 {tunnel_url}")
            print("=" * 68)
        print("💻 Computer URL:      http://localhost:8000")
        print("📖 Swagger API Docs:  http://localhost:8000/docs")
        print("=" * 68)

        try:
            server_proc.wait()
        except KeyboardInterrupt:
            print("\nStopping server and public tunnel...")
            server_proc.terminate()
            if tunnel_proc:
                tunnel_proc.terminate()
        return

    cmd = [str(VENV_PYTHON), "server.py"]
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nServer stopped.")

def run_streamlit():
    print("=" * 60)
    print("🏨 Starting Hotel Analytics Streamlit Dashboard")
    print("👉 Streamlit URL:   http://localhost:8501")
    print("=" * 60)
    env = os.environ.copy()
    env["HOME"] = str(BASE_DIR)
    cmd = [
        str(VENV_PYTHON), "-m", "streamlit", "run", "app.py",
        "--server.headless=true", "--server.port=8501"
    ]
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nStreamlit stopped.")

def run_all():
    print("=" * 65)
    print("🏨 Starting Hotel Analytics Platform:")
    print("👉 1. Web App (Recommended): http://localhost:8000")
    print("👉 2. Streamlit Dashboard:    http://localhost:8501")
    print("=" * 65)
    env = os.environ.copy()
    env["HOME"] = str(BASE_DIR)
    
    server_proc = subprocess.Popen([str(VENV_PYTHON), "server.py"])
    st_proc = subprocess.Popen([
        str(VENV_PYTHON), "-m", "streamlit", "run", "app.py",
        "--server.headless=true", "--server.port=8501"
    ], env=env)

    try:
        server_proc.wait()
        st_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
        server_proc.terminate()
        st_proc.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hotel Analytics Launcher")
    parser.add_argument("--all", action="store_true", help="Launch both FastAPI and Streamlit")
    parser.add_argument("--streamlit", action="store_true", help="Launch Streamlit only")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI server only")
    parser.add_argument("--network", action="store_true", help="Bind to 0.0.0.0 for local network Wi-Fi access")
    parser.add_argument("--public", "--share", action="store_true", help="Launch with a global public HTTPS link for mobile and other devices")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.streamlit:
        run_streamlit()
    else:
        run_server(public=args.public, network=args.network)
        run_server(public=args.public)

