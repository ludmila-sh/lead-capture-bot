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

## Phase 2 — Deep-link entry & segment routing
- Handle `/start <param>` from deep links (`t.me/<bot>?start=спина`)
- Route by `param` to the matching lead magnet / segment (Спина / Шея-плечи / Мама),
  deliver the right resource, tag the source
- aiogram FSM or callback routing where a branch needs follow-up

## Phase 3 — Handoff + logging
- On "Написать эксперту" or a health question → notify the expert (their chat_id)
  with short user context
- Log interactions (file first; later spreadsheet / DB)

## Phase 4 — Payments & access
- Payment link (e.g. Lava / Tribute)
- On payment → auto-generate a one-time invite to the closed content channel

## Phase 5 — Deploy & analytics
- Switch to webhook, host on mini-PC / VPS, add a process manager
- Sync funnel events to the tracking spreadsheet
