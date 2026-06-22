# 🤖 Telegram Bot with Groq AI (100% Free)

A Telegram bot that replies like a real human using Groq's free LLaMA 3 API.

## ✨ Features
- **Human-like typing delays** — shows "typing..." for a realistic amount of time
- **Conversation memory** — remembers context within a session
- **Natural replies** — tuned to avoid robotic, formal responses
- **Multilingual** — responds in whatever language the user writes in
- **Free forever** — Groq API is free (very generous limits)

---

## 🚀 Setup (Step by Step)

### Step 1 — Get your Telegram Bot Token (Free)

1. Open Telegram → search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g. `My Smart Bot`)
4. Choose a username ending in `bot` (e.g. `mysmartgroq_bot`)
5. BotFather gives you a token like:
   ```
   7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Copy and save it

---

### Step 2 — Get your Groq API Key (Free)

1. Go to **https://console.groq.com**
2. Sign up (Google login works)
3. Go to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_...`)

Free tier limits (very generous):
- LLaMA 3.3 70B: **30 requests/min**, **14,400 req/day**
- No credit card needed

---

### Step 3 — Install & Configure

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Open bot.py and fill in your keys at the top:
TELEGRAM_TOKEN = "7123456789:AAFxxx..."   # ← paste here
GROQ_API_KEY   = "gsk_xxx..."             # ← paste here
```

---

### Step 4 — Run the Bot

```bash
python bot.py
```

You'll see:
```
🤖 Starting Telegram Bot with Groq AI...
   Model: llama-3.3-70b-versatile
   Press Ctrl+C to stop
```

Now open your Telegram bot and start chatting! 🎉

---

## 🧠 Customizing the Personality

In `bot.py`, edit the `SYSTEM_PROMPT` variable to change how the bot behaves:

```python
SYSTEM_PROMPT = """You are a friendly assistant who...
- talks like a friend, not a robot
- uses casual language
- ...
"""
```

**Ideas:**
- Customer support agent for your business
- Jain community helper bot (for jainsamaj.org!)
- Study buddy / tutor
- Personal assistant
- Any character/persona

---

## 🔄 Available Models (Free on Groq)

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `llama-3.3-70b-versatile` | Medium | ⭐⭐⭐⭐⭐ | Best overall (recommended) |
| `llama-3.1-8b-instant` | Fast | ⭐⭐⭐ | Quick responses |
| `gemma2-9b-it` | Fast | ⭐⭐⭐⭐ | Good alternative |
| `mixtral-8x7b-32768` | Medium | ⭐⭐⭐⭐ | Long context |

Change `GROQ_MODEL` in `bot.py` to switch.

---

## 📋 Bot Commands

| Command | What it does |
|---------|-------------|
| `/start` | Greet the bot |
| `/reset` | Clear conversation memory |
| `/help` | Show help |

---

## 🖥️ Running 24/7 (Free Options)

### Option A — Railway.app (Recommended, Free)
1. Push your code to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Set environment variables: `TELEGRAM_TOKEN` and `GROQ_API_KEY`
4. Done! Runs 24/7 free

### Option B — Render.com (Free)
1. Push to GitHub
2. Create a "Background Worker" on render.com
3. Add environment variables
4. Free tier: 750 hrs/month

### Option C — Your own PC/VPS
```bash
# Run in background with screen
screen -S telebot
python bot.py
# Press Ctrl+A then D to detach
```

---

## 📁 File Structure

```
telegram-groq-bot/
├── bot.py           ← Main bot (edit this)
├── requirements.txt ← Python packages
├── .env.example     ← Key template
└── README.md        ← This file
```

---

## ❓ Troubleshooting

**Bot not responding?**
- Make sure the bot is running (`python bot.py`)
- Check the token is correct (no extra spaces)
- Try `/start` first

**Groq errors?**
- Check your API key at console.groq.com
- Free tier is rate-limited — add a longer delay if needed

**"Conflict" error?**
- Only one instance of the bot can run at a time
- Kill other running instances first
