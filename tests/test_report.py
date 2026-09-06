from datetime import date
from decimal import Decimal

from catalyst_demo.models import Trade
from catalyst_demo.report import engagement, format_engagement

DAY = date(2026, 9, 4)


def sent(acct, sym):
    return {"account_id": acct, "symbol": sym, "catalyst": {"kind": "price_move"}, "sent_on": DAY.isoformat()}


def test_engagement_counts_clients_who_traded_on_the_day():
    log = [sent("ACC-1", "SMCI"), sent("ACC-2", "SOXL"), sent("ACC-3", "NVDA")]
    trades = [
        Trade("ACC-1", "SMCI", DAY, 3, Decimal("1")),
        Trade("ACC-1", "AAPL", DAY, 1, Decimal("1")),
        Trade("ACC-2", "TSLA", DAY, 1, Decimal("1")),
        Trade("ACC-3", "NVDA", date(2026, 9, 5), 1, Decimal("1")),  # next day, not counted
    ]
    e = engagement(log, trades, DAY)
    assert (e.notified, e.traded, e.traded_pct) == (3, 2, 66.7)
    assert [(r.account_id, r.trades_after, r.traded_symbol) for r in e.rows] == [
        ("ACC-1", 2, True), ("ACC-2", 1, False), ("ACC-3", 0, False),
    ]
    text = format_engagement(e)
    assert "traded same day: 2 (66.7%)" in text and "ACC-3" not in text
