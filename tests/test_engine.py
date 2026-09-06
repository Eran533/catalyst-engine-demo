"""End-to-end over a tiny in-memory data set."""
from datetime import date
from decimal import Decimal

from catalyst_demo import engine
from catalyst_demo.market_data import PriceHistory, trading_days
from catalyst_demo.models import Client, Position, Trade
from catalyst_demo.notifier import CollectingNotifier
from catalyst_demo.state import State

TODAY = date(2026, 9, 4)
START = date(2026, 6, 1)


def prices_with(today_moves):
    """History alternating $100/$105, then today's close at 100 moved by the
    given percent. So a move past +5% is also a 52-week high and a negative
    move is a 52-week low, while small moves are just noise."""
    days = trading_days(START, TODAY)
    series = {}
    for sym, pct in today_moves.items():
        rows = [(d, 100.0 + 5.0 * (i % 2)) for i, d in enumerate(days[:-1])]
        rows.append((TODAY, round(100.0 * (1 + pct / 100), 2)))
        series[sym] = rows
    return PriceHistory(series)


def make_world():
    clients = [
        Client("ACC-1", "Noa Levi", "he", Decimal("5000")),    # dormant, likes SMCI (+7%)
        Client("ACC-2", "Liam Smith", "en", Decimal("50000")),  # dormant, holds AAPL (flat) and traded SOXL (-6%)
        Client("ACC-3", "Maya Katz", "en", Decimal("900")),     # active -> never notified
        Client("ACC-4", "Leo Brown", "en", Decimal("100")),     # dormant, favourite is flat -> nothing
    ]
    old = date(2026, 8, 1)
    trades = [
        Trade("ACC-1", "SMCI", old, 5, Decimal("100")),
        Trade("ACC-2", "SOXL", old, 5, Decimal("100")),
        Trade("ACC-3", "SMCI", date(2026, 9, 3), 5, Decimal("100")),
        Trade("ACC-4", "MSFT", old, 5, Decimal("100")),
    ]
    positions = [Position("ACC-2", "AAPL", 10)]
    prices = prices_with({"SMCI": 7.0, "SOXL": -6.0, "AAPL": 0.0, "MSFT": 0.5})
    return clients, trades, positions, prices


def test_plan_notifies_dormant_clients_whose_favourites_moved_ranked_by_score():
    clients, trades, positions, prices = make_world()
    notifications, summary = engine.plan(TODAY, clients, trades, positions, prices, State())
    assert [n.account_id for n in notifications] == ["ACC-2", "ACC-1"]  # bigger balance first
    assert notifications[0].symbol == "SOXL"
    assert notifications[1].language == "he" and "SMCI" in notifications[1].subject
    assert summary.dormant == 3 and summary.symbols_with_catalyst == 2 and summary.suppressed == 0


def test_run_records_state_and_second_run_same_day_sends_nothing():
    clients, trades, positions, prices = make_world()
    state, out = State(), CollectingNotifier()
    first = engine.run(TODAY, clients, trades, positions, prices, state, out)
    second = engine.run(TODAY, clients, trades, positions, prices, state, out)
    assert first.sent == 2 and second.sent == 0 and second.suppressed == 2
    assert len(out.sent) == 2


def test_dry_run_sends_and_records_nothing():
    clients, trades, positions, prices = make_world()
    state, out = State(), CollectingNotifier()
    summary = engine.run(TODAY, clients, trades, positions, prices, state, out, dry_run=True)
    assert summary.sent == 0 and out.sent == [] and state.by_client == {}


def test_send_cap_keeps_the_highest_scores():
    clients, trades, positions, prices = make_world()
    notifications, _ = engine.plan(TODAY, clients, trades, positions, prices, State(),
                                   engine.Config(send_cap=1))
    assert [n.account_id for n in notifications] == ["ACC-2"]


def test_failed_delivery_is_not_recorded():
    class Flaky:
        def send(self, n):
            return n.account_id != "ACC-1"

    clients, trades, positions, prices = make_world()
    state = State()
    summary = engine.run(TODAY, clients, trades, positions, prices, state, Flaky())
    assert summary.sent == 1 and "ACC-1" not in state.by_client and "ACC-2" in state.by_client
