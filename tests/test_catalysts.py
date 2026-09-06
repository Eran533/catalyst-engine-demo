from decimal import Decimal

from catalyst_demo import catalysts as cat
from catalyst_demo.models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Catalyst


def flat(n, price=100.0):
    return [price] * n


def test_price_move_above_threshold_is_a_catalyst():
    hits = cat.detect("X", 4.0, flat(40))
    assert [c.kind for c in hits] == [PRICE_MOVE]
    assert hits[0].detail["change_pct"] == 4.0


def test_price_move_below_threshold_is_ignored():
    assert cat.detect("X", 3.9, flat(40)) == []


def test_negative_move_counts_and_has_down_direction():
    hits = cat.detect("X", -6.0, flat(40))
    assert hits[0].kind == PRICE_MOVE and hits[0].direction == "down"


def test_unknown_change_is_not_a_move():
    assert cat.detect("X", None, flat(40)) == []


def test_52w_high_when_today_is_the_max():
    closes = flat(39, 100.0) + [101.0]
    assert [c.kind for c in cat.detect("X", 1.0, closes)] == [WK52_HIGH]


def test_52w_low_when_today_is_the_min():
    closes = flat(39, 100.0) + [99.0]
    assert [c.kind for c in cat.detect("X", -1.0, closes)] == [WK52_LOW]


def test_too_little_history_never_judges_extremes():
    closes = flat(10, 100.0) + [150.0]
    assert cat.detect("X", 1.0, closes) == []


def test_window_only_looks_at_trailing_closes():
    # a much higher close outside the window must not block a "high"
    closes = [500.0] + flat(39, 100.0) + [101.0]
    assert [c.kind for c in cat.detect("X", 1.0, closes, window=40)] == [WK52_HIGH]


def test_move_and_extreme_can_coexist():
    closes = flat(39, 100.0) + [106.0]
    kinds = {c.kind for c in cat.detect("X", 6.0, closes)}
    assert kinds == {PRICE_MOVE, WK52_HIGH}


def test_strongest_prefers_extreme_over_move():
    move = Catalyst(PRICE_MOVE, "X", {"change_pct": 12.0})
    high = Catalyst(WK52_HIGH, "X", {"price": 1.0})
    assert cat.strongest([move, high]) is high


def test_strongest_breaks_ties_by_size():
    small = Catalyst(PRICE_MOVE, "X", {"change_pct": 4.0})
    big = Catalyst(PRICE_MOVE, "Y", {"change_pct": -9.0})
    assert cat.strongest([small, big]) is big


def test_priority_score_scales_balance_by_strength():
    move = Catalyst(PRICE_MOVE, "X", {"change_pct": 8.0})  # strength 2.0
    assert cat.priority_score(Decimal("1000"), [move]) == 3000.0
    assert cat.priority_score(Decimal("1000"), []) == 0.0
