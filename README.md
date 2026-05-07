# ⚡ Screen Agent — Autonomous AI Desktop Co-Pilot

> **Select any region of your screen → Give a natural language instruction → Watch the AI do it for you.**

Screen Agent is a fully autonomous, vision-powered desktop automation tool. It captures a region of your screen, overlays a precision coordinate grid, sends the visual to a powerful AI model, and executes the resulting mouse clicks, keyboard inputs, scrolls, and drags — all without you lifting a finger.

---

## 🎯 What It Can Do

| Capability | Example |
|---|---|
| **Click anything** | *"Click the Submit button"* |
| **Type text** | *"Type my email address in the form"* |
| **Send messages** | *"Send a message saying Hello, how are you?"* — auto-presses Enter |
| **Search the web** | *"Search for Python tutorials on Google"* |
| **Fill forms** | *"Fill out the registration form with my details"* |
| **Scroll pages** | *"Scroll down to find the pricing section"* |
| **Drag & drop** | *"Drag the file to the uploads area"* |
| **Keyboard shortcuts** | *"Select all text and copy it"* |
| **Multi-step tasks** | *"Open a new tab, go to GitHub, and star the first repo"* |
| **Conversational loops** | *"Keep replying to the chat with relevant responses"* |

---

## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:

- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
- **Git** (optional, for cloning) — [Download here](https://git-scm.com/)

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Screen-agent.git
cd Screen-agent
```

Or just download the ZIP and extract it.

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Set Up Your API Key

The agent uses **OpenRouter** (free tier available) to access powerful vision AI models.

1. Get your free API key at [openrouter.ai](https://openrouter.ai)
2. Open the `.env` file in the project folder
3. Paste your key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_BACKEND=openrouter
```

---

### 4. Launch the Agent

```bash
python -W ignore main.py --now
```

That's it! The agent is now running.

---

## 🖥️ How to Use It

### Step 1 — Trigger the Screen Selector

Press the global hotkey:

```
Ctrl + Shift + S
```

Your screen will darken and a crosshair will appear.

### Step 2 — Select Your Region

Click and **drag a red selection box** around the area you want the agent to control (e.g., a browser window, a chat app, a form).

### Step 3 — Give an Instruction

The agent panel pops up. Type your instruction in plain English:

> *"Click the Plus icon next to the chat input and type Hello world, then send it."*

### Step 4 — Watch It Execute

The agent will:
1. Analyze the screenshot with the AI precision grid overlay
2. Plan the sequence of actions
3. Execute them step-by-step (click → type → scroll → etc.)
4. Automatically re-capture the screen to see the result
5. Continue with the next step if the task isn't finished

Press **⏹ Stop** at any time to interrupt execution.

---

## ⚙️ Configuration

All settings are in the `.env` file:

| Setting | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | Your OpenRouter API key |
| `DEFAULT_BACKEND` | `openrouter` | Use `openrouter` (cloud) or `ollama` (local) |
| `OPENROUTER_MODEL` | `auto` | Specific model or `auto` to pick best available |
| `OLLAMA_HOST` | `http://localhost:11434` | URL of your local Ollama server |
| `OLLAMA_MODEL` | `llava` | Default local vision model |
| `CONTEXT_WINDOW_SIZE` | `20` | How many messages to keep in memory |

---

## 🤖 AI Backends

### ☁️ OpenRouter (Default — Recommended)

Uses powerful cloud-hosted vision models. No local hardware needed.

1. Sign up at [openrouter.ai](https://openrouter.ai) (free credits available)
2. Copy your API key to `.env`
3. The agent auto-selects the best available vision model

### 🏠 Local Ollama (Privacy Mode)

Run 100% offline with your own hardware. Requires a GPU (8GB+ VRAM recommended).

1. Install [Ollama](https://ollama.ai)
2. Pull a vision model:
   ```bash
   ollama pull llava
   # or for better quality:
   ollama pull minicpm-v
   ```
3. Ollama starts **automatically** when Screen Agent launches — no need to run `ollama serve` manually!
4. Switch in `.env`:
   ```env
   DEFAULT_BACKEND=ollama
   ```

> **Note:** If local Ollama fails, the agent silently falls back to OpenRouter automatically.

---

## 🛠️ Advanced Launch Options

```bash
# Standard launch with system tray icon
python -W ignore main.py

# Launch the selector immediately (no tray)
python -W ignore main.py --now

# Safe mode - log actions but don't execute them
python -W ignore main.py --dry-run

# Disable system tray (hotkey only)
python -W ignore main.py --no-tray
```

### One-Click Launch (Windows)

Double-click **`launch.bat`** to start the agent in the background silently.

---

## 🏗️ Project Structure

```
Screen-agent/
├── main.py                  # Entry point — hotkey, tray, orchestration
├── launch.bat               # One-click Windows launcher
├── .env                     # Your API keys and config
├── requirements.txt         # Python dependencies
│
├── core/
│   ├── capture.py           # Screen region selector + analysis grid overlay
│   ├── executor.py          # Action parser & PyAutoGUI execution engine
│   └── memory.py            # Conversation memory + system prompt
│
├── backends/
│   ├── base.py              # Abstract backend interface
│   ├── manager.py           # Backend switcher with silent failover
│   ├── openrouter_backend.py# Cloud AI via OpenRouter API
│   └── ollama_backend.py    # Local AI via Ollama
│
└── ui/
    ├── agent_window.py      # Floating chat window (streaming, bubbles, controls)
    ├── overlay.py           # Fullscreen selection overlay (red highlight)
    └── tray.py              # Windows system tray icon
```

---

## 🔬 How It Works — Under the Hood

### 1. Visual Coordinate Grid
Every screenshot is processed by the **Analysis Grid Engine** (`core/capture.py`) before being sent to the AI. A 20×20 precision grid is overlaid on the image with faint lines every 50 units and bold lines every 100 units on a 0–1000 normalized scale. This gives the AI a **spatial ruler** to reference, dramatically improving targeting accuracy.

### 2. Bounding Box Coordinates
Instead of asking the AI to guess a single `(X, Y)` pixel, the agent instructs it to output a **bounding box** `[xmin, ymin, xmax, ymax]` around the target element. The execution engine then calculates the exact center of that box for the mouse click. This matches how modern AI vision models are trained (on object detection data), making coordinates far more accurate.

### 3. Normalized Coordinate System
All AI coordinates are in a **0–1000 normalized scale** (not raw pixels). The executor translates them to actual screen pixels using the captured region's real dimensions and monitor offset. This makes the system resolution-independent.

### 4. Autonomous Execution Loop
After each batch of actions, the agent automatically:
- Recaptures a fresh screenshot of the same region
- Checks if the task is complete (`RESPONSE: DONE`) or needs more steps (`RESPONSE: CONTINUING`)
- If continuing, silently feeds the new screenshot back to the AI for the next round of actions

This loop runs until the task is finished or you click Stop.

### 5. Streaming Response
The AI response streams token-by-token into the chat bubble in real time, so you can see the agent's reasoning (ANALYSIS, PLAN, ACTIONS) as it thinks.

---

## 🎮 Action Reference

The agent understands these commands:

| Action | Syntax | Description |
|---|---|---|
| Click | `CLICK(xmin, ymin, xmax, ymax)` | Left-click the center of a bounding box |
| Right-click | `RCLICK(xmin, ymin, xmax, ymax)` | Right-click |
| Double-click | `DCLICK(xmin, ymin, xmax, ymax)` | Double-click |
| Type | `TYPE("hello world")` | Type text at the current cursor position |
| Press key | `PRESS("enter")` | Press a keyboard key |
| Hotkey | `HOTKEY(ctrl, c)` | Press a key combination |
| Scroll | `SCROLL(x, y, clicks)` | Scroll up/down |
| Hover | `HOVER(xmin, ymin, xmax, ymax)` | Move mouse without clicking (opens tooltips/dropdowns) |
| Drag | `DRAG(sx, sy, ex, ey)` | Click-hold and drag |
| Wait | `WAIT(500)` | Wait N milliseconds |
| Screenshot | `SCREENSHOT()` | Force a new screenshot mid-task |

---

## 🧠 Tips for Best Results

1. **Select a tightly-cropped region** — Don't select your entire screen. Zoom into just the window or panel you want to control. Smaller = more accurate.

2. **Be explicit** — Instead of *"fill the form"*, say *"click the Name field and type John Doe, then click the Email field and type john@example.com"*.

3. **Use "send" or "search"** — The agent automatically presses Enter after typing when you say *"send a message"* or *"search for"*.

4. **For dropdowns** — Say *"click the dropdown and select the second option"*.

5. **Multi-step is fine** — *"Open Notepad, type Hello World, save the file as test.txt"* works as a single instruction.

---

## 🐛 Troubleshooting

### Agent can't find a button
- Try selecting a smaller, more focused region around just that button
- Describe the button more precisely: *"Click the blue button labeled 'Continue'"*

### Clicks are landing in the wrong place
- Make sure your selected region is exactly the window you want to control
- Don't move or resize the target window after selecting the region

### OpenRouter API errors
- Check your API key is correct in `.env`
- Verify you have credits at [openrouter.ai](https://openrouter.ai)

### Ollama not connecting
- Run `ollama pull llava` in a terminal first
- The agent will auto-start Ollama, but the model must be downloaded

---

## 📋 Requirements

```
Pillow>=10.0.0
pyautogui>=0.9.54
requests>=2.31.0
python-dotenv>=1.0.0
keyboard>=0.13.5
pystray>=0.19.5
mss>=9.0.1
```

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [PyAutoGUI](https://pyautogui.readthedocs.io/) — Mouse & keyboard automation
- [OpenRouter](https://openrouter.ai) — Unified AI API gateway
- [Ollama](https://ollama.ai) — Local LLM runner
- [Pillow](https://pillow.readthedocs.io/) — Image processing

---

<div align="center">
  <strong>Built with ❤️ — An autonomous AI agent for everyone.</strong>
</div>
