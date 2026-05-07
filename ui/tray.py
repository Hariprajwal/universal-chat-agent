"""
ui/tray.py
System tray icon using pystray.
Stays running in background, launches agent on hotkey or menu click.
"""

import threading
from PIL import Image, ImageDraw


def create_tray_icon() -> Image.Image:
    """Create a simple tray icon programmatically."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark circle background
    draw.ellipse([2, 2, 62, 62], fill="#0d0d1a", outline="#00d4ff", width=3)

    # Eye shape
    draw.ellipse([16, 20, 48, 44], fill="#00d4ff")
    draw.ellipse([22, 26, 42, 38], fill="#0d0d1a")
    draw.ellipse([26, 29, 38, 35], fill="#7c3aed")

    return img


class TrayApp:
    """
    Manages the system tray icon and menu.
    Provides callbacks for launching the agent and quitting.
    """

    def __init__(self, on_activate: callable, on_quit: callable):
        self.on_activate = on_activate
        self.on_quit = on_quit
        self._icon = None

    def start(self):
        """Start tray icon (blocking — run in separate thread)."""
        try:
            import pystray

            icon_image = create_tray_icon()

            menu = pystray.Menu(
                pystray.MenuItem(
                    "🚀 Start Agent  (Ctrl+Shift+S)",
                    lambda: threading.Thread(
                        target=self.on_activate, daemon=True
                    ).start()
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "❌ Quit",
                    lambda: self._quit()
                )
            )

            self._icon = pystray.Icon(
                "ScreenAgent",
                icon_image,
                "Screen Agent",
                menu
            )
            self._icon.run()

        except ImportError:
            print("[Tray] pystray not installed — tray icon disabled.")
        except Exception as e:
            print(f"[Tray] Error: {e}")

    def _quit(self):
        if self._icon:
            self._icon.stop()
        self.on_quit()

    def notify(self, title: str, message: str):
        """Show a system tray notification."""
        try:
            if self._icon:
                self._icon.notify(message, title)
        except Exception:
            pass
