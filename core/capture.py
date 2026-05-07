"""
core/capture.py
Screen region selector — draws a fullscreen transparent tkinter overlay
for drag-to-select, then captures via mss.
"""

import tkinter as tk
from tkinter import ttk
import mss
import mss.tools
from PIL import Image, ImageTk
import io
import base64
import threading


class RegionSelector:
    """
    Fullscreen overlay for drag-to-select screen region.
    Returns a PIL Image of the captured area.
    """

    def __init__(self):
        self.result_image: Image.Image | None = None
        self.result_region: dict | None = None
        self._start_x = 0
        self._start_y = 0
        self._rect_id = None
        self._cancelled = False

    def select_region(self) -> tuple[Image.Image | None, dict | None]:
        """Block until user selects a region. Returns (PIL Image, Region Dict) or (None, None)."""
        self._cancelled = False
        self.result_image = None

        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-alpha", 0.25)
        root.attributes("-topmost", True)
        root.configure(bg="black")
        root.config(cursor="crosshair")
        root.title("Chat Agent — Select Region")

        canvas = tk.Canvas(root, bg="black", cursor="crosshair",
                           highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Instruction label
        label = canvas.create_text(
            root.winfo_screenwidth() // 2, 40,
            text="Drag to select a region  •  ESC to cancel",
            fill="white",
            font=("Segoe UI", 14, "bold")
        )

        rect_id = [None]
        start = [0, 0]

        def on_press(event):
            start[0], start[1] = event.x, event.y
            if rect_id[0]:
                canvas.delete(rect_id[0])
            rect_id[0] = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#00d4ff", width=2, dash=(6, 3)
            )

        def on_drag(event):
            if rect_id[0]:
                canvas.coords(rect_id[0], start[0], start[1], event.x, event.y)

        def on_release(event):
            x1 = min(start[0], event.x)
            y1 = min(start[1], event.y)
            x2 = max(start[0], event.x)
            y2 = max(start[1], event.y)

            if (x2 - x1) < 10 or (y2 - y1) < 10:
                # Too small — treat as full screen
                x1, y1, x2, y2 = 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()

            self.result_region = {"top": y1, "left": x1,
                                  "width": x2 - x1, "height": y2 - y1}
            root.destroy()

        def on_escape(event):
            self._cancelled = True
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Escape>", on_escape)

        root.mainloop()

        if self._cancelled or not self.result_region:
            return None, None

        # Capture the selected region
        return self._capture_region(self.result_region), self.result_region

    def _capture_region(self, region: dict) -> Image.Image:
        """Capture a specific screen region using mss."""
        with mss.mss() as sct:
            screenshot = sct.grab(region)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

    def capture_fullscreen(self) -> Image.Image:
        """Capture the entire screen."""
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img


def image_to_base64(img: Image.Image, max_size: tuple = (1280, 720)) -> str:
    """Convert PIL Image to base64 string, resizing if needed."""
    img.thumbnail(max_size, Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def draw_analysis_grid(img: Image.Image) -> Image.Image:
    """Draws a 10x10 coordinate grid on the image to act as a visual scaffold for VLMs."""
    from PIL import ImageDraw
    grid_img = img.copy()
    draw = ImageDraw.Draw(grid_img, "RGBA")
    w, h = img.size
    
    cols, rows = 20, 20
    line_color = (0, 212, 255, 60)   # Fainter cyan for dense grid
    major_line_color = (0, 212, 255, 180) # Stronger cyan for 10x10 marks
    text_color = (255, 255, 255, 255)
    text_bg = (0, 0, 0, 200)
    
    for i in range(1, cols):
        x = int(w * (i / cols))
        is_major = (i % 2 == 0)
        draw.line([(x, 0), (x, h)], fill=major_line_color if is_major else line_color, width=1)
        if is_major:
            label = str(int((i / cols) * 1000))
            draw.rectangle([x-14, 0, x+14, 12], fill=text_bg)
            draw.text((x-10, 0), label, fill=text_color)
            draw.rectangle([x-14, h-12, x+14, h], fill=text_bg)
            draw.text((x-10, h-12), label, fill=text_color)
        
    for i in range(1, rows):
        y = int(h * (i / rows))
        is_major = (i % 2 == 0)
        draw.line([(0, y), (w, y)], fill=major_line_color if is_major else line_color, width=1)
        if is_major:
            label = str(int((i / rows) * 1000))
            draw.rectangle([0, y-6, 26, y+6], fill=text_bg)
            draw.text((2, y-6), label, fill=text_color)
            draw.rectangle([w-26, y-6, w, y+6], fill=text_bg)
            draw.text((w-24, y-6), label, fill=text_color)

    # Center crosshairs
    for i in range(cols):
        for j in range(rows):
            cx = int(w * ((i + 0.5) / cols))
            cy = int(h * ((j + 0.5) / rows))
            draw.line([(cx-2, cy), (cx+2, cy)], fill=line_color, width=1)
            draw.line([(cx, cy-2), (cx, cy+2)], fill=line_color, width=1)

    return grid_img


if __name__ == "__main__":
    selector = RegionSelector()
    print("Select a region on screen...")
    img = selector.select_region()
    if img:
        print(f"Captured: {img.size}")
        img.save("test_capture.png")
        print("Saved to test_capture.png")
    else:
        print("Cancelled.")
