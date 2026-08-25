# ✈️ AI Travel Agent

A personal AI-powered travel agent that searches live flight and hotel prices, tracks fares over time, and sends you alerts when prices drop — all accessible via Telegram.

Built with Claude AI, SerpAPI, and Python.

---

## What it does

- **Search flights** — find real-time prices for any route in the world
- **Search hotels** — get live hotel options with prices and ratings
- **Price alerts** — tell it to watch a route and get emailed when fares drop below your threshold
- **Memory** — remembers your home airport, preferences, and past searches across sessions
- **Telegram interface** — chat with it from your phone like a real travel agent

---

## Example conversations

You: Find me flights to Dublin in March
Agent: Here are the best fares for SFO → DUB on March 4, 2027...

You: Watch this route and alert me when it drops below $700
Agent: Got it! I'll monitor SFO → DUB and email you when prices drop below $700.

You: What hotels do you recommend in Dublin for those dates?
Agent: Here are the top options in Dublin for March 4–18...


---

## Tech stack

- **AI** — [Claude API](https://anthropic.com) (claude-sonnet-4-6)
- **Flight & hotel data** — [SerpAPI](https://serpapi.com) (Google Flights + Google Hotels)
- **Notifications** — Gmail via SMTP
- **Interface** — Telegram Bot API
- **Memory** — JSON file (local persistence)
- **Scheduler** — macOS launchd (24hr price checks)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ruchirpipalia-spec/travel-agent.git
cd travel-agent
```

### 2. Install dependencies

```bash
pip3 install anthropic requests python-dotenv python-telegram-bot
```

### 3. Get your API keys

You need four API keys:

| Key | Where to get it |
|-----|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `SERPAPI_KEY` | [serpapi.com/dashboard](https://serpapi.com/dashboard) |
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/botfather) on Telegram |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | [Google App Passwords](https://myaccount.google.com/apppasswords) |

### 4. Create your .env file

```bash
touch .env
```

Add your keys:

    ANTHROPIC_API_KEY=your_key_here
    SERPAPI_KEY=your_key_here
    TELEGRAM_BOT_TOKEN=your_token_here
    GMAIL_ADDRESS=your@gmail.com
    GMAIL_APP_PASSWORD=your_app_password_here


### 5. Run the Telegram bot

```bash
python3 telegram_bot.py
```

Open Telegram, find your bot, and start chatting.

### 6. Run the price alert checker manually

```bash
python3 alerts.py
```

---

## Setting up automatic price checks (macOS)

To run price checks every 24 hours automatically in the background:

```bash
cat > ~/Library/LaunchAgents/com.travelagent.pricechecker.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.travelagent.pricechecker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/YOUR/PATH/TO/travel-agent/alerts.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/YOUR/PATH/TO/travel-agent</string>
    <key>StartInterval</key>
    <integer>86400</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/YOUR/PATH/TO/travel-agent/alerts.log</string>
    <key>StandardErrorPath</key>
    <string>/YOUR/PATH/TO/travel-agent/alerts.log</string>
</dict>
</plist>
EOF
```

Replace `/YOUR/PATH/TO/travel-agent` with your actual path, then:

```bash
launchctl load ~/Library/LaunchAgents/com.travelagent.pricechecker.plist
```

---

## Project structure

```
travel-agent/
├── agent.py          # Main chatbot logic, flight/hotel search, memory
├── alerts.py         # Background price checker and email alerts
├── memory.py         # Memory read/write functions
├── telegram_bot.py   # Telegram interface
├── .env              # API keys (never commit this)
└── .gitignore        # Keeps .env and memory.json off GitHub
```

---

## How it works

Your message goes to the Telegram bot → passed to Claude AI → Claude decides whether to search flights, hotels, or save a price alert → SerpAPI fetches live data → Claude formats the response → you get a reply in Telegram.

Price alerts are saved to `memory.json`. A separate scheduler runs `alerts.py` every 24 hours, checks current prices via SerpAPI, and sends a Gmail notification if any watched route drops below your threshold.

---

## Notes

- SerpAPI free tier includes 250 searches/month — enough for personal use with 24hr checking on a few routes
- The Telegram bot requires your terminal to be running locally, or deploy to Railway/Render for 24/7 uptime
- Memory is stored locally in `memory.json` — not synced across devices

---

## Built by

Ruchir Pipalia — built as a learning project starting from zero coding experience.
