# 🐷 Sniff

An open-source AI assistant that can make phone calls on your behalf. Like Muse or Instinct, but with a voice — it can call restaurants, schedule appointments, and handle errands over the phone.

Built with Gemini Flash, Pipecat, Twilio, and Cartesia. Runs for under $5/month.

## What it does

- **Voice calling** — places outbound calls, talks to humans, detects voicemail, leaves messages with your callback number
- **Chat via Telegram** — conversational AI with memory, emoji reactions, and HTML formatting
- **Web search** — DuckDuckGo for general queries, Scrappa API for flights/hotels/shopping
- **Browser automation** — browser-use for tasks that require clicking buttons and filling forms
- **Semantic memory** — remembers your preferences across conversations using vector embeddings

## Demo

### 📞 Voice Calling — `place_call`
Sniff calls a restaurant, books a table, and sends back a summary with confirmation details.

<p align="center">
  <img src="blog/demo/booking-reservation-demo.gif" width="300" alt="Sniff booking a restaurant reservation via phone call" />
</p>

### ✈️ Flight Search — `scrappa_search`
Real-time flight pricing from structured APIs. Sniff finds the cheapest options and formats them for quick scanning.

<p align="center">
  <img src="blog/demo/flight-search-p1.PNG" width="300" />
  <img src="blog/demo/flight-search-p2.PNG" width="300" />
</p>

### 🍽️ Restaurant Search — `web_search`
Sniff searches for restaurants matching your criteria and returns ratings, price range, and standout dishes.

<p align="center">
  <img src="blog/demo/restaurant-p1.PNG" width="300" />
  <img src="blog/demo/restaurant-p2.PNG" width="300" />
</p>

## Architecture

```
Telegram → FastAPI → Gemini Flash (agentic tool loop)
                         ├── web_search (DuckDuckGo)
                         ├── scrappa_search (structured data)
                         ├── browse_web (browser-use + Chromium)
                         ├── remember (vector embeddings)
                         └── place_call → Twilio → Pipecat pipeline
                                            ├── Cartesia STT (ink-2)
                                            ├── Gemini Flash (voice LLM)
                                            └── Cartesia TTS (sonic-3.5)
```

## How calling works

1. User asks Sniff to call someone (always requires explicit confirmation)
2. Sniff triggers an outbound call via Twilio
3. Twilio connects to a WebSocket endpoint where a [Pipecat](https://github.com/pipecat-ai/pipecat) pipeline handles real-time audio
4. **STT**: Cartesia ink-2 transcribes the other person's speech
5. **LLM**: Gemini 3.6 Flash (with minimal thinking for low latency) generates responses
6. **TTS**: Cartesia sonic-3.5 speaks the response back
7. Twilio AMD detects voicemail — the bot leaves a message with your callback number
8. When the call ends, Gemini summarizes the transcript and sends it to you on Telegram

The voice pipeline uses a security-hardened prompt — no user details, phone numbers, or memories are leaked into the call context.

## Cost breakdown

| Component | Cost |
|-----------|------|
| GCP e2-micro (Always Free) | $0 |
| Gemini Flash | ~$1-2/mo |
| Cartesia (free tier, ~20 min/mo) | $0 |
| Twilio (number + minutes) | ~$2/mo |
| SQLite | $0 |
| **Total** | **~$3-4/mo** |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- API keys for: Gemini, Twilio, Telegram Bot, Cartesia, Scrappa

### 1. Clone and install

```bash
git clone https://github.com/yourusername/sniff.git
cd sniff
uv sync
```

### 2. Set up environment

```bash
cp .env.example .env
# Fill in your API keys
```

### 3. Add yourself to the database

The database (SQLite) is created automatically on first run. Add yourself using the included script:

```bash
uv run python -c "
from memory.db import get_db
import uuid
db = get_db()
db.execute(
    'INSERT INTO users (id, phone_number, telegram_id, name, persona_name, timezone) VALUES (?, ?, ?, ?, ?, ?)',
    (str(uuid.uuid4()), '+1234567890', 123456789, 'Your Name', 'Your Name', 'America/New_York')
)
db.commit()
print('User created!')
"
```

### 4. Expose your local server

Sniff needs a public URL for Twilio and Telegram webhooks. Use Cloudflare Tunnel:

```bash
cloudflared tunnel --url localhost:8000
```

Set `APP_BASE_URL` in `.env` to the tunnel URL, then update your Twilio phone number's webhook:

```bash
uv run python scripts/update_twilio_webhook.py
```

This points Twilio's voice webhook to your tunnel URL. Re-run this whenever your tunnel URL changes.

### 5. Run

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

On startup, Sniff registers its Telegram webhook automatically.

## Project structure

```
sniff/
├── main.py                          # FastAPI app + routes
├── config.py                        # Pydantic settings
├── agent/
│   ├── core.py                      # Gemini agentic loop (tool calls + summarization)
│   ├── prompt.py                    # System prompt builder
│   └── tools.py                     # Tool definitions
├── capabilities/
│   ├── call/
│   │   ├── outbound.py              # Twilio outbound call trigger
│   │   ├── pipeline.py              # Pipecat voice pipeline (STT → LLM → TTS)
│   │   ├── session.py               # In-memory call session management
│   │   └── summary.py               # Post-call transcript summarization
│   ├── search/
│   │   ├── web.py                   # DuckDuckGo search
│   │   └── scrappa.py               # Scrappa structured search API
│   └── browser/
│       └── tasks.py                 # browser-use agent
├── memory/
│   ├── db.py                        # SQLite connection + schema
│   ├── history.py                   # Conversation history
│   └── semantic.py                  # Embeddings + cosine similarity search
├── interfaces/
│   └── telegram.py                  # Telegram Bot API (send, react, emoji picker)
├── webhooks/
│   ├── telegram.py                  # Telegram webhook (dedup, routing)
│   ├── voice.py                     # Twilio voice webhooks (outbound + AMD)
│   └── stream.py                    # WebSocket endpoint for Pipecat
├── auth/
│   └── users.py                     # User model + SQLite lookups
```

## Legal

Sniff identifies itself as an AI assistant on calls — it does not impersonate the user. If you deploy this, be aware of your local laws around AI-initiated calls and call recording consent.

## License

MIT
