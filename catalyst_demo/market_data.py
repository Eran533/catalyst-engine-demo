"""Daily close prices.

`PriceHistory` is the only thing the rest of the engine talks to. It can be
loaded from a CSV (the demo) or generated as a seeded random walk (the data
generator). In production this seam is where a real market-data feed plugs in.
"""
from __future__ import annotations

import csv
import random
from bisect import bisect_right
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def trading_days(start: date, end: date) -> List[date]:
    """Weekdays from start to end inclusive. Exchange holidays are ignored,
    which is good enough for a demo and stated in the README."""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


class PriceHistory:
    def __init__(self, series: Dict[str, List[Tuple[date, float]]]):
        # each series is sorted by date ascending
        self._series = {s: sorted(rows) for s, rows in series.items()}
        self._dates = {s: [d for d, _ in rows] for s, rows in self._series.items()}

    # ---- construction -------------------------------------------------

    @classmethod
    def from_csv(cls, path: Path) -> "PriceHistory":
        series: Dict[str, List[Tuple[date, float]]] = {}
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                series.setdefault(row["symbol"], []).append(
                    (date.fromisoformat(row["date"]), float(row["close"]))
                )
        return cls(series)

    @classmethod
    def synthetic(
        cls,
        symbols: Iterable[str],
        start: date,
        end: date,
        seed: int = 7,
        daily_vol: float = 0.02,
    ) -> "PriceHistory":
        """A seeded geometric random walk per symbol. Deterministic for a seed."""
        rng = random.Random(seed)
        days = trading_days(start, end)
        series: Dict[str, List[Tuple[date, float]]] = {}
        for sym in symbols:
            price = rng.uniform(8.0, 400.0)
            drift = rng.uniform(-0.0004, 0.0008)
            rows = []
            for d in days:
                price *= 1.0 + rng.gauss(drift, daily_vol)
                rows.append((d, round(max(price, 0.5), 2)))
            series[sym] = rows
        return cls(series)

    def to_csv(self, path: Path) -> None:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["symbol", "date", "close"])
            for sym in sorted(self._series):
                for d, close in self._series[sym]:
                    w.writerow([sym, d.isoformat(), f"{close:.2f}"])

    def override_close(self, symbol: str, on: date, close: float) -> None:
        """Used by the data generator to script a catalyst on a chosen day."""
        rows = self._series[symbol]
        for i, (d, _) in enumerate(rows):
            if d == on:
                rows[i] = (d, round(close, 2))
                return
        raise KeyError(f"{symbol} has no bar on {on}")

    # ---- queries ------------------------------------------------------

    @property
    def symbols(self) -> List[str]:
        return sorted(self._series)

    def closes(self, symbol: str, end: date, days: int) -> List[float]:
        """Up to `days` closes ending on or before `end`, oldest first."""
        rows = self._series.get(symbol, [])
        idx = bisect_right(self._dates[symbol], end) if rows else 0
        return [c for _, c in rows[max(0, idx - days) : idx]]

    def close_on(self, symbol: str, on: date) -> Optional[float]:
        rows = self._series.get(symbol, [])
        if not rows:
            return None
        idx = bisect_right(self._dates[symbol], on)
        if idx == 0 or rows[idx - 1][0] != on:
            return None
        return rows[idx - 1][1]

    def daily_change_pct(self, symbol: str, on: date) -> Optional[float]:
        """Percent change from the previous close to the close on `on`."""
        last_two: Sequence[float] = self.closes(symbol, on, 2)
        if len(last_two) < 2 or self.close_on(symbol, on) is None:
            return None
        prev, today = last_two
        if prev == 0:
            return None
        return round((today - prev) / prev * 100.0, 2)
