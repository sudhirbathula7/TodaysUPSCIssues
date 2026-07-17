"""
============================================================
Today's UPSC Issues
Page Footer Component
Created by Sudhir
============================================================

Draws:

- Brand name
- Website | YouTube | Telegram
- Daily document code
- Page number

The component draws inside the Rectangle supplied by layout.py.
============================================================
"""

from reportlab.pdfbase.pdfmetrics import stringWidth

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# FOOTER TEXT
# ==========================================================

FOOTER_BRAND = "UPSC Issues by Kumar"
FOOTER_LINKS = "Website | YouTube | Telegram"


# ==========================================================
# FOOTER FONT SETTINGS
# ==========================================================

BRAND_FONT_NAME = BOLD_FONT
BRAND_FONT_SIZE = 7.8

LINKS_FONT_NAME = FONTS.footer.name
LINKS_FONT_SIZE = 7.2

CODE_FONT_NAME = BOLD_FONT
CODE_FONT_SIZE = 7.4

PAGE_FONT_NAME = FONTS.footer.name
PAGE_FONT_SIZE = 7.2


# ==========================================================
# FOOTER SPACING
# ==========================================================

FOOTER_HORIZONTAL_PADDING = 14.0
RIGHT_GROUP_GAP = 14.0


# ==========================================================
# DRAW FOOTER
# ==========================================================

def draw_footer(
    pdf,
    box: Rectangle,
    document_code: str,
    page_number: int,
    total_pages: int,
) -> None:
    """
    Draw the complete footer.

    Example:

        UPSC Issues by Kumar | Website | YouTube | Telegram
        #TUI-260717   Page 1 / 2
    """

    if not document_code or not document_code.strip():
        raise ValueError(
            "Footer document_code cannot be empty."
        )

    if page_number < 1:
        raise ValueError(
            "Footer page_number must be at least 1."
        )

    if total_pages < page_number:
        raise ValueError(
            "Footer total_pages cannot be smaller than page_number."
        )

    draw_rounded_box(
        canvas=pdf,
        x=box.x,
        y=box.y,
        width=box.width,
        height=box.height,
        fill_color=COLOURS.box_background,
        stroke_color=COLOURS.border,
        radius=BOX_RADIUS,
    )

    left_x = (
        box.x
        + FOOTER_HORIZONTAL_PADDING
    )

    right_x = (
        box.right
        - FOOTER_HORIZONTAL_PADDING
    )

    baseline_y = (
        box.center_y
        - 2.4
    )

    code_text = document_code.strip()

    page_text = (
        f"Page {page_number} / {total_pages}"
    )

    code_width = stringWidth(
        code_text,
        CODE_FONT_NAME,
        CODE_FONT_SIZE,
    )

    page_width = stringWidth(
        page_text,
        PAGE_FONT_NAME,
        PAGE_FONT_SIZE,
    )

    right_group_width = (
        code_width
        + RIGHT_GROUP_GAP
        + page_width
    )

    right_group_start = (
        right_x
        - right_group_width
    )

    pdf.saveState()

    try:
        # Brand
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        pdf.drawString(
            left_x,
            baseline_y,
            FOOTER_BRAND,
        )

        brand_width = stringWidth(
            FOOTER_BRAND,
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        # Separator before platform links
        separator_x = (
            left_x
            + brand_width
            + 7.0
        )

        pdf.setFillColor(
            COLOURS.muted_text
        )

        pdf.setFont(
            LINKS_FONT_NAME,
            LINKS_FONT_SIZE,
        )

        pdf.drawString(
            separator_x,
            baseline_y,
            f"| {FOOTER_LINKS}",
        )

        # Daily document code
        pdf.setFillColor(
            COLOURS.text
        )

        pdf.setFont(
            CODE_FONT_NAME,
            CODE_FONT_SIZE,
        )

        pdf.drawString(
            right_group_start,
            baseline_y,
            code_text,
        )

        # Page number
        pdf.setFont(
            PAGE_FONT_NAME,
            PAGE_FONT_SIZE,
        )

        pdf.drawRightString(
            right_x,
            baseline_y,
            page_text,
        )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — FOOTER COMPONENT")
    print("=" * 60)

    print(f"Brand : {FOOTER_BRAND}")
    print(f"Links : {FOOTER_LINKS}")

    print("-" * 60)
    print("✓ Footer component loaded successfully")
    print("=" * 60)