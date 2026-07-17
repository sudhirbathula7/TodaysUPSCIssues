from xml.sax.saxutils import escape
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS

def _question(text, width, max_height):
    size, leading = 8.7, 10.7
    while size >= 7.4:
        style = ParagraphStyle("recall", fontName=BOLD_FONT, fontSize=size, leading=leading,
                               textColor=COLOURS.text, alignment=TA_LEFT, spaceBefore=0,
                               spaceAfter=0, splitLongWords=False)
        p = Paragraph(escape(text), style)
        _, h = p.wrap(width, max_height)
        if h <= max_height:
            return p, h
        size -= 0.2
        leading = max(9.0, leading - 0.2)
    return p, h

def draw_recall_questions(pdf, box: Rectangle, questions) -> None:
    if len(questions) != 2:
        raise ValueError("Recall Questions must contain exactly two questions.")

    left, right = box.x + 8.0, box.right - 8.0
    heading_y = box.top - 9.0 - 8.7
    qtop = heading_y - 9.0
    text_x = left + 21.0
    width = right - text_x
    each = (qtop - box.y - 9.0 - 8.0) / 2

    p1, h1 = _question(str(questions[0]).strip(), width, each)
    p2, h2 = _question(str(questions[1]).strip(), width, each)

    q1y = qtop - h1
    q2top = q1y - 8.0
    q2y = q2top - h2

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 8.7)
        pdf.drawString(left, heading_y, "RECALL QUESTIONS")

        pdf.setFont(BOLD_FONT, 7.5)
        pdf.drawString(left, qtop - 7.5, "Q1.")
        p1.drawOn(pdf, text_x, q1y)

        pdf.drawString(left, q2top - 7.5, "Q2.")
        p2.drawOn(pdf, text_x, q2y)
    finally:
        pdf.restoreState()

    draw_horizontal_line(pdf, box.x, box.y, box.right, thickness=0.3)
