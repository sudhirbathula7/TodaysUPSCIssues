"""
============================================================
Today's UPSC Issues
Five Content Sections Component
Created by Sudhir
============================================================

Draws the five locked learning sections:

1. Core Issue
2. What's Happening?
3. Why It Matters
4. Key Challenges
5. The Way Forward

Features:

- Automatic text wrapping
- Bold keywords through ReportLab markup
- Automatic font reduction when required
- Consistent spacing
- Overflow validation
- Printer-friendly rounded outer box

The component draws inside the Rectangle supplied by layout.py.
============================================================
"""

from dataclasses import dataclass
from html import escape as html_escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# LOCKED SECTION HEADINGS
# ==========================================================

LOCKED_HEADINGS = (
    "Core Issue",
    "What's Happening?",
    "Why It Matters",
    "Key Challenges",
    "The Way Forward",
)


# ==========================================================
# CONTENT DATA
# ==========================================================

@dataclass(frozen=True, slots=True)
class ContentSection:
    """
    Represents one heading and explanation.
    """

    heading: str
    text: str


# ==========================================================
# FONT SETTINGS
# ==========================================================

HEADING_FONT_NAME = BOLD_FONT
HEADING_FONT_SIZE = 9.8
HEADING_LEADING = 11

BODY_FONT_NAME = FONTS.body.name
BODY_FONT_SIZE = 9.5
BODY_LEADING = 11.5

MIN_BODY_FONT_SIZE = 8.4
MIN_BODY_LEADING = 10.2

MIN_HEADING_FONT_SIZE = 8.4
MIN_HEADING_LEADING = 9.6

FONT_REDUCTION_STEP = 0.2

# ==========================================================
# SPACING SETTINGS
# ==========================================================

HORIZONTAL_PADDING = 9.0
VERTICAL_PADDING = 8.0

HEADING_TEXT_GAP = 3
SECTION_GAP = 4


# ==========================================================
# PARAGRAPH STYLES
# ==========================================================

def _create_heading_style(
    font_size: float,
    leading: float,
) -> ParagraphStyle:
    """
    Create the section-heading paragraph style.
    """

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
    """
    Create the body paragraph style.
    """

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
# TEXT PREPARATION
# ==========================================================

def _prepare_body_text(text: str) -> str:
    """
    Prepare body text for ReportLab Paragraph.

    Supported markup:

        <b>important keyword</b>

    Other special characters are escaped safely.
    """

    if not text:
        return ""

    # Preserve supported bold tags while escaping all other text.
    placeholder_open = "__BOLD_OPEN__"
    placeholder_close = "__BOLD_CLOSE__"

    prepared = (
        text.replace("<b>", placeholder_open)
        .replace("</b>", placeholder_close)
    )

    prepared = html_escape(
        prepared,
        quote=False,
    )

    prepared = (
        prepared.replace(placeholder_open, "<b>")
        .replace(placeholder_close, "</b>")
    )

    return prepared


# ==========================================================
# VALIDATION
# ==========================================================

