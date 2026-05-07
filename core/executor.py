"""
core/executor.py
PyAutoGUI action executor.
Parses structured AI response text and executes mouse/keyboard actions.
"""

import re
import time
import pyautogui
import pyperclip
from dataclasses import dataclass
from typing import Callable, Optional

# Safety settings
pyautogui.FAILSAFE = True       # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.15          # Small pause between actions

# Regex patterns for action parsing
ACTION_PATTERNS = {
    "CLICK":      re.compile(r"CLICK\((\d+),\s*(\d+)\)"),
    "RCLICK":     re.compile(r"RCLICK\((\d+),\s*(\d+)\)"),
    "DCLICK":     re.compile(r"DCLICK\((\d+),\s*(\d+)\)"),
    "TYPE":       re.compile(r'TYPE\("((?:[^"\\]|\\.)*)"\)'),
    "HOTKEY":     re.compile(r"HOTKEY\(([^)]+)\)"),
    "SCROLL":     re.compile(r"SCROLL\((\d+),\s*(\d+),\s*(-?\d+)\)"),
    "WAIT":       re.compile(r"WAIT\((\d+)\)"),
    "SCREENSHOT": re.compile(r"SCREENSHOT\(\)"),
    "NONE":       re.compile(r"NONE"),
}


@dataclass
class Action:
    action_type: str
    args: tuple
    raw: str

    def __str__(self):
        return f"{self.action_type}({', '.join(str(a) for a in self.args)})"


@dataclass
class ExecutionResult:
    success: bool
    actions_executed: list[str]
    errors: list[str]
    needs_screenshot: bool = False


