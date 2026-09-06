"""Command line entry point.

    python -m catalyst_demo run --date 2026-09-04 [--dry-run] [--data data]
    python -m catalyst_demo report --date 2026-09-04
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import engine
from .io import load_clients, load_positions, load_trades
from .market_data import PriceHistory
from .notifier import ConsoleNotifier, JsonlNotifier, MultiNotifier
from .report import engagement, format_engagement, load_send_log
from .state import State


def _load(data: Path):
    return (
        load_clients(data / "clients.csv"),
        load_trades(data / "trades.csv"),
        load_positions(data / "positions.csv"),
        PriceHistory.from_csv(data / "prices.csv"),
    )


def cmd_run(args: argparse.Namespace) -> int:
    data = Path(args.data)
    clients, trades, positions, prices = _load(data)
    state_path = data / "state.json"
    state = State.load(state_path)
    config = engine.Config(send_cap=args.cap)

    if args.dry_run:
        notifications, summary = engine.plan(args.date, clients, trades, positions, prices, state, config)
        print(f"DRY RUN {summary.today}: {summary.dormant} dormant clients, "
              f"{summary.symbols_with_catalyst}/{summary.symbols_checked} symbols with a catalyst, "
              f"{len(notifications)} would be sent, {summary.suppressed} suppressed")
        for n in notifications[: args.show]:
            print(f"  {n.score:>12,.0f}  {n.account_id}  {n.subject}")
        return 0

    notifier = MultiNotifier(ConsoleNotifier(), JsonlNotifier(data / "sent.jsonl"))
    summary = engine.run(args.date, clients, trades, positions, prices, state, notifier, config)
    state.save(state_path)
    print(f"\n{summary.today}: sent {summary.sent}, suppressed {summary.suppressed}, "
          f"{summary.symbols_with_catalyst}/{summary.symbols_checked} symbols had a catalyst")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    data = Path(args.data)
    log_path = data / "sent.jsonl"
    if not log_path.exists():
        print("no sent.jsonl yet; run the engine first", file=sys.stderr)
        return 1
    trades = load_trades(data / "trades.csv")
    print(format_engagement(engagement(load_send_log(log_path, args.date), trades, args.date)))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="catalyst_demo", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default="data", help="folder with clients/trades/positions/prices CSVs")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="detect catalysts and send today's notifications")
    r.add_argument("--date", type=date.fromisoformat, required=True)
    r.add_argument("--dry-run", action="store_true", help="plan only, send nothing, record nothing")
    r.add_argument("--cap", type=int, default=0, help="max notifications to send (0 = all)")
    r.add_argument("--show", type=int, default=15, help="rows to print in a dry run")
    r.set_defaults(fn=cmd_run)

    g = sub.add_parser("report", help="who traded on the day they were notified")
    g.add_argument("--date", type=date.fromisoformat, required=True)
    g.set_defaults(fn=cmd_report)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
