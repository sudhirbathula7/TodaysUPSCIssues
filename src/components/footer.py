"""
============================================================
UPSC Issues by Kumar
Page Footer Component
Created by Sudhir
============================================================
"""

from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

from src.components.helpers import (
    draw_horizontal_line,
    draw_svg_icon,
)
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# TEXT
# ==========================================================

FOOTER_BRAND = "UPSC Issues by Kumar"

WEBSITE_TEXT = "Website"
YOUTUBE_TEXT = "YouTube"
TELEGRAM_TEXT = "Telegram"


# ==========================================================
# ASSET PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOCIAL_ICON_DIR = (
    PROJECT_ROOT
    / "assets"
    / "logos"
    / "social"
)

WEBSITE_ICON = SOCIAL_ICON_DIR / "website.svg"
YOUTUBE_ICON = SOCIAL_ICON_DIR / "youtube.svg"
TELEGRAM_ICON = SOCIAL_ICON_DIR / "telegram.svg"


# ==========================================================
# FONT SETTINGS
# ==========================================================

BRAND_FONT_NAME = BOLD_FONT
BRAND_FONT_SIZE = 7.6

SOCIAL_FONT_NAME = FONTS.footer.name
SOCIAL_FONT_SIZE = 7.3

CODE_FONT_NAME = BOLD_FONT
CODE_FONT_SIZE = 7.5

PAGE_FONT_NAME = FONTS.footer.name
PAGE_FONT_SIZE = 7.1


# ==========================================================
# GEOMETRY
# ==========================================================

FOOTER_HORIZONTAL_PADDING = 10.0

SOCIAL_ICON_SIZE = 8.2
ICON_TEXT_GAP = 3.0
SOCIAL_GROUP_GAP = 9.0

BRAND_SOCIAL_GAP = 10.0
CODE_PAGE_GAP = 13.0

DIVIDER_WIDTH = 0.45


# ==========================================================
# DRAW SOCIAL ITEM
# ==========================================================

def _draw_social_item(
    pdf,
    icon_path: Path,
    text: str,
    x: float,
    baseline_y: float,
) -> float:
    """
    Draw one social icon and label.

    Returns:
        Total occupied width.
    """

    icon_y = (
        baseline_y
        - 1.0
    )

    icon_drawn = draw_svg_icon(
        canvas=pdf,
        filepath=icon_path,
        x=x,
        y=icon_y,
        width=SOCIAL_ICON_SIZE,
        height=SOCIAL_ICON_SIZE,
    )

    if icon_drawn:
        text_x = (
            x
            + SOCIAL_ICON_SIZE
            + ICON_TEXT_GAP
        )
    else:
        text_x = x

    pdf.setFillColor(
        COLOURS.muted_text
    )

    pdf.setFont(
        SOCIAL_FONT_NAME,
        SOCIAL_FONT_SIZE,
    )

    pdf.drawString(
        text_x,
        baseline_y,
        text,
    )

    text_width = stringWidth(
        text,
        SOCIAL_FONT_NAME,
        SOCIAL_FONT_SIZE,
    )

    return (
        text_x
        + text_width
        - x
    )


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

    Left:
        UPSC Issues by Kumar
        Website | YouTube | Telegram

    Right:
        Document code
        Page X / Y
    """

    if pdf is None:
        raise ValueError(
            "Footer PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Footer box cannot be None."
        )

    if not document_code or not document_code.strip():
        raise ValueError(
            "Footer document_code cannot be empty."
        )

    if page_number < 1:
        raise ValueError(
            "Footer page_number must be at least 1."
        )

    if total_pages < 1:
        raise ValueError(
            "Footer total_pages must be at least 1."
        )

    if page_number > total_pages:
        raise ValueError(
            "Footer page_number cannot exceed total_pages."
        )

    document_code = document_code.strip()

    # ------------------------------------------------------
    # TOP DIVIDER
    # ------------------------------------------------------

    draw_horizontal_line(
        canvas=pdf,
        x1=box.x,
        y=box.top,
        x2=box.right,
        thickness=DIVIDER_WIDTH,
    )

    left_edge = (
        box.x
        + FOOTER_HORIZONTAL_PADDING
    )

    right_edge = (
        box.right
        - FOOTER_HORIZONTAL_PADDING
    )

    baseline_y = (
        box.center_y
        - 2.4
    )

    # ------------------------------------------------------
    # RIGHT GROUP
    # ------------------------------------------------------

    page_text = (
        f"Page {page_number} / {total_pages}"
    )

    code_width = stringWidth(
        document_code,
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
        + CODE_PAGE_GAP
        + page_width
    )

    right_group_x = (
        right_edge
        - right_group_width
    )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    pdf.saveState()

    try:
        # Brand label
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        pdf.drawString(
            left_edge,
            baseline_y,
            FOOTER_BRAND,
        )

        brand_width = stringWidth(
            FOOTER_BRAND,
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        social_x = (
            left_edge
            + brand_width
            + BRAND_SOCIAL_GAP
        )

        # Website
        occupied = _draw_social_item(
            pdf=pdf,
            icon_path=WEBSITE_ICON,
            text=WEBSITE_TEXT,
            x=social_x,
            baseline_y=baseline_y,
        )

        social_x += (
            occupied
            + SOCIAL_GROUP_GAP
        )

        # YouTube
        occupied = _draw_social_item(
            pdf=pdf,
            icon_path=YOUTUBE_ICON,
            text=YOUTUBE_TEXT,
            x=social_x,
            baseline_y=baseline_y,
        )

        social_x += (
            occupied
            + SOCIAL_GROUP_GAP
        )

        # Telegram
        _draw_social_item(
            pdf=pdf,
            icon_path=TELEGRAM_ICON,
            text=TELEGRAM_TEXT,
            x=social_x,
            baseline_y=baseline_y,
        )

        # Document code
        pdf.setFillColor(
            COLOURS.text
        )

        pdf.setFont(
            CODE_FONT_NAME,
            CODE_FONT_SIZE,
        )

        pdf.drawString(
            right_group_x,
            baseline_y,
            document_code,
        )

        # Page number
        pdf.setFont(
            PAGE_FONT_NAME,
            PAGE_FONT_SIZE,
        )

        pdf.drawRightString(
            right_edge,
            baseline_y,
            page_text,
        )

    finally:
        pdf.restoreState()