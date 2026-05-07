"""
ui/agent_window.py
Compact floating agent window — chat history, command input.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image

# Color palette
BG_DARK    = "#0d0d1a"
BG_PANEL   = "#13131f"
BG_INPUT   = "#1a1a2e"
BG_MSG_U   = "#1e2a45"
BG_MSG_A   = "#1a2810"
ACCENT     = "#00d4ff"
GREEN      = "#22c55e"
ORANGE     = "#f97316"
RED        = "#ef4444"
TEXT_MAIN  = "#e2e8f0"
TEXT_DIM   = "#64748b"
FONT_UI    = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI Semibold", 10)


class AgentWindow:
    """
    Compact agent interaction window.
    Shows chat and input. Remains always on top.
    """

    def __init__(self, screenshot: Image.Image, region: dict, memory, backend_manager):
        self.screenshot = screenshot
        self.region = region
        self.memory = memory
        self.backend_manager = backend_manager
        self._stop_flag = False
        self.root = None

    def show(self):
        """Launch the agent window (blocking)."""
        self.root = tk.Tk()
        self.root.title("⚡ Screen Agent")
        
        # Make it a compact, always-on-top tool window
        self.root.geometry("400x550")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG_DARK)
        self.root.minsize(300, 400)

        self._build_ui()
        self._apply_dark_scrollbars()
        self._load_history()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_ui(self):
        """Build all UI components."""
        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(self.root, bg=BG_PANEL, height=40)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        title_lbl = tk.Label(
            topbar, text="⚡ Screen Agent",
            bg=BG_PANEL, fg=ACCENT,
            font=FONT_TITLE
        )
        title_lbl.pack(side="left", padx=10, pady=8)

        # Backend toggle
        self._backend_var = tk.StringVar(value=self.backend_manager.current_name)
        
        # Simple text button to switch backend
        self._backend_btn = tk.Button(
            topbar, text=self.backend_manager.current_name.capitalize(),
            bg="#2a2a3e", fg=TEXT_MAIN, font=("Segoe UI", 8),
            relief="flat", cursor="hand2", padx=6, pady=2,
            command=self._toggle_backend
        )
        self._backend_btn.pack(side="right", padx=10, pady=8)

        # Status dot
        self._status_dot = tk.Label(topbar, text="●", bg=BG_PANEL,
                                    fg=GREEN, font=("Segoe UI", 12))
        self._status_dot.pack(side="right", padx=2)

        # Clear button
        clear_btn = tk.Button(
            topbar, text="🗑", bg=BG_PANEL, fg=TEXT_DIM,
            font=("Segoe UI", 10), relief="flat", cursor="hand2",
            command=self._clear_memory
        )
        clear_btn.pack(side="right", padx=2)

        # ── Chat area ───────────────────────────────────────
        chat_container = tk.Frame(self.root, bg=BG_PANEL, relief="flat", bd=0)
        chat_container.pack(fill="both", expand=True, padx=4, pady=4)

        self._chat_canvas = tk.Canvas(chat_container, bg=BG_PANEL, highlightthickness=0)
        chat_scroll = ttk.Scrollbar(chat_container, orient="vertical", command=self._chat_canvas.yview)
        self._chat_canvas.configure(yscrollcommand=chat_scroll.set)
        
        chat_scroll.pack(side="right", fill="y")
        self._chat_canvas.pack(side="left", fill="both", expand=True)

        self._messages_frame = tk.Frame(self._chat_canvas, bg=BG_PANEL)
        self._canvas_window = self._chat_canvas.create_window((0, 0), window=self._messages_frame, anchor="nw")
        
        self._messages_frame.bind(
            "<Configure>",
            lambda e: self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox("all"))
        )
        self._chat_canvas.bind(
            "<Configure>",
            lambda e: self._chat_canvas.itemconfig(self._canvas_window, width=e.width)
        )
        self._chat_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # ── Input area ───────────────────────────────────────
        input_frame = tk.Frame(self.root, bg=BG_INPUT, height=80)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        self._input_text = tk.Text(
            input_frame, bg=BG_INPUT, fg=TEXT_MAIN,
            font=("Segoe UI", 10), wrap="word",
            insertbackground=ACCENT, relief="flat",
            height=3, bd=0
        )
        self._input_text.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        self._input_text.insert("1.0", "Type instruction...")
        self._input_text.bind("<FocusIn>", self._on_input_focus)
        self._input_text.bind("<Return>", self._on_enter)

        btn_frame = tk.Frame(input_frame, bg=BG_INPUT)
        btn_frame.pack(side="right", padx=8, pady=8)

        self._send_btn = tk.Button(
            btn_frame, text="➤", bg=ACCENT, fg="#0d0d1a",
            font=("Segoe UI Semibold", 12), relief="flat", cursor="hand2",
            padx=12, pady=4, command=self._send_message
        )
        self._send_btn.pack(fill="x")

        self._stop_btn = tk.Button(
            btn_frame, text="⏹", bg=RED, fg="white",
            font=("Segoe UI Semibold", 12), relief="flat", cursor="hand2",
            padx=12, pady=0, command=self._stop_agent
        )
        self._stop_btn.pack(fill="x", pady=(2, 0))
        self._stop_btn.config(state="disabled")

        # Status bar
        self._status_bar = tk.Label(
            self.root, text="Ready. Area is continuously monitored.",
            bg=BG_PANEL, fg=TEXT_DIM, font=("Segoe UI", 8),
            anchor="w", pady=2
        )
        self._status_bar.pack(fill="x", side="bottom", padx=8)

    def _toggle_backend(self):
        """Toggle between OpenRouter and Ollama."""
        current = self.backend_manager.current_name
        new_backend = "ollama" if current == "openrouter" else "openrouter"
        self.backend_manager.switch(new_backend)
        self._backend_btn.config(text=new_backend.capitalize())
        self._set_status(f"Switched to {new_backend}", GREEN)

    def _load_history(self):
        for msg in self.memory.messages:
            if msg.role == "user":
                self._add_chat_bubble("You", msg.content, BG_MSG_U, ACCENT)
            elif msg.role == "assistant":
                self._add_chat_bubble("Agent", msg.content, BG_MSG_A, GREEN)

    def _add_chat_bubble(self, sender: str, text: str, bg_color: str, accent_color: str):
        bubble = tk.Frame(self._messages_frame, bg=bg_color, padx=8, pady=6)
        bubble.pack(fill="x", padx=6, pady=4)

        tk.Label(bubble, text=sender, bg=bg_color, fg=accent_color, 
                 font=("Segoe UI Semibold", 9)).pack(anchor="w")

        msg_text = tk.Text(
            bubble, bg=bg_color, fg=TEXT_MAIN, font=FONT_UI,
            wrap="word", relief="flat", bd=0, height=1
        )
        msg_text.insert("1.0", text)
        msg_text.config(state="disabled")
        
        line_count = int(msg_text.index("end-1c").split(".")[0])
        msg_text.config(height=min(line_count + 1, 20))
        msg_text.pack(fill="x", pady=(2, 0))

        self.root.after(50, self._scroll_chat_bottom)
        return bubble

    def _add_streaming_bubble(self, sender: str, bg_color: str, accent_color: str) -> tk.Text:
        bubble = tk.Frame(self._messages_frame, bg=bg_color, padx=8, pady=6)
        bubble.pack(fill="x", padx=6, pady=4)

        header = tk.Frame(bubble, bg=bg_color)
        header.pack(fill="x")
        
        tk.Label(header, text=sender, bg=bg_color, fg=accent_color, 
                 font=("Segoe UI Semibold", 9)).pack(side="left")

        self._typing_lbl = tk.Label(header, text=" ●●●", bg=bg_color, fg=TEXT_DIM, font=("Segoe UI", 9))
        self._typing_lbl.pack(side="left")

        msg_text = tk.Text(
            bubble, bg=bg_color, fg=TEXT_MAIN, font=FONT_UI,
            wrap="word", relief="flat", bd=0, height=2
        )
        msg_text.pack(fill="x", pady=(2, 0))
        return msg_text

    def _scroll_chat_bottom(self):
        self._chat_canvas.update_idletasks()
        self._chat_canvas.yview_moveto(1.0)

    def _on_mousewheel(self, event):
        self._chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_input_focus(self, event):
        if self._input_text.get("1.0", "end-1c") == "Type instruction...":
            self._input_text.delete("1.0", "end")

    def _on_enter(self, event):
        if event.state & 0x1:  # Shift held
            return None
        self._send_message()
        return "break"

    def _send_message(self):
        user_text = self._input_text.get("1.0", "end-1c").strip()
        if not user_text or user_text == "Type instruction...":
            return

        self._input_text.delete("1.0", "end")
        self._set_ui_busy(True)
        self._stop_flag = False

        self._add_chat_bubble("You", user_text, BG_MSG_U, ACCENT)

        from core.capture import image_to_base64
        screenshot_b64 = image_to_base64(self.screenshot)
        self.memory.add_user_message(user_text, screenshot_b64=screenshot_b64)

        agent_text_widget = self._add_streaming_bubble("Agent", BG_MSG_A, GREEN)
        full_response = [""]

        def on_chunk(chunk: str):
            if self._stop_flag: return
            full_response[0] += chunk
            agent_text_widget.config(state="normal")
            agent_text_widget.insert("end", chunk)
            agent_text_widget.config(state="disabled")
            line_count = int(agent_text_widget.index("end-1c").split(".")[0])
            agent_text_widget.config(height=min(line_count + 1, 30))
            self._scroll_chat_bottom()

        def run_agent():
            try:
                messages = self.memory.get_context_messages(region=self.region)
                self.backend_manager.stream(messages, on_chunk)

                if not self._stop_flag:
                    if hasattr(self, "_typing_lbl"):
                        self._typing_lbl.destroy()
                    self.memory.add_assistant_message(full_response[0], actions=[])
                    self.root.after(0, lambda: self._execute_response(full_response[0]))
            except Exception as e:
                self.root.after(0, lambda: self._add_chat_bubble("System", f"❌ Error: {str(e)}", "#2d0a0a", RED))
                self.root.after(0, lambda: self._set_status("Error occurred", RED))
            finally:
                self.root.after(0, lambda: self._set_ui_busy(False))

        self._set_status("Agent thinking...", ORANGE)
        threading.Thread(target=run_agent, daemon=True).start()

    def _execute_response(self, response_text: str):
        from core.executor import ActionExecutor

        def log_action(msg: str):
            self.root.after(0, lambda: self._set_status(msg, ORANGE))

        executor = ActionExecutor(
            dry_run=False, 
            on_action=log_action,
            offset_x=self.region.get("left", 0),
            offset_y=self.region.get("top", 0),
            region_w=self.region.get("width", 1000),
            region_h=self.region.get("height", 1000)
        )
        actions = executor.parse_response(response_text)
        
        if not actions:
            self._set_status("Ready.", GREEN)
            return

        def run_actions():
            result = executor.execute(actions)
            if result.needs_screenshot:
                self.root.after(500, self._auto_recapture)
            else:
                # Default to recapture anyway so it constantly sees the live area
                self.root.after(500, self._auto_recapture)
                
            status = "✅ Actions completed" if result.success else f"⚠ {len(result.errors)} errors"
            self.root.after(0, lambda: self._set_status(status, GREEN if result.success else RED))

        threading.Thread(target=run_actions, daemon=True).start()

    def _auto_recapture(self):
        """Auto-capture a fresh screenshot of the *same region*."""
        try:
            from core.capture import RegionSelector
            selector = RegionSelector()
            # Capture exactly the same region again!
            img = selector._capture_region(self.region)
            self.screenshot = img
            self._set_status("Area recaptured ✓", GREEN)
        except Exception as e:
            self._set_status(f"Recapture failed: {e}", RED)

    def _clear_memory(self):
        if messagebox.askyesno("Clear", "Clear conversation history?"):
            self.memory.clear()
            for widget in self._messages_frame.winfo_children():
                widget.destroy()
            self._set_status("Memory cleared", ORANGE)

    def _stop_agent(self):
        self._stop_flag = True
        self._set_status("Stopped", RED)

    def _set_ui_busy(self, busy: bool):
        self._send_btn.config(state="disabled" if busy else "normal")
        self._stop_btn.config(state="normal" if busy else "disabled")
        self._status_dot.config(fg=ORANGE if busy else GREEN)

    def _set_status(self, msg: str, color: str = TEXT_DIM):
        self._status_bar.config(text=msg, fg=color)

    def _apply_dark_scrollbars(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar", background=BG_INPUT, troughcolor=BG_PANEL, arrowcolor=TEXT_DIM)

    def _on_close(self):
        self._stop_flag = True
        self.root.destroy()
