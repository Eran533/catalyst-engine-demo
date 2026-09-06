"""HTML card for one notification: what the client sees inside the platform popup.

Design: a deep-navy surface with hairline rules, a serif headline, and one large
monospace focal number (the move, or the 52-week price). The accent colour
follows direction, emerald for up and coral for down, and that is the only thing
that changes with the news. No call to action and no advice: the card reports a
fact about a stock the client already knows.

Two layouts share one template: `desktop` (wide, two columns) and `mobile`
(tall, stacked). The card fills the white content area of a platform popup; the
popup's own title bar and buttons are not part of this HTML.
"""
from __future__ import annotations

from datetime import date
from html import escape

from .models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Notification

_TEXT = {
    "en": {
        "kicker": "MARKET CATALYST",
        "traded_before": "a stock you have traded before",
        PRICE_MOVE: "{symbol} is {direction} {change}% today",
        WK52_HIGH: "{symbol} set a new 52-week high",
        WK52_LOW: "{symbol} touched a 52-week low",
        "stat_label": {PRICE_MOVE: "today's move", WK52_HIGH: "52-week high", WK52_LOW: "52-week low"},
        "last": "last",
        "prev": {WK52_HIGH: "previous high", WK52_LOW: "previous low"},
        "footer": "Prices are delayed and for information only. Not investment advice.",
        "brand": "DEMO BROKER",
        "up": "up", "down": "down",
    },
    "he": {
        "kicker": "אירוע שוק",
        "traded_before": "מניה שסחרת בה בעבר",
        PRICE_MOVE: "{symbol} {direction} היום {change}%",
        WK52_HIGH: "{symbol} קבעה שיא 52 שבועות",
        WK52_LOW: "{symbol} נגעה בשפל 52 שבועות",
        "stat_label": {PRICE_MOVE: "תנועה היום", WK52_HIGH: "שיא 52 שבועות", WK52_LOW: "שפל 52 שבועות"},
        "last": "אחרון",
        "prev": {WK52_HIGH: "שיא קודם", WK52_LOW: "שפל קודם"},
        "footer": "המחירים מושהים ולמידע בלבד. אין לראות בכך ייעוץ השקעות.",
        "brand": "DEMO BROKER",
        "up": "עלתה", "down": "ירדה",
    },
}

_CSS = """
:root {
  --paper: #0d1b34; --paper-2: #16294a; --ink: #eef2f9; --ink-2: #aab7cd; --ink-3: #7387a3;
  --line: #233655; --up: #2fd39a; --down: #ff6f61; --accent: var(--ink);
  --serif: Georgia, "Times New Roman", serif;
  --sans: "Heebo", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", Menlo, Consolas, monospace;
}
body[data-move="up"]   { --accent: var(--up); }
body[data-move="down"] { --accent: var(--down); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--paper); color: var(--ink); font-family: var(--sans); }
.card { position: relative; overflow: hidden; background: var(--paper); }
.card::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--accent); }
[dir="rtl"] .card::before { inset: 0 0 0 auto; }
.ghost { position: absolute; right: -8px; bottom: -28px; font: 600 150px var(--mono); color: var(--accent); opacity: .06; }
[dir="rtl"] .ghost { right: auto; left: -8px; }
.head { display: flex; align-items: center; gap: 12px; }
.badge { width: 44px; height: 44px; border-radius: 12px; background: var(--paper-2); border: 1px solid var(--line);
         text-align: center; line-height: 42px; font: 600 12px/42px var(--mono); color: var(--accent);
         flex-shrink: 0; direction: ltr; }
/* the header row is laid out left-to-right and mirrored by hand for Hebrew,
   which renders more predictably than a right-to-left flex row */
.head, .body, .foot { direction: ltr; }
[dir="rtl"] .head, [dir="rtl"] .body, [dir="rtl"] .foot { flex-direction: row-reverse; }
[dir="rtl"] .kicker, [dir="rtl"] .symbol, [dir="rtl"] .col-text, [dir="rtl"] .disclaimer,
[dir="rtl"] .stat-label { direction: rtl; text-align: right; }
.stat.long { font-size: 34px; }
/* numbers and dates always read left-to-right, even inside a Hebrew card */
.stat, .stat-sub, .chip, bdi { direction: ltr; unicode-bidi: isolate; }
[dir="rtl"] .stat, [dir="rtl"] .stat-sub { text-align: right; }
.kicker { font: 600 10px var(--sans); letter-spacing: .18em; color: var(--ink-3); }
.symbol { font: 600 15px var(--mono); margin-top: 3px; }
.chip { margin-inline-start: auto; font: 500 10px var(--mono); color: var(--ink-3); border: 1px solid var(--line);
        border-radius: 999px; padding: 4px 10px; background: var(--paper-2); white-space: nowrap; }
.stat { font: 600 44px var(--mono); color: var(--accent); letter-spacing: -.02em; line-height: 1; }
.stat-label { font: 500 10px var(--sans); letter-spacing: .14em; color: var(--ink-2); margin-top: 6px; }
.stat-sub { font: 500 10.5px var(--mono); color: var(--ink-3); margin-top: 3px; }
.headline { font: 600 19px/1.25 var(--serif); }
.who { font: 400 12px/1.5 var(--sans); color: var(--ink-2); margin-top: 6px; }
.rule { height: 1px; background: var(--line); }
.foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.brand { font: 600 11px var(--mono); color: var(--ink-2); white-space: nowrap; }
.disclaimer { font: 400 10px/1.4 var(--sans); color: var(--ink-3); }

/* desktop: 496 x 225, two columns */
body[data-layout="desktop"] .card { width: 496px; height: 225px; padding: 18px 20px 14px 24px; }
body[data-layout="desktop"] .body { display: flex; gap: 20px; margin-top: 14px; }
body[data-layout="desktop"] .col-stat { flex: 0 0 150px; }
body[data-layout="desktop"] .divider { width: 1px; background: var(--line); }
body[data-layout="desktop"] .col-text { flex: 1; }
body[data-layout="desktop"] .rule { margin: 14px 0 10px; }

/* mobile: 382 x 499, stacked */
body[data-layout="mobile"] .card { width: 382px; height: 499px; padding: 22px 22px 18px 26px; display: flex; flex-direction: column; }
body[data-layout="mobile"] .body { margin-top: 28px; flex: 1; }
body[data-layout="mobile"] .stat { font-size: 56px; }
body[data-layout="mobile"] .stat.long { font-size: 46px; }
body[data-layout="mobile"] .divider { display: none; }
body[data-layout="mobile"] .col-text { margin-top: 26px; }
body[data-layout="mobile"] .headline { font-size: 24px; }
body[data-layout="mobile"] .who { font-size: 13px; margin-top: 10px; }
body[data-layout="mobile"] .rule { margin: 0 0 12px; }
"""

