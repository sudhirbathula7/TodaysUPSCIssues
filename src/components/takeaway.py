"""
============================================================
UPSC Issues by Kumar
Key Takeaway Component
Created by Sudhir
============================================================
"""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import (
    draw_rounded_box,
    draw_svg_icon,
)
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# TEXT
# ==========================================================

SECTION_TITLE = "KEY TAKEAWAY"


# ==========================================================
# ICON
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TAKEAWAY_ICON = (
    PROJECT_ROOT
    / "assets"
    / "logos"
    / "revision"
    / "takeaway.svg"
)

ICON_SIZE = 11.0
ICON_TEXT_GAP = 5.0


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 9.6

BODY_FONT_NAME = FONTS.body.name
BODY_FONT_SIZE = 9.4
BODY_LEADING = 11.2

MIN_BODY_FONT_SIZE = 8.0
MIN_BODY_LEADING = 9.6

FONT_REDUCTION_STEP = 0.2


# ==========================================================
# SPACING
# ==========================================================

HORIZONTAL_PADDING = 9.0
VERTICAL_PADDING = 8.0

HEADING_BOTTOM_GAP = 7.0


# ==========================================================
# PARAGRAPH STYLE
# ==========================================================

def _create_paragraph_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """
    Create the Key Takeaway paragraph style.
    """

    return ParagraphStyle(
        name=f"takeaway_{font_size:.1f}",
        fontName=BODY_FONT_NAME,
        fontSize=font_size,
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
# TEXT FITTING
# ==========================================================

def _build_takeaway_paragraph(
    takeaway: str,
    available_width: float,
    available_height: float,
) -> tuple[Paragraph, float]:
    """
    Build a takeaway paragraph that fits safely inside the box.
    """

    if available_width <= 0:
        raise ValueError(
            "Key Takeaway text width must be greater than zero."
        )

    if available_height <= 0:
        raise ValueError(
            "Key Takeaway text height must be greater than zero."
        )

    font_size = BODY_FONT_SIZE
    leading = BODY_LEADING

    while font_size >= MIN_BODY_FONT_SIZE:
        style = _create_paragraph_style(
            font_size=font_size,
            leading=leading,
        )

        paragraph = Paragraph(
            escape(takeaway),
            style,
        )

        _, paragraph_height = paragraph.wrap(
            available_width,
            available_height,
        )

        if paragraph_height <= available_height:
            return paragraph, paragraph_height

        font_size -= FONT_REDUCTION_STEP
        leading = max(
            MIN_BODY_LEADING,
            leading - FONT_REDUCTION_STEP,
        )

    raise ValueError(
        "Key Takeaway is too long to fit safely inside "
        "the allocated box."
    )


# ==========================================================
# DRAW KEY TAKEAWAY
# ==========================================================

def draw_takeaway(
    pdf,
    box: Rectangle,
    takeaway: str,
) -> None:
    """
    Draw the complete Key Takeaway box.
    """

    if pdf is None:
        raise ValueError(
            "Key Takeaway PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Key Takeaway box cannot be None."
        )

    if not takeaway or not takeaway.strip():
        raise ValueError(
            "Key Takeaway text cannot be empty."
        )

    takeaway = takeaway.strip()

    # ------------------------------------------------------
    # OUTER BOX
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
    # INTERNAL GEOMETRY
    # ------------------------------------------------------

    left_x = (
        box.x
        + HORIZONTAL_PADDING
    )

    right_x = (
        box.right
        - HORIZONTAL_PADDING
    )

    top_y = (
        box.top
        - VERTICAL_PADDING
    )

    heading_y = (
        top_y
        - HEADING_FONT_SIZE
    )

    icon_y = (
        heading_y
        + (
            HEADING_FONT_SIZE
            - ICON_SIZE
        ) / 2
    )

    icon_drawn = draw_svg_icon(
        canvas=pdf,
        filepath=TAKEAWAY_ICON,
        x=left_x,
        y=icon_y,
        width=ICON_SIZE,
        height=ICON_SIZE,
    )

    heading_x = (
        left_x
        + ICON_SIZE
        + ICON_TEXT_GAP
        if icon_drawn
        else left_x
    )

    body_top = (
        heading_y
        - HEADING_BOTTOM_GAP
    )

    body_bottom = (
        box.y
        + VERTICAL_PADDING
    )

    available_width = (
        right_x
        - left_x
    )

    available_height = (
        body_top
        - body_bottom
    )

    paragraph, paragraph_height = _build_takeaway_paragraph(
        takeaway=takeaway,
        available_width=available_width,
        available_height=available_height,
    )

    paragraph_y = (
        body_top
        - paragraph_height
    )

    if paragraph_y < body_bottom:
        raise ValueError(
            "Key Takeaway text exceeds the safe content area."
        )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

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
            heading_x,
            heading_y,
            SECTION_TITLE,
        )

        paragraph.drawOn(
            pdf,
            left_x,
            paragraph_y,
        )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":
    print("=" * 60)
    print(
        "UPSC ISSUES BY KUMAR — "
        "KEY TAKEAWAY COMPONENT"
    )
    print("=" * 60)

    print(
        "Takeaway icon:",
        "FOUND"
        if TAKEAWAY_ICON.is_file()
        else "MISSING",
    )

    print("✓ Empty takeaway validation enabled")
    print("✓ Automatic text fitting enabled")
    print("✓ Overflow protection enabled")
    print("✓ Rounded box retained")
    print("=" * 60)