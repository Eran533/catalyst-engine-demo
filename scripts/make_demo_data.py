"""Generate the synthetic data set in ./data. Deterministic for a given seed.

    python scripts/make_demo_data.py [--seed 7] [--clients 200] [--out data]

Nothing here comes from a real brokerage: account ids, names, balances, trades
and prices are all invented. Tickers are real symbols so the output reads
naturally, but their prices are a random walk.

A handful of catalysts are scripted onto the last trading day so a first run
has something to show. They are listed in data/README.md.
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalyst_demo.market_data import PriceHistory, trading_days  # noqa: E402

SYMBOLS = [
    "AAPL", "AMD", "AMZN", "ARM", "AVGO", "BA", "COIN", "CRWD", "DIS", "GOOGL",
    "HOOD", "INTC", "IREN", "META", "MRVL", "MSFT", "MSTR", "MU", "NFLX", "NVDA",
    "PLTR", "PYPL", "QQQ", "RIVN", "SHOP", "SMCI", "SNAP", "SOFI", "SOXL", "SPY",
    "TSLA", "TSM", "UBER", "UNH", "VRT", "WMT", "XOM",
]

FIRST = ["Noa", "Daniel", "Maya", "Yoav", "Tamar", "Omer", "Shira", "Eitan", "Lior", "Adi",
         "Emma", "Liam", "Olivia", "Ethan", "Sophia", "Mason", "Ava", "Lucas", "Mia", "Leo"]
LAST = ["Levi", "Cohen", "Peretz", "Mizrahi", "Friedman", "Katz", "Biton", "Azulay",
        "Smith", "Johnson", "Brown", "Miller", "Davis", "Wilson", "Taylor", "Clark"]

START = date(2025, 6, 2)
END = date(2026, 9, 4)   # last trading day in the set; run the engine on this date

# (symbol, kind, size): scripted catalysts on END so the demo shows results
SCRIPTED = [
    ("SMCI", "price_move", +7.4),
    ("SOXL", "price_move", -5.9),
    ("NVDA", "52w_high", None),
    ("RIVN", "52w_low", None),
    ("HOOD", "price_move", +4.6),
]


def make_clients(rng: random.Random, n: int):
    out = []
    for i in range(1, n + 1):
        lang = "he" if rng.random() < 0.6 else "en"
        balance = round(rng.lognormvariate(8.0, 1.1), 2)  # median ~ $3k, long tail
        out.append({
            "account_id": f"ACC-{i:04d}",
            "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "language": lang,
            "balance": f"{balance:.2f}",
        })
    return out


def make_trades(rng: random.Random, clients, prices: PriceHistory):
    """Each client has two or three favourite symbols and a personal activity
    level. About 40% go quiet in the last few weeks so the universe is not empty."""
    days = trading_days(START, END)
    trades = []
    positions = []
    for c in clients:
        favs = rng.sample(SYMBOLS, k=rng.choice([2, 2, 3]))
        activity = rng.uniform(0.02, 0.25)          # chance of trading on a given day
        quiet_from = None
        if rng.random() < 0.4:
            quiet_from = END - timedelta(days=rng.randint(10, 120))
        for d in days:
            if quiet_from and d > quiet_from:
                break
            if rng.random() < activity:
                sym = rng.choice(favs) if rng.random() < 0.85 else rng.choice(SYMBOLS)
                px = prices.close_on(sym, d) or 100.0
                qty = rng.choice([-1, 1]) * rng.randint(1, 60)
                trades.append({
                    "account_id": c["account_id"], "symbol": sym, "trade_date": d.isoformat(),
                    "quantity": qty, "price": f"{px * rng.uniform(0.995, 1.005):.2f}",
                })
        # A few of the quiet clients come back on the last day and trade one of
        # the scripted catalyst symbols, so the engagement report has rows.
        if quiet_from and rng.random() < 0.12:
            sym = rng.choice([s for s, _, _ in SCRIPTED])
            favs.append(sym)
            px = prices.close_on(sym, END) or 100.0
            for _ in range(rng.randint(1, 4)):
                trades.append({
                    "account_id": c["account_id"], "symbol": sym, "trade_date": END.isoformat(),
                    "quantity": rng.randint(1, 40), "price": f"{px * rng.uniform(0.995, 1.005):.2f}",
                })
        if rng.random() < 0.5:
            positions.append({"account_id": c["account_id"], "symbol": rng.choice(favs),
                              "quantity": rng.randint(1, 80)})
    return trades, positions


def script_catalysts(prices: PriceHistory) -> None:
    for sym, kind, size in SCRIPTED:
        closes = prices.closes(sym, END, 252)
        prev = closes[-2]
        if kind == "price_move":
            prices.override_close(sym, END, prev * (1 + size / 100.0))
        elif kind == "52w_high":
            prices.override_close(sym, END, max(closes[:-1]) * 1.02)
        elif kind == "52w_low":
            prices.override_close(sym, END, min(closes[:-1]) * 0.98)


def write_csv(path: Path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--clients", type=int, default=200)
    p.add_argument("--out", default="data")
    args = p.parse_args(argv)

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    prices = PriceHistory.synthetic(SYMBOLS, START, END, seed=args.seed)
    script_catalysts(prices)
    clients = make_clients(rng, args.clients)
    trades, positions = make_trades(rng, clients, prices)

    prices.to_csv(out / "prices.csv")
    write_csv(out / "clients.csv", clients, ["account_id", "name", "language", "balance"])
    write_csv(out / "trades.csv", trades, ["account_id", "symbol", "trade_date", "quantity", "price"])
    write_csv(out / "positions.csv", positions, ["account_id", "symbol", "quantity"])
    (out / "README.md").write_text(
        "# Synthetic demo data\n\n"
        f"Generated by `scripts/make_demo_data.py --seed {args.seed} --clients {args.clients}`.\n"
        "Every account, name, balance, trade and price is invented.\n\n"
        f"Last trading day in the set: **{END}**. Scripted catalysts on that day:\n\n"
        + "".join(f"- {s}: {k}{'' if v is None else f' {v:+.1f}%'}\n" for s, k, v in SCRIPTED)
    )
    print(f"wrote {len(clients)} clients, {len(trades)} trades, {len(positions)} positions, "
          f"{len(SYMBOLS)} symbols x {len(trading_days(START, END))} days -> {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
