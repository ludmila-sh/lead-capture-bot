"""All client-facing text and button labels — the single place a non-developer edits.

Code/identifiers: English. User-facing strings: Russian.
This mirrors the external "source of truth" (the scripts spreadsheet).
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Lead magnets / segments ----------------------------------------------
# One entry per social-funnel segment. The key is the deep-link parameter
# (t.me/<bot>?start=<key>) — Telegram allows only [A-Za-z0-9_-], so keys are
# latin slugs even though the funnel talks about "спина" / "мама".
# `link` is a placeholder resource URL — replace per deployment.


@dataclass(frozen=True)
class LeadMagnet:
    label: str  # human name for logs / source tagging, e.g. "Спина"
    link: str  # URL of the resource to deliver
    text: str  # message body; may contain the "{link}" placeholder


# Used when /start arrives with no parameter or an unknown one.
DEFAULT_SEGMENT = "base"

LEAD_MAGNETS: dict[str, LeadMagnet] = {
    "base": LeadMagnet(
        label="Общая",
        link="https://www.youtube.com/watch?v=FfyhZFAmhSE",
        text=(
            "Держите бесплатную практику 🎁\n\n"
            "👉 {link}\n\n"
            "Короткая последовательность на 15 минут — можно выполнять дома, без инвентаря.\n\n"
            "Напишите пару слов о себе: что беспокоит и чего хотели бы достичь? "
            "Так эксперт сможет подсказать точнее."
        ),
    ),
    "spina": LeadMagnet(
        label="Спина",
        link="https://www.youtube.com/watch?v=GAAB323gC3M",
        text=(
            "Держите бесплатную практику для спины 🎁\n\n"
            "👉 {link}\n\n"
            "Мягкая последовательность на 15 минут, чтобы разгрузить поясницу — "
            "дома, без инвентаря.\n\n"
            "Напишите пару слов о себе: что беспокоит и как давно? "
            "Так эксперт сможет подсказать точнее."
        ),
    ),
    "sheya": LeadMagnet(
        label="Шея-плечи",
        link="https://www.youtube.com/watch?v=WfPSddHeTmo&t=1141s",
        text=(
            "Держите бесплатную практику для шеи и плеч 🎁\n\n"
            "👉 {link}\n\n"
            "15 минут мягкой работы, чтобы снять зажимы после рабочего дня — "
            "дома, без инвентаря.\n\n"
            "Напишите пару слов о себе: что беспокоит и как давно? "
            "Так эксперт сможет подсказать точнее."
        ),
    ),
    "mama": LeadMagnet(
        label="Мама",
        link="https://www.youtube.com/watch?v=xLC6SaigJsM",
        text=(
            "Держите бесплатную практику для мам 🎁\n\n"
            "👉 {link}\n\n"
            "Бережная последовательность на 15 минут для восстановления — "
            "можно заниматься дома, пока малыш спит.\n\n"
            "Напишите пару слов о себе: сколько времени прошло после родов и что беспокоит? "
            "Так эксперт сможет подсказать точнее."
        ),
    ),
}


def find_segment(raw: str | None) -> str | None:
    """Return a known segment key for a /start parameter, or None if unknown."""
    key = (raw or "").strip().lower()
    return key if key in LEAD_MAGNETS else None


def lead_magnet(segment: str | None) -> LeadMagnet:
    """Resolve a segment key to its LeadMagnet, falling back to the default."""
    return LEAD_MAGNETS.get(segment or "", LEAD_MAGNETS[DEFAULT_SEGMENT])


# --- Button labels --------------------------------------------------------
BTN_PRACTICE = "🧘 Практика"
BTN_FAQ = "❓ Частые вопросы"
BTN_EXPERT = "💬 Написать эксперту"
BTN_SUBSCRIBE = "📣 Подписаться на канал"
BTN_WRITE_EXPERT = "💬 Открыть чат с экспертом"
BTN_BACK_TO_MENU = "🏠 В меню"
BTN_BACK_TO_FAQ = "⬅️ К вопросам"

# --- Screens -----------------------------------------------------------------
GREETING = (
    "Здравствуйте! 🙏\n\n"
    "Это бот-помощник. Здесь можно:\n"
    "• получить бесплатную практику;\n"
    "• прочитать ответы на частые вопросы;\n"
    "• написать эксперту напрямую.\n\n"
    "Выберите, что вам интересно:"
)

MENU_PROMPT = "Чем могу помочь?"

# Shown once, right before the lead magnet, when a user arrives via a deep link.
GREETING_LEAD = "Спасибо, что заглянули! 🙏 Ниже — обещанная практика."

FAQ_INTRO = "Выберите вопрос:"

# List of (question, answer). 3–5 entries. Question doubles as the button label.
FAQ = [
    (
        "С чего начать новичку?",
        "Начните с бесплатной практики из раздела «Практика» — она рассчитана на любой "
        "уровень. Оптимально заниматься 2–3 раза в неделю.",
    ),
    (
        "Нужен ли инвентарь?",
        "Нет. Достаточно коврика и удобной одежды. Блоки и ремень при желании можно "
        "заменить книгами и поясом.",
    ),
    (
        "Сколько длится занятие?",
        "Бесплатная практика — 15 минут. Занятия с экспертом обычно длятся 60–75 минут.",
    ),
    (
        "Как проходят занятия с экспертом?",
        "Онлайн по видеосвязи, индивидуально или в мини-группе. Расписание и стоимость "
        "эксперт присылает в личном сообщении.",
    ),
    (
        "У меня боль в спине — можно заниматься?",
        "Это важный вопрос, и заочно на него ответить нельзя. Напишите эксперту через "
        "раздел «Написать эксперту» — он подскажет, что подойдёт именно вам.",
    ),
]

EXPERT = (
    "Эксперт ответит на вопросы о занятиях, расписании и стоимости и поможет подобрать "
    "практику под вашу ситуацию.\n\n"
    "Нажмите кнопку ниже, чтобы открыть чат:"
)

# Sent to the user after we have notified the expert about a handoff.
HANDOFF_ACK = (
    "Я передал ваш запрос эксперту — он свяжется с вами здесь, в Telegram. "
    "Если хотите, можете написать ему сами:"
)

# Free-text messages containing any of these (case-insensitive substring) are
# treated as a health question -> hand off to the expert, never answered by the bot.
HEALTH_KEYWORDS = [
    "боль",
    "болит",
    "болью",
    "ноет",
    "защемил",
    "защемление",
    "спазм",
    "поясниц",
    "грыж",
    "протруз",
    "остеохондроз",
    "сколиоз",
    "травм",
    "диагноз",
    "операц",
    "врач",
    "мрт",
    "давлен",
    "головокружен",
    "беремен",
    "родила",
    "послеродов",
    "колено",
    "сустав",
]

HEALTH_REPLY = (
    "Спасибо, что написали. Это важный вопрос про здоровье, и отвечать на него "
    "заочно я не могу. Я передал ваше сообщение эксперту — он свяжется с вами. "
    "Вы также можете написать ему напрямую:"
)

# Message the bot sends to the expert's chat. All fields are filled in code.
HANDOFF_TO_EXPERT = (
    "🔔 <b>Новый лид</b>\n\n"
    "Имя: {name}\n"
    "Контакт: {contact}\n"
    "ID: <code>{user_id}</code>\n"
    "Сегмент: {segment}\n"
    "Повод: {reason}"
)

# Shown for any input the bot does not understand (free text, unknown callback).
FALLBACK = (
    "Спасибо за сообщение! Я бот и работаю по меню. Если это вопрос эксперту — "
    "нажмите «💬 Написать эксперту». А пока вот меню:"
)
