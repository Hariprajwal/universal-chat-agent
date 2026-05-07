"""
main.py
Screen Agent — Entry point.

Usage:
    python main.py          # Start with system tray + hotkey listener
    python main.py --now    # Launch agent immediately (skip tray)
"""

import os
import sys
import threading
import argparse
import time
import io
import subprocess

# Fix Unicode output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── Load env before any imports ──────────────────────────────
from dotenv import load_dotenv
load_dotenv()

from core.capture import RegionSelector, image_to_base64
from core.memory import ContextMemory
from backends.manager import BackendManager
from ui.agent_window import AgentWindow
from ui.tray import TrayApp


# ── Global shared state ──────────────────────────────────────
memory = ContextMemory()
backend_manager = BackendManager()
_agent_lock = threading.Lock()
_agent_running = False


def launch_agent():
    """Full pipeline: overlay → capture → agent window."""
    global _agent_running

    with _agent_lock:
        if _agent_running:
            print("[main] Agent already running, ignoring trigger.")
            return
        _agent_running = True

    try:
        print("[main] Launching region selector...")

        selector = RegionSelector()
        screenshot, region = selector.select_region()

        if screenshot is None:
            print("[main] Capture cancelled.")
            return

        print(f"[main] Captured {screenshot.size} — opening agent window")

        window = AgentWindow(
            screenshot=screenshot,
            region=region,
            memory=memory,
            backend_manager=backend_manager,
        )
        window.show()  # Blocking until window closes

    except Exception as e:
        print(f"[main] Error in agent pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        with _agent_lock:
            _agent_running = False


def register_hotkey():
    """Register global hotkey Ctrl+Shift+S."""
    try:
        import keyboard
        hotkey = "ctrl+shift+s"
        keyboard.add_hotkey(hotkey, lambda: threading.Thread(
            target=launch_agent, daemon=True
        ).start())
        print(f"[main] ✅ Hotkey registered: {hotkey.upper()}")
        return True
    except ImportError:
        print("[main] ⚠ 'keyboard' package not installed — hotkey disabled.")
        return False
    except Exception as e:
        print(f"[main] ⚠ Could not register hotkey: {e}")
        return False


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║           ⚡  SCREEN AGENT  ⚡                  ║
║  AI-powered screen interaction tool              ║
║  Hotkey: Ctrl + Shift + S                        ║
╚══════════════════════════════════════════════════╝
""")


def check_backends():
    """Print backend availability on startup."""
    print("[main] Checking backends...")
    status = backend_manager.check_all_backends()
    for name, available in status.items():
        icon = "✅" if available else "❌"
        print(f"  {icon} {name}")

    if not any(status.values()):
        print("[main] ⚠ WARNING: No backends available!")
        print("  → Set OPENROUTER_API_KEY in .env  OR")
        print("  → Run 'ollama serve' for local backend")
    else:
        info = backend_manager.get_model_info()
        print(f"[main] Active model: {info.get('model', 'unknown')} "
              f"({info.get('backend', 'unknown')})")


def start_ollama_if_needed():
    """Attempt to start Ollama if it's not already running."""
    from backends.ollama_backend import OllamaBackend
    ollama = OllamaBackend()
    if not ollama.is_available():
        print("[main] 🚀 Ollama not detected. Attempting to start 'ollama serve'...")
        try:
            # Start ollama serve in a background process
            # Use CREATE_NO_WINDOW on Windows to prevent console popup
            creationflags = 0x08000000 if sys.platform == "win32" else 0
            subprocess.Popen(["ollama", "serve"], creationflags=creationflags)
            
            # Wait a few seconds for it to warm up
            for _ in range(8):
                time.sleep(1)
                if ollama.is_available():
                    print("[main] ✅ Ollama started successfully.")
                    return True
        except Exception as e:
            print(f"[main] ❌ Could not start Ollama: {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Screen Agent")
    parser.add_argument("--now", action="store_true",
                        help="Launch agent immediately without tray")
    parser.add_argument("--no-tray", action="store_true",
                        help="Disable system tray (hotkey only)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log actions without executing (safe mode)")
    args = parser.parse_args()

    # Automatically start Ollama if configured as default or available
    start_ollama_if_needed()

    print_banner()
    check_backends()

    if args.dry_run:
        os.environ["DRY_RUN"] = "1"
        print("[main] 🔒 DRY RUN MODE — actions will be logged but not executed")

    if args.now:
        # Direct launch without tray
        launch_agent()
        return

    # Register global hotkey
    hotkey_ok = register_hotkey()

    if args.no_tray or not hotkey_ok:
        print("[main] Running in hotkey-only mode. Press Ctrl+C to quit.")
        try:
            import keyboard
            keyboard.wait()
        except ImportError:
            while True:
                time.sleep(1)
        return

    # Start system tray (blocking)
    print("[main] Starting system tray icon...")
    print("[main] Right-click tray icon or press Ctrl+Shift+S to launch")

    tray = TrayApp(
        on_activate=launch_agent,
        on_quit=lambda: sys.exit(0)
    )
    tray.start()


if __name__ == "__main__":
    main()
