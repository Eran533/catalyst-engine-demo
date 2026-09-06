"""Idempotency state: have we already contacted this client today.

Two guards, both one day in the demo: a client gets at most one notification
per day, and the same (client, symbol, catalyst) is not repeated within the
cooldown. The state is a small JSON file written atomically so a crash mid-run
never leaves a half-written file behind.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Dict

from .models import Catalyst

MIN_DAYS_BETWEEN_NOTIFICATIONS = 1
CATALYST_COOLDOWN_DAYS = 1


def _key(account_id: str, c: Catalyst) -> str:
    return f"{account_id}|{c.symbol}|{c.kind}"


class State:
    def __init__(self, by_client: Dict[str, str] = None, by_catalyst: Dict[str, str] = None):
        self.by_client: Dict[str, str] = dict(by_client or {})
        self.by_catalyst: Dict[str, str] = dict(by_catalyst or {})

    @classmethod
    def load(cls, path: Path) -> "State":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            return cls()
        return cls(data.get("by_client"), data.get("by_catalyst"))

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump({"by_client": self.by_client, "by_catalyst": self.by_catalyst}, f, indent=2, sort_keys=True)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def is_suppressed(
        self,
        account_id: str,
        c: Catalyst,
        today: date,
        min_days: int = MIN_DAYS_BETWEEN_NOTIFICATIONS,
        cooldown: int = CATALYST_COOLDOWN_DAYS,
    ) -> bool:
        last_client = self.by_client.get(account_id)
        if last_client and (today - date.fromisoformat(last_client)).days < min_days:
            return True
        last_cat = self.by_catalyst.get(_key(account_id, c))
        if last_cat and (today - date.fromisoformat(last_cat)).days < cooldown:
            return True
        return False

    def record(self, account_id: str, c: Catalyst, today: date) -> None:
        iso = today.isoformat()
        self.by_client[account_id] = iso
        self.by_catalyst[_key(account_id, c)] = iso
