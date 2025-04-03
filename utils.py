import re
import html
import json
from aiogram.types import BotCommand


with open("translations.json", "r", encoding="utf-8") as f:
    _translations = json.load(f)

def extract_translations(key: str, lang: str = "en") -> str:
    return _translations.get(key, {}).get(lang, _translations.get(key, {}).get("en", key))


def get_bot_commands(lang: str = "en") -> list[BotCommand]:
    cmd_data = _translations.get("commands.menu", {}).get(lang, {})
    return [
        BotCommand(command="start", description=cmd_data.get("start", "Start")),
        BotCommand(command="newsession", description=cmd_data.get("newsession", "New session")),
        BotCommand(command="sessions", description=cmd_data.get("sessions", "Sessions")),
        BotCommand(command="lang", description=cmd_data.get("lang", "Language")),
        # BotCommand(command="me", description=cmd_data.get("me", "Profile")),
    ]


def markdown_to_html(text: str) -> str:
    # First decode any HTML entities like &x27; → '
    text = html.unescape(text)

    # Escape only what Telegram needs
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Headers: ### Title → <b>Title</b>
    text = re.sub(r'#+\s*(.+)', r'<b>\1</b>', text)

    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

    # Italic: *text* or _text_
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<i>\1</i>', text)

    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # Bullets
    text = re.sub(r'(?m)^[-*+]\s+', r'• ', text)

    return text
