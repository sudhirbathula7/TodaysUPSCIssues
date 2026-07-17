"""
============================================================
Today's UPSC Issues
Recall Questions Component
Created by Sudhir
============================================================

Draws:

- Recall Questions heading
- Two numbered recall questions
- Automatic wrapping
- Automatic font reduction when needed

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

SECTION_TITLE = "RECALL QUESTIONS"


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 8.7

QUESTION_FONT_NAME = BOLD_FONT
QUESTION_FONT_SIZE = 8.4
QUESTION_LEADING = 10.4

MIN_QUESTION_FONT_SIZE = 7.2
MIN_QUESTION_LEADING = 8.8

NUMBER_FONT_NAME = BOLD_FONT
NUMBER_FONT_SIZE = 7.4


# ==========================================================
# GEOMETRY SETTINGS
# ==========================================================

HORIZONTAL_PADDING = 8.0
VERTICAL_PADDING = 7.0

HEADING_BOTTOM_GAP = 9.0
QUESTION_GAP = 6.0

NUMBER_BOX_SIZE = 14.0
NUMBER_BOX_RADIUS = 4.0
NUMBER_TEXT_GAP = 5.0


# ==========================================================
# QUESTION PARAGRAPH
# ==========================================================

def _build_question_paragraph(
    question: str,
    width: float,
    max_height: float,
) -> tuple[Paragraph, float]:
    """
    Build a wrapped question paragraph that fits the
    available area.
    """

    font_size = QUESTION_FONT_SIZE
    leading = QUESTION_LEADING

    while font_size >= MIN_QUESTION_FONT_SIZE:

        style = ParagraphStyle(
            name="recall_question",
            fontName=QUESTION_FONT_NAME,
            fontSize=font_size,
            leading=leading,
            textColor=COLOURS.text,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            splitLongWords=False,
        )

        paragraph = Paragraph(
            escape(question),
            style,
        )

        _, height = paragraph.wrap(
            width,
            max_height,
        )

        if height <= max_height:
            return paragraph, height

        font_size -= 0.2
        leading = max(
            MIN_QUESTION_LEADING,
            leading - 0.2,
        )

    style = ParagraphStyle(
        name="recall_question_minimum",
        fontName=QUESTION_FONT_NAME,
        fontSize=MIN_QUESTION_FONT_SIZE,
        leading=MIN_QUESTION_LEADING,
        textColor=COLOURS.text,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=False,
    )

    paragraph = Paragraph(
        escape(question),
        style,
    )

    _, height = paragraph.wrap(
        width,
        max_height,
    )

    return paragraph, height


# ==========================================================
# DRAW NUMBER MARKER
# ==========================================================

def _draw_number_marker(
    pdf,
    number: int,
    x: float,
    y: float,
) -> None:
    """
    Draw one small white rounded number box.
    """

    pdf.setFillColor(
        COLOURS.box_background
    )

    pdf.setStrokeColor(
        COLOURS.border
    )

    pdf.roundRect(
        x,
        y,
        NUMBER_BOX_SIZE,
        NUMBER_BOX_SIZE,
        NUMBER_BOX_RADIUS,
        stroke=1,
        fill=1,
    )

    pdf.setFillColor(
        COLOURS.primary
    )

    pdf.setFont(
        NUMBER_FONT_NAME,
        NUMBER_FONT_SIZE,
    )

    pdf.drawCentredString(
        x + (NUMBER_BOX_SIZE / 2),
        y + 4.0,
        str(number),
    )


# ==========================================================
# DRAW RECALL QUESTIONS
# ==========================================================

def draw_recall_questions(
    pdf,
    box: Rectangle,
    questions: list[str] | tuple[str, str],
) -> None:
    """
    Draw exactly two recall questions.

    Example:

        RECALL QUESTIONS

        [1] What is the core issue?
        [2] What is the main challenge?
    """

    if len(questions) != 2:
        raise ValueError(
            "Recall Questions must contain exactly two questions."
        )

    question_1 = str(questions[0]).strip()
    question_2 = str(questions[1]).strip()

    if not question_1 or not question_2:
        raise ValueError(
            "Recall questions cannot be empty."
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

    question_area_top = (
        heading_y
        - HEADING_BOTTOM_GAP
    )

    question_text_x = (
        left_x
        + NUMBER_BOX_SIZE
        + NUMBER_TEXT_GAP
    )

    question_text_width = (
        right_x
        - question_text_x
    )

    available_question_height = (
        question_area_top
        - box.y
        - VERTICAL_PADDING
        - QUESTION_GAP
    )

    each_question_max_height = (
        available_question_height / 2
    )

    paragraph_1, height_1 = _build_question_paragraph(
        question=question_1,
        width=question_text_width,
        max_height=each_question_max_height,
    )

    paragraph_2, height_2 = _build_question_paragraph(
        question=question_2,
        width=question_text_width,
        max_height=each_question_max_height,
    )

    question_1_top = question_area_top
    question_1_y = (
        question_1_top
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

    marker_1_y = (
        question_1_top
        - NUMBER_BOX_SIZE
        + 1.0
    )

    marker_2_y = (
        question_2_top
        - NUMBER_BOX_SIZE
        + 1.0
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

        # Question 1
        _draw_number_marker(
            pdf,
            1,
            left_x,
            marker_1_y,
        )

        paragraph_1.drawOn(
            pdf,
            question_text_x,
            question_1_y,
        )

        # Question 2
        _draw_number_marker(
            pdf,
            2,
            left_x,
            marker_2_y,
        )

        paragraph_2.drawOn(
            pdf,
            question_text_x,
            question_2_y,
        )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — RECALL QUESTIONS")
    print("=" * 60)
    print("✓ Exactly two questions supported")
    print("✓ Automatic wrapping enabled")
    print("✓ Automatic font reduction enabled")
    print("=" * 60)