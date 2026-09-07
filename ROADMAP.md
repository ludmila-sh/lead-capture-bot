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
- All texts in `content/texts.py`

## Phase 2 — Deep-link entry & segment routing  *(done)*
- Handle `/start <param>` from deep links (`t.me/<bot>?start=spina` — Telegram allows
  only `[A-Za-z0-9_-]` in `start`, so segment keys are latin slugs: `spina` / `sheya` / `mama`)
- Route by `param` to the matching lead magnet / segment (Спина / Шея-плечи / Мама),
  deliver the right resource, tag the source (logged; storage in Phase 3)
- Unknown / missing param → safe fallback (greeting + menu), raw value logged
- Segments live in `content/texts.py` (`LEAD_MAGNETS`); `menu:practice` serves `DEFAULT_SEGMENT`

## Phase 3 — Handoff + logging  *(done)*
- On "Написать эксперту" or a health question → notify the expert (`EXPERT_CHAT_ID`,
  optional) with short user context (name, contact, id, segment, reason, message)
- Health questions detected by keyword list in `content/texts.py` (`HEALTH_KEYWORDS`);
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

## Phase 5 — Payments & access
- Decide provider (Lava / Tribute / YooKassa / Telegram Stars) and access model
- Payment link; on payment → auto-generate a one-time invite to the closed content channel
- Track `paid` events (extend `_SHEET_EVENTS`)

## Phase 6 — Deploy
- Switch to webhook, host on mini-PC / VPS, add a process manager
- (spreadsheet sync now lands in Phase 4)
