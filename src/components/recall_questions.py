"""
============================================================
UPSC Issues by Kumar
Recall Question Component
Version 3.1
Created by Sudhir
============================================================

PURPOSE

Draw one contextual recall question and five revision anchors
inside the PDF recall box.

DISPLAY FORMAT

Topic: Recall question?

Anchor 1 | Anchor 2 | Anchor 3 | Anchor 4 | Anchor 5
============================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
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

SECTION_TITLE = "RECALL"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECALL_ICON = PROJECT_ROOT / "assets" / "logos" / "revision" / "recall.svg"

ICON_SIZE = 11.0
ICON_TEXT_GAP = 5.0

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 8.7

QUESTION_FONT_NAME = "Helvetica"
QUESTION_BOLD_FONT_NAME = "Helvetica-Bold"
QUESTION_FONT_SIZE = 8.2
QUESTION_LEADING = 10.2
MIN_QUESTION_FONT_SIZE = 6.6
MIN_QUESTION_LEADING = 8.0

ANCHOR_FONT_NAME = "Helvetica"
ANCHOR_FONT_SIZE = 6.9
ANCHOR_LEADING = 8.3
MIN_ANCHOR_FONT_SIZE = 5.7
MIN_ANCHOR_LEADING = 6.8

FONT_REDUCTION_STEP = 0.2

HORIZONTAL_PADDING = 8.0
VERTICAL_PADDING = 8.0
HEADING_BOTTOM_GAP = 6.0
QUESTION_ANCHOR_GAP = 5.0


def _clean_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty.")
    return cleaned


def _clean_anchors(anchors: Any) -> list[str]:
    if not isinstance(anchors, (list, tuple)):
        raise TypeError("Revision anchors must be supplied as a list or tuple.")

    cleaned: list[str] = []
    for index, anchor in enumerate(anchors, start=1):
        value = _clean_text(anchor, field_name=f"Revision anchor {index}")
        if value not in cleaned:
            cleaned.append(value)

    if len(cleaned) != 5:
        raise ValueError(
            "Revision anchors must contain exactly five unique non-empty items."
        )
    return cleaned


def _extract_question(questions: Any) -> str:
    if isinstance(questions, str):
        return _clean_text(questions, field_name="Recall question")

    if not isinstance(questions, (list, tuple)):
        raise TypeError(
            "Recall question must be supplied as a string, list or tuple."
        )

    if len(questions) != 1:
        raise ValueError("Recall Questions must contain exactly one question.")

    return _clean_text(questions[0], field_name="Recall question")


def _format_question_markup(question: str) -> str:
    if ":" not in question:
        return escape(question)

    topic, remainder = question.split(":", 1)
    topic = topic.strip()
    remainder = remainder.strip()

    if not topic or not remainder:
        return escape(question)

    return (
        f'<font name="{QUESTION_BOLD_FONT_NAME}">{escape(topic)}:</font> '
        f"{escape(remainder)}"
    )


def _question_style(font_size: float, leading: float) -> ParagraphStyle:
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


def _anchor_style(font_size: float, leading: float) -> ParagraphStyle:
    return ParagraphStyle(
        name=f"recall_anchors_{font_size:.1f}",
        fontName=ANCHOR_FONT_NAME,
        fontSize=font_size,
        leading=leading,
        textColor=COLOURS.primary,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=False,
        allowWidows=0,
        allowOrphans=0,
    )


def _fit_content(
    question: str,
    anchors_text: str,
    text_width: float,
    available_height: float,
) -> tuple[Paragraph, float, Paragraph, float]:
    if text_width <= 0:
        raise ValueError("Recall content width must be greater than zero.")
    if available_height <= 0:
        raise ValueError("Recall content height must be greater than zero.")

    question_size = QUESTION_FONT_SIZE
    question_leading = QUESTION_LEADING
    anchor_size = ANCHOR_FONT_SIZE
    anchor_leading = ANCHOR_LEADING
    question_markup = _format_question_markup(question)

    while (
        question_size >= MIN_QUESTION_FONT_SIZE
        and anchor_size >= MIN_ANCHOR_FONT_SIZE
    ):
        question_paragraph = Paragraph(
            question_markup,
            _question_style(question_size, question_leading),
        )
        anchor_paragraph = Paragraph(
            escape(anchors_text),
            _anchor_style(anchor_size, anchor_leading),
        )

        _, question_height = question_paragraph.wrap(text_width, available_height)
        _, anchor_height = anchor_paragraph.wrap(text_width, available_height)

        if question_height + QUESTION_ANCHOR_GAP + anchor_height <= available_height:
            return (
                question_paragraph,
                question_height,
                anchor_paragraph,
                anchor_height,
            )

        question_size -= FONT_REDUCTION_STEP
        question_leading = max(
            MIN_QUESTION_LEADING,
            question_leading - FONT_REDUCTION_STEP,
        )
        anchor_size -= FONT_REDUCTION_STEP
        anchor_leading = max(
            MIN_ANCHOR_LEADING,
            anchor_leading - FONT_REDUCTION_STEP,
        )

    raise ValueError(
        "Recall question and anchors are too long to fit inside the allocated PDF box."
    )


def draw_recall_questions(
    pdf,
    box: Rectangle,
    questions,
    anchors=None,
) -> None:
    """Draw one recall question and five horizontal anchors."""

    if pdf is None:
        raise ValueError("Recall PDF canvas cannot be None.")
    if box is None:
        raise ValueError("Recall box cannot be None.")

    question = _extract_question(questions)

    if anchors is None:
        raise ValueError(
            "Five revision anchors are required for the Version 3.1 recall box."
        )

    cleaned_anchors = _clean_anchors(anchors)
    anchors_text = " | ".join(cleaned_anchors)

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

    left_x = box.x + HORIZONTAL_PADDING
    right_x = box.right - HORIZONTAL_PADDING
    top_y = box.top - VERTICAL_PADDING
    heading_y = top_y - HEADING_FONT_SIZE

    icon_x = left_x
    icon_y = heading_y + (HEADING_FONT_SIZE - ICON_SIZE) / 2

    icon_drawn = draw_svg_icon(
        canvas=pdf,
        filepath=RECALL_ICON,
        x=icon_x,
        y=icon_y,
        width=ICON_SIZE,
        height=ICON_SIZE,
    )

    heading_x = (
        icon_x + ICON_SIZE + ICON_TEXT_GAP
        if icon_drawn
        else left_x
    )

    content_top = heading_y - HEADING_BOTTOM_GAP
    content_bottom = box.y + VERTICAL_PADDING
    text_width = right_x - left_x
    available_height = content_top - content_bottom

    (
        question_paragraph,
        question_height,
        anchor_paragraph,
        anchor_height,
    ) = _fit_content(
        question=question,
        anchors_text=anchors_text,
        text_width=text_width,
        available_height=available_height,
    )

    question_y = content_top - question_height
    anchor_y = question_y - QUESTION_ANCHOR_GAP - anchor_height

    pdf.saveState()
    try:
        pdf.setFillColor(COLOURS.primary)
        pdf.setFont(HEADING_FONT_NAME, HEADING_FONT_SIZE)
        pdf.drawString(heading_x, heading_y, SECTION_TITLE)

        question_paragraph.drawOn(pdf, left_x, question_y)
        anchor_paragraph.drawOn(pdf, left_x, anchor_y)
    finally:
        pdf.restoreState()


if __name__ == "__main__":
    print("=" * 60)
    print("UPSC ISSUES BY KUMAR — RECALL QUESTION COMPONENT V3.1")
    print("=" * 60)
    print("Recall icon:", "FOUND" if RECALL_ICON.is_file() else "MISSING")
    print("✓ Exactly one recall question required")
    print("✓ Exactly five revision anchors required")
    print("✓ Topic-before-colon bold formatting enabled")
    print("✓ Horizontal anchor display enabled")
    print("✓ Automatic font fitting enabled")
    print("=" * 60)