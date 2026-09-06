"""Who is dormant, and which symbols does each of them care about.

Pure functions over in-memory lists. In production these are SQL queries over
the trade history and open positions; the shape of the answer is the same.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .market_data import trading_days
from .models import Client, Position, Trade

INACTIVE_TRADING_DAYS = 7  # dormant = no trade for at least this many trading days
FAVOURITE_LOOKBACK_DAYS = 365
TOP_N_FAVOURITES = 2


def last_trade_date(trades: Iterable[Trade], account_id: str, before: date) -> Optional[date]:
    """Most recent trade strictly before `before`. Today's trades are excluded on
    purpose: the run happens during the day, and a trade made after the push is
    the response we are trying to cause, not a reason to skip the client."""
    dates = [t.trade_date for t in trades if t.account_id == account_id and t.trade_date < before]
    return max(dates) if dates else None


def trading_days_since(last: date, today: date) -> int:
    """Trading days strictly after `last` up to and including `today`."""
    if last >= today:
        return 0
    return len(trading_days(last + timedelta(days=1), today))


def dormant_clients(
    clients: Sequence[Client],
    trades: Sequence[Trade],
    today: date,
    inactive_days: int = INACTIVE_TRADING_DAYS,
) -> List[Tuple[Client, int]]:
    """Clients whose last trade is at least `inactive_days` trading days ago.
    Clients who never traded have no favourites and are skipped. Returns
    (client, days_inactive) pairs."""
    out = []
    for c in clients:
        last = last_trade_date(trades, c.account_id, today)
        if last is None:
            continue
        idle = trading_days_since(last, today)
        if idle >= inactive_days:
            out.append((c, idle))
    return out


def favourites(
    trades: Sequence[Trade],
    positions: Sequence[Position],
    account_id: str,
    today: date,
    lookback_days: int = FAVOURITE_LOOKBACK_DAYS,
    top_n: int = TOP_N_FAVOURITES,
) -> List[str]:
    """Symbols currently held are always favourites; then the `top_n` most
    traded symbols inside the lookback window. Order: held first, then by
    trade count."""
    held = sorted({p.symbol for p in positions if p.account_id == account_id and p.quantity != 0})
    since = today - timedelta(days=lookback_days)
    counts = Counter(
        t.symbol
        for t in trades
        if t.account_id == account_id and since <= t.trade_date <= today and t.symbol not in held
    )
    traded = [s for s, _ in counts.most_common(top_n)]
    return held + traded


def build_universe(
    clients: Sequence[Client],
    trades: Sequence[Trade],
    positions: Sequence[Position],
    today: date,
    inactive_days: int = INACTIVE_TRADING_DAYS,
) -> Dict[str, Tuple[Client, int, List[str]]]:
    """account_id -> (client, days_inactive, favourite symbols) for every dormant
    client with at least one favourite."""
    universe = {}
    for client, idle in dormant_clients(clients, trades, today, inactive_days):
        favs = favourites(trades, positions, client.account_id, today)
        if favs:
            universe[client.account_id] = (client, idle, favs)
    return universe
