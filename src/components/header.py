"""
============================================================
Today's UPSC Issues
Page Header Component
Created by Sudhir
============================================================

Draws:

- Main title: TODAY'S UPSC ISSUES
- Small brand line: UPSC Issues by Kumar
- Bold Daily Edition and full date on the right

All header content is vertically centred inside the rectangle
provided by layout.py.
============================================================
"""

from reportlab.pdfbase.pdfmetrics import stringWidth

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# HEADER TEXT
# ==========================================================

HEADER_TITLE = "TODAY'S UPSC ISSUES"
HEADER_BRAND = "UPSC Issues by Kumar"
EDITION_LABEL = "Daily Edition"


# ==========================================================
# HEADER FONT SETTINGS
# ==========================================================

TITLE_FONT_NAME = FONTS.brand_title.name
TITLE_FONT_SIZE = 17.0
MIN_TITLE_FONT_SIZE = 13.5

BRAND_FONT_NAME = FONTS.header_meta.name
BRAND_FONT_SIZE = 7.2

DATE_FONT_NAME = BOLD_FONT
DATE_FONT_SIZE = 9.5
MIN_DATE_FONT_SIZE = 8.0


# ==========================================================
# HEADER SPACING
# ==========================================================

# The title starts this far from the left border.
# The date ends the same distance from the right border.
HEADER_HORIZONTAL_PADDING = 14.0

# Space between title and small brand line.
TITLE_BRAND_GAP = 3.0


# ==========================================================
# FONT-FITTING HELPER
# ==========================================================

def _fit_font_size(
    text: str,
    font_name: str,
    preferred_size: float,
    available_width: float,
    minimum_size: float,
) -> float:
    """
    Reduce the font size gradually until the text fits inside
    the available width.
    """

    font_size = preferred_size

    while (
        stringWidth(
            text,
            font_name,
            font_size,
        ) > available_width
        and font_size > minimum_size
    ):
        font_size -= 0.2

    return max(
        font_size,
        minimum_size,
    )


# ==========================================================
# DRAW HEADER
# ==========================================================

def draw_header(
    pdf,
    box: Rectangle,
    date_text: str,
) -> None:
    """
    Draw the complete page header.

    Example:

        TODAY'S UPSC ISSUES       Daily Edition | 17 July 2026
        UPSC Issues by Kumar
    """

    if not date_text or not date_text.strip():
        raise ValueError(
            "Header date_text cannot be empty."
        )

    # ------------------------------------------------------
    # DRAW OUTER HEADER BOX
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # HORIZONTAL GEOMETRY
    # ------------------------------------------------------

    left_x = (
        box.x
        + HEADER_HORIZONTAL_PADDING
    )

    right_x = (
        box.right
        - HEADER_HORIZONTAL_PADDING
    )

    edition_text = (
        f"{EDITION_LABEL} | {date_text}"
    )

    preferred_date_width = stringWidth(
        edition_text,
        DATE_FONT_NAME,
        DATE_FONT_SIZE,
    )

    # Small safety space between title and date.
    title_date_gap = 18.0

    right_reserved_width = (
        preferred_date_width
        + title_date_gap
    )

    title_available_width = (
        box.width
        - (2 * HEADER_HORIZONTAL_PADDING)
        - right_reserved_width
    )

    title_font_size = _fit_font_size(
        text=HEADER_TITLE,
        font_name=TITLE_FONT_NAME,
        preferred_size=TITLE_FONT_SIZE,
        available_width=title_available_width,
        minimum_size=MIN_TITLE_FONT_SIZE,
    )

    date_font_size = _fit_font_size(
        text=edition_text,
        font_name=DATE_FONT_NAME,
        preferred_size=DATE_FONT_SIZE,
        available_width=right_reserved_width,
        minimum_size=MIN_DATE_FONT_SIZE,
    )
        # ------------------------------------------------------
    # VERTICAL CENTRING
    # ------------------------------------------------------

    # Approximate visible height of each text line.
    title_visible_height = (
        title_font_size * 0.76
    )

    brand_visible_height = (
        BRAND_FONT_SIZE * 0.76
    )

    text_block_height = (
        title_visible_height
        + TITLE_BRAND_GAP
        + brand_visible_height
    )

    # Centre the title + brand block vertically.
    block_bottom = (
        box.center_y
        - (text_block_height / 2)
    )

    brand_y = block_bottom

    title_y = (
        brand_y
        + brand_visible_height
        + TITLE_BRAND_GAP
    )

    # The date is aligned with the main title baseline.
    date_y = title_y

    # ------------------------------------------------------
    # DRAW HEADER TEXT
    # ------------------------------------------------------

    pdf.saveState()

    try:
        # Main title
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            TITLE_FONT_NAME,
            title_font_size,
        )

        pdf.drawString(
            left_x,
            title_y,
            HEADER_TITLE,
        )

        # Small publisher imprint
        pdf.setFillColor(
            COLOURS.muted_text
        )

        pdf.setFont(
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        pdf.drawString(
            left_x,
            brand_y,
            HEADER_BRAND,
        )

        # Bold edition and full date
        pdf.setFillColor(
            COLOURS.text
        )

        pdf.setFont(
            DATE_FONT_NAME,
            date_font_size,
        )

        pdf.drawRightString(
            right_x,
            date_y,
            edition_text,
        )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — HEADER COMPONENT")
    print("=" * 60)

    print(f"Main title       : {HEADER_TITLE}")
    print(f"Title size       : {TITLE_FONT_SIZE}")
    print(f"Brand            : {HEADER_BRAND}")
    print(f"Brand size       : {BRAND_FONT_SIZE}")
    print(f"Edition label    : {EDITION_LABEL}")
    print(f"Date size        : {DATE_FONT_SIZE}")
    print(f"Horizontal inset : {HEADER_HORIZONTAL_PADDING}")

    print("-" * 60)
    print("✓ Header component loaded successfully")
    print("=" * 60)