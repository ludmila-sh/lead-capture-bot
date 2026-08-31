# CLAUDE.md

Guidance for working in this repository. Read this and ROADMAP.md before writing code.

## Project

Telegram bot — the entry point of a social → Telegram funnel for a solo expert
(coach, trainer, tutor, therapist, consultant …). People arrive from Instagram or
another social channel via a deep link, the bot greets them, instantly delivers a
lead magnet, invites them to the expert's channel, answers FAQ, and hands warm leads
over to the human expert. This repo is the Telegram side only, and it is a reusable
template — client specifics live in content, not code.

## Stack

- Python 3.11+
- **aiogram 3.x** (latest stable) — official Telegram Bot API, fully async
- python-dotenv for configuration
- Long polling for local/dev; webhook later (see ROADMAP Phase 5)

## Hard constraints — safety & correctness (do not violate)

- **Official Telegram Bot API ONLY.** Never use Pyrogram, Telethon, or any MTProto /
  userbot approach — those automate a personal account and risk bans. This bot is a
  separate BotFather identity.
- **Secrets come from the environment.** `BOT_TOKEN` and any keys load from `.env`
  via python-dotenv. Never hardcode secrets. `.env` is git-ignored; ship `.env.example`.
- **The bot must never crash on unexpected input.** Any unknown message or callback →
  a safe fallback (show the menu again) or handoff. Losing a lead to an error is the
  worst possible failure.
- **The bot answers only FAQ and logistics automatically.** Anything about health,
  pain, diagnoses, or a real sales conversation → hand off to the human expert.
  No medical advice, ever.

## Architecture & conventions

- **All client-specific content lives in one place:** `content/texts.py` (texts, menu
  labels, FAQ). Values that differ per deployment (handoff username, channel URL) come
  from `.env` via `config.py`. Handlers reference these — no inline strings, no hardcoded
  client data in handler logic. This lets a non-developer reconfigure the bot for a new
  client and mirrors the external "source of truth" (the scripts spreadsheet).
- Suggested structure:
  - `bot.py` — entry: build Bot + Dispatcher, include routers, start polling
  - `config.py` — load env
  - `handlers/` — routers: `start.py`, `menu.py`, `faq.py`, `handoff.py`
  - `keyboards.py` — inline keyboards
  - `content/texts.py` — all messages and button labels
- Code, filenames, identifiers in **English**; user-facing strings in **Russian**.
- Async throughout, type hints, small focused functions.
- Log key events (start, button taps, handoff) to stdout.

## Funnel context (how the pieces connect)

- Entry is a deep link `t.me/<bot>?start=<source>`. The `start` parameter carries the
  lead-magnet / segment / source, so the bot delivers the right resource and can tag it.
- The bot delivers the lead magnet first (instant), then offers a "subscribe to channel"
  button. The **bot** is the interactive front door + qualifier; the **channel** is the
  broadcast / nurture home.

## Run

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill `BOT_TOKEN`, `EXPERT_HANDOFF_USERNAME`, `CHANNEL_URL`
4. `python -m src.bot` (run from the repo root; code lives in the `src/` package)

## Current scope

Build **Phase 1 (MVP menu)** from ROADMAP.md first. Do not build later phases unless
explicitly asked. Keep it minimal and working over complete.
