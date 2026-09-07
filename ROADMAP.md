# ROADMAP

Phased plan. Build one phase at a time. Phase 1 is the first target.

## Phase 0 — Setup  *(do first)*
- Repo, virtualenv, `requirements.txt` (aiogram, python-dotenv)
- `.env.example` with `BOT_TOKEN`, `EXPERT_HANDOFF_USERNAME`, `CHANNEL_URL`
- Minimal `bot.py` that runs and replies to `/start`

## Phase 1 — MVP menu  *(first target)*
- `/start` → greeting + inline menu:
  `[🧘 Практика]  [❓ Частые вопросы]  [💬 Написать эксперту]`
- **Практика** → fixed message with lead-magnet link (placeholder) + open question,
  plus a "Подписаться на канал" button (uses `CHANNEL_URL`)
- **Частые вопросы** → 3–5 fixed Q&A (sub-menu or list with a back button)
- **Написать эксперту** → message with a handoff link (uses `EXPERT_HANDOFF_USERNAME`)
- Safe fallback for any other input (re-show menu)
- All texts in `content/texts.yaml` (loaded + validated by `content/texts.py`)

## Phase 2 — Deep-link entry & segment routing  *(done)*
- Handle `/start <param>` from deep links (`t.me/<bot>?start=spina` — Telegram allows
  only `[A-Za-z0-9_-]` in `start`, so keys are latin slugs)
- Segments (code words → keys): СПИНА→`spina`, ОФИС→`office`, МАМА→`mama`,
  ТРЕНЕР→`trener` (soft, deep-link only, never advertised). `base` = fallback for
  a bare `/start` / unknown param.
- Deep link → greeting + magnet + open question (two messages, instant — no timed
  follow-ups; those stay in Instagram/ChatPlace)
- Unknown / missing param → safe fallback (greeting + menu), raw value logged
- Segments live in `content/texts.yaml` (`lead_magnets`); `menu:practice` serves `default_segment`

## Phase 3 — Handoff + logging  *(done)*
- On "Написать эксперту" or a health question → notify the expert (`EXPERT_CHAT_ID`,
  optional) with short user context (name, contact, id, segment, reason, message)
- Health questions detected by keyword list in `content/texts.yaml` (`health_keywords`);
  bot never answers them — hands off + reassures the user
- Interactions appended as JSON lines to `data/interactions.jsonl`
  (`INTERACTION_LOG_PATH`), also echoed to stdout — see `src/events.py`
- Last entry segment kept in memory (`src/state.py`) for handoff context

## Phase 4 — Analytics in Google Sheets  *(done)*
- Mirror funnel milestones — `start`, `magnet_delivered`, `handoff`,
  `subscribed` / `unsubscribed` — as rows in a client-owned Google Sheet, so docs /
  lead magnets / analytics live in one place
- Write directly via `gspread` + a service account (background thread, fire-and-forget);
  `data/interactions.jsonl` stays the durable offline backup
- Active only when `GOOGLE_SERVICE_ACCOUNT_JSON` + `ANALYTICS_SPREADSHEET_ID` are set —
  see `src/sheets.py`, `src/events.py` (`_SHEET_EVENTS`), README
- Subscription tracking: `src/handlers/subscription.py` — bot must be channel admin;
  `CHANNEL_ID` for a private channel, else `@username` from `CHANNEL_URL`
- `python -m src.sheets` — verify connection / repair header row
- `python -m src.stats [--csv]` — local per-segment report from the JSONL
- Still manual (not from this bot): Instagram reach / CTR / feedback → a monthly tab
  the expert fills in the same spreadsheet

## Phase 5 — Payments & access  *(research done — see `docs/payments.md`)*
- **Blocked on client actions first:** confirm expert's legal status (НПД via «Профдоход»),
  get written МНС confirmation that yoga wellness classes qualify
- **Now (manual):** «Профдоход» + «Оплати» link/QR the trainer sends by hand — 0% fee,
  Belarus only; no bot change needed
- **Later:** Lava.top for RU/abroad clients (test payout first); Tribute for a paid
  closed channel; separate tax regime for selling video content
- **Minimal bot step (when decided):** menu button «💳 Оплатить занятие» → `PAYMENT_URL`
  from `.env`; log `payment_link_opened`. Real payment confirmation needs a provider
  with an API/webhook.

## Phase 6 — Deploy
- Currently: long polling on the developer's server (Koyeb) during the support window
- Later: a host non-IT people can run (hoster.by VPS or similar), process manager /
  auto-restart, `.env` + `secrets/` on the host, log rotation
- Webhook instead of long polling is optional

## Backlog (agreed, do later — don't lose these)
- **Deep-link source granularity.** Encode campaign/placement in the start param
  (`spina__reels_oct`), keep storing `raw_param` verbatim, split into
  segment / campaign columns in the sheet. Needs a naming convention with the client.
- **"Сводка" tab with time series.** Per-day × per-segment counts, conversion %
  (`start → magnet → subscribed → handoff`), simple charts. Squeeze every useful
  metric out of the raw events (time-to-handoff, drop-off, repeat visitors).
- Table archival: **decided not to bother** — volume is tiny (~100/mo is nothing).
  Revisit only if it ever gets large; then one tab per year.
- `python -m src.sheets sync` — backfill sheet rows from JSONL after an outage.
