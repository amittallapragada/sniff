# 🐷 Sniff

An open-source AI assistant that can make phone calls on your behalf. Think Muse or Instinct, but with a voice — it can call restaurants, schedule appointments, and handle errands over the phone.

Built with Gemini Flash, Pipecat, Twilio, and Cartesia. Runs for under $5/month.

## What it does

- **Voice calling** — places outbound calls, talks to humans, detects voicemail, leaves messages with your callback number
- **Chat via Telegram** — conversational AI with memory, emoji reactions, and HTML formatting
- **Web search** — DuckDuckGo for general queries, Scrappa API for flights/hotels/shopping
- **Browser automation** — browser-use for tasks that require clicking buttons and filling forms
- **Semantic memory** — remembers your preferences across conversations using pgvector embeddings

## Architecture

```
Telegram → FastAPI → Gemini Flash (agentic tool loop)
                         ├── web_search (DuckDuckGo)
                         ├── scrappa_search (structured data)
                         ├── browse_web (browser-use + Chromium)
                         ├── remember (pgvector embeddings)
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
| Supabase (free tier) | $0 |
| **Total** | **~$3-4/mo** |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A Supabase project
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

### 3. Set up the database

Run the migration against your Supabase project:

```bash
psql $DATABASE_URL -f supabase/migrations/001_initial.sql
```

Then add yourself to the `users` table:

```sql
INSERT INTO users (phone_number, telegram_id, name, persona_name, timezone)
VALUES ('+1234567890', 123456789, 'Your Name', 'Your Name', 'America/New_York');
```

### 4. Expose your local server

Sniff needs a public URL for Twilio and Telegram webhooks. Use Cloudflare Tunnel:

```bash
cloudflared tunnel --url localhost:8000
```

Set `APP_BASE_URL` in `.env` to the tunnel URL.

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
│   ├── db.py                        # Supabase client
│   ├── history.py                   # Conversation history
│   └── semantic.py                  # Embeddings + vector search
├── interfaces/
│   └── telegram.py                  # Telegram Bot API (send, react, emoji picker)
├── webhooks/
│   ├── telegram.py                  # Telegram webhook (dedup, routing)
│   ├── voice.py                     # Twilio voice webhooks (outbound + AMD)
│   └── stream.py                    # WebSocket endpoint for Pipecat
├── auth/
│   └── users.py                     # User model + Supabase lookups
└── supabase/
    └── migrations/
        └── 001_initial.sql          # Database schema
```

## Legal

Sniff identifies itself as an AI assistant on calls — it does not impersonate the user. If you deploy this, be aware of your local laws around AI-initiated calls and call recording consent.

## License

MIT
