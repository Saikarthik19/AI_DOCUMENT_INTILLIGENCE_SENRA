"""
DocuMind AI Application Runner
Launches the FastAPI backend and Streamlit frontend concurrently or individually.

Usage:
    python run.py backend    # Run FastAPI backend on port 8000
    python run.py frontend   # Run Streamlit frontend on port 8501
    python run.py all        # Run both concurrently (default)
"""

import sys
import subprocess
import time
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_backend():
    print("[*] Starting FastAPI backend on http://localhost:8000 ...")
    cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    return subprocess.Popen(cmd)

def run_frontend():
    print("[*] Starting Streamlit frontend on http://localhost:8501 ...")
    cmd = [sys.executable, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.headless", "true"]
    return subprocess.Popen(cmd)

def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if mode == "backend":
        proc = run_backend()
        proc.wait()
    elif mode == "frontend":
        proc = run_frontend()
        proc.wait()
    elif mode == "all":
        p_backend = run_backend()
        time.sleep(2)
        p_frontend = run_frontend()
        try:
            p_backend.wait()
            p_frontend.wait()
        except KeyboardInterrupt:
            print("\nShutting down DocuMind AI services...")
            p_backend.terminate()
            p_frontend.terminate()
    else:
        print(f"Unknown mode: {mode}. Choose from 'backend', 'frontend', or 'all'.")

if __name__ == "__main__":
    main()
