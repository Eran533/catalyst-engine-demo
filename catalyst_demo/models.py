"""Plain data types shared by every module. Nothing here touches I/O."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, Optional

PRICE_MOVE = "price_move"
WK52_HIGH = "52w_high"
WK52_LOW = "52w_low"


@dataclass(frozen=True)
class Client:
    account_id: str
    name: str
    language: str  # "en" or "he"
    balance: Decimal


@dataclass(frozen=True)
class Trade:
    account_id: str
    symbol: str
    trade_date: date
    quantity: int
    price: Decimal


@dataclass(frozen=True)
class Position:
    account_id: str
    symbol: str
    quantity: int


@dataclass(frozen=True)
class Catalyst:
    """One reason a symbol is interesting today."""

    kind: str  # PRICE_MOVE, WK52_HIGH or WK52_LOW
    symbol: str
    detail: Dict[str, float] = field(default_factory=dict)

    @property
    def direction(self) -> str:
        if self.kind == WK52_HIGH:
            return "up"
        if self.kind == WK52_LOW:
            return "down"
        return "up" if self.detail.get("change_pct", 0.0) >= 0 else "down"

    def strength(self, price_move_pct: float = 4.0) -> float:
        """Relative importance for ranking. A 52-week extreme is a fixed 1.5;
        a price move scales with its size and is capped at 3.0."""
        if self.kind in (WK52_HIGH, WK52_LOW):
            return 1.5
        return min(abs(self.detail.get("change_pct", 0.0)) / price_move_pct, 3.0)


@dataclass
class Notification:
    account_id: str
    client_name: str
    language: str
    symbol: str
    catalyst: Catalyst
    subject: str
    body: str
    score: float
    sent_on: Optional[date] = None
