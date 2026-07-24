"""
============================================================
Today's UPSC Issues
Five Content Sections Component
Version 2.0
Created by Sudhir
============================================================

Draws the five locked learning sections:

1. Current Context
2. Why It Matters for UPSC
3. Core Concept
4. Challenges
5. Way Forward

Design:

- No outer content box
- Monochrome SVG icon before each heading
- Full-width explanation text
- Thin horizontal divider between sections
- Automatic wrapping
- Bold keyword support using <b>...</b>
- Automatic font reduction when required
============================================================
"""

from dataclasses import dataclass
from html import escape as html_escape
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import (
    draw_horizontal_line,
    draw_svg_icon,
)
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# LOCKED HEADINGS
# ==========================================================

LOCKED_HEADINGS = (
    "Current Context",
    "Why It Matters for UPSC",
    "Core Concept",
    "Challenges",
    "Way Forward",
)


# ==========================================================
# ICON PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SECTION_ICON_DIR = (
    PROJECT_ROOT
    / "assets"
    / "logos"
    / "sections"
)

# Existing Version 1.0 icon files are reused.
# Only the displayed section headings have changed.
SECTION_ICONS = {
    "Current Context": (
        SECTION_ICON_DIR
        / "happening.svg"
    ),
    "Why It Matters for UPSC": (
        SECTION_ICON_DIR
        / "why_matters.svg"
    ),
    "Core Concept": (
        SECTION_ICON_DIR
        / "core_issue.svg"
    ),
    "Challenges": (
        SECTION_ICON_DIR
        / "challenges.svg"
    ),
    "Way Forward": (
        SECTION_ICON_DIR
        / "way_forward.svg"
    ),
}


# ==========================================================
# DATA MODEL
# ==========================================================

@dataclass(frozen=True, slots=True)
class ContentSection:
    """Represents one learning section."""

    heading: str
    text: str


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 9.8
HEADING_LEADING = 11.2

BODY_FONT_NAME = FONTS.body.name
BODY_FONT_SIZE = 9.5
BODY_LEADING = 11.5

MIN_HEADING_FONT_SIZE = 8.2
MIN_HEADING_LEADING = 9.6

MIN_BODY_FONT_SIZE = 8.0
MIN_BODY_LEADING = 9.8

FONT_REDUCTION_STEP = 0.2


# ==========================================================
# ICON SETTINGS
# ==========================================================

ICON_SIZE = 11.0
ICON_TEXT_GAP = 5.0


# ==========================================================
# SPACING SETTINGS
# ==========================================================

HORIZONTAL_PADDING = 7.0
VERTICAL_PADDING = 6.0

HEADING_TEXT_GAP = 3.0

DIVIDER_GAP_ABOVE = 2.0
DIVIDER_GAP_BELOW = 2.0
SECTION_GAP = 7.0

DIVIDER_LINE_WIDTH = 0.30
DIVIDER_HORIZONTAL_INSET = 0.0


# ==========================================================
# PARAGRAPH STYLES
# ==========================================================

