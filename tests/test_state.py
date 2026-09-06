from datetime import date

from catalyst_demo.models import PRICE_MOVE, WK52_HIGH, Catalyst
from catalyst_demo.state import State

D1, D2 = date(2026, 9, 3), date(2026, 9, 4)
MOVE = Catalyst(PRICE_MOVE, "AAPL", {"change_pct": 5.0})
HIGH = Catalyst(WK52_HIGH, "AAPL", {"price": 1.0})


def test_fresh_state_suppresses_nothing():
    assert not State().is_suppressed("A", MOVE, D1)


def test_same_day_second_message_is_suppressed():
    s = State()
    s.record("A", MOVE, D1)
    assert s.is_suppressed("A", HIGH, D1)       # different catalyst, same client, same day
    assert not s.is_suppressed("B", MOVE, D1)   # other client unaffected


def test_next_day_is_allowed_again():
    s = State()
    s.record("A", MOVE, D1)
    assert not s.is_suppressed("A", MOVE, D2)


def test_round_trip_through_disk_is_atomic_and_lossless(tmp_path):
    s = State()
    s.record("A", MOVE, D1)
    path = tmp_path / "nested" / "state.json"
    s.save(path)
    loaded = State.load(path)
    assert loaded.by_client == {"A": "2026-09-03"}
    assert loaded.by_catalyst == {"A|AAPL|price_move": "2026-09-03"}
    assert not list(tmp_path.glob("**/*.tmp"))


def test_corrupt_file_loads_as_empty(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json")
    assert State.load(path).by_client == {}
