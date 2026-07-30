# GGBH Speed2Lead Bot

A Telegram bot for **Gulf Gateway Business Hub (GGBH)** that answers customer questions about UAE
business setup and immigration, and automatically qualifies leads into a spreadsheet — no CRM,
no database, and only two API keys to configure.

> This is a working prototype. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how it's built and
> [`knowledge/README.md`](knowledge/README.md) for what the bot knows (and its known data gaps).

## Features

- Answers customer doubts on business activities, approvals, visas, and attested-degree/designation
  rules — grounded in `knowledge/customer/*.md`, not guesswork.
- Automatically recognizes a qualified lead mid-conversation (name + contact + interest) and logs it
  to a local Excel file — no Google Sheets, no service-account credentials.
- Scope-locked to business setup/immigration topics only; won't get pulled into unrelated chat.
- Closes an idle conversation after a couple of minutes with an AI-generated summary.
- Runs on Telegram long polling — no public URL, domain, or TLS certificate required.

## Prerequisites

- A Telegram bot token — create one via [@BotFather](https://t.me/BotFather) (`/newbot`).
- An [Anthropic API key](https://console.anthropic.com/).
- Either **Python 3.11+** (for a local/venv run) or **Docker**.

## Setup

1. Clone this repository and `cd` into it.
2. Copy the environment template and fill in your two keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY`. Everything else in `.env.example`
   is optional and already has a sensible default — leave it as-is unless you want to change it.
   **Never commit `.env`** — it's already gitignored.

### Run locally (Python venv)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

The bot will log in, delete any old webhook, and start long-polling Telegram. Message your bot on
Telegram to test it.

### Run with Docker

```bash
docker build -t ggbh-speed2lead .
docker run --env-file .env -v "$(pwd)/data:/app/data" ggbh-speed2lead
```

The volume mount keeps `data/leads.xlsx` (recorded leads) and the dedupe state persisted across
container restarts — without it, leads recorded during a run are lost when the container is removed.

## Configuration reference

| Variable | Required | Default | Notes |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | — | From @BotFather |
| `ANTHROPIC_API_KEY` | Yes | — | From the Anthropic Console |
| `CLAUDE_MODEL` | No | `claude-opus-5` | Any current Claude model ID |
| `LEADS_EXCEL_PATH` | No | `data/leads.xlsx` | Where qualified leads are appended |
| `INACTIVITY_TIMEOUT_SECONDS` | No | `120` | How long a chat can be idle before it's auto-closed with a summary |

## Editing the bot's knowledge

Everything the bot knows about business setup and immigration lives in `knowledge/customer/*.md` and
is loaded directly into its system prompt at startup (`app/prompts.py`). Edit those files and restart
the bot to change what it knows — no code changes needed. See `knowledge/README.md` for what each
file covers and two flagged data gaps that are intentionally left unresolved rather than guessed at.

## Project status

Prototype stage — see `ARCHITECTURE.md` → "Known limitations" for what to revisit before any
production use (single-process in-memory chat history, no file locking on the leads spreadsheet
under concurrent load, etc.).
