"""The daily run. Wires universe, catalysts, state, templates and notifier."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Sequence, Tuple

from . import catalysts as cat
from .market_data import PriceHistory
from .models import Client, Notification, Position, Trade
from .notifier import Notifier
from .state import State
from .templates import render
from .universe import INACTIVE_TRADING_DAYS, build_universe


@dataclass
class Config:
    inactive_days: int = INACTIVE_TRADING_DAYS
    price_move_pct: float = cat.PRICE_MOVE_PCT
    window: int = cat.WK52_WINDOW_DAYS
    min_history: int = cat.MIN_HISTORY_DAYS
    send_cap: int = 0  # 0 = unlimited; production runs with a daily budget


@dataclass
class RunSummary:
    today: date
    dormant: int
    symbols_checked: int
    symbols_with_catalyst: int
    candidates: int
    suppressed: int
    sent: int


def plan(
    today: date,
    clients: Sequence[Client],
    trades: Sequence[Trade],
    positions: Sequence[Position],
    prices: PriceHistory,
    state: State,
    config: Config = Config(),
) -> Tuple[List[Notification], RunSummary]:
    """Everything up to sending: the ranked list of notifications for today."""
    universe = build_universe(clients, trades, positions, today, config.inactive_days)

    # Detect once per symbol, not once per client.
    symbols = sorted({s for _, _, favs in universe.values() for s in favs})
    found: Dict[str, list] = {}
    for sym in symbols:
        closes = prices.closes(sym, today, config.window)
        if not closes or prices.close_on(sym, today) is None:
            continue
        hits = cat.detect(sym, prices.daily_change_pct(sym, today), closes,
                          config.price_move_pct, config.window, config.min_history)
        if hits:
            found[sym] = hits

    candidates: List[Notification] = []
    suppressed = 0
    for account_id, (client, _idle, favs) in universe.items():
        hits = [c for s in favs for c in found.get(s, [])]
        if not hits:
            continue
        headline = cat.strongest(hits)
        if state.is_suppressed(account_id, headline, today):
            suppressed += 1
            continue
        subject, body = render(headline, client.name, client.language)
        candidates.append(Notification(
            account_id=account_id, client_name=client.name, language=client.language,
            symbol=headline.symbol, catalyst=headline, subject=subject, body=body,
            score=cat.priority_score(client.balance, hits), sent_on=today,
        ))

    candidates.sort(key=lambda n: n.score, reverse=True)
    if config.send_cap:
        candidates = candidates[: config.send_cap]

    summary = RunSummary(today, len(universe), len(symbols), len(found),
                         len(candidates) + suppressed, suppressed, 0)
    return candidates, summary


def run(
    today: date,
    clients: Sequence[Client],
    trades: Sequence[Trade],
    positions: Sequence[Position],
    prices: PriceHistory,
    state: State,
    notifier: Notifier,
    config: Config = Config(),
    dry_run: bool = False,
) -> RunSummary:
    """Plan, then send. State is only recorded for messages that were delivered,
    so a failed send is retried on the next run instead of being lost."""
    notifications, summary = plan(today, clients, trades, positions, prices, state, config)
    if dry_run:
        return summary
    for n in notifications:
        if notifier.send(n):
            state.record(n.account_id, n.catalyst, today)
            summary.sent += 1
    return summary
