# -*- coding: utf-8 -*-
"""
SV Logging utilities: ASCII-only log formatter to avoid Windows console emoji corruption.
Does not affect message content; only sanitizes log output.
"""
import logging
import re
from typing import Optional

# Map common emojis to ASCII tags for logs
EMOJI_TAGS = {
    '✅': '[OK]', '✔': '[OK]', '❌': '[ERR]', '✖': '[ERR]', '⚠': '[WARN]',
    '🚀': '[START]', '🌅': '[MORNING]', '🌞': '[NOON]', '🌆': '[EVENING]',
    '🧠': '[ML]', '🤖': '[BOT]', '📊': '[CHART]', '📈': '[UP]', '📉': '[DOWN]',
    '📅': '[CAL]', '📰': '[NEWS]', '🔗': '[LINK]', '💡': '[HINT]', '🔥': '[HOT]',
    '🔍': '[SEARCH]', '🏆': '[TROPHY]', '🎯': '[TARGET]', '🔮': '[FORECAST]',
    '🛡': '[RISK]', '⚡': '[FAST]', '🌍': '[WORLD]', '🌐': '[WORLD]',
    '📂': '[SAVE]', '📁': '[DIR]', '📄': '[FILE]', '🧭': '[NAV]', '⭐': '[STAR]',
    '🧪': '[TEST]', '🔧': '[CFG]', '⏰': '[TIME]', '🕒': '[TIME]', '₿': '[BTC]',
}

EMOJI_PATTERN = re.compile('|'.join(map(re.escape, EMOJI_TAGS.keys())))


def _replace_emojis(text: str) -> str:
    def repl(m):
        return EMOJI_TAGS.get(m.group(0), '')
    return EMOJI_PATTERN.sub(repl, text)


def sanitize_log_text(text: str) -> str:
    if text is None:
        return text
    try:
        # Replace known emojis with tags
        s = _replace_emojis(text)
        # Finally strip any remaining non-ASCII bytes to avoid mojibake
        s = s.encode('ascii', 'ignore').decode('ascii')
        return s
    except Exception:
        try:
            return text.encode('ascii', 'ignore').decode('ascii')
        except Exception:
            return '[LOG]'


class AsciiSanitizingFormatter(logging.Formatter):
    """Formatter that replaces emojis with ASCII tags and strips non-ASCII."""
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return sanitize_log_text(formatted)


def install_ascii_logging(fmt: Optional[str] = None, datefmt: Optional[str] = None) -> None:
    """Install ASCII-sanitizing formatter on all existing handlers; add StreamHandler if none.
    Idempotent and safe to call multiple times.
    """
    root = logging.getLogger()
    if fmt is None:
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = AsciiSanitizingFormatter(fmt=fmt, datefmt=datefmt)

    # Remove existing handlers to avoid duplicate outputs and enforce sanitization
    for h in list(root.handlers):
        root.removeHandler(h)
    
    # Add a single sanitized stream handler
    h = logging.StreamHandler()
    h.setFormatter(formatter)
    root.addHandler(h)

    # Ensure at least INFO level by default
    if root.level == logging.NOTSET:
        root.setLevel(logging.INFO)
