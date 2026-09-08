"""Rebuild the client workspace spreadsheet from docs/FYSM.xlsx.

Produces docs/Fysom — рабочая таблица.xlsx with:
  * tabs reordered and grouped (emoji prefixes), a "how to use" line on each;
  * a new 📈 Дашборд tab with live formulas over Аналитика + 👥 Клиенты;
  * 👥 Клиенты reworked into a mini-CRM (absorbs the old Воронка, which is dropped);
  * Аналитика kept EXACTLY named (the bot appends rows there — do not rename).

Run:  python scripts/build_workspace.py
Needs: openpyxl  (pip install openpyxl — dev-only, not a bot dependency)
"""

from __future__ import annotations

from pathlib import Path

import yaml
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "FYSM.xlsx"
DST = ROOT / "docs" / "Fysom — рабочая таблица.xlsx"

# Tab names, and how to reference them in a formula (quote names with spaces/emoji).
AN = "Аналитика"
CL = "👥 Клиенты"
CL_REF = "'👥 Клиенты'"

# Segment keys, straight from the bot's texts, plus "none" (bare/unknown /start).
_TEXTS = yaml.safe_load((ROOT / "src" / "content" / "texts.yaml").read_text("utf-8"))
SEGMENTS = list(_TEXTS["lead_magnets"]) + ["none"]

TITLE_FONT = Font(bold=True, size=13)
NOTE_FONT = Font(italic=True, size=9, color="666666")
HEAD_FONT = Font(bold=True)
HEAD_FILL = PatternFill("solid", fgColor="F0F0F0")
WRAP = Alignment(wrap_text=True, vertical="top")