def _normalise_sections(
    sections: (
        list[ContentSection]
        | tuple[ContentSection, ...]
        | list[tuple[str, str]]
        | tuple[tuple[str, str], ...]
    ),
) -> tuple[ContentSection, ...]:
    """
    Convert input into validated ContentSection objects.
    """

    if len(sections) != 5:
        raise ValueError(
            "The content box must contain exactly five sections."
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
        raise ValueError(
            "Content headings must follow the locked order:\n"
            + "\n".join(
                f"{index}. {heading}"
                for index, heading in enumerate(
                    LOCKED_HEADINGS,
                    start=1,
                )
            )
        )

    return tuple(normalised)


# ==========================================================
# PARAGRAPH BUILDING
# ==========================================================

def _build_paragraphs(
    sections: tuple[ContentSection, ...],
    content_width: float,
    heading_font_size: float,
    heading_leading: float,
    body_font_size: float,
    body_leading: float,
) -> list[tuple[Paragraph, float, Paragraph, float]]:
    """
    Build heading and body paragraphs for all five sections.

    Returns a list containing:

        heading paragraph,
        heading height,
        body paragraph,
        body height
    """

    heading_style = _create_heading_style(
        heading_font_size,
        heading_leading,
    )

    body_style = _create_body_style(
        body_font_size,
        body_leading,
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
            content_width,
            1000,
        )

        body_paragraph = Paragraph(
            _prepare_body_text(section.text),
            body_style,
        )

        _, body_height = body_paragraph.wrap(
            content_width,
            1000,
        )

        paragraph_data.append(
            (
                heading_paragraph,
                heading_height,
                body_paragraph,
                body_height,
            )
        )

    return paragraph_data


def _calculate_total_height(
    paragraph_data: list[
        tuple[Paragraph, float, Paragraph, float]
    ],
) -> float:
    """
    Calculate the total vertical height required.
    """

    text_height = sum(
        heading_height + body_height
        for (
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

    section_gaps = (
        (len(paragraph_data) - 1)
        * SECTION_GAP
    )

    return (
        text_height
        + heading_body_gaps
        + section_gaps
    )


# ==========================================================
# TEXT FITTING
# ==========================================================

def _fit_content(
    sections: tuple[ContentSection, ...],
    content_width: float,
    available_height: float,
) -> tuple[
    list[tuple[Paragraph, float, Paragraph, float]],
    float,
]:
    """
    Reduce heading and body font sizes until all five
    sections fit inside the available height.
    """

    heading_font_size = HEADING_FONT_SIZE
    heading_leading = HEADING_LEADING

    body_font_size = BODY_FONT_SIZE
    body_leading = BODY_LEADING

    while True:
        paragraph_data = _build_paragraphs(
            sections=sections,
            content_width=content_width,
            heading_font_size=heading_font_size,
            heading_leading=heading_leading,
            body_font_size=body_font_size,
            body_leading=body_leading,
        )

        required_height = _calculate_total_height(
            paragraph_data
        )

        if required_height <= available_height:
            return paragraph_data, required_height

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
                "the available content box, even at the minimum "
                "font sizes. Reduce the text length or increase "
                "the content-box height."
            )

        if can_reduce_body:
            body_font_size = max(
                MIN_BODY_FONT_SIZE,
                body_font_size - FONT_REDUCTION_STEP,
            )

            body_leading = max(
                MIN_BODY_LEADING,
                body_leading - FONT_REDUCTION_STEP,
            )

        if can_reduce_heading:
            heading_font_size = max(
                MIN_HEADING_FONT_SIZE,
                heading_font_size - FONT_REDUCTION_STEP,
            )

            heading_leading = max(
                MIN_HEADING_LEADING,
                heading_leading - FONT_REDUCTION_STEP,
            )


# ==========================================================
# DRAW CONTENT SECTIONS
# ==========================================================

def draw_content_sections(
    pdf,
    box: Rectangle,
    sections: (
        list[ContentSection]
        | tuple[ContentSection, ...]
        | list[tuple[str, str]]
        | tuple[tuple[str, str], ...]
    ),
) -> None:
    """
    Draw the five locked learning sections.

    Expected order:

    1. Core Issue
    2. What's Happening?
    3. Why It Matters
    4. Key Challenges
    5. The Way Forward
    """

    normalised_sections = _normalise_sections(
        sections
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
    # AVAILABLE DRAWING AREA
    # ------------------------------------------------------

    content_x = (
        box.x
        + HORIZONTAL_PADDING
    )

    content_top = (
        box.top
        - VERTICAL_PADDING
    )

    content_width = (
        box.width
        - (2 * HORIZONTAL_PADDING)
    )

    available_height = (
        box.height
        - (2 * VERTICAL_PADDING)
    )

    if content_width <= 0:
        raise ValueError(
            "Content-section drawing width is invalid."
        )

    if available_height <= 0:
        raise ValueError(
            "Content-section drawing height is invalid."
        )

    paragraph_data, required_height = _fit_content(
        sections=normalised_sections,
        content_width=content_width,
        available_height=available_height,
    )

    # Vertically centre the complete five-section block
    # when the content is shorter than the available area.
    extra_height = (
        available_height
        - required_height
    )

    cursor_y = (
        content_top
        - (extra_height / 2)
    )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    pdf.saveState()

    try:
        for index, (
            heading_paragraph,
            heading_height,
            body_paragraph,
            body_height,
        ) in enumerate(paragraph_data):

            heading_y = (
                cursor_y
                - heading_height
            )

            heading_paragraph.drawOn(
                pdf,
                content_x,
                heading_y,
            )

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

            if index < len(paragraph_data) - 1:
                cursor_y -= SECTION_GAP

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — FIVE CONTENT SECTIONS")
    print("=" * 60)

    for number, heading in enumerate(
        LOCKED_HEADINGS,
        start=1,
    ):
        print(f"{number}. {heading}")

    print("-" * 60)
    print("✓ Automatic wrapping enabled")
    print("✓ Bold keyword markup enabled")
    print("✓ Automatic font reduction enabled")
    print("✓ Overflow validation enabled")
    print("=" * 60)