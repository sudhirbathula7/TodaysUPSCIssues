"""
============================================================
Today's UPSC Issues
Quick Facts Component
Created by Sudhir
============================================================

Draws:

- QUICK FACTS heading
- Five to seven concise bullet facts
- Automatic text wrapping
- Automatic font reduction when needed
- White printer-friendly rounded box

The component draws inside the Rectangle supplied by layout.py.
============================================================
"""

from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# TEXT
# ==========================================================

SECTION_TITLE = "QUICK FACTS"


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 9.2

FACT_FONT_NAME = FONTS.quick_fact.name
FACT_FONT_SIZE = 8.6
FACT_LEADING = 10.4

MIN_FACT_FONT_SIZE = 7.4
MIN_FACT_LEADING = 9.0

FONT_REDUCTION_STEP = 0.2


# ==========================================================
# GEOMETRY SETTINGS
# ==========================================================

HORIZONTAL_PADDING = 9.0
VERTICAL_PADDING = 8.0

HEADING_BOTTOM_GAP = 6.0
FACT_GAP = 4.0

BULLET_RADIUS = 1.5
BULLET_TEXT_GAP = 6.0


# ==========================================================
# FACT PARAGRAPH STYLE
# ==========================================================

def _create_fact_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """
    Create the wrapped Quick Facts paragraph style.
    """

    return ParagraphStyle(
        name=f"quick_fact_{font_size:.1f}",
        fontName=FACT_FONT_NAME,
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
# VALIDATION
# ==========================================================

def _normalise_facts(
    facts: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    """
    Validate and clean the Quick Facts input.
    """

    if len(facts) != 5:
     raise ValueError(
        "Quick Facts must contain exactly 5 facts."
    )

    normalised = tuple(
        str(fact).strip()
        for fact in facts
    )

    if any(not fact for fact in normalised):
        raise ValueError(
            "Quick Facts cannot contain empty items."
        )

    return normalised


# ==========================================================
# PARAGRAPH BUILDING
# ==========================================================

def _build_fact_paragraphs(
    facts: tuple[str, ...],
    text_width: float,
    font_size: float,
    leading: float,
) -> list[tuple[Paragraph, float]]:
    """
    Build wrapped paragraphs for all Quick Facts.
    """

    style = _create_fact_style(
        font_size=font_size,
        leading=leading,
    )

    paragraph_data = []

    for fact in facts:
        paragraph = Paragraph(
            escape(fact),
            style,
        )

        _, height = paragraph.wrap(
            text_width,
            1000,
        )

        paragraph_data.append(
            (paragraph, height)
        )

    return paragraph_data


def _calculate_required_height(
    paragraph_data: list[tuple[Paragraph, float]],
) -> float:
    """
    Calculate the total height needed for all facts.
    """

    facts_height = sum(
        height
        for _, height in paragraph_data
    )

    gaps_height = (
        (len(paragraph_data) - 1)
        * FACT_GAP
    )

    return (
        facts_height
        + gaps_height
    )


# ==========================================================
# TEXT FITTING
# ==========================================================

def _fit_facts(
    facts: tuple[str, ...],
    text_width: float,
    available_height: float,
) -> tuple[list[tuple[Paragraph, float]], float]:
    """
    Reduce the fact font size until all items fit.
    """

    font_size = FACT_FONT_SIZE
    leading = FACT_LEADING

    while True:
        paragraph_data = _build_fact_paragraphs(
            facts=facts,
            text_width=text_width,
            font_size=font_size,
            leading=leading,
        )

        required_height = _calculate_required_height(
            paragraph_data
        )

        if required_height <= available_height:
            return paragraph_data, required_height

        if font_size <= MIN_FACT_FONT_SIZE:
            raise ValueError(
                "Quick Facts do not fit inside the available "
                "box. Reduce the number or length of facts."
            )

        font_size = max(
            MIN_FACT_FONT_SIZE,
            font_size - FONT_REDUCTION_STEP,
        )

        leading = max(
            MIN_FACT_LEADING,
            leading - FONT_REDUCTION_STEP,
        )


# ==========================================================
# DRAW BULLET
# ==========================================================

def _draw_bullet(
    pdf,
    x: float,
    y: float,
) -> None:
    """
    Draw one simple filled circular bullet.
    """

    pdf.saveState()

    pdf.setFillColor(
        COLOURS.primary
    )

    pdf.circle(
        x,
        y,
        BULLET_RADIUS,
        stroke=0,
        fill=1,
    )

    pdf.restoreState()


# ==========================================================
# DRAW QUICK FACTS
# ==========================================================

def draw_quick_facts(
    pdf,
    box: Rectangle,
    facts: list[str] | tuple[str, ...],
) -> None:
    """
    Draw the complete Quick Facts box.

    Supports 5–7 facts.
    """

    normalised_facts = _normalise_facts(
        facts
    )

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

    facts_top = (
        heading_y
        - HEADING_BOTTOM_GAP
    )

    bullet_x = (
        left_x
        + BULLET_RADIUS
    )

    text_x = (
        left_x
        + (2 * BULLET_RADIUS)
        + BULLET_TEXT_GAP
    )

    text_width = (
        right_x
        - text_x
    )

    available_facts_height = (
        facts_top
        - box.y
        - VERTICAL_PADDING
    )

    paragraph_data, required_height = _fit_facts(
        facts=normalised_facts,
        text_width=text_width,
        available_height=available_facts_height,
    )

    # Vertically centre the facts inside their available area.
    extra_height = (
        available_facts_height
        - required_height
    )

    cursor_y = (
        facts_top
        - (extra_height / 2)
    )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    pdf.saveState()

    try:
        # Heading
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            HEADING_FONT_NAME,
            HEADING_FONT_SIZE,
        )

        pdf.drawString(
            left_x,
            heading_y,
            SECTION_TITLE,
        )

        # Facts
        for index, (
            paragraph,
            paragraph_height,
        ) in enumerate(paragraph_data):

            paragraph_y = (
                cursor_y
                - paragraph_height
            )

            # Align bullet near the first line's visual centre.
            bullet_y = (
                cursor_y
                - min(
                    paragraph_height / 2,
                    FACT_LEADING * 0.45,
                )
            )

            _draw_bullet(
                pdf,
                bullet_x,
                bullet_y,
            )

            paragraph.drawOn(
                pdf,
                text_x,
                paragraph_y,
            )

            cursor_y = paragraph_y

            if index < len(paragraph_data) - 1:
                cursor_y -= FACT_GAP

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — QUICK FACTS")
    print("=" * 60)
    print("✓ Supports 5–7 facts")
    print("✓ Automatic wrapping enabled")
    print("✓ Automatic font reduction enabled")
    print("✓ Printer-friendly bullet layout enabled")
    print("=" * 60)