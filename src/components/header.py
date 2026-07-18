"""
============================================================
UPSC Issues by Kumar
Page Header Component
Created by Sudhir
============================================================
"""

from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth

from src.components.helpers import (
    draw_horizontal_line,
    draw_logo,
    draw_svg_icon,
)
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# HEADER TEXT
# ==========================================================

HEADER_TITLE = "TODAY'S UPSC ISSUES"
HEADER_BRAND = "UPSC Issues by Kumar"
EDITION_LABEL = "Daily Edition"


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRANDING_DIR = (
    PROJECT_ROOT
    / "assets"
    / "branding"
)

LEGACY_LOGO_DIR = (
    PROJECT_ROOT
    / "assets"
    / "logos"
    / "page"
)


# ==========================================================
# BRANDING ASSETS
# ==========================================================

PRIMARY_LOGO = (
    BRANDING_DIR
    / "logo_color_pdf.png"
)

LEGACY_LOGO = (
    LEGACY_LOGO_DIR
    / "today_upsc_logo.png"
)

CALENDAR_ICON = (
    LEGACY_LOGO_DIR
    / "calendar.svg"
)


# ==========================================================
# FONT SETTINGS
# ==========================================================

TITLE_FONT_NAME = FONTS.brand_title.name
TITLE_FONT_SIZE = 16.0
MIN_TITLE_FONT_SIZE = 12.5

BRAND_FONT_NAME = FONTS.header_meta.name
BRAND_FONT_SIZE = 7.0

DATE_FONT_NAME = BOLD_FONT
DATE_FONT_SIZE = 9.2
MIN_DATE_FONT_SIZE = 7.8


# ==========================================================
# GEOMETRY
# ==========================================================

HEADER_HORIZONTAL_PADDING = 10.0

LOGO_WIDTH = 31.0
LOGO_HEIGHT = 31.0
LOGO_TEXT_GAP = 7.0

TITLE_BRAND_GAP = 3.0
TITLE_DATE_GAP = 18.0

CALENDAR_ICON_SIZE = 11.0
CALENDAR_TEXT_GAP = 5.0

DIVIDER_WIDTH = 0.50


# ==========================================================
# ASSET RESOLUTION
# ==========================================================

def _resolve_logo_path() -> Path:
    """
    Return the first available official logo.

    Priority:
    1. New branding folder logo
    2. Previous page-logo location

    If neither exists, the preferred branding path is returned.
    The draw_logo helper may then handle the missing asset safely.
    """

    if PRIMARY_LOGO.exists():
        return PRIMARY_LOGO

    if LEGACY_LOGO.exists():
        return LEGACY_LOGO

    return PRIMARY_LOGO


# ==========================================================
# FONT FITTING
# ==========================================================

