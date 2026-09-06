"""Is anything happening in a symbol today. Pure functions, no I/O."""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Sequence

from .models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Catalyst

PRICE_MOVE_PCT = 4.0      # a daily move at least this large is a catalyst
WK52_WINDOW_DAYS = 252    # trailing closes that make up a "52-week" window
MIN_HISTORY_DAYS = 30     # fewer closes than this and we do not judge extremes


def detect(
    symbol: str,
    change_pct: Optional[float],
    closes: Sequence[float],
    price_move_pct: float = PRICE_MOVE_PCT,
    window: int = WK52_WINDOW_DAYS,
    min_history: int = MIN_HISTORY_DAYS,
) -> List[Catalyst]:
    """Catalysts for one symbol on one day.

    change_pct  today's percent move, or None if unknown.
    closes      trailing daily closes oldest..newest; closes[-1] is today's.
    """
    found: List[Catalyst] = []

    if change_pct is not None and abs(change_pct) >= price_move_pct:
        found.append(Catalyst(PRICE_MOVE, symbol, {"change_pct": change_pct, "price": closes[-1] if closes else 0.0}))

    recent = list(closes[-window:])
    if len(recent) >= min_history:
        today = recent[-1]
        history = recent[:-1]
        if today > max(history):
            found.append(Catalyst(WK52_HIGH, symbol, {"price": today, "prev_high": max(history)}))
        elif today < min(history):
            found.append(Catalyst(WK52_LOW, symbol, {"price": today, "prev_low": min(history)}))

    return found


def strongest(catalysts: Sequence[Catalyst]) -> Catalyst:
    """Headline catalyst: a 52-week extreme beats any price move, then strength."""
    return max(catalysts, key=lambda c: (c.kind in (WK52_HIGH, WK52_LOW), c.strength()))


def priority_score(balance: Decimal, catalysts: Sequence[Catalyst]) -> float:
    """Rank clients for sending: balance scaled by the strongest catalyst, so a
    bigger account with a bigger move goes first when the send budget is tight."""
    if not catalysts:
        return 0.0
    return round(float(balance) * (1.0 + max(c.strength() for c in catalysts)), 2)
