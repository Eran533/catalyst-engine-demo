"""Did the notification lead to anything. Reads the JSON-lines send log and the
trade history, and reports who traded on the day they were notified."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Sequence

from .models import Trade


@dataclass
class EngagementRow:
    account_id: str
    symbol: str
    catalyst: str
    trades_after: int
    traded_symbol: bool


@dataclass
class Engagement:
    day: date
    notified: int
    traded: int
    rows: List[EngagementRow]

    @property
    def traded_pct(self) -> float:
        return round(100.0 * self.traded / self.notified, 1) if self.notified else 0.0


def load_send_log(path: Path, day: date) -> List[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("sent_on") == day.isoformat():
                rows.append(row)
    return rows


def engagement(send_log: Sequence[dict], trades: Sequence[Trade], day: date) -> Engagement:
    by_account: Dict[str, List[Trade]] = {}
    for t in trades:
        if t.trade_date == day:
            by_account.setdefault(t.account_id, []).append(t)

    rows: List[EngagementRow] = []
    for n in send_log:
        acct = n["account_id"]
        after = by_account.get(acct, [])
        rows.append(EngagementRow(
            account_id=acct, symbol=n["symbol"], catalyst=n["catalyst"]["kind"],
            trades_after=len(after), traded_symbol=any(t.symbol == n["symbol"] for t in after),
        ))
    rows.sort(key=lambda r: (-r.trades_after, r.account_id))
    return Engagement(day, len(rows), sum(1 for r in rows if r.trades_after), rows)


def format_engagement(e: Engagement) -> str:
    lines = [
        f"Engagement for {e.day}",
        f"  notified: {e.notified}",
        f"  traded same day: {e.traded} ({e.traded_pct}%)",
        "",
        f"  {'account':<10} {'symbol':<7} {'catalyst':<11} {'trades':>6}  same symbol",
    ]
    for r in e.rows:
        if r.trades_after:
            lines.append(f"  {r.account_id:<10} {r.symbol:<7} {r.catalyst:<11} {r.trades_after:>6}  {'yes' if r.traded_symbol else 'no'}")
    return "\n".join(lines)