class ActionExecutor:
    """
    Parses and executes structured actions from AI response.
    Supports dry-run mode for testing without actual mouse movement.
    """

    def __init__(self, dry_run: bool = False,
                 on_action: Optional[Callable[[str], None]] = None,
                 offset_x: int = 0,
                 offset_y: int = 0,
                 region_w: int = 1000,
                 region_h: int = 1000):
        """
        Args:
            dry_run: If True, log actions but don't execute them.
            on_action: Callback called before each action executes (for UI logging).
            offset_x: X offset to add to parsed coordinates (from cropped screen region).
            offset_y: Y offset to add to parsed coordinates.
            region_w: Actual width of the cropped region (for 0-1000 un-normalization).
            region_h: Actual height of the cropped region.
        """
        self.dry_run = dry_run
        self.on_action = on_action  # e.g., lambda msg: ui.log(msg)
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.region_w = region_w
        self.region_h = region_h

    def _unnormalize(self, nx: int, ny: int) -> tuple[int, int]:
        """Convert 0-1000 scale coordinate back to absolute screen pixel."""
        # Calculate relative pixel in the cropped image
        rx = int((nx / 1000.0) * self.region_w)
        ry = int((ny / 1000.0) * self.region_h)
        # Add the screen offset
        return rx + self.offset_x, ry + self.offset_y

    def parse_response(self, response_text: str) -> list[Action]:
        """Extract structured actions from AI response text."""
        actions = []

        # Find the ACTIONS: block
        actions_block = ""
        if "ACTIONS:" in response_text:
            parts = response_text.split("ACTIONS:")
            if len(parts) > 1:
                # Take text until next major section
                block = parts[1]
                for stop_marker in ["RESPONSE:", "ANALYSIS:", "PLAN:"]:
                    if stop_marker in block:
                        block = block.split(stop_marker)[0]
                actions_block = block

        if not actions_block:
            return actions

        for line in actions_block.strip().splitlines():
            line = line.strip().lstrip("- ").strip()
            if not line:
                continue

            parsed = self._parse_action_line(line)
            if parsed:
                actions.append(parsed)

        return actions

    def _parse_action_line(self, line: str) -> Optional[Action]:
        """Parse a single action line into an Action object."""
        for action_type, pattern in ACTION_PATTERNS.items():
            match = pattern.search(line)
            if match:
                return Action(
                    action_type=action_type,
                    args=match.groups(),
                    raw=line
                )
        return None

    def execute(self, actions: list[Action]) -> ExecutionResult:
        """Execute a list of parsed actions."""
        executed = []
        errors = []
        needs_screenshot = False

        for action in actions:
            try:
                self._log(f"▶ {action}")
                if not self.dry_run:
                    result = self._execute_single(action)
                    if result == "SCREENSHOT":
                        needs_screenshot = True
                else:
                    self._log(f"  [DRY RUN] Skipped execution")
                executed.append(str(action))
            except Exception as e:
                err_msg = f"❌ {action}: {str(e)}"
                errors.append(err_msg)
                self._log(err_msg)

        return ExecutionResult(
            success=len(errors) == 0,
            actions_executed=executed,
            errors=errors,
            needs_screenshot=needs_screenshot
        )

    def execute_from_response(self, response_text: str) -> ExecutionResult:
        """Parse and execute actions from a raw AI response string."""
        actions = self.parse_response(response_text)
        if not actions:
            return ExecutionResult(success=True, actions_executed=[], errors=[])
        return self.execute(actions)

    def _execute_single(self, action: Action) -> Optional[str]:
        """Execute a single action. Returns 'SCREENSHOT' if re-capture needed."""
        atype = action.action_type
        args = action.args

        if atype == "NONE":
            return None

        elif atype == "CLICK":
            x, y = self._unnormalize(int(args[0]), int(args[1]))
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.click(x, y)

        elif atype == "RCLICK":
            x, y = self._unnormalize(int(args[0]), int(args[1]))
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.rightClick(x, y)

        elif atype == "DCLICK":
            x, y = self._unnormalize(int(args[0]), int(args[1]))
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.doubleClick(x, y)

        elif atype == "TYPE":
            text = args[0].replace("\\n", "\n").replace("\\t", "\t")
            # Use clipboard paste for speed + unicode support
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")

        elif atype == "HOTKEY":
            keys = [k.strip() for k in args[0].split(",")]
            pyautogui.hotkey(*keys)

        elif atype == "SCROLL":
            x, y = self._unnormalize(int(args[0]), int(args[1]))
            clicks = int(args[2])
            pyautogui.scroll(clicks, x=x, y=y)

        elif atype == "WAIT":
            ms = int(args[0])
            time.sleep(ms / 1000.0)

        elif atype == "SCREENSHOT":
            return "SCREENSHOT"

        return None

    def _log(self, msg: str):
        """Log action via callback or print."""
        if self.on_action:
            self.on_action(msg)
        else:
            print(msg)

    @staticmethod
    def extract_section(response_text: str, section: str) -> str:
        """Extract a named section (ANALYSIS, PLAN, RESPONSE) from AI output."""
        sections = ["ANALYSIS:", "PLAN:", "ACTIONS:", "RESPONSE:"]
        start_marker = f"{section}:"
        if start_marker not in response_text:
            return ""

        start = response_text.index(start_marker) + len(start_marker)
        text = response_text[start:]

        # Find next section
        for other in sections:
            if other != start_marker and other in text:
                text = text[:text.index(other)]

        return text.strip()


if __name__ == "__main__":
    sample_response = """
ANALYSIS: I see a login form with username and password fields.
PLAN:
1. Click the username field
2. Type the username
3. Click the password field
4. Type the password
5. Click login button

ACTIONS:
- CLICK(640, 300)
- TYPE("testuser@example.com")
- HOTKEY(tab)
- TYPE("password123")
- CLICK(640, 450)
- SCREENSHOT()

RESPONSE: I'll fill in the login form with the test credentials now.
"""

    executor = ActionExecutor(dry_run=True)
    actions = executor.parse_response(sample_response)
    print(f"Parsed {len(actions)} actions:")
    for a in actions:
        print(f"  {a}")

    result = executor.execute(actions)
    print(f"\nResult: {result}")
