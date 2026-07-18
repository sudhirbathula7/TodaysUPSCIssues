"""
============================================================
UPSC Issues by Kumar
Recall Questions Component
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
from src.styles import BOLD_FONT, COLOURS


# ==========================================================
# TEXT
# ==========================================================

SECTION_TITLE = "RECALL QUESTIONS"


# ==========================================================
# ICON
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RECALL_ICON = (
    PROJECT_ROOT
    / "assets"
    / "logos"
    / "revision"
    / "recall.svg"
)

ICON_SIZE = 11.0
ICON_TEXT_GAP = 5.0


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 8.7

QUESTION_FONT_NAME = BOLD_FONT
QUESTION_FONT_SIZE = 8.7
QUESTION_LEADING = 10.7

MIN_QUESTION_FONT_SIZE = 6.6
MIN_QUESTION_LEADING = 7.8

LABEL_FONT_NAME = BOLD_FONT
LABEL_FONT_SIZE = 7.5

FONT_REDUCTION_STEP = 0.2


# ==========================================================
# SPACING
# ==========================================================

HORIZONTAL_PADDING = 8.0
VERTICAL_PADDING = 8.0

HEADING_BOTTOM_GAP = 7.0
QUESTION_GAP = 5.0

LABEL_AREA_WIDTH = 18.0
LABEL_TEXT_GAP = 3.0


# ==========================================================
# QUESTION STYLE
# ==========================================================

def _create_question_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """
    Create the recall-question paragraph style.
    """

    return ParagraphStyle(
        name=f"recall_question_{font_size:.1f}",
        fontName=QUESTION_FONT_NAME,
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
# QUESTION FITTING
# ==========================================================

def _fit_questions(
    question_1: str,
    question_2: str,
    text_width: float,
    available_height: float,
) -> tuple[
    Paragraph,
    float,
    Paragraph,
    float,
]:
    """
    Fit both questions together inside the available area.

    Both questions use the same font size so the box remains
    visually consistent.
    """

    if text_width <= 0:
        raise ValueError(
            "Recall question width must be greater than zero."
        )

    if available_height <= 0:
        raise ValueError(
            "Recall question height must be greater than zero."
        )

    font_size = QUESTION_FONT_SIZE
    leading = QUESTION_LEADING

    while font_size >= MIN_QUESTION_FONT_SIZE:
        style = _create_question_style(
            font_size=font_size,
            leading=leading,
        )

        paragraph_1 = Paragraph(
            escape(question_1),
            style,
        )

        paragraph_2 = Paragraph(
            escape(question_2),
            style,
        )

        _, height_1 = paragraph_1.wrap(
            text_width,
            available_height,
        )

        _, height_2 = paragraph_2.wrap(
            text_width,
            available_height,
        )

        total_required_height = (
            height_1
            + QUESTION_GAP
            + height_2
        )

        if total_required_height <= available_height:
            return (
                paragraph_1,
                height_1,
                paragraph_2,
                height_2,
            )

        font_size -= FONT_REDUCTION_STEP
        leading = max(
            MIN_QUESTION_LEADING,
            leading - FONT_REDUCTION_STEP,
        )

    raise ValueError(
        "Recall questions are too long to fit safely inside "
        "the allocated box. Reduce their length slightly."
    )


# ==========================================================
# DRAW RECALL QUESTIONS
# ==========================================================

def draw_recall_questions(
    pdf,
    box: Rectangle,
    questions,
) -> None:
    """
    Draw exactly two recall questions inside a rounded box.
    """

    if pdf is None:
        raise ValueError(
            "Recall Questions PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Recall Questions box cannot be None."
        )

    if not isinstance(
        questions,
        (list, tuple),
    ):
        raise TypeError(
            "Recall Questions must be supplied as a list or tuple."
        )

    if len(questions) != 2:
        raise ValueError(
            "Recall Questions must contain exactly two questions."
        )

    question_1 = str(
        questions[0]
    ).strip()

    question_2 = str(
        questions[1]
    ).strip()

    if not question_1 or not question_2:
        raise ValueError(
            "Recall questions cannot be empty."
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

    icon_x = left_x

    icon_y = (
        heading_y
        + (
            HEADING_FONT_SIZE
            - ICON_SIZE
        ) / 2
    )

    icon_drawn = draw_svg_icon(
        canvas=pdf,
        filepath=RECALL_ICON,
        x=icon_x,
        y=icon_y,
        width=ICON_SIZE,
        height=ICON_SIZE,
    )

    heading_x = (
        icon_x
        + ICON_SIZE
        + ICON_TEXT_GAP
        if icon_drawn
        else left_x
    )

    question_area_top = (
        heading_y
        - HEADING_BOTTOM_GAP
    )

    text_x = (
        left_x
        + LABEL_AREA_WIDTH
        + LABEL_TEXT_GAP
    )

    text_width = (
        right_x
        - text_x
    )

    content_bottom = (
        box.y
        + VERTICAL_PADDING
    )

    available_height = (
        question_area_top
        - content_bottom
    )

    (
        paragraph_1,
        height_1,
        paragraph_2,
        height_2,
    ) = _fit_questions(
        question_1=question_1,
        question_2=question_2,
        text_width=text_width,
        available_height=available_height,
    )

    question_1_y = (
        question_area_top
        - height_1
    )

    question_2_top = (
        question_1_y
        - QUESTION_GAP
    )

    question_2_y = (
        question_2_top
        - height_2
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
            heading_x,
            heading_y,
            SECTION_TITLE,
        )

        pdf.setFont(
            LABEL_FONT_NAME,
            LABEL_FONT_SIZE,
        )

        pdf.drawString(
            left_x,
            question_area_top
            - LABEL_FONT_SIZE,
            "Q1.",
        )

        paragraph_1.drawOn(
            pdf,
            text_x,
            question_1_y,
        )

        pdf.drawString(
            left_x,
            question_2_top
            - LABEL_FONT_SIZE,
            "Q2.",
        )

        paragraph_2.drawOn(
            pdf,
            text_x,
            question_2_y,
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
        "RECALL QUESTIONS COMPONENT"
    )
    print("=" * 60)

    print(
        "Recall icon:",
        "FOUND"
        if RECALL_ICON.is_file()
        else "MISSING",
    )

    print("✓ Exactly two recall questions required")
    print("✓ Shared automatic font fitting enabled")
    print("✓ Long-question support enabled")
    print("=" * 60)