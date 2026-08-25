# ✈️ AI Travel Agent

A personal AI-powered travel agent that searches live flight and hotel prices, tracks fares over time, and sends you alerts when prices drop — all accessible via Telegram.

Built with Claude AI, SerpAPI, and Python. Started from zero coding experience.

---

## What it does

- **Search flights** — find real-time prices for any route in the world
- **Search hotels** — get live hotel options with prices and ratings
- **Price alerts** — tell it to watch a route and get emailed when fares drop below your threshold
- **Memory** — remembers your home airport, preferences, and past searches across sessions
- **Telegram interface** — chat with it from your phone like a real travel agent
- **24/7 cloud** — runs on Railway, always online even when your laptop is off

---

## Example conversations

You: Find me flights to Dublin in March
Agent: Here are the best fares for SFO → DUB on March 4, 2027...

You: Watch this route and alert me when it drops below $700
Agent: Got it! I'll monitor SFO → DUB and email you when prices drop below $700.

You: What hotels do you recommend in Dublin for those dates?
Agent: Here are the top options in Dublin for March 4–18...

You: Actually change my alert to under $650
Agent: Done! Updated your Dublin alert to below $650.


---

## Tech stack

- **AI** — [Claude API](https://anthropic.com) (claude-sonnet-4-6)
- **Flight & hotel data** — [SerpAPI](https://serpapi.com) (Google Flights + Google Hotels)
- **Memory** — [Supabase](https://supabase.com) (cloud database, persists across sessions)
- **Notifications** — Gmail via SMTP
- **Interface** — Telegram Bot API
- **Hosting** — Railway (24/7 cloud deployment)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ruchirpipalia-spec/travel-agent.git
cd travel-agent
```

### 2. Install dependencies

```bash
pip3 install anthropic requests python-dotenv python-telegram-bot supabase
```

### 3. Get your API keys

You need these accounts and keys:

| Key | Where to get it |
|-----|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `SERPAPI_KEY` | [serpapi.com/dashboard](https://serpapi.com/dashboard) |
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/botfather) on Telegram |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon public key |

### 4. Set up Supabase

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to **SQL Editor** and run this query:

```sql
CREATE TABLE memory (
    id TEXT PRIMARY KEY DEFAULT 'main',
    preferences JSONB DEFAULT '{"home_airport": null, "preferred_airlines": [], "typical_trip_length": null, "seat_preference": null, "budget_range": null}',
    past_searches JSONB DEFAULT '[]',
    watched_routes JSONB DEFAULT '[]',
    conversation_history JSONB DEFAULT '[]',
    last_destination TEXT DEFAULT null,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO memory (id) VALUES ('main') ON CONFLICT DO NOTHING;
```

4. Go to **Project Settings → API** and copy your Project URL and anon public key

### 5. Create your .env file

```bash
touch .env
```

Add your keys:
    ANTHROPIC_API_KEY=your_key_here
    SERPAPI_KEY=your_key_here
    TELEGRAM_BOT_TOKEN=your_token_here
    GMAIL_ADDRESS=your@gmail.com
    GMAIL_APP_PASSWORD=your_app_password_here
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your_anon_key_here


### 6. Run locally

```bash
python3 telegram_bot.py
```

Open Telegram, find your bot, and start chatting.

---

## Deploy to Railway (24/7 hosting)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Click **New Project → Deploy from GitHub repo** and select your repo
4. Go to **Variables** and add all your API keys from `.env`
5. Railway will auto-deploy — your bot is now always online

---

## Project structure

travel-agent/
├── agent.py # Main chatbot logic, flight/hotel search, memory
├── alerts.py # Background price checker and email alerts
├── memory.py # Supabase cloud memory read/write functions
├── telegram_bot.py # Telegram interface + 24hr price check scheduler
├── requirements.txt # Python dependencies
├── Procfile # Tells Railway how to run the bot
├── .env # API keys (never commit this)
└── .gitignore # Keeps .env and memory.json off GitHub


---

## How it works

**When you send a message:**
Your message → Telegram → Claude AI → SerpAPI (if needed) → Claude formats response → Telegram reply

**When prices are checked (every 24 hours automatically):**
Scheduler wakes up → reads watched routes from Supabase → checks live prices via SerpAPI → sends Gmail alert if price drops below threshold

**Memory** is stored in Supabase so it persists forever — across sessions, redeploys, and restarts.

---

## Cost breakdown (personal use)

| Service | Cost |
|---------|------|
| Anthropic API | ~$1–2/month |
| SerpAPI | Free (250 searches/month) |
| Supabase | Free tier |
| Railway | ~$5/month after free trial |
| **Total** | **~$6–7/month** |

---

## Notes

- SerpAPI free tier includes 250 searches/month — enough for personal use with daily checking on a few routes
- Anthropic API charges per message — very cheap for personal use
- Memory is stored in Supabase and persists across all sessions and deployments

---

## Built by

Ruchir Pipalia — built as a learning project starting from zero coding experience.

[github.com/ruchirpipalia-spec/travel-agent](https://github.com/ruchirpipalia-spec/travel-agent)