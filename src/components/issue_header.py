"""
============================================================
UPSC Issues by Kumar
Issue Header Component
Created by Sudhir
============================================================
"""

from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from src.components.helpers import draw_horizontal_line
from src.layout import Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS
from reportlab.pdfbase.pdfmetrics import stringWidth


# ==========================================================
# FONT SETTINGS
# ==========================================================

ISSUE_NUMBER_FONT_SIZE = 14.0

TITLE_FONT_SIZE = 12.8
TITLE_MIN_FONT_SIZE = 10.0
TITLE_LEADING = 14.4
TITLE_MIN_LEADING = 11.8

GS_FONT_SIZE = 8.0
CATEGORY_FONT_SIZE = 6.2


# ==========================================================
# GEOMETRY
# ==========================================================

LEFT_PADDING = 7.0
RIGHT_PADDING = 10.0

NUMBER_AREA_WIDTH = 22.0
NUMBER_TITLE_GAP = 10.0

META_AREA_WIDTH = 62.0
TITLE_META_GAP = 8.0

VERTICAL_PADDING = 5.0

META_LINE_GAP = 4.0
DIVIDER_WIDTH = 0.45


# ==========================================================
# TITLE FITTING
# ==========================================================

def _build_title(
    title: str,
    available_width: float,
    available_height: float,
) -> tuple[Paragraph, float]:
    """
    Create a title paragraph that fits inside two lines.
    """

    font_size = TITLE_FONT_SIZE
    leading = TITLE_LEADING

    paragraph = None
    paragraph_height = 0.0

    while font_size >= TITLE_MIN_FONT_SIZE:
        style = ParagraphStyle(
            name=f"issue_title_{font_size:.1f}",
            fontName=BOLD_FONT,
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

        paragraph = Paragraph(
            escape(title),
            style,
        )

        _, paragraph_height = paragraph.wrap(
            available_width,
            available_height,
        )

        maximum_two_line_height = (
            leading * 2
            + 0.5
        )

        if (
            paragraph_height <= available_height
            and paragraph_height <= maximum_two_line_height
        ):
            return paragraph, paragraph_height

        font_size -= 0.2
        leading = max(
            TITLE_MIN_LEADING,
            leading - 0.2,
        )

    if paragraph is None:
        raise ValueError(
            "Unable to create issue title paragraph."
        )

    return paragraph, paragraph_height


# ==========================================================
# MAJOR TOPIC
# ==========================================================

def _major_topic_lines(
     text: str,
     font_name: str,
     font_size: float,
     max_width: float,
    ) -> list[str]:
    """
    Wrap the GS subject into the minimum number of lines
    that fit inside the available width.
    """

    words = text.split()

    if not words:
        return []

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:

        trial = f"{current} {word}"

        if (
            stringWidth(
                trial,
                font_name,
                font_size,
            )
            <= max_width
        ):
            current = trial
        else:
            lines.append(current)
            current = word

    lines.append(current)

    return lines


# ==========================================================
# DRAW ISSUE HEADER
# ==========================================================

def draw_issue_header(
    pdf,
    box: Rectangle,
    issue_number: int,
    title: str,
    gs_paper: str,
    category: str = "",
    rating: str = "",
) -> None:
    """
    Draw one issue header.

    Left:
        Issue number

    Centre:
        Issue title

    Right, centred:
        GS paper
        First major subject only
        One subject word per line

    The rating argument is accepted for compatibility with the
    PDF generator but is intentionally not displayed.
    """

    if pdf is None:
        raise ValueError(
            "Issue header PDF canvas cannot be None."
        )

    if box is None:
        raise ValueError(
            "Issue header box cannot be None."
        )

    if issue_number < 1:
        raise ValueError(
            "Issue number must be at least 1."
        )

    if not title or not title.strip():
        raise ValueError(
            "Issue title cannot be empty."
        )

    if not gs_paper or not gs_paper.strip():
        raise ValueError(
            "Issue GS paper cannot be empty."
        )

    title = title.strip()
    gs_paper = gs_paper.strip()
    category = category.strip()

    left_edge = (
        box.x
        + LEFT_PADDING
    )

    right_edge = (
        box.right
        - RIGHT_PADDING
    )

    title_x = (
        left_edge
        + NUMBER_AREA_WIDTH
        + NUMBER_TITLE_GAP
    )

    meta_area_x = (
        right_edge
        - META_AREA_WIDTH
    )

    meta_center_x = (
        meta_area_x
        + (META_AREA_WIDTH / 2)
    )

    title_width = (
        meta_area_x
        - TITLE_META_GAP
        - title_x
    )

    title_height = (
        box.height
        - (VERTICAL_PADDING * 2)
    )

    if title_width <= 0:
        raise ValueError(
            "Issue header title area has no available width."
        )

    title_paragraph, title_paragraph_height = _build_title(
        title=title,
        available_width=title_width,
        available_height=title_height,
    )

    title_y = (
        box.center_y
        - (title_paragraph_height / 2)
    )

    issue_number_y = (
        box.center_y
        - (ISSUE_NUMBER_FONT_SIZE * 0.34)
    )

    major_topic = (
      category
      .split("|", maxsplit=1)[0]
     .strip()
    )

    topic_lines = _major_topic_lines(
      text=major_topic,
      font_name=FONTS.issue_meta.name,
      font_size=CATEGORY_FONT_SIZE,
      max_width=META_AREA_WIDTH - 4.0,
    )

    meta_rows: list[
        tuple[str, str, float, object]
    ] = [
        (
            gs_paper,
            BOLD_FONT,
            GS_FONT_SIZE,
            COLOURS.primary,
        )
    ]

    for topic_line in topic_lines:
        meta_rows.append(
            (
                topic_line,
                FONTS.issue_meta.name,
                CATEGORY_FONT_SIZE,
                COLOURS.muted_text,
            )
        )

    meta_total_height = sum(
        font_size * 0.76
        for _, _, font_size, _ in meta_rows
    )

    if len(meta_rows) > 1:
        meta_total_height += (
            META_LINE_GAP
            * (len(meta_rows) - 1)
        )

    current_meta_y = (
        box.center_y
        + (meta_total_height / 2)
    )

    pdf.saveState()

    try:
        # Issue number
        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            BOLD_FONT,
            ISSUE_NUMBER_FONT_SIZE,
        )

        pdf.drawCentredString(
            left_edge
            + (NUMBER_AREA_WIDTH / 2),
            issue_number_y,
            str(issue_number),
        )

        # Issue title
        title_paragraph.drawOn(
            pdf,
            title_x,
            title_y,
        )

        # GS paper and major topic
        for (
            text,
            font_name,
            font_size,
            colour,
        ) in meta_rows:
            visible_height = (
                font_size * 0.76
            )

            current_meta_y -= visible_height

            pdf.setFillColor(
                colour
            )

            pdf.setFont(
                font_name,
                font_size,
            )

            pdf.drawCentredString(
                meta_center_x,
                current_meta_y,
                text,
            )

            current_meta_y -= META_LINE_GAP

    finally:
        pdf.restoreState()

    draw_horizontal_line(
        canvas=pdf,
        x1=box.x,
        y=box.y,
        x2=box.right,
        thickness=DIVIDER_WIDTH,
    )