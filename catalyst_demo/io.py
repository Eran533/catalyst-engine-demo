"""CSV loaders for the demo data set. Production reads the same shapes from SQL."""
from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List

from .models import Client, Position, Trade


def load_clients(path: Path) -> List[Client]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Client(r["account_id"], r["name"], r["language"], Decimal(r["balance"]))
            for r in csv.DictReader(f)
        ]


def load_trades(path: Path) -> List[Trade]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Trade(r["account_id"], r["symbol"], date.fromisoformat(r["trade_date"]),
                  int(r["quantity"]), Decimal(r["price"]))
            for r in csv.DictReader(f)
        ]


def load_positions(path: Path) -> List[Position]:
    with open(path, newline="", encoding="utf-8") as f:
        return [Position(r["account_id"], r["symbol"], int(r["quantity"])) for r in csv.DictReader(f)]
