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
Optional: `EXPERT_CHAT_ID` (expert lead notifications), `CHANNEL_ID` (private-channel
subscription tracking), Google Sheets analytics (below).

## Тексты бота

Встроенный источник — `src/content/texts.yaml` (сообщения, кнопки, лид-магниты,
FAQ, `health_keywords`). При старте валидируется; бот не запустится с явной
ошибкой. Сегменты (deep-link): `spina`, `office`, `mama`, `trener` (непубличный),
`base` (по умолчанию).

**Правка без доступа к хостингу.** Если настроена аналитика в Google Sheets,
вкладка `Тексты бота` (`key | value`) в той же таблице переопределяет строки из
YAML. Бот перечитывает её:
- один раз при старте,
- каждые `TEXTS_RELOAD_SECONDS` секунд (по умолчанию 180; `0` — только по команде),
- по команде `/reload` от админа (`ADMIN_IDS`, по умолчанию — `EXPERT_CHAT_ID`).

Пустая ячейка = значение из кода. Если правки ломают проверку (нет обязательного
ключа, `{link}` в тексте магнита и т.п.) — бот их **не применяет** и остаётся на
последних рабочих текстах; причина пишется в лог и в ответ на `/reload`.
Ключи оверрайдов: `screens.<...>`, `buttons.<...>`, `lead_magnets.<seg>.<field>`,
`faq.<N>.<q|a>`, `default_segment`. Шаблон вкладки создаёт
`python scripts/build_workspace.py`.

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
5. `pip install -r requirements.txt` (добавился `gspread`).
6. Проверьте связь и создайте лист с шапкой:
   ```
   python -m src.sheets
   ```
   При успехе печатает `OK …` и готовую формулу для вкладки «Сводка». Эту же
   команду запустите, если случайно очистили лист и шапка пропала (бот тоже
   восстановит её сам — перед каждой записью и при рестарте).

Если переменные не заданы — бот работает как обычно, пишет только `data/interactions.jsonl`.

### Колонки листа `events`

`timestamp` · `event` · `user_id` · `username` · `name` · `segment` · `raw_param` · `reason`

- `start` — каждый `/start`; `segment` = ключ сегмента или `none`, `raw_param` = сырой deep-link.
- `magnet_delivered` — лид-магнит реально отправлен (deep-link или кнопка «Практика»).
- `handoff` — лид ушёл эксперту (кнопка или вопрос о здоровье); повод — в `reason`.
- `subscribed` / `unsubscribed` — вступление/выход из канала (см. ниже).

### Трекинг подписки на канал

Чтобы события `subscribed` / `unsubscribed` фиксировались, **добавьте бота
администратором в канал** (любые права; без этого Telegram не присылает
`chat_member`-апдейты). Для **приватного** канала укажите `CHANNEL_ID` в `.env`
(для публичного хватает `@username` из `CHANNEL_URL`). После добавления бота в
консоли появится строка `bot membership in ... (id=...)` — там и виден id.

Сегмент подписчика берётся из памяти процесса (последний `/start`); если бот
перезапускался между `/start` и подпиской — будет `none`.

### Вкладка «Сводка»

Создайте второй лист и вставьте в `A1` формулу, которую печатает `python -m src.sheets`
(она уже подставляет имя вашего листа; в русской локали замените `,` на `;`).

Проще — вставить сводную таблицу (*Данные → Сводная таблица*) по листу событий:
строки — `segment`, значения — `COUNTA(event)` с фильтром по нужному типу.

### Локальный отчёт

Без доступа к Google, прямо из JSONL:

```
python -m src.stats            # таблица по сегментам
python -m src.stats --csv      # CSV в stdout
```
