"""
============================================================
Today's UPSC Issues
Key Takeaway Component
Created by Sudhir
============================================================

Draws:

- KEY TAKEAWAY heading
- One concise takeaway paragraph
- Automatic wrapping
- Automatic font reduction
- Top-aligned body text
- Rounded printer-friendly box
============================================================
"""

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# TEXT
# ==========================================================

SECTION_TITLE = "KEY TAKEAWAY"


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 9.2

BODY_FONT_NAME = FONTS.body.name
BODY_FONT_SIZE = 9.4
BODY_LEADING = 11.2

MIN_FONT_SIZE = 8.2
MIN_LEADING = 10.0

FONT_STEP = 0.2


# ==========================================================
# GEOMETRY
# ==========================================================

HORIZONTAL_PADDING = 9.0
VERTICAL_PADDING = 8.0
HEADING_GAP = 5.0


# ==========================================================
# PARAGRAPH STYLE
# ==========================================================

def _paragraph_style(
    size: float,
    leading: float,
) -> ParagraphStyle:
    """
    Create the takeaway paragraph style.
    """

    return ParagraphStyle(
        name=f"takeaway_{size:.1f}",
        fontName=BODY_FONT_NAME,
        fontSize=size,
        leading=leading,
        textColor=COLOURS.text,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=False,
        allowWidows=0,
        allowOrphans=0,
    )


# ==========================================================
# DRAW TAKEAWAY
# ==========================================================

def draw_takeaway(
    pdf,
    box: Rectangle,
    takeaway: str,
) -> None:
    """
    Draw the Key Takeaway box.
    """

    if not takeaway or not takeaway.strip():
        raise ValueError(
            "Key Takeaway text cannot be empty."
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

    left = (
        box.x
        + HORIZONTAL_PADDING
    )

    top = (
        box.top
        - VERTICAL_PADDING
    )

    available_width = (
        box.width
        - (2 * HORIZONTAL_PADDING)
    )

    available_height = (
        box.height
        - (2 * VERTICAL_PADDING)
        - HEADING_FONT_SIZE
        - HEADING_GAP
    )

    size = BODY_FONT_SIZE
    leading = BODY_LEADING

    while True:
        style = _paragraph_style(
            size=size,
            leading=leading,
        )

        paragraph = Paragraph(
            takeaway.strip(),
            style,
        )

        _, paragraph_height = paragraph.wrap(
            available_width,
            1000,
        )

        if paragraph_height <= available_height:
            break

        if size <= MIN_FONT_SIZE:
            raise ValueError(
                "Key Takeaway does not fit inside the "
                "available box. Reduce its length."
            )

        size = max(
            MIN_FONT_SIZE,
            size - FONT_STEP,
        )

        leading = max(
            MIN_LEADING,
            leading - FONT_STEP,
        )

    heading_y = (
        top
        - HEADING_FONT_SIZE
    )

    paragraph_y = (
        heading_y
        - HEADING_GAP
        - paragraph_height
    )

    pdf.saveState()

    try:
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            HEADING_FONT_NAME,
            HEADING_FONT_SIZE,
        )

        pdf.drawString(
            left,
            heading_y,
            SECTION_TITLE,
        )

        paragraph.drawOn(
            pdf,
            left,
            paragraph_y,
        )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — KEY TAKEAWAY")
    print("=" * 60)
    print("✓ Top-aligned takeaway text")
    print("✓ Automatic wrapping enabled")
    print("✓ Automatic font reduction enabled")
    print("=" * 60)