from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

def draw_takeaway(pdf, box: Rectangle, takeaway: str) -> None:
    if not takeaway or not takeaway.strip():
        raise ValueError("Key Takeaway text cannot be empty.")

    left = box.x + 9.0
    top = box.top - 8.0
    width = box.width - 18.0
    available = box.height - 16.0 - 9.2 - 5.0

    size, leading = 9.4, 11.2
    while True:
        style = ParagraphStyle("takeaway", fontName=FONTS.body.name, fontSize=size,
                               leading=leading, textColor=COLOURS.text, alignment=TA_LEFT,
                               spaceBefore=0, spaceAfter=0, splitLongWords=False)
        p = Paragraph(takeaway.strip(), style)
        _, h = p.wrap(width, 1000)
        if h <= available:
            break
        if size <= 8.2:
            raise ValueError("Key Takeaway does not fit.")
        size = max(8.2, size - 0.2)
        leading = max(10.0, leading - 0.2)

    heading_y = top - 9.2
    paragraph_y = heading_y - 5.0 - h

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 9.2)
        pdf.drawString(left, heading_y, "KEY TAKEAWAY")
        p.drawOn(pdf, left, paragraph_y)
    finally:
        pdf.restoreState()

    draw_horizontal_line(pdf, box.x, box.y, box.right, thickness=0.3)
