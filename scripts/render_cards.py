"""Render sample notification cards to docs/cards/ as HTML, and as PNG when
WeasyPrint and PyMuPDF are installed (they are optional; the HTML is enough).

    python scripts/render_cards.py
"""
from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalyst_demo.card import render_card, render_popup  # noqa: E402
from catalyst_demo.models import PRICE_MOVE, WK52_HIGH, WK52_LOW, Catalyst, Notification  # noqa: E402
from catalyst_demo.templates import render  # noqa: E402

DAY = date(2026, 9, 4)
OUT = Path(__file__).resolve().parents[1] / "docs" / "cards"

SAMPLES = [
    ("smci_up_en", "en", "Eran Blank", Catalyst(PRICE_MOVE, "SMCI", {"change_pct": 7.4, "price": 156.70})),
    ("soxl_down_he", "he", "Eran Blank", Catalyst(PRICE_MOVE, "SOXL", {"change_pct": -5.9, "price": 199.40})),
    ("nvda_high_en", "en", "Eran Blank", Catalyst(WK52_HIGH, "NVDA", {"price": 385.18, "prev_high": 377.63})),
    ("rivn_low_he", "he", "Eran Blank", Catalyst(WK52_LOW, "RIVN", {"price": 353.62, "prev_low": 360.84})),
]


def notification(lang: str, name: str, c: Catalyst) -> Notification:
    subject, body = render(c, name, lang)
    return Notification("ACC-0417", name, lang, c.symbol, c, subject, body, 0.0, DAY)


def to_png(html_path: Path, png_path: Path, width: int, height: int) -> bool:
    try:
        import fitz  # PyMuPDF
        from weasyprint import CSS, HTML
    except ImportError:
        return False
    pdf = html_path.with_suffix(".pdf")
    page = CSS(string=f"@page {{ size: {width}px {height}px; margin: 0; }}")
    HTML(filename=str(html_path)).write_pdf(str(pdf), stylesheets=[page])
    doc = fitz.open(str(pdf))
    doc[0].get_pixmap(dpi=192).save(str(png_path))
    pdf.unlink()
    return True


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made_png = False
    for slug, lang, name, c in SAMPLES:
        n = notification(lang, name, c)
        for layout, (w, h) in (("desktop", (496, 225)), ("mobile", (382, 499))):
            html_path = OUT / f"{slug}_{layout}.html"
            html_path.write_text(render_card(n, layout), encoding="utf-8")
            made_png = to_png(html_path, html_path.with_suffix(".png"), w, h) or made_png
        popup_path = OUT / f"{slug}_popup.html"
        popup_path.write_text(render_popup(n), encoding="utf-8")
        made_png = to_png(popup_path, popup_path.with_suffix(".png"), 390, 720) or made_png
    print(f"wrote {len(SAMPLES) * 3} cards to {OUT}" + ("" if made_png else " (HTML only; install weasyprint + pymupdf for PNG)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
