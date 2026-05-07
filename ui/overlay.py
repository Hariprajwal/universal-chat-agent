"""
ui/overlay.py
Fullscreen transparent overlay for screen region selection.
Draws crosshair, selection rectangle with live dimensions.
"""

import tkinter as tk
from PIL import Image


class ScreenOverlay:
    """
    Draws a fullscreen semi-transparent overlay.
    User drags to select a region.
    Returns (x, y, width, height) or None if cancelled.
    """

    def __init__(self):
        self._result = None
        self._cancelled = False

    def select(self) -> dict | None:
        """Show overlay and block until selection is made. Returns region dict or None."""
        self._result = None
        self._cancelled = False

        root = tk.Tk()
        root.title("Screen Agent")
        root.attributes("-fullscreen", True)
        root.attributes("-alpha", 0.3)
        root.attributes("-topmost", True)
        root.configure(bg="#0a0a1a")
        root.config(cursor="crosshair")

        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        canvas = tk.Canvas(
            root, bg="#0a0a1a",
            cursor="crosshair",
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)

        # --- Draw instruction text ---
        canvas.create_text(
            screen_w // 2, 30,
            text="🖱  Drag to select a region  •  ESC to cancel",
            fill="#00d4ff",
            font=("Segoe UI", 13, "bold"),
            tags="hint"
        )

        # State
        start = [0, 0]
        rect_id = [None]
        dim_text_id = [None]

        def on_press(event):
            start[0], start[1] = event.x, event.y
            if rect_id[0]:
                canvas.delete(rect_id[0])
            if dim_text_id[0]:
                canvas.delete(dim_text_id[0])
            rect_id[0] = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#ff0033",  # Bright Red
                width=4,            # Thicker border
                tags="selection"
            )

        def on_drag(event):
            if rect_id[0]:
                canvas.coords(rect_id[0], start[0], start[1], event.x, event.y)

            # Live dimension label
            w = abs(event.x - start[0])
            h = abs(event.y - start[1])
            x_mid = (start[0] + event.x) // 2
            y_bot = max(start[1], event.y) + 16

            if dim_text_id[0]:
                canvas.delete(dim_text_id[0])
            dim_text_id[0] = canvas.create_text(
                x_mid, y_bot,
                text=f"{w} × {h}",
                fill="#ffffff",
                font=("Segoe UI", 10, "bold"),
                tags="dims"
            )

        def on_release(event):
            x1 = min(start[0], event.x)
            y1 = min(start[1], event.y)
            x2 = max(start[0], event.x)
            y2 = max(start[1], event.y)

            if (x2 - x1) < 10 or (y2 - y1) < 10:
                # Too tiny — capture full screen
                self._result = {
                    "top": 0, "left": 0,
                    "width": screen_w, "height": screen_h
                }
            else:
                self._result = {
                    "top": y1, "left": x1,
                    "width": x2 - x1, "height": y2 - y1
                }
            root.destroy()

        def on_escape(event):
            self._cancelled = True
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Escape>", on_escape)

        root.mainloop()

        if self._cancelled:
            return None
        return self._result
