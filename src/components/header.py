"""
============================================================
Today's UPSC Issues
Page Header Component
Created by Sudhir
============================================================
"""

from datetime import datetime
from pathlib import Path

from src.components.helpers import (
    draw_horizontal_line,
    draw_logo,
)
from src.styles import (
    COLOURS,
    FONTS,
    HEADER_BOTTOM_LINE_WIDTH,
    SPACING,
)


def draw_header(
    canvas,
    page_width: float,
    page_height: float,
    date_text: str,
    logo_path: str | Path | None = None,
    page_number: int | None = None,
) -> float:
    """
    Draw the page header.

    Returns the y-coordinate immediately below the header.
    """

    left = SPACING.page_inner_padding + 8
    right = page_width - SPACING.page_inner_padding - 8
    top = page_height - SPACING.page_inner_padding - 8

    logo_width = 34
    logo_height = 34
    logo_x = left
    logo_y = top - logo_height

    title_x = left

    if logo_path:
        logo_drawn = draw_logo(
            canvas=canvas,
            filepath=logo_path,
            x=logo_x,
            y=logo_y,
            width=logo_width,
            height=logo_height,
        )

        if logo_drawn:
            title_x = logo_x + logo_width + 10

    canvas.saveState()

    title_font = FONTS.brand_title
    canvas.setFillColor(COLOURS.primary)
    canvas.setFont(title_font.name, title_font.size)
    canvas.drawString(
        title_x,
        top - title_font.size,
        "TODAY'S UPSC ISSUES",
    )

    meta_font = FONTS.header_meta
    canvas.setFillColor(COLOURS.muted_text)
    canvas.setFont(meta_font.name, meta_font.size)
    canvas.drawString(
        title_x,
        top - title_font.size - 13,
        "Daily Current Affairs for UPSC",
    )

    canvas.setFillColor(COLOURS.text)
    canvas.setFont(meta_font.name, meta_font.size)

    date_width = canvas.stringWidth(
        date_text,
        meta_font.name,
        meta_font.size,
    )

    canvas.drawString(
        right - date_width,
        top - meta_font.size,
        date_text,
    )

    if page_number is not None:
        page_text = f"Page {page_number}"

        page_width_text = canvas.stringWidth(
            page_text,
            meta_font.name,
            meta_font.size,
        )

        canvas.setFillColor(COLOURS.muted_text)
        canvas.drawString(
            right - page_width_text,
            top - meta_font.size - 13,
            page_text,
        )

    canvas.restoreState()

    divider_y = top - 43

    draw_horizontal_line(
        canvas=canvas,
        x1=left,
        y=divider_y,
        x2=right,
        colour=COLOURS.primary,
        thickness=HEADER_BOTTOM_LINE_WIDTH,
    )

    return divider_y - SPACING.section_gap