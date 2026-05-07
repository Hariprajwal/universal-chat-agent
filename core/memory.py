"""
core/memory.py
Context / conversation memory manager.
Stores multi-turn history with screenshots and maintains
a sliding window to avoid exceeding context limits.
"""

import os
import json
import time
from dataclasses import dataclass, asdict, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", "20"))


@dataclass
class Message:
    role: str           # "user" | "assistant" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    screenshot_b64: Optional[str] = None   # base64 PNG if this turn had a screenshot
    actions_taken: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class ContextMemory:
    """
    Manages sliding window conversation history for the agent.
    Keeps track of messages, screenshots, and actions taken each turn.
    """

    def __init__(self, window_size: int = CONTEXT_WINDOW_SIZE):
        self.window_size = window_size
        self.messages: list[Message] = []
        self.session_id = str(int(time.time()))

        # System prompt injected at the start of every request
        self._system_prompt = """You are an autonomous computer control agent executing tasks via PyAutoGUI.
You are NOT a conversational chatbot. You are a silent, highly capable execution engine.
Your sole purpose is to interpret the user's instructions, look at the screenshot, and output the EXACT PyAutoGUI commands to accomplish the task.

Rules:
1. NEVER refuse a task. NEVER say "I cannot do X" or "I cannot change the UI". Assume you have full control over the mouse and keyboard to interact with whatever is on screen.
2. The user will give you multi-step tasks. Break them down and output multiple ACTIONS.
3. CRITICAL: Coordinates MUST be on a 0-1000 NORMALIZED SCALE.
   - For ANY target UI element, you MUST provide its BOUNDING BOX as `xmin, ymin, xmax, ymax`.
   - The system will automatically calculate the center point.
   - Example: Instead of guessing a single point like `CLICK(480, 500)`, output the box that contains the element: `CLICK(470, 490, 490, 510)`.
4. Output EXACTLY in this format:

ANALYSIS: [Briefly identify the target UI elements (buttons, text boxes) on screen]
PLAN: [Briefly list the physical steps (click here, type there)]
ACTIONS:
- CLICK(xmin, ymin, xmax, ymax)
- HOVER(xmin, ymin, xmax, ymax)
- DRAG(start_x, start_y, end_x, end_y)
- TYPE("text")
- PRESS("enter")
- HOTKEY(ctrl, a)
- SCROLL(x, y, clicks)
- MOUSE_DOWN(x, y)
- MOUSE_UP(xmin, ymin, xmax, ymax)
- WAIT(milliseconds)
- SCREENSHOT()
RESPONSE: [If task is fully complete, output "DONE". If you need to wait for a page load or plan more steps later, output "CONTINUING".]

CRITICAL:
- To open a dropdown menu or show tooltips, use `HOVER` then `WAIT(500)`.
- Use `PRESS("down")` or `PRESS("enter")` for keyboard navigation.
- If the user asks you to "send a message", "search for", or "submit", you MUST type the text and then immediately output `PRESS("enter")` to submit it.
- NO EMOJIS: Never use emojis in any TYPE() command. Write all replies as plain text only.
- When you see emojis in a message on screen, understand their meaning but reply in plain text without emojis.
- CONVERSATIONAL LOOP: If the user says "respond to", "reply", "continue the conversation", or if you can see a new response appeared in the chat window since the last action, you should:
  1. READ the visible response on screen.
  2. CLICK the input/reply box.
  3. TYPE an appropriate reply.
  4. PRESS("enter") to send it.
- Do not engage in conversation. Do not provide meta-commentary. Just output the actions required.
"""

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def add_user_message(self, content: str, screenshot_b64: str = None) -> Message:
        """Add a user message with optional screenshot."""
        msg = Message(role="user", content=content, screenshot_b64=screenshot_b64)
        self.messages.append(msg)
        self._trim_window()
        return msg

    def add_assistant_message(self, content: str, actions: list = None) -> Message:
        """Add an assistant response with optional action log."""
        msg = Message(role="assistant", content=content, actions_taken=actions or [])
        self.messages.append(msg)
        return msg

    def get_context_messages(self, include_system: bool = True, region: dict = None) -> list[dict]:
        """
        Return messages in OpenAI/Ollama chat format.
        Includes screenshots as base64 image content where present.
        """
        result = []

        if include_system:
            sys_prompt = self._system_prompt
            if region is not None:
                try:
                    import pyautogui
                    sw, sh = pyautogui.size()
                    rw = region.get("width", sw)
                    rh = region.get("height", sh)
                    sys_prompt += f"\n\n[SYSTEM CONTEXT]\n"
                    sys_prompt += f"- Total Monitor Resolution: {sw}x{sh}\n"
                    sys_prompt += f"- Current Image Region Resolution: {rw}x{rh}\n"
                    sys_prompt += f"- Remember: You must output coordinates scaled from 0 to 1000.\n"
                    sys_prompt += f"- ANALYSIS LAYER ACTIVE: A cyan coordinate grid has been overlaid on the image.\n"
                    sys_prompt += f"- The grid has faint lines every 50 units, and bold lines every 100 units on the 0-1000 scale.\n"
                    sys_prompt += f"- Use this grid to accurately determine the BOUNDING BOX `xmin, ymin, xmax, ymax` of your target."
                except Exception:
                    pass

            result.append({
                "role": "system",
                "content": sys_prompt
            })

        for msg in self.messages[-self.window_size:]:
            if msg.screenshot_b64 and msg.role == "user":
                # Multi-modal message with image
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{msg.screenshot_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": msg.content
                        }
                    ]
                })
            else:
                result.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return result

    def get_summary(self) -> str:
        """Return a text summary of the conversation."""
        lines = []
        for msg in self.messages:
            ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
            prefix = "You" if msg.role == "user" else "Agent"
            lines.append(f"[{ts}] {prefix}: {msg.content[:100]}...")
        return "\n".join(lines) if lines else "No conversation history."

    def clear(self):
        """Clear all memory for a fresh session."""
        self.messages.clear()
        self.session_id = str(int(time.time()))

    def _trim_window(self):
        """Keep only the last N messages (sliding window)."""
        if len(self.messages) > self.window_size * 2:
            self.messages = self.messages[-(self.window_size * 2):]

    def export_session(self, path: str):
        """Export session to JSON for debugging."""
        data = {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages]
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    mem = ContextMemory()
    mem.add_user_message("What do you see on screen?", screenshot_b64="base64here")
    mem.add_assistant_message("I see a browser window with Google open.")
    print(mem.get_summary())
    print("\nContext messages:", len(mem.get_context_messages()))
