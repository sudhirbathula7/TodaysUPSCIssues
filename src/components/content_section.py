from dataclasses import dataclass
from html import escape as html_escape
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

LOCKED_HEADINGS = ("Core Issue", "What's Happening?", "Why It Matters", "Key Challenges", "The Way Forward")

@dataclass(frozen=True, slots=True)
class ContentSection:
    heading: str
    text: str

def _prepare(text):
    o, c = "__BO__", "__BC__"
    prepared = text.replace("<b>", o).replace("</b>", c)
    prepared = html_escape(prepared, quote=False)
    return prepared.replace(o, "<b>").replace(c, "</b>")

def _style(name, font, size, leading, colour):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=colour, alignment=TA_LEFT, spaceBefore=0,
                          spaceAfter=0, splitLongWords=False)

def draw_content_sections(pdf, box: Rectangle, sections) -> None:
    if len(sections) != 5:
        raise ValueError("Exactly five content sections are required.")

    normal = []
    for item in sections:
        s = item if isinstance(item, ContentSection) else ContentSection(str(item[0]), str(item[1]))
        normal.append(ContentSection(s.heading.strip(), s.text.strip()))

    if tuple(s.heading for s in normal) != LOCKED_HEADINGS:
        raise ValueError("Content headings do not match the locked order.")

    width = box.width - 14.0
    top = box.top - 8.0
    available = box.height - 16.0

    hs, hl, bs, bl = 9.8, 11.2, 9.5, 11.5
    while True:
        hstyle = _style("heading", BOLD_FONT, hs, hl, COLOURS.primary)
        bstyle = _style("body", FONTS.body.name, bs, bl, COLOURS.text)
        data, required = [], 0.0
        for s in normal:
            hp = Paragraph(html_escape(s.heading, quote=False), hstyle)
            _, hh = hp.wrap(width, 1000)
            bp = Paragraph(_prepare(s.text), bstyle)
            _, bh = bp.wrap(width, 1000)
            data.append((hp, hh, bp, bh))
            required += hh + 4.0 + bh
        required += 4 * (3.0 + 4.0 + 7.0)

        if required <= available:
            break
        if bs <= 8.4 and hs <= 8.4:
            raise ValueError("The five content sections do not fit.")
        bs, bl = max(8.4, bs - 0.2), max(10.2, bl - 0.2)
        hs, hl = max(8.4, hs - 0.2), max(9.6, hl - 0.2)

    cursor = top - (available - required) / 2
    pdf.saveState()
    try:
        for i, (hp, hh, bp, bh) in enumerate(data):
            hy = cursor - hh
            hp.drawOn(pdf, box.x + 7.0, hy)
            by = hy - 4.0 - bh
            bp.drawOn(pdf, box.x + 7.0, by)
            cursor = by

            if i < 4:
                divider_y = cursor - 3.0
                draw_horizontal_line(pdf, box.x, divider_y, box.right, thickness=0.3)
                cursor = divider_y - 4.0 - 7.0
    finally:
        pdf.restoreState()
