from reportlab.pdfbase.pdfmetrics import stringWidth
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

HEADER_TITLE = "TODAY'S UPSC ISSUES"
HEADER_BRAND = "UPSC Issues by Kumar"
EDITION_LABEL = "Daily Edition"

TITLE_FONT_NAME = FONTS.brand_title.name
TITLE_FONT_SIZE = 17.0
MIN_TITLE_FONT_SIZE = 13.5
BRAND_FONT_NAME = FONTS.header_meta.name
BRAND_FONT_SIZE = 7.2
DATE_FONT_NAME = BOLD_FONT
DATE_FONT_SIZE = 9.5
MIN_DATE_FONT_SIZE = 8.0
HEADER_HORIZONTAL_PADDING = 14.0
TITLE_BRAND_GAP = 3.0

def _fit(text, font, preferred, width, minimum):
    size = preferred
    while stringWidth(text, font, size) > width and size > minimum:
        size -= 0.2
    return max(size, minimum)

def draw_header(pdf, box: Rectangle, date_text: str) -> None:
    if not date_text or not date_text.strip():
        raise ValueError("Header date_text cannot be empty.")

    draw_horizontal_line(pdf, box.x, box.y, box.right, thickness=0.5)

    left_x = box.x + HEADER_HORIZONTAL_PADDING
    right_x = box.right - HEADER_HORIZONTAL_PADDING
    edition_text = f"{EDITION_LABEL} | {date_text.strip()}"

    preferred_date_width = stringWidth(edition_text, DATE_FONT_NAME, DATE_FONT_SIZE)
    right_reserved_width = preferred_date_width + 18.0
    title_width = box.width - (2 * HEADER_HORIZONTAL_PADDING) - right_reserved_width

    title_size = _fit(HEADER_TITLE, TITLE_FONT_NAME, TITLE_FONT_SIZE, title_width, MIN_TITLE_FONT_SIZE)
    date_size = _fit(edition_text, DATE_FONT_NAME, DATE_FONT_SIZE, right_reserved_width, MIN_DATE_FONT_SIZE)

    title_visible = title_size * 0.76
    brand_visible = BRAND_FONT_SIZE * 0.76
    block_bottom = box.center_y - ((title_visible + TITLE_BRAND_GAP + brand_visible) / 2)
    brand_y = block_bottom
    title_y = brand_y + brand_visible + TITLE_BRAND_GAP

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(TITLE_FONT_NAME, title_size)
        pdf.drawString(left_x, title_y, HEADER_TITLE)

        pdf.setFillColor(COLOURS.muted_text)
        pdf.setFont(BRAND_FONT_NAME, BRAND_FONT_SIZE)
        pdf.drawString(left_x, brand_y, HEADER_BRAND)

        pdf.setFillColor(COLOURS.text)
        pdf.setFont(DATE_FONT_NAME, date_size)
        pdf.drawRightString(right_x, title_y, edition_text)
    finally:
        pdf.restoreState()