_TEMPLATE = """<!doctype html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8" />
<title>{title}</title>
<style>{css}</style>
</head>
<body data-move="{move}" data-layout="{layout}">
<div class="card">
  <div class="ghost">{arrow}</div>
  <div class="head">
    <div class="badge">{badge}</div>
    <div>
      <div class="kicker">{kicker}</div>
      <div class="symbol">{symbol}</div>
    </div>
    <div class="chip">{chip}</div>
  </div>
  <div class="body">
    <div class="col-stat">
      <div class="{stat_class}">{stat}</div>
      <div class="stat-label">{stat_label}</div>
      <div class="stat-sub">{stat_sub}</div>
    </div>
    <div class="divider"></div>
    <div class="col-text">
      <div class="headline">{headline}</div>
      <div class="who">{who}</div>
    </div>
  </div>
  <div class="rule"></div>
  <div class="foot">
    <div class="brand">{brand}</div>
    <div class="disclaimer">{footer}</div>
  </div>
</div>
</body>
</html>
"""


def render_card(n: Notification, layout: str = "desktop", on: date = None) -> str:
    """Self-contained HTML for one notification. `layout` is desktop or mobile."""
    lang = n.language if n.language in _TEXT else "en"
    t = _TEXT[lang]
    c = n.catalyst
    on = on or n.sent_on or date.today()
    change = c.detail.get("change_pct", 0.0)
    price = c.detail.get("price", 0.0)

    if c.kind == PRICE_MOVE:
        stat = f"{change:+.1f}%"
        stat_sub = f"{t['last']} ${price:,.2f}"
    else:
        stat = f"${price:,.2f}"
        prev_key = "prev_high" if c.kind == WK52_HIGH else "prev_low"
        stat_sub = f"{t['prev'][c.kind]} ${c.detail.get(prev_key, 0.0):,.2f}"

    # Escape the pieces, then wrap the number in <bdi> so a minus sign stays on
    # the left of the digits inside a right-to-left sentence.
    headline = t[c.kind].format(
        symbol=escape(c.symbol), direction=t[c.direction],
        change=f"<bdi>{change:+.1f}</bdi>",
    )
    who = f"{escape(n.client_name)} · {t['traded_before']}"

    return _TEMPLATE.format(
        lang=lang, dir="rtl" if lang == "he" else "ltr", title=escape(n.subject), css=_CSS,
        move=c.direction, layout=layout, arrow="↗" if c.direction == "up" else "↘",
        badge=escape(c.symbol[:4]), kicker=t["kicker"], symbol=escape(c.symbol),
        chip=on.strftime("%d %b %Y").upper(), stat=stat, stat_label=t["stat_label"][c.kind],
        stat_class="stat long" if len(stat) > 5 else "stat",
        stat_sub=stat_sub, headline=headline, who=who, brand=t["brand"], footer=t["footer"],
    )
