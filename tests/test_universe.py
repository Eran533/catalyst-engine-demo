from datetime import date
from decimal import Decimal

from catalyst_demo import universe as u
from catalyst_demo.models import Client, Position, Trade

TODAY = date(2026, 9, 4)  # a Friday


def client(i, balance="1000"):
    return Client(f"ACC-{i}", f"Client {i}", "en", Decimal(balance))


def trade(acct, sym, d):
    return Trade(acct, sym, d, 1, Decimal("10"))


def test_trading_days_since_counts_weekdays_only():
    assert u.trading_days_since(date(2026, 8, 28), TODAY) == 5   # Mon..Fri
    assert u.trading_days_since(TODAY, TODAY) == 0


def test_dormant_needs_no_trade_for_n_trading_days():
    c1, c2, c3 = client(1), client(2), client(3)
    trades = [
        trade("ACC-1", "AAPL", date(2026, 8, 20)),  # 11 trading days ago -> dormant
        trade("ACC-2", "AAPL", date(2026, 9, 2)),   # 2 trading days ago -> active
        trade("ACC-1", "AAPL", TODAY),               # a trade today does not un-dormant a client
    ]  # ACC-3 never traded -> skipped
    dormant = u.dormant_clients([c1, c2, c3], trades, TODAY, inactive_days=7)
    assert [(c.account_id, idle) for c, idle in dormant] == [("ACC-1", 11)]


def test_favourites_are_held_first_then_most_traded():
    trades = [trade("ACC-1", "TSLA", date(2026, 1, 5))] * 3 + \
             [trade("ACC-1", "AMD", date(2026, 2, 5))] * 2 + \
             [trade("ACC-1", "NVDA", date(2026, 3, 5))]
    positions = [Position("ACC-1", "SPY", 10)]
    assert u.favourites(trades, positions, "ACC-1", TODAY, top_n=2) == ["SPY", "TSLA", "AMD"]


def test_favourites_ignore_trades_outside_lookback():
    old = [trade("ACC-1", "OLD", date(2024, 1, 1))] * 5
    recent = [trade("ACC-1", "NEW", date(2026, 6, 1))]
    assert u.favourites(old + recent, [], "ACC-1", TODAY) == ["NEW"]


def test_build_universe_only_keeps_dormant_clients_with_favourites():
    c1, c2 = client(1), client(2)
    trades = [trade("ACC-1", "AAPL", date(2026, 8, 1)), trade("ACC-2", "AAPL", date(2026, 9, 3))]
    uni = u.build_universe([c1, c2], trades, [], TODAY)
    assert list(uni) == ["ACC-1"]
    _, idle, favs = uni["ACC-1"]
    assert favs == ["AAPL"] and idle > 7
