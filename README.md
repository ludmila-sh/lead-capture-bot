# lead-capture-bot

Configurable Telegram funnel bot for solo experts: captures leads from social, delivers a lead magnet, answers FAQ, and hands warm leads to a human.

See `CLAUDE.md` for architecture and `ROADMAP.md` for the phased plan.

## Run

```
python -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy env.example .env                              # then fill it in
python -m src.bot
```

Required in `.env`: `BOT_TOKEN`, `EXPERT_HANDOFF_USERNAME`, `CHANNEL_URL`.
Optional: `EXPERT_CHAT_ID` (expert lead notifications), Google Sheets analytics (below).

## Аналитика в Google Sheets

Бот дублирует ключевые события воронки — `start`, `magnet_delivered`, `handoff` —
строками в Google-таблицу. Локально всё всегда пишется в `data/interactions.jsonl`
(это резервная копия), таблица — витрина для заказчика.

### Разовая настройка

1. **Создайте service account** в [Google Cloud Console](https://console.cloud.google.com/):
   *IAM & Admin → Service Accounts → Create*. Включите в проекте **Google Sheets API**
   (*APIs & Services → Library → Google Sheets API → Enable*).
2. **Скачайте ключ**: у аккаунта → *Keys → Add key → Create new key → JSON*.
   Положите файл в `secrets/` в корне репо (папка в `.gitignore`), например
   `secrets/service-account.json`.
3. **Создайте таблицу** в Google Sheets и **расшарьте** её на email service account
   (вида `...@...iam.gserviceaccount.com`) с ролью **Editor**.
4. **Заполните `.env`**:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON=secrets/service-account.json
   ANALYTICS_SPREADSHEET_ID=<токен из URL таблицы между /d/ и /edit>
   ANALYTICS_WORKSHEET=events
   ```
5. `pip install -r requirements.txt` (добавился `gspread`) и перезапустите бота.
   Лист `events` с шапкой создастся автоматически при первом событии.

Если переменные не заданы — бот работает как обычно, пишет только `data/interactions.jsonl`.

### Колонки листа `events`

`timestamp` · `event` · `user_id` · `username` · `name` · `segment` · `raw_param` · `reason`

- `start` — каждый `/start`; `segment` = ключ сегмента или `none`, `raw_param` = сырой deep-link.
- `magnet_delivered` — лид-магнит реально отправлен (deep-link или кнопка «Практика»).
- `handoff` — лид ушёл эксперту (кнопка или вопрос о здоровье); повод — в `reason`.

### Вкладка «Сводка»

Создайте второй лист и вставьте в `A1` формулу (в русской локали разделитель `;`):

```
=QUERY(events!A2:H; "select F, count(C), sum(if(B='magnet_delivered',1,0)), sum(if(B='handoff',1,0)) where B is not null group by F label F 'Сегмент'"; 0)
```

Проще — вставить сводную таблицу (*Данные → Сводная таблица*) по листу `events`:
строки — `segment`, значения — `COUNTA(event)` с фильтром по нужному типу.

### Локальный отчёт

Без доступа к Google, прямо из JSONL:

```
python -m src.stats            # таблица по сегментам
python -m src.stats --csv      # CSV в stdout
```
