# GGBH Speed2Lead Bot — Architecture

A Telegram bot for Gulf Gateway Business Hub (GGBH) that answers customer questions about UAE
business setup and immigration, and automatically qualifies leads into a spreadsheet. This doc
covers how it's built and how it's currently running.

## Overview

```
Telegram user
     │  message
     ▼
python-telegram-bot (long polling — no public URL needed)
     │
     ▼
app/handlers.py  ──────────────┐
     │  chat history            │  idle timer (2 min, resets per message)
     ▼                          ▼
app/llm.py  ──uses──►  app/prompts.py (system prompt + knowledge/customer/*.md)
     │
     ├─► Claude API (model: claude-opus-5)
     │       └─ if the visitor gave name + contact + interest → calls the
     │          record_qualified_lead tool
     │
     └─► app/leads.py ──► data/leads.xlsx  (local Excel file, no Google Sheets)
```

There's no database and no web server — the whole thing is one Python process that keeps a
long-lived connection open to Telegram (`getUpdates`) and calls the Anthropic API per message.

## Files

| File | Role |
|---|---|
| `app/main.py` | Entry point. Builds the bot and calls `application.run_polling()`. |
| `app/handlers.py` | Telegram-facing glue: routes `/start`, text messages, and button taps. Keeps an in-memory `conversation_store` (chat history) and the idle-close timer. |
| `app/llm.py` | Calls Claude. Runs a small manual tool-use loop: ask Claude for a reply → if it wants to record a lead, call the tool, save it, ask Claude again for the final reply to send. Also has `get_conversation_summary()` for the idle-close message. |
| `app/prompts.py` | Builds the system prompt at import time by concatenating every file in `knowledge/customer/*.md`, plus the persona/scope/lead-capture instructions. This is the bot's entire "knowledge." |
| `app/leads.py` | Appends a row to `data/leads.xlsx` (openpyxl) when a lead is recorded, and tracks which chats have already been recorded (`data/captured_leads.json`) so the same visitor isn't logged twice. |
| `app/config.py` | Reads everything from environment variables / `.env` — only `TELEGRAM_BOT_TOKEN` and `ANTHROPIC_API_KEY` are required; everything else has a default. |
| `knowledge/customer/*.md` | The actual knowledge — business activities & approvals, visa/immigration rules, nationality document requirements, designation/degree rules. Editing these changes what the bot knows on its next restart. |

## How it was built

1. Started from a GDRFA designation list, a qualifications lookup, and an internal training manual
   (originally for a different company, "DSBH") and rebuilt the relevant rules as a GGBH-branded,
   **customer-facing only** knowledge base — no internal ERP steps, portal click-throughs, or staff
   email templates, since those aren't useful to a customer-facing bot.
2. Wired that knowledge base directly into the system prompt (`app/prompts.py`), so the bot answers
   from it instead of guessing.
3. Added lead qualification as a Claude **tool call** (`record_qualified_lead`) rather than
   keyword-matching or a rigid form — the model decides naturally, mid-conversation, once it has a
   name, a way to reach the visitor, and their interest.
4. Chose a **local Excel file** over Google Sheets for lead storage specifically so the project only
   needs two secrets (Telegram token, Anthropic key) — a Google Sheets integration would have
   required a separate service-account credentials file.
5. Chose **long polling** over a webhook/FastAPI server so the bot needs no public URL, domain, or
   TLS certificate — it just needs outbound internet access, which matters for cheap, throwaway
   hosting of a prototype.
6. Added a strict scope-lock in the system prompt (business setup/immigration only, no off-topic
   answers) and a 2-minute inactivity timer per chat that sends an AI-generated summary and clears
   that chat's history when a visitor goes quiet.

## How it's hosted right now

**Locally** — running directly on this machine inside the project's `.venv`, as a background
process (`python -m app.main`), reading real credentials from a local `.env` file (gitignored,
never committed). It is **not** deployed to any cloud service yet. Anyone testing it does so by
messaging the bot on Telegram directly; the process must stay running on this machine for the bot
to respond.

**Not yet done, but planned:** deploying the existing `Dockerfile` to Railway (or Fly.io) so the
bot runs continuously without this machine needing to stay on. Since it's long-polling, that move
needs no extra networking setup — just the same two environment variables set in the host's
dashboard, and ideally a small persistent volume mounted at `/app/data` so `leads.xlsx` survives
restarts/redeploys.

## Data & secrets

- `.env` (real secrets) and `data/` (leads spreadsheet + dedupe state, real customer contact info)
  are both gitignored — neither should ever be committed or pushed.
- `.env.example` is the committed template with placeholder values only.
- Conversation history (`conversation_store` in `handlers.py`) lives in memory only — it resets
  whenever the process restarts. Lead records in `data/leads.xlsx` persist across restarts as long
  as the `data/` folder itself isn't deleted.

## Known limitations (prototype-stage)

- Single process, in-memory chat history — doesn't scale past one instance and forgets active
  conversations on restart (recorded leads in the Excel file are unaffected).
- No file locking on `leads.xlsx` — fine for low, single-process traffic; would need revisiting
  under real concurrent load.
- Two knowledge-base gaps are flagged rather than guessed at: a handful of specialized designations
  with unconfirmed degree requirements, and the Bangladesh outside-country eligible-designations
  list, which was never supplied as source data. See `knowledge/README.md`.
