"""How a notification leaves the engine.

The engine only knows the `Notifier` protocol. The demo ships a console
printer and a JSON-lines writer; production swaps in a client that calls the
broker's push API. Every notifier returns True on delivery so the engine can
record state only for messages that actually went out.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List, Protocol

from .models import Notification


class Notifier(Protocol):
    def send(self, n: Notification) -> bool: ...


class ConsoleNotifier:
    def send(self, n: Notification) -> bool:
        print(f"[{n.account_id}] {n.subject}\n    {n.body}")
        return True


class JsonlNotifier:
    """Appends one JSON object per notification. Doubles as the send log the
    engagement report reads."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, n: Notification) -> bool:
        row = asdict(n)
        row["sent_on"] = n.sent_on.isoformat() if n.sent_on else None
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True


class CollectingNotifier:
    """Keeps everything in memory. Used by tests and dry runs."""

    def __init__(self) -> None:
        self.sent: List[Notification] = []

    def send(self, n: Notification) -> bool:
        self.sent.append(n)
        return True


class MultiNotifier:
    def __init__(self, *notifiers: Notifier):
        self.notifiers = notifiers

    def send(self, n: Notification) -> bool:
        return all(nf.send(n) for nf in self.notifiers)
