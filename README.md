<div align="center">

# 💬 Chat Agent

### The AI That Texts Back For You

**An open-source, vision-powered AI agent that reads your screen and replies to messages on WhatsApp, Slack, Telegram, Discord — like a real human would.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![OpenRouter](https://img.shields.io/badge/Powered%20by-OpenRouter-purple?style=flat-square)](https://openrouter.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square&logo=windows)](https://microsoft.com/windows)

</div>

---

## 🤔 What Is Chat Agent?

**Chat Agent is a GUI-based AI bot that lives on your desktop.** It watches any window you point it at — WhatsApp Web, Slack, Telegram Desktop, Discord, iMessage — and automatically reads and responds to incoming messages like a real human being.

No APIs. No browser extensions. No app integrations. It works at the **pixel level** — it sees your screen the same way you do, and it types on your behalf.

Think of it as having a **virtual you** that keeps your chats alive when you're busy.

> 🎯 **Core use case:** Open WhatsApp Web. Select the chat window. Turn on Watch Mode. Walk away. Chat Agent reads every message and replies naturally, contextually, and in plain human language — 24/7.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 👁 **Watch Mode** | Passively monitors any chat window and auto-replies to new messages |
| 🧠 **Vision AI** | Uses multimodal AI to actually *read* what's on your screen |
| 💬 **Human-like Replies** | Trained to write like a real person — no "Certainly!" or "As an AI..." ever |
| 🖱️ **Full Desktop Control** | Clicks, types, scrolls, drags — full PyAutoGUI-powered automation |
| ⚡ **Autonomous Loop** | Executes multi-step tasks without stopping until the job is done |
| 🔄 **Silent Failover** | OpenRouter (cloud) by default, local Ollama as optional privacy mode |
| 🚀 **Auto-launches Ollama** | If configured for local mode, starts Ollama automatically on boot |
| 📱 **Platform Agnostic** | Works with any desktop chat app — WhatsApp, Slack, Telegram, Discord, Teams |

---

## 🎬 How It Works — The 30-Second Version

```
1. You press Ctrl+Shift+S
2. You drag a box around your chat window
3. Chat Agent captures the screen
4. It sends the screenshot to a vision AI model
5. The AI reads the message and decides what to type
6. Chat Agent clicks the input box and types the reply
7. It hits Enter to send
8. It watches for the next message and repeats — forever
```

All of this happens in the background. You don't touch anything.

---

## 🚀 Quick Start

### Step 1 — Clone the repo

```bash
git clone https://github.com/your-username/chat-agent.git
cd chat-agent
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Get a free API key

Chat Agent uses [OpenRouter](https://openrouter.ai) to access vision AI models.
Sign up free → copy your key → paste it in `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_BACKEND=openrouter
```

> 💡 OpenRouter has a free tier. You don't need a credit card to get started.

### Step 4 — Launch

```bash
python -W ignore main.py --now
```

> **⚠️ Watch Mode must be active for the agent to auto-reply to messages.** After selecting your chat window, click the `👁 Watch` button in the top bar of the agent panel. It turns green when active. Without Watch Mode ON, the agent won't respond automatically.

---

## 👁 Watch Mode — The Core Feature

Watch Mode is what makes Chat Agent special. It's a passive screen monitor that keeps running in the background, watching for new messages.

### How to enable it:

1. Press `Ctrl + Shift + S`
2. Drag a selection box around your chat window (WhatsApp, Slack, etc.)
3. Optionally type a context message like:
   > *"You are me. Respond to these WhatsApp messages naturally."*
4. Click the **`👁 Watch`** button — it turns **green**
5. That's it. Leave it running.

### What happens next:

- Every **1.5 seconds**, the agent captures the **bottom 35%** of your selected window (where new messages always appear) using ultra-fast `mss` screen capture
- When a new message arrives, it **waits 4 seconds** (debounce) to collect all messages the person sent before composing a reply
- The AI sees the **full conversation** for context, then writes a reply in plain, human-sounding language
- It sends **1 or 2 messages** per trigger (decided dynamically based on what feels natural)
- After sending, it resets and resumes watching — **no manual action required**
- Click **⏹ Stop** or the green Watch button again to disable

### Watch Mode settings at a glance:

| Parameter | Value |
|---|---|
| Capture method | `mss` (fastest Python screen capture) |
| Capture region | Bottom 35% of selected window |
| Change detection | MD5 hash of 32×32 grayscale thumbnail |
| Poll interval | 1.5 seconds |
| Debounce wait | 4 seconds |
| Replies per message | 1–2 (AI decides) |
| Reply tone | Casual, human, plain text — no emojis |
| Auto-reset after reply | Yes (5 second cooldown) |
| Stuck/crash recovery | Automatic |

---

## 💬 Supported Platforms

Chat Agent works on **any desktop app** because it operates at the pixel level — not through APIs or browser plugins.

| Platform | Desktop App Required? | Notes |
|---|---|---|
| **WhatsApp** | WhatsApp Web (browser) | Works perfectly |
| **Telegram** | Telegram Desktop | Works perfectly |
| **Slack** | Slack Desktop or Web | Works perfectly |
| **Discord** | Discord App or Web | Works perfectly |
| **Microsoft Teams** | Teams Desktop | Works perfectly |
| **Instagram DMs** | Browser | Works |
| **Facebook Messenger** | Browser | Works |
| **iMessage** | Only on Mac | Works on Mac with minor setup |
| **Signal** | Signal Desktop | Works |
| **Any text chat** | — | If you can see it, Chat Agent can read it |

---

## 🧠 The AI Behind It

### Why vision AI?

Traditional chatbots use APIs and webhooks. Chat Agent uses **multimodal vision models** — the same technology behind GPT-4o's image understanding. Instead of integrating with each platform's API (which requires registration, approval, and maintenance), Chat Agent just *looks at your screen*.

This means:
- ✅ Works on **any platform** without any integration
- ✅ Reads the **full conversation context** visually
- ✅ Sees UI changes in **real time**
- ✅ No account access, no tokens, no scopes

### Coordinate Grid System

Every screenshot is overlaid with a **20×20 precision grid** before being sent to the AI. The grid uses a 0–1000 normalized coordinate system with:
- Faint lines every 50 units
- Bold lines every 100 units

This gives the AI a spatial ruler so it can pinpoint UI elements like input boxes, send buttons, and message bubbles with high accuracy.

### Bounding Box Targeting

Instead of clicking a single `(X, Y)` pixel (which is error-prone), the AI outputs a **bounding box** `[xmin, ymin, xmax, ymax]` around the target element. The executor calculates the center of the box and clicks there. This is how modern vision models are trained — on object detection data — making it naturally more accurate.

---

## 🤖 Human-Like Replies

Chat Agent is specifically tuned to **not sound like an AI**. The system prompt explicitly instructs the model to:

- Write casually, like a real person texting
- Use contractions naturally ("I'm", "it's", "that's")
- Vary sentence length for a natural rhythm
- **Never** use phrases like *"Certainly!", "Of course!", "I understand your concern", "As an AI..."*
- Keep replies appropriately short or long based on context
- Match the energy of the conversation (brief reply to a brief message, fuller reply to a detailed question)

---

## ⚙️ Configuration

All settings live in the `.env` file:

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Backend: openrouter (cloud) or ollama (local)
DEFAULT_BACKEND=openrouter

# Optional: pin a specific model
OPENROUTER_MODEL=auto

# Local Ollama settings (if using local mode)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llava

# Memory: how many messages to keep in context
CONTEXT_WINDOW_SIZE=20
```

---

## 🏠 Local Mode (Privacy-First)

If you want **100% offline** operation with no data leaving your machine:

1. Install [Ollama](https://ollama.ai)
2. Pull a vision-capable model:
   ```bash
   ollama pull llava
   # Better quality:
   ollama pull minicpm-v
   ```
3. Update `.env`:
   ```env
   DEFAULT_BACKEND=ollama
   ```
4. Launch normally — Chat Agent **auto-starts Ollama** in the background if it isn't already running

> If Ollama fails for any reason (model not found, too slow, etc.), Chat Agent silently falls back to OpenRouter without interrupting the session.

---

## 🛠️ All Launch Options

```bash
# Standard launch (system tray + hotkey)
python -W ignore main.py

# Launch selector immediately — recommended for quick use
python -W ignore main.py --now

# Safe mode — log actions without executing
python -W ignore main.py --dry-run

# Hotkey only, no system tray
python -W ignore main.py --no-tray
```

**One-click launch on Windows:** Double-click `launch.bat`

**Global hotkey:** `Ctrl + Shift + S` — works from anywhere on your desktop

---

## 🏗️ Architecture

```
chat-agent/
├── main.py                     # Entry point, hotkey, tray, orchestration
├── launch.bat                  # One-click Windows launcher
├── .env                        # API keys and configuration
├── requirements.txt            # Python dependencies
│
├── core/
│   ├── capture.py              # Region selector + 20x20 analysis grid overlay
│   ├── executor.py             # Action parser + PyAutoGUI execution engine
│   └── memory.py               # Sliding window memory + system prompt
│
├── backends/
│   ├── base.py                 # Abstract backend interface
│   ├── manager.py              # Backend switcher + silent failover
│   ├── openrouter_backend.py   # Cloud AI via OpenRouter
│   └── ollama_backend.py       # Local AI via Ollama (auto-start)
│
└── ui/
    ├── agent_window.py         # Floating chat panel (streaming, Watch Mode)
    ├── overlay.py              # Fullscreen region selector overlay
    └── tray.py                 # Windows system tray icon
```

---

## 🎮 Full Action Reference

The AI can execute any of these actions on your screen:

| Action | Syntax | What it does |
|---|---|---|
| Left click | `CLICK(xmin, ymin, xmax, ymax)` | Clicks the center of the bounding box |
| Right click | `RCLICK(xmin, ymin, xmax, ymax)` | Right-click |
| Double click | `DCLICK(xmin, ymin, xmax, ymax)` | Double-click |
| Type text | `TYPE("your text here")` | Types via clipboard paste (supports all Unicode) |
| Press key | `PRESS("enter")` | Press any keyboard key |
| Key combo | `HOTKEY(ctrl, c)` | Press a keyboard shortcut |
| Scroll | `SCROLL(x, y, clicks)` | Scroll the mouse wheel |
| Hover | `HOVER(xmin, ymin, xmax, ymax)` | Move mouse (opens tooltips/dropdowns) |
| Drag | `DRAG(sx, sy, ex, ey)` | Click-hold and drag |
| Wait | `WAIT(500)` | Pause for N milliseconds |
| Screenshot | `SCREENSHOT()` | Force re-capture mid-task |

---

## 💡 Tips & Best Practices

### For Watch Mode (Auto-Reply)

1. **Select only the chat panel** — not your entire browser window. The smaller the region, the faster and more accurate the detection.

2. **Give context first** — Before enabling Watch Mode, type a short description:
   > *"This is my WhatsApp. Reply as me. Keep it casual and friendly."*

3. **Watch Mode must be ON** — Click the `👁 Watch` button and confirm it turns green before stepping away. Nothing auto-replies unless Watch Mode is active.

4. **Don't switch windows** — Keep the chat app visible and in the foreground so the screen capture region stays accurate.

### For Manual Tasks

5. **Be specific in your instructions** — *"Click the blue Send button"* works better than *"send it"*.

6. **Chained tasks work great** — *"Open a new tab, go to google.com, search for Python tutorials, and click the first result"* executes as one instruction.

7. **Auto-Enter is built in** — Saying *"search for X"* or *"send a message saying Y"* automatically presses Enter after typing.

---

## 🐛 Troubleshooting

### Watch Mode isn't responding to messages

- ✅ Make sure the `👁 Watch` button is **green** (active)
- ✅ Your chat window must be **visible on screen** (not minimized)
- ✅ Select only the chat panel — not the entire desktop
- 🔍 Check the terminal for `[Watch]` debug logs to trace what's happening

### Agent clicks in the wrong place

- Select a smaller, tighter region around the target window
- Don't move or resize the target window after selecting the region

### OpenRouter errors

- Verify your `OPENROUTER_API_KEY` in `.env`
- Check your credits at [openrouter.ai](https://openrouter.ai)

### Local Ollama not working

- Run `ollama pull llava` first to download the model
- The agent auto-starts Ollama, but the model file must exist locally
- Check that your GPU has enough VRAM (8GB+ recommended for llava)

---

## 📦 Requirements

```
Pillow>=10.0.0
pyautogui>=0.9.54
requests>=2.31.0
python-dotenv>=1.0.0
keyboard>=0.13.5
pystray>=0.19.5
mss>=9.0.1
pyperclip>=1.8.2
```

Install all at once:
```bash
pip install -r requirements.txt
```

---

## 🤝 Contributing

Pull requests are welcome! Areas where contributions would be especially valuable:

- 🌍 **Multi-language support** — Better handling of non-English chat conversations
- 🧪 **Test suite** — Unit tests for the executor and parser
- 🎨 **UI improvements** — Better dark theme, resizable window, chat history export
- 📱 **Platform-specific tuning** — Optimized region presets for WhatsApp, Slack, etc.
- 🔧 **Config UI** — A settings panel instead of editing `.env` directly

---

## 📝 License

MIT License — free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [PyAutoGUI](https://pyautogui.readthedocs.io/) — Cross-platform mouse & keyboard automation
- [OpenRouter](https://openrouter.ai) — Unified API for 100+ AI models
- [Ollama](https://ollama.ai) — Run large language models locally
- [Pillow](https://pillow.readthedocs.io/) — Image processing
- [mss](https://python-mss.readthedocs.io/) — Ultra-fast cross-platform screen capture

---

<div align="center">

**If Chat Agent saved you time, give it a ⭐ — it helps others find it!**

Made with ❤️ — An autonomous AI that chats like a human.

</div>
