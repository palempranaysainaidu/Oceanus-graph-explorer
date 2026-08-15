"""
Oceanus Unified Web Application Launcher
Launches the Unified FastAPI Backend (Port 8000) and Next.js Frontend (Port 9002) in a single command.
"""

import os
import sys
import time
import subprocess
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend-chatbot-test", "API")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

def print_header():
    print("=" * 60)
    print("🌊 OCEANUS UNIFIED AGENTIC RAG WEB APPLICATION 🌊")
    print("=" * 60)
    print(f"📁 Root Directory: {ROOT_DIR}")
    print("⚡ Single Server Architecture Initializing...")
    print("-" * 60)

def main():
    print_header()
    
    # Environment setting
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # 1. Start Unified Backend Server (Port 8000)
    print("🚀 [1/2] Starting Unified Python Backend Server (Port 8000)...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_process = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR, env=env)
    
    time.sleep(3)
    
    # 2. Start Frontend Next.js Server (Port 9002)
    print("🎨 [2/2] Starting Next.js Frontend Application (Port 9002)...")
    frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"]
    frontend_process = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR, env=env)
    
    print("-" * 60)
    print("✅ BOTH SERVERS STARTED SUCCESSFULLY!")
    print("  👉 Web App UI:        http://localhost:9002")
    print("  👉 Interactive Docs:  http://localhost:8000/docs")
    print("  👉 Float Map Data:    http://localhost:8000/api/floats")
    print("=" * 60)
    print("Press CTRL+C in this terminal to stop both servers.")

    time.sleep(2)
    webbrowser.open("http://localhost:9002")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Oceanus servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("👋 Oceanus servers stopped cleanly.")

if __name__ == "__main__":
    main()
