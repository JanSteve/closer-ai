#!/usr/bin/env python3
"""
One-Click Launcher for CLOSER AI Web Console.
Starts the server and automatically opens the dashboard in your default browser.
"""

import sys
import time
import webbrowser
from pathlib import Path

root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from src.closer.web.dashboard import run_web_console


def main():
    port = 8501
    url = f"http://localhost:{port}/"
    print("=" * 60)
    print("   CLOSER AI: WEB CONSOLE LAUNCHER")
    print(f"   Opening dashboard at: {url}")
    print("=" * 60)

    # Delay slightly to allow the server socket to bind before browser opens
    import threading
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    run_web_console(port=port)


if __name__ == "__main__":
    main()