def _fit_font_size(
    text: str,
    font_name: str,
    preferred_size: float,
    available_width: float,
    minimum_size: float,
) -> float:
    """
    Reduce the font size until the supplied text fits inside
    the available width.
    """

    if available_width <= 0:
        return minimum_size

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
    Draw the complete UPSC Issues page header.

    Header layout:

    Left:
        Logo
        TODAY'S UPSC ISSUES
        UPSC Issues by Kumar

    Right:
        Calendar icon
        Daily Edition | Date
    """

    if pdf is None:
        raise ValueError(
            "Header PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Header box cannot be None."
        )

    if not date_text or not date_text.strip():
        raise ValueError(
            "Header date_text cannot be empty."
        )

    date_text = date_text.strip()
    logo_path = _resolve_logo_path()

    # ------------------------------------------------------
    # HEADER SEPARATOR
    # ------------------------------------------------------

    draw_horizontal_line(
        canvas=pdf,
        x1=box.x,
        y=box.y,
        x2=box.right,
        thickness=DIVIDER_WIDTH,
    )

    left_edge = (
        box.x
        + HEADER_HORIZONTAL_PADDING
    )

    right_edge = (
        box.right
        - HEADER_HORIZONTAL_PADDING
    )

    # ------------------------------------------------------
    # LEFT LOGO
    # ------------------------------------------------------

    logo_y = (
        box.center_y
        - (LOGO_HEIGHT / 2)
    )

    logo_drawn = draw_logo(
        canvas=pdf,
        filepath=logo_path,
        x=left_edge,
        y=logo_y,
        width=LOGO_WIDTH,
        height=LOGO_HEIGHT,
    )

    if logo_drawn:
        title_x = (
            left_edge
            + LOGO_WIDTH
            + LOGO_TEXT_GAP
        )
    else:
        title_x = left_edge

    # ------------------------------------------------------
    # RIGHT DATE GROUP
    # ------------------------------------------------------

    edition_text = (
        f"{EDITION_LABEL} | {date_text}"
    )

    preferred_date_text_width = stringWidth(
        edition_text,
        DATE_FONT_NAME,
        DATE_FONT_SIZE,
    )

    preferred_right_group_width = (
        CALENDAR_ICON_SIZE
        + CALENDAR_TEXT_GAP
        + preferred_date_text_width
    )

    right_group_x = (
        right_edge
        - preferred_right_group_width
    )

    calendar_y = (
        box.center_y
        - (CALENDAR_ICON_SIZE / 2)
        + 1.0
    )

    calendar_drawn = draw_svg_icon(
        canvas=pdf,
        filepath=CALENDAR_ICON,
        x=right_group_x,
        y=calendar_y,
        width=CALENDAR_ICON_SIZE,
        height=CALENDAR_ICON_SIZE,
    )

    if calendar_drawn:
        date_text_x = (
            right_group_x
            + CALENDAR_ICON_SIZE
            + CALENDAR_TEXT_GAP
        )
    else:
        date_text_x = right_group_x

    # ------------------------------------------------------
    # AVAILABLE WIDTHS
    # ------------------------------------------------------

    title_available_width = (
        date_text_x
        - TITLE_DATE_GAP
        - title_x
    )

    title_font_size = _fit_font_size(
        text=HEADER_TITLE,
        font_name=TITLE_FONT_NAME,
        preferred_size=TITLE_FONT_SIZE,
        available_width=title_available_width,
        minimum_size=MIN_TITLE_FONT_SIZE,
    )

    date_available_width = max(
        right_edge - date_text_x,
        preferred_date_text_width,
    )

    date_font_size = _fit_font_size(
        text=edition_text,
        font_name=DATE_FONT_NAME,
        preferred_size=DATE_FONT_SIZE,
        available_width=date_available_width,
        minimum_size=MIN_DATE_FONT_SIZE,
    )

    # ------------------------------------------------------
    # VERTICAL ALIGNMENT
    # ------------------------------------------------------

    title_visible_height = (
        title_font_size * 0.76
    )

    brand_visible_height = (
        BRAND_FONT_SIZE * 0.76
    )

    title_block_height = (
        title_visible_height
        + TITLE_BRAND_GAP
        + brand_visible_height
    )

    block_bottom = (
        box.center_y
        - (title_block_height / 2)
    )

    brand_y = block_bottom

    title_y = (
        brand_y
        + brand_visible_height
        + TITLE_BRAND_GAP
    )

    date_visible_height = (
        date_font_size * 0.76
    )

    date_y = (
        box.center_y
        - (date_visible_height / 2)
        + 1.0
    )

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
            title_x,
            title_y,
            HEADER_TITLE,
        )

        # Brand signature
        pdf.setFillColor(
            COLOURS.muted_text
        )

        pdf.setFont(
            BRAND_FONT_NAME,
            BRAND_FONT_SIZE,
        )

        pdf.drawString(
            title_x,
            brand_y,
            HEADER_BRAND,
        )

        # Edition and date
        pdf.setFillColor(
            COLOURS.text
        )

        pdf.setFont(
            DATE_FONT_NAME,
            date_font_size,
        )

        pdf.drawString(
            date_text_x,
            date_y,
            edition_text,
        )

    finally:
        pdf.restoreState()