def _create_heading_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """Create the section-heading paragraph style."""

    return ParagraphStyle(
        name=f"content_heading_{font_size:.1f}",
        fontName=HEADING_FONT_NAME,
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


def _create_body_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """Create the explanation paragraph style."""

    return ParagraphStyle(
        name=f"content_body_{font_size:.1f}",
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
# BODY MARKUP
# ==========================================================

def _prepare_body_text(text: str) -> str:
    """
    Escape body text while preserving supported bold tags.

    Supported markup:

        <b>important keyword</b>
    """

    bold_open_placeholder = "__BOLD_OPEN__"
    bold_close_placeholder = "__BOLD_CLOSE__"

    prepared = (
        text.replace(
            "<b>",
            bold_open_placeholder,
        )
        .replace(
            "</b>",
            bold_close_placeholder,
        )
    )

    prepared = html_escape(
        prepared,
        quote=False,
    )

    prepared = (
        prepared.replace(
            bold_open_placeholder,
            "<b>",
        )
        .replace(
            bold_close_placeholder,
            "</b>",
        )
    )

    return prepared


# ==========================================================
# VALIDATION
# ==========================================================

def _normalise_sections(
    sections,
) -> tuple[ContentSection, ...]:
    """Convert input into validated ContentSection objects."""

    if not isinstance(sections, (list, tuple)):
        raise TypeError(
            "Content sections must be supplied as a list or tuple."
        )

    if len(sections) != 5:
        raise ValueError(
            "The content area must contain exactly five sections."
        )

    normalised: list[ContentSection] = []

    for item in sections:
        if isinstance(item, ContentSection):
            section = item
        else:
            try:
                heading, text = item
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "Each content section must be a ContentSection "
                    "or a two-item (heading, text) tuple."
                ) from error

            section = ContentSection(
                heading=str(heading),
                text=str(text),
            )

        heading = section.heading.strip()
        text = section.text.strip()

        if not heading:
            raise ValueError(
                "Content section headings cannot be empty."
            )

        if not text:
            raise ValueError(
                f"Content for '{heading}' cannot be empty."
            )

        normalised.append(
            ContentSection(
                heading=heading,
                text=text,
            )
        )

    received_headings = tuple(
        section.heading
        for section in normalised
    )

    if received_headings != LOCKED_HEADINGS:
        required_order = "\n".join(
            f"{index}. {heading}"
            for index, heading in enumerate(
                LOCKED_HEADINGS,
                start=1,
            )
        )

        raise ValueError(
            "Content headings must follow the locked "
            f"Version 2.0 order:\n{required_order}"
        )

    return tuple(normalised)


# ==========================================================
# PARAGRAPH BUILDING
# ==========================================================

def _build_paragraphs(
    sections: tuple[ContentSection, ...],
    heading_width: float,
    body_width: float,
    heading_font_size: float,
    heading_leading: float,
    body_font_size: float,
    body_leading: float,
) -> list[
    tuple[
        ContentSection,
        Paragraph,
        float,
        Paragraph,
        float,
    ]
]:
    """Build heading and body paragraphs for all sections."""

    heading_style = _create_heading_style(
        font_size=heading_font_size,
        leading=heading_leading,
    )

    body_style = _create_body_style(
        font_size=body_font_size,
        leading=body_leading,
    )

    paragraph_data = []

    for section in sections:
        heading_paragraph = Paragraph(
            html_escape(
                section.heading,
                quote=False,
            ),
            heading_style,
        )

        _, heading_height = heading_paragraph.wrap(
            heading_width,
            1000,
        )

        body_paragraph = Paragraph(
            _prepare_body_text(section.text),
            body_style,
        )

        _, body_height = body_paragraph.wrap(
            body_width,
            1000,
        )

        paragraph_data.append(
            (
                section,
                heading_paragraph,
                heading_height,
                body_paragraph,
                body_height,
            )
        )

    return paragraph_data


# ==========================================================
# HEIGHT CALCULATION
# ==========================================================

def _calculate_total_height(
    paragraph_data,
) -> float:
    """Calculate the complete required vertical height."""

    text_height = sum(
        heading_height + body_height
        for (
            _,
            _,
            heading_height,
            _,
            body_height,
        ) in paragraph_data
    )

    heading_body_gaps = (
        len(paragraph_data)
        * HEADING_TEXT_GAP
    )

    divider_spacing = (
        (len(paragraph_data) - 1)
        * (
            DIVIDER_GAP_ABOVE
            + DIVIDER_GAP_BELOW
            + SECTION_GAP
        )
    )

    return (
        text_height
        + heading_body_gaps
        + divider_spacing
    )


# ==========================================================
# CONTENT FITTING
# ==========================================================

def _fit_content(
    sections: tuple[ContentSection, ...],
    heading_width: float,
    body_width: float,
    available_height: float,
):
    """Reduce font sizes until all content fits safely."""

    heading_font_size = HEADING_FONT_SIZE
    heading_leading = HEADING_LEADING

    body_font_size = BODY_FONT_SIZE
    body_leading = BODY_LEADING

    while True:
        paragraph_data = _build_paragraphs(
            sections=sections,
            heading_width=heading_width,
            body_width=body_width,
            heading_font_size=heading_font_size,
            heading_leading=heading_leading,
            body_font_size=body_font_size,
            body_leading=body_leading,
        )

        required_height = _calculate_total_height(
            paragraph_data
        )

        if required_height <= available_height:
            return (
                paragraph_data,
                required_height,
            )

        can_reduce_body = (
            body_font_size
            > MIN_BODY_FONT_SIZE
        )

        can_reduce_heading = (
            heading_font_size
            > MIN_HEADING_FONT_SIZE
        )

        if not can_reduce_body and not can_reduce_heading:
            raise ValueError(
                "The five content sections do not fit inside "
                "the available content area. Reduce the "
                "explanation lengths."
            )

        if can_reduce_body:
            body_font_size = max(
                MIN_BODY_FONT_SIZE,
                body_font_size
                - FONT_REDUCTION_STEP,
            )

            body_leading = max(
                MIN_BODY_LEADING,
                body_leading
                - FONT_REDUCTION_STEP,
            )

        if can_reduce_heading:
            heading_font_size = max(
                MIN_HEADING_FONT_SIZE,
                heading_font_size
                - FONT_REDUCTION_STEP,
            )

            heading_leading = max(
                MIN_HEADING_LEADING,
                heading_leading
                - FONT_REDUCTION_STEP,
            )


# ==========================================================
# DRAW CONTENT SECTIONS
# ==========================================================

def draw_content_sections(
    pdf,
    box: Rectangle,
    sections,
) -> None:
    """
    Draw the five Version 2.0 learning sections.

    Each section contains:

    - SVG icon
    - Heading
    - Full-width explanation
    - Divider below, except after the final section
    """

    if pdf is None:
        raise ValueError(
            "Content section PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Content section box cannot be None."
        )

    normalised_sections = _normalise_sections(
        sections
    )

    content_x = (
        box.x
        + HORIZONTAL_PADDING
    )

    content_top = (
        box.top
        - VERTICAL_PADDING
    )

    body_width = (
        box.width
        - (2 * HORIZONTAL_PADDING)
    )

    heading_width = (
        body_width
        - ICON_SIZE
        - ICON_TEXT_GAP
    )

    available_height = (
        box.height
        - (2 * VERTICAL_PADDING)
    )

    if heading_width <= 0:
        raise ValueError(
            "Content heading width is invalid."
        )

    if body_width <= 0:
        raise ValueError(
            "Content body width is invalid."
        )

    if available_height <= 0:
        raise ValueError(
            "Content drawing height is invalid."
        )

    (
        paragraph_data,
        required_height,
    ) = _fit_content(
        sections=normalised_sections,
        heading_width=heading_width,
        body_width=body_width,
        available_height=available_height,
    )

    extra_height = (
        available_height
        - required_height
    )

    cursor_y = (
        content_top
        - (extra_height / 2)
    )

    pdf.saveState()

    try:
        for index, (
            section,
            heading_paragraph,
            heading_height,
            body_paragraph,
            body_height,
        ) in enumerate(paragraph_data):

            # ------------------------------------------
            # HEADING
            # ------------------------------------------

            heading_y = (
                cursor_y
                - heading_height
            )

            icon_x = content_x

            icon_y = (
                heading_y
                + (
                    heading_height
                    - ICON_SIZE
                ) / 2
            )

            icon_path = SECTION_ICONS.get(
                section.heading
            )

            icon_drawn = False

            if icon_path is not None:
                icon_drawn = draw_svg_icon(
                    canvas=pdf,
                    filepath=icon_path,
                    x=icon_x,
                    y=icon_y,
                    width=ICON_SIZE,
                    height=ICON_SIZE,
                )

            if icon_drawn:
                heading_x = (
                    icon_x
                    + ICON_SIZE
                    + ICON_TEXT_GAP
                )
            else:
                heading_x = content_x

            heading_paragraph.drawOn(
                pdf,
                heading_x,
                heading_y,
            )

            # ------------------------------------------
            # EXPLANATION
            # ------------------------------------------

            body_top = (
                heading_y
                - HEADING_TEXT_GAP
            )

            body_y = (
                body_top
                - body_height
            )

            body_paragraph.drawOn(
                pdf,
                content_x,
                body_y,
            )

            cursor_y = body_y

            # ------------------------------------------
            # DIVIDER
            # ------------------------------------------

            if index < len(paragraph_data) - 1:
                divider_y = (
                    cursor_y
                    - DIVIDER_GAP_ABOVE
                )

                draw_horizontal_line(
                    canvas=pdf,
                    x1=(
                        box.x
                        + DIVIDER_HORIZONTAL_INSET
                    ),
                    y=divider_y,
                    x2=(
                        box.right
                        - DIVIDER_HORIZONTAL_INSET
                    ),
                    thickness=DIVIDER_LINE_WIDTH,
                )

                cursor_y = (
                    divider_y
                    - DIVIDER_GAP_BELOW
                    - SECTION_GAP
                )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":
    print("=" * 64)
    print(
        "TODAY'S UPSC ISSUES — "
        "VERSION 2.0 CONTENT SECTIONS"
    )
    print("=" * 64)

    for number, heading in enumerate(
        LOCKED_HEADINGS,
        start=1,
    ):
        icon_path = SECTION_ICONS[heading]

        status = (
            "FOUND"
            if icon_path.is_file()
            else "MISSING"
        )

        print(
            f"{number}. {heading} — {status}"
        )

    print("-" * 64)
    print("✓ Version 2.0 headings enabled")
    print("✓ Existing SVG icons reused")
    print("✓ Bold keyword support enabled")
    print("✓ Automatic text fitting enabled")
    print("✓ Overflow protection enabled")
    print("=" * 64)