def _style_header(ws, row: int, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL


def _autosize(ws, widths: dict[int, int]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def _copy_sheet(src_ws, dst_wb: Workbook, title: str, note: str) -> None:
    """Copy values verbatim, prepend a one-line 'how to use' note."""
    ws = dst_wb.create_sheet(title)
    ws["A1"] = src_ws["A1"].value or title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = note
    ws["A2"].font = NOTE_FONT
    r = 4
    for row in src_ws.iter_rows(min_row=2, values_only=True):  # skip old title row
        if all(v is None for v in row):
            r += 1
            continue
        for i, val in enumerate(row, start=1):
            if val is not None:
                ws.cell(row=r, column=i, value=val)
        r += 1
    ws.freeze_panes = "A4"
    for col in range(1, (src_ws.max_column or 1) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 26
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = WRAP


def build() -> None:
    src = load_workbook(SRC, data_only=True)
    wb = Workbook()
    wb.remove(wb.active)

    # 1 — 📌 Старт (from Памятка)
    start = wb.create_sheet("📌 Старт")
    pam = src["Памятка"]
    start["A1"] = "📌 Старт — быстрая шпаргалка"
    start["A1"].font = TITLE_FONT
    start["A2"] = (
        "Читай первым. Жёлтое [ ... ] — впиши своё. "
        "Вкладки с 📊/📈 заполняются автоматически из бота, остальные — руками."
    )
    start["A2"].font = NOTE_FONT
    r = 4
    for row in pam.iter_rows(min_row=4, values_only=True):
        if all(v is None for v in row):
            r += 1
            continue
        for i, val in enumerate(row, start=1):
            if val is not None:
                start.cell(row=r, column=i, value=val)
        r += 1
    # The copied "ЦЕПОЧКА БОТА" block still described the Instagram chain with
    # timed follow-ups. Replace it with the actual Telegram flow.
    for row in start.iter_rows():
        if row[0].value and "ЦЕПОЧКА" in str(row[0].value):
            base = row[0].row
            start.cell(row=base, column=1, value="ЦЕПОЧКА БОТА (Telegram, коротко)")
            new_chain = [
                (
                    "По кодовому слову",
                    "одно сообщение: привет + практика + превью видео",
                ),
                ("По /start без слова", "приветствие с фото Артёма + меню"),
                ("Открытый вопрос", "Артём задаёт лично в переписке (бот его не шлёт)"),
                ("Дожимы 3 ч / 24 ч", "только в Instagram, в Telegram их нет"),
            ]
            for j, (a, b) in enumerate(new_chain, start=base + 1):
                start.cell(row=j, column=1, value=a)
                start.cell(row=j, column=2, value=b)
            # Wipe any leftover old chain lines ("1 | Приветствие …", "5 | Дожим …").
            for j in range(base + 1 + len(new_chain), base + 10):
                a = str(start.cell(row=j, column=1).value or "")
                bcell = str(start.cell(row=j, column=2).value or "")
                if (
                    a[:1].isdigit()
                    or "Дожим" in a + bcell
                    or "Приветств" in a + bcell
                    or "урок" in a + bcell
                ):
                    # NB: cell(..., value=None) is a no-op in openpyxl; assign .value
                    start.cell(row=j, column=1).value = None
                    start.cell(row=j, column=2).value = None
            break

    start["A" + str(r + 1)] = "КАК УСТРОЕН ЭТОТ ФАЙЛ"
    start["A" + str(r + 1)].font = HEAD_FONT
    guide = [
        "📈 Дашборд — сводные цифры воронки. Ничего не трогай, обновляется сам.",
        "Аналитика — бот пишет сюда каждое действие. НЕ переименовывай вкладку.",
        "👥 Клиенты — веди руками: лид → пробное → активен → ушёл.",
        "💬 Скрипты — тексты автоответов (Telegram и Instagram). Правишь тут.",
        "🧪 Тест гипотез / 📅 Контент-план — для рекламы и съёмок.",
    ]
    for i, line in enumerate(guide, start=r + 2):
        start.cell(row=i, column=1, value=line)
    # Bold + shade the ALL-CAPS section headers copied from Памятка.
    for row in start.iter_rows(min_col=1, max_col=1):
        cell = row[0]
        v = str(cell.value or "")
        if v and v == v.upper() and len(v) > 4 and any(ch.isalpha() for ch in v):
            cell.font = HEAD_FONT
            cell.fill = HEAD_FILL
    _autosize(start, {1: 42, 2: 62})
    for row in start.iter_rows():
        for cell in row:
            cell.alignment = WRAP
    start.freeze_panes = "A4"

    # 2 — 📈 Дашборд (new)
    _build_dashboard(wb)

    # 3 — 👥 Клиенты (mini-CRM; absorbs Воронка)
    _build_clients(wb, src)

    # 4 — Аналитика (bot-owned; keep exact name, header row only)
    an = wb.create_sheet("Аналитика")
    header = [
        "timestamp",
        "event",
        "user_id",
        "username",
        "name",
        "segment",
        "raw_param",
        "reason",
    ]
    an.append(header)  # header only — the bot appends real rows below it
    _style_header(an, 1, len(header))
    an.freeze_panes = "A2"
    an.column_dimensions["C"].number_format = "@"  # user_id as text
    _autosize(an, {1: 22, 2: 18, 3: 16, 4: 18, 5: 18, 6: 12, 7: 14, 8: 26})

    # 5–8 — scripts & marketing (verbatim copies with a note)
    _copy_sheet(
        src["Скрипты Телеграм бота"],
        wb,
        "💬 Скрипты Telegram",
        "Тексты Telegram-бота. АКТУАЛЬНЫЕ тексты живут в проекте (content/texts.yaml); "
        "здесь — сценарий и FAQ для согласования с Артёмом. Меню бота: Практика / "
        "Частые вопросы / Написать Артёму. Оплаты и авто-доступа пока нет.",
    )
    _copy_sheet(
        src["Скрипты автоответов в Instagram"],
        wb,
        "💬 Скрипты Instagram",
        "Автоответы в Instagram/ChatPlace (это НЕ Telegram-бот). Кодовые слова: "
        "СПИНА, ОФИС, МАМА, ТРЕНЕР. Ссылки в бот: t.me/<bot>?start=spina|office|mama|trener.",
    )
    _copy_sheet(
        src["Тест гипотез"],
        wb,
        "🧪 Тест гипотез",
        "Один креатив = одна строка. CTR считается сам. Ориентир: CTR выше 1%.",
    )
    _copy_sheet(
        src["Контент-план"],
        wb,
        "📅 Контент-план",
        "План съёмок: ~3 рилса, 1 карусель, 5 сторис в неделю.",
    )

    # The old "Воронка" tab is dropped: its lead list is now the auto Аналитика
    # tab, and manual tracking moved into 👥 Клиенты.

    wb.save(DST)
    print(f"wrote {DST}")
    print("tabs:", [ws.title for ws in wb.worksheets])


def _section(ws, coord: str, text: str) -> None:
    ws[coord] = text
    ws[coord].font = HEAD_FONT
    ws[coord].fill = HEAD_FILL


def _build_dashboard(wb: Workbook) -> None:
    ws = wb.create_sheet("📈 Дашборд")
    ws["A1"] = "📈 Дашборд"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = (
        "Считается сам из «Аналитики» и «Клиентов». Ничего не редактируй. "
        "Формулы посчитаются после импорта в Google Sheets."
    )
    ws["A2"].font = NOTE_FONT

    a = "Аналитика"
    # (label, formula, is_percent). "SECTION" label => a shaded sub-header.
    rows = [
        ("SECTION", "Воронка (за всё время)", False),
        ("Переходов в бот", f'=COUNTIF({a}!B:B,"start")', False),
        ("Практик выдано", f'=COUNTIF({a}!B:B,"magnet_delivered")', False),
        ("Подписок на канал", f'=COUNTIF({a}!B:B,"subscribed")', False),
        ("Отписок от канала", f'=COUNTIF({a}!B:B,"unsubscribed")', False),
        ("Обращений к Артёму", f'=COUNTIF({a}!B:B,"handoff")', False),
        (
            "Уникальных людей",
            f'=IFERROR(COUNTA(UNIQUE(FILTER({a}!C2:C,{a}!C2:C<>""))),0)',
            False,
        ),
        ("", "", False),
        ("SECTION", "Конверсии", False),
        (
            "переход → подписка",
            f'=IFERROR(COUNTIF({a}!B:B,"subscribed")/COUNTIF({a}!B:B,"start"),0)',
            True,
        ),
        (
            "переход → Артём",
            f'=IFERROR(COUNTIF({a}!B:B,"handoff")/COUNTIF({a}!B:B,"start"),0)',
            True,
        ),
        ("", "", False),
        ("SECTION", "Клиенты", False),
        ("Активных", f'=COUNTIF({CL_REF}!H:H,"Активен")', False),
        ("Доход в месяц, $", f'=SUMIF({CL_REF}!H:H,"Активен",{CL_REF}!E:E)', False),
        ("Ушли", f'=COUNTIF({CL_REF}!H:H,"Ушёл")', False),
    ]
    for i, (label, formula, is_pct) in enumerate(rows, start=4):
        if label == "SECTION":
            _section(ws, f"A{i}", formula)
            continue
        ws.cell(row=i, column=1, value=label)
        if formula:
            cell = ws.cell(row=i, column=2, value=formula)
            if is_pct:
                cell.number_format = "0%"

    # "По сегментам" — a COUNTIFS grid (Google Sheets QUERY has no if()).
    _section(ws, "D4", "По сегментам")
    seg_cols = [
        ("Сегмент", None),
        ("Переходов", "start"),
        ("Практик", "magnet_delivered"),
        ("Подписок", "subscribed"),
        ("К Артёму", "handoff"),
    ]
    for c, (head, _ev) in enumerate(seg_cols, start=4):
        cell = ws.cell(row=5, column=c, value=head)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
    for r, seg in enumerate(SEGMENTS, start=6):
        ws.cell(row=r, column=4, value=seg)
        for c, (_head, ev) in enumerate(seg_cols, start=4):
            if ev is None:
                continue
            ws.cell(
                row=r,
                column=c,
                value=f'=COUNTIFS({a}!$F:$F,$D{r},{a}!$B:$B,"{ev}")',
            )
    _autosize(ws, {1: 26, 2: 14, 3: 3, 4: 16, 5: 12, 6: 12, 7: 12, 8: 12})
    ws.freeze_panes = "A4"


def _build_clients(wb: Workbook, src: Workbook) -> None:
    ws = wb.create_sheet("👥 Клиенты")
    ws["A1"] = "👥 Клиенты — мини-CRM"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = (
        "Строка на человека, за которого держишься: лид → пробное → активен → ушёл. "
        "Полный список всех, кто заходил, — во вкладке «Аналитика» (авто). "
        "«Сводка» справа считается сама."
    )
    ws["A2"].font = NOTE_FONT
    header = [
        "Имя / @",
        "Контакт",
        "Сегмент",
        "Продукт",
        "Цена/мес $",
        "Дата старта",
        "Оплачен до",
        "Статус",
        "Заметка",
    ]
    ws.append([])  # row 3 spacer
    ws.append(header)  # row 4
    _style_header(ws, 4, len(header))
    ws.append(
        [
            "@maria_y",
            "t.me/maria_y",
            "spina",
            "Онлайн-группа",
            50,
            "2026-08-15",
            "2026-09-15",
            "Активен",
            "Пришла по слову СПИНА",
        ]
    )
    _section(ws, "K4", "Сводка")
    summary = [
        ("Активных", '=COUNTIF(H5:H1000,"Активен")'),
        ("Доход в месяц, $", '=SUMIF(H5:H1000,"Активен",E5:E1000)'),
        ("Пробных", '=COUNTIF(H5:H1000,"Пробное")'),
        ("Лидов", '=COUNTIF(H5:H1000,"Лид")'),
        ("Ушли", '=COUNTIF(H5:H1000,"Ушёл")'),
    ]
    for i, (label, formula) in enumerate(summary, start=5):
        ws.cell(row=i, column=11, value=label)
        ws.cell(row=i, column=12, value=formula)
    ws.freeze_panes = "A5"
    _autosize(
        ws,
        {1: 16, 2: 20, 3: 12, 4: 16, 5: 12, 6: 13, 7: 13, 8: 12, 9: 30, 11: 18, 12: 10},
    )
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = WRAP


if __name__ == "__main__":
    build()
