"""Message text in the client's language. Keep this the only place that knows
how to phrase things, so a copy change never touches the engine."""
from __future__ import annotations

from typing import Tuple

from .models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Catalyst

_SUBJECT = {
    "en": {
        PRICE_MOVE: "{symbol} moved {change:+.1f}% today",
        WK52_HIGH: "{symbol} hit a 52-week high",
        WK52_LOW: "{symbol} hit a 52-week low",
    },
    "he": {
        PRICE_MOVE: "{symbol} זז היום {change:+.1f}%",
        WK52_HIGH: "{symbol} הגיע לשיא 52 שבועות",
        WK52_LOW: "{symbol} הגיע לשפל 52 שבועות",
    },
}

_BODY = {
    "en": {
        PRICE_MOVE: "Hi {name}, {symbol}, a stock you have traded before, is {direction} {change:+.1f}% today at ${price:,.2f}. Worth a look.",
        WK52_HIGH: "Hi {name}, {symbol}, a stock you have traded before, just set a new 52-week high at ${price:,.2f}.",
        WK52_LOW: "Hi {name}, {symbol}, a stock you have traded before, just touched a 52-week low at ${price:,.2f}.",
    },
    "he": {
        PRICE_MOVE: "שלום {name}, המניה {symbol} שסחרת בה בעבר {direction} היום {change:+.1f}% למחיר ${price:,.2f}. שווה מבט.",
        WK52_HIGH: "שלום {name}, המניה {symbol} שסחרת בה בעבר קבעה שיא 52 שבועות חדש במחיר ${price:,.2f}.",
        WK52_LOW: "שלום {name}, המניה {symbol} שסחרת בה בעבר נגעה בשפל 52 שבועות במחיר ${price:,.2f}.",
    },
}

_DIRECTION = {"en": {"up": "up", "down": "down"}, "he": {"up": "עלתה", "down": "ירדה"}}


def render(c: Catalyst, client_name: str, language: str) -> Tuple[str, str]:
    """(subject, body) for one catalyst. Unknown languages fall back to English."""
    lang = language if language in _SUBJECT else "en"
    fields = {
        "name": client_name,
        "symbol": c.symbol,
        "change": c.detail.get("change_pct", 0.0),
        "price": c.detail.get("price", 0.0),
        "direction": _DIRECTION[lang][c.direction],
    }
    return _SUBJECT[lang][c.kind].format(**fields), _BODY[lang][c.kind].format(**fields)
