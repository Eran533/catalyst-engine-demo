from datetime import date

from catalyst_demo.card import logo_data_uri, render_card, render_popup
from catalyst_demo.models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Catalyst, Notification

DAY = date(2026, 9, 4)


def notif(lang, kind, detail, symbol="SMCI"):
    c = Catalyst(kind, symbol, detail)
    return Notification("ACC-1", "Eran Blank", lang, symbol, c, "subj", "body", 0.0, DAY)


def test_price_move_card_shows_the_move_as_the_focal_stat():
    html = render_card(notif("en", PRICE_MOVE, {"change_pct": 7.4, "price": 156.7}))
    assert 'data-move="up"' in html and 'dir="ltr"' in html and 'class="notif-desktop"' in html
    assert '<div class="stat-num ltr">+7.4%</div>' in html and '<span class="arrow">▲</span>' in html
    assert "<bdi>SMCI</bdi> is up <bdi>7.4%</bdi> today" in html and "Last $156.70" in html
    assert "<span>Change today</span>" in html


def test_drop_uses_a_typographic_minus_and_the_down_colour():
    html = render_card(notif("en", PRICE_MOVE, {"change_pct": -3.3, "price": 20.0}, "ADBE"))
    assert 'data-move="down"' in html and '<div class="stat-num ltr">−3.3%</div>' in html and "▼" in html
    assert "<bdi>ADBE</bdi> is down <bdi>3.3%</bdi> today" in html


def test_52w_high_card_shows_the_price_and_previous_high():
    html = render_card(notif("en", WK52_HIGH, {"price": 385.18, "prev_high": 377.63}, "NVDA"), layout="mobile")
    assert '<div class="stat-num ltr">$385.18</div>' in html and "Previous high $377.63" in html
    assert 'class="notif-mobile"' in html and "New 52-week high for <bdi>NVDA</bdi>" in html
    assert "<span>52-week high</span>" in html


def test_52w_low_card_shows_previous_low():
    html = render_card(notif("en", WK52_LOW, {"price": 10.0, "prev_low": 11.5}, "RIVN"))
    assert "Previous low $11.50" in html and "New 52-week low for <bdi>RIVN</bdi>" in html


def test_hebrew_card_is_rtl_and_down_coloured_for_a_drop():
    html = render_card(notif("he", PRICE_MOVE, {"change_pct": -5.9, "price": 199.4}, "SOXL"))
    assert 'dir="rtl"' in html and 'data-move="down"' in html and "ירדה היום ב-<bdi>5.9%</bdi>" in html
    assert "אחרון $199.40" in html


def test_card_carries_the_demo_look():
    html = render_card(notif("en", PRICE_MOVE, {"change_pct": 1.0, "price": 1.0}))
    assert "fonts.googleapis.com" in html and "Space+Grotesk" in html and "Rubik" in html and "Assistant" in html
    assert 'class="eyebrow">Market note<' in html and 'class="acct ltr">ACC-1<' in html
    assert 'src="data:image/svg+xml' in html and 'class="stat-panel"' in html and 'class="glow a"' in html
    assert "support@demobroker.example" in html and 'class="brand ltr">Demo Broker<' in html


def test_popup_wraps_the_card_in_platform_chrome():
    html = render_popup(notif("en", WK52_HIGH, {"price": 427.89, "prev_high": 415.53}, "UNH"))
    for piece in ('class="bar"', 'class="t">New 52-week high for <bdi>UNH</bdi><', "Hello <strong>Eran Blank</strong>,",
                  "you have traded <bdi>UNH</bdi> before", "support@demobroker.example", "The Demo Broker team",
                  "Stop these notes", 'class="btn ok">Got it<', 'class="acct ltr">ACC-1<', "$427.89",
                  "Previous high $415.53"):
        assert piece in html


def test_hebrew_popup_uses_hebrew_buttons():
    html = render_popup(notif("he", PRICE_MOVE, {"change_pct": -5.9, "price": 1.0}))
    assert 'dir="rtl"' in html and "להפסיק הערות כאלה" in html and "הבנתי" in html
    assert 'class="t"><bdi>SMCI</bdi> ירדה היום ב-<bdi>5.9%</bdi><' in html


def test_client_name_and_symbol_are_escaped():
    n = notif("en", PRICE_MOVE, {"change_pct": 5.0, "price": 1.0}, symbol="A<B")
    n.client_name = "<b>x</b>"
    for layout in ("desktop", "mobile"):
        html = render_card(n, layout)
        assert "<b>x</b>" not in html and "A<B" not in html and "A&lt;B" in html
    assert "&lt;b&gt;x&lt;/b&gt;" in render_card(n, "mobile") and "&lt;b&gt;x&lt;/b&gt;" in render_popup(n)


def test_logo_tile_is_a_data_uri_with_the_ticker():
    uri = logo_data_uri("NVDA")
    assert uri.startswith("data:image/svg+xml") and "NVDA" in uri and "%235a9e1c" in uri
    assert logo_data_uri("ZZZQ") != logo_data_uri("NVDA")
