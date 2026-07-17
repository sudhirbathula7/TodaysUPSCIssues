from reportlab.pdfbase.pdfmetrics import stringWidth
from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS

FOOTER_BRAND = "UPSC Issues by Kumar"
FOOTER_LINKS = "Website | YouTube | Telegram"

def draw_footer(pdf, box: Rectangle, document_code: str, page_number: int, total_pages: int) -> None:
    if not document_code or not document_code.strip():
        raise ValueError("Footer document_code cannot be empty.")
    if page_number < 1 or total_pages < page_number:
        raise ValueError("Invalid footer page values.")

    draw_horizontal_line(pdf, box.x, box.top, box.right, thickness=0.45)

    left_x = box.x + 14.0
    right_x = box.right - 14.0
    y = box.center_y - 2.4
    page_text = f"Page {page_number} / {total_pages}"

    code_width = stringWidth(document_code, BOLD_FONT, 7.4)
    page_width = stringWidth(page_text, FONTS.footer.name, 7.2)
    right_group_start = right_x - (code_width + 14.0 + page_width)

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(BOLD_FONT, 7.8)
        pdf.drawString(left_x, y, FOOTER_BRAND)

        brand_width = stringWidth(FOOTER_BRAND, BOLD_FONT, 7.8)
        pdf.setFillColor(COLOURS.muted_text)
        pdf.setFont(FONTS.footer.name, 7.2)
        pdf.drawString(left_x + brand_width + 7.0, y, f"| {FOOTER_LINKS}")

        pdf.setFillColor(COLOURS.text)
        pdf.setFont(BOLD_FONT, 7.4)
        pdf.drawString(right_group_start, y, document_code)

        pdf.setFont(FONTS.footer.name, 7.2)
        pdf.drawRightString(right_x, y, page_text)
    finally:
        pdf.restoreState()
