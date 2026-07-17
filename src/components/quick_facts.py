from xml.sax.saxutils import escape
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

def draw_quick_facts(pdf, box: Rectangle, facts) -> None:
    if len(facts) != 5:
        raise ValueError("Quick Facts must contain exactly 5 facts.")

    left, right = box.x + 9.0, box.right - 9.0
    heading_y = box.top - 6.0 - 9.2
    facts_top = heading_y - 4.0
    bullet_x = left + 1.4
    text_x = left + 2.8 + 6.0
    width = right - text_x
    available = facts_top - box.y - 6.0

    size, leading = 8.3, 9.8
    while True:
        style = ParagraphStyle("fact", fontName=FONTS.quick_fact.name, fontSize=size,
                               leading=leading, textColor=COLOURS.text, alignment=TA_LEFT,
                               spaceBefore=0, spaceAfter=0, splitLongWords=False)
        data = []
        required = 0.0
        for fact in facts:
            p = Paragraph(escape(str(fact).strip()), style)
            _, h = p.wrap(width, 1000)
            data.append((p, h))
            required += h
        required += 4 * 2.5
        if required <= available:
            break
        if size <= 7.0:
            raise ValueError("Quick Facts do not fit.")
        size = max(7.0, size - 0.2)
        leading = max(8.2, leading - 0.2)

    cursor = facts_top - (available - required) / 2

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 9.2)
        pdf.drawString(left, heading_y, "QUICK FACTS")

        for i, (p, h) in enumerate(data):
            py = cursor - h
            bullet_y = cursor - min(h / 2, leading * 0.45)
            pdf.setFillColor(COLOURS.primary)
            pdf.circle(bullet_x, bullet_y, 1.4, stroke=0, fill=1)
            p.drawOn(pdf, text_x, py)
            cursor = py - (2.5 if i < 4 else 0)
    finally:
        pdf.restoreState()

    draw_horizontal_line(pdf, box.x, box.y, box.right, thickness=0.3)
