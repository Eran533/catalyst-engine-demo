from datetime import date
from decimal import Decimal

from catalyst_demo.card import render_card, render_popup
from catalyst_demo.models import PRICE_MOVE, WK52_HIGH, Catalyst, Notification

DAY = date(2026, 9, 4)


def notif(lang, kind, detail, symbol="SMCI"):
    c = Catalyst(kind, symbol, detail)
    return Notification("ACC-1", "Maya Cohen", lang, symbol, c, "subj", "body", 0.0, DAY)


def test_price_move_card_shows_the_move_as_the_focal_stat():
    html = render_card(notif("en", PRICE_MOVE, {"change_pct": 7.4, "price": 156.7}))
    assert 'data-move="up"' in html and 'dir="ltr"' in html
    assert '<div class="stat">+7.4%</div>' in html
    assert "SMCI is up <bdi>+7.4</bdi>% today" in html and "last $156.70" in html


def test_52w_high_card_shows_the_price_and_previous_high():
    html = render_card(notif("en", WK52_HIGH, {"price": 385.18, "prev_high": 377.63}, "NVDA"), layout="mobile")
    assert '<div class="stat long">$385.18</div>' in html and "previous high $377.63" in html
    assert 'data-layout="mobile"' in html and "new 52-week high" in html


def test_hebrew_card_is_rtl_and_coral_for_a_drop():
    html = render_card(notif("he", PRICE_MOVE, {"change_pct": -5.9, "price": 199.4}, "SOXL"))
    assert 'dir="rtl"' in html and 'data-move="down"' in html and "ירדה" in html


def test_popup_wraps_the_card_in_platform_chrome():
    html = render_popup(notif("en", WK52_HIGH, {"price": 427.89, "prev_high": 415.53}, "UNH"))
    for piece in ('class="bar"', "Hi <b>Maya Cohen</b>,", "UNH is at a 52-week high.",
                  "support@demobroker.example", "Don't show this again", 'class="chip">ACC-1<'):
        assert piece in html


def test_hebrew_popup_uses_hebrew_buttons():
    html = render_popup(notif("he", PRICE_MOVE, {"change_pct": -5.9, "price": 1.0}))
    assert 'dir="rtl"' in html and "אל תציגו שוב" in html and "אישור" in html


def test_client_name_is_escaped():
    n = notif("en", PRICE_MOVE, {"change_pct": 5.0, "price": 1.0})
    n.client_name = "<b>x</b>"
    assert "<b>x</b>" not in render_card(n) and "&lt;b&gt;x&lt;/b&gt;" in render_card(n)
