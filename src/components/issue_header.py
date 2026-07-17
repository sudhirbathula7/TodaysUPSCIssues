from xml.sax.saxutils import escape
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

def _title(title, width, height):
    size, leading = 12.8, 14.4
    while size >= 10.0:
        style = ParagraphStyle("issue_title", fontName=BOLD_FONT, fontSize=size, leading=leading,
                               textColor=COLOURS.text, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0,
                               splitLongWords=False)
        p = Paragraph(escape(title), style)
        _, h = p.wrap(width, height)
        if h <= height and h <= leading * 2 + 0.5:
            return p, h
        size -= 0.2
        leading = max(11.8, leading - 0.2)
    return p, h

def draw_issue_header(pdf, box: Rectangle, issue_number: int, title: str, gs_paper: str, category: str) -> None:
    left = box.x + 8.0
    right = box.right - 16.0
    number_area = 22.0
    title_x = left + number_area + 10.0
    right_area_x = right - 70.0
    title_width = right_area_x - 8.0 - title_x
    title_height = box.height - 10.0

    p, h = _title(title.strip(), title_width, title_height)
    title_y = box.center_y - h / 2
    number_y = box.center_y - (12.0 * 0.34)

    group_height = 8.0 + (3.0 + 8.4 if category else 0)
    group_bottom = box.center_y - group_height / 2
    cat_y = group_bottom
    gs_y = cat_y + (8.4 + 3.0 if category else 0)

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 12.0)
        pdf.drawCentredString(left + number_area / 2, number_y, str(issue_number))

        p.drawOn(pdf, title_x, title_y)

        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 8.0)
        pdf.drawRightString(right, gs_y, gs_paper.strip())

        if category:
            pdf.setFillColor(COLOURS.muted_text)
            pdf.setFont(FONTS.issue_meta.name, 7.3)
            pdf.drawRightString(right, cat_y, category.strip())
    finally:
        pdf.restoreState()

    draw_horizontal_line(pdf, box.x, box.y, box.right, thickness=0.45)
