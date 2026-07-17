"""
============================================================
Today's UPSC Issues
Issue Header Component
Created by Sudhir
============================================================

Draws:

- Issue number inside a small rounded box
- One-line or two-line issue title
- GS badge on the right
- Topic/category aligned below the GS badge

The component draws inside the Rectangle supplied by layout.py.
============================================================
"""

from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph

from src.components.helpers import draw_rounded_box
from src.layout import BOX_RADIUS, Rectangle
from src.styles import BOLD_FONT, COLOURS, FONTS


# ==========================================================
# FONT SETTINGS
# ==========================================================

NUMBER_FONT_NAME = BOLD_FONT
NUMBER_FONT_SIZE = 10.0

TITLE_FONT_NAME = BOLD_FONT
TITLE_FONT_SIZE = 12.2
TITLE_LEADING = 14.0

MIN_TITLE_FONT_SIZE = 10.0
MIN_TITLE_LEADING = 11.8

GS_FONT_NAME = BOLD_FONT
GS_FONT_SIZE = 7.8

CATEGORY_FONT_NAME = FONTS.issue_meta.name
CATEGORY_FONT_SIZE = 6.9
CATEGORY_LEADING = 8.0


# ==========================================================
# GEOMETRY SETTINGS
# ==========================================================

HORIZONTAL_PADDING = 8.0
VERTICAL_PADDING = 5.0

NUMBER_BOX_WIDTH = 22.0
NUMBER_BOX_HEIGHT = 22.0
NUMBER_BOX_RADIUS = 5.0

NUMBER_TITLE_GAP = 7.0

RIGHT_AREA_WIDTH = 60.0
TITLE_RIGHT_GAP = 7.0

BADGE_HORIZONTAL_PADDING = 7.0
BADGE_VERTICAL_PADDING = 3.0
BADGE_RADIUS = 3.0

CATEGORY_TOP_GAP = 3.0


# ==========================================================
# TITLE FITTING
# ==========================================================

def _build_title_paragraph(
    title: str,
    width: float,
    height: float,
) -> tuple[Paragraph, float, float]:
    """
    Build a title paragraph that fits within a maximum of
    two lines.
    """

    font_size = TITLE_FONT_SIZE
    leading = TITLE_LEADING

    while font_size >= MIN_TITLE_FONT_SIZE:

        style = ParagraphStyle(
            name="issue_header_title",
            fontName=TITLE_FONT_NAME,
            fontSize=font_size,
            leading=leading,
            textColor=COLOURS.text,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            splitLongWords=False,
        )

        paragraph = Paragraph(
            escape(title),
            style,
        )

        wrapped_width, wrapped_height = paragraph.wrap(
            width,
            height,
        )

        if (
            wrapped_height <= height
            and wrapped_height <= (leading * 2 + 0.5)
        ):
            return (
                paragraph,
                wrapped_width,
                wrapped_height,
            )

        font_size -= 0.2
        leading = max(
            MIN_TITLE_LEADING,
            leading - 0.2,
        )

    style = ParagraphStyle(
        name="issue_header_title_minimum",
        fontName=TITLE_FONT_NAME,
        fontSize=MIN_TITLE_FONT_SIZE,
        leading=MIN_TITLE_LEADING,
        textColor=COLOURS.text,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=False,
    )

    paragraph = Paragraph(
        escape(title),
        style,
    )

    wrapped_width, wrapped_height = paragraph.wrap(
        width,
        height,
    )

    return paragraph, wrapped_width, wrapped_height


# ==========================================================
# DRAW ISSUE HEADER
# ==========================================================

def draw_issue_header(
    pdf,
    box: Rectangle,
    issue_number: int,
    title: str,
    gs_paper: str,
    category: str,
) -> None:
    """
    Draw one compact issue header.
    """

    if issue_number < 1:
        raise ValueError(
            "issue_number must be at least 1."
        )

    if not title or not title.strip():
        raise ValueError(
            "Issue title cannot be empty."
        )

    if not gs_paper or not gs_paper.strip():
        raise ValueError(
            "GS paper cannot be empty."
        )

    title = title.strip()
    gs_paper = gs_paper.strip()
    category = (category or "").strip()

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

    left_x = box.x + HORIZONTAL_PADDING
    right_x = box.right - HORIZONTAL_PADDING

    number_box_x = left_x
    number_box_y = box.center_y - (NUMBER_BOX_HEIGHT / 2)

    title_x = (
        number_box_x
        + NUMBER_BOX_WIDTH
        + NUMBER_TITLE_GAP
    )

    right_area_x = (
        right_x
        - RIGHT_AREA_WIDTH
    )

    title_width = (
        right_area_x
        - TITLE_RIGHT_GAP
        - title_x
    )

    title_height = (
        box.height
        - (2 * VERTICAL_PADDING)
    )

    # ------------------------------------------------------
    # TITLE
    # ------------------------------------------------------

    (
        title_paragraph,
        _,
        title_wrapped_height,
    ) = _build_title_paragraph(
        title=title,
        width=title_width,
        height=title_height,
    )

    title_y = (
        box.center_y
        - (title_wrapped_height / 2)
    )

    # ------------------------------------------------------
    # GS BADGE
    # ------------------------------------------------------

    badge_text_width = stringWidth(
        gs_paper,
        GS_FONT_NAME,
        GS_FONT_SIZE,
    )

    badge_width = (
        badge_text_width
        + (2 * BADGE_HORIZONTAL_PADDING)
    )

    badge_height = (
        GS_FONT_SIZE
        + (2 * BADGE_VERTICAL_PADDING)
    )

    badge_x = right_area_x + 6
    badge_y = box.center_y + 2.5

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    category_style = ParagraphStyle(
        name="issue_category",
        fontName=CATEGORY_FONT_NAME,
        fontSize=CATEGORY_FONT_SIZE,
        leading=CATEGORY_LEADING,
        textColor=COLOURS.muted_text,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=0,
        splitLongWords=False,
    )

    category_paragraph = Paragraph(
        escape(category),
        category_style,
    )

    _, category_height = category_paragraph.wrap(
        RIGHT_AREA_WIDTH,
        box.height,
    )

    category_y = (
        badge_y
        - CATEGORY_TOP_GAP
        - category_height
    )

    # ------------------------------------------------------
    # DRAW
    # ------------------------------------------------------

    pdf.saveState()

    try:
        # Number box
        pdf.setFillColor(COLOURS.box_background
        )
        

        pdf.setStrokeColor(
            COLOURS.border
        )

        pdf.roundRect(
            number_box_x,
            number_box_y,
            NUMBER_BOX_WIDTH,
            NUMBER_BOX_HEIGHT,
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
            number_box_x + (NUMBER_BOX_WIDTH / 2),
            number_box_y + 6.2,
            str(issue_number),
        )

        # Title
        title_paragraph.drawOn(
            pdf,
            title_x,
            title_y,
        )

        # GS badge
        pdf.setFillColor(COLOURS.box_background)

        pdf.setStrokeColor(
            COLOURS.border
        )

        pdf.roundRect(
            badge_x,
            badge_y,
            badge_width,
            badge_height,
            BADGE_RADIUS,
            stroke=1,
            fill=1,
        )

        pdf.setFillColor(
            COLOURS.primary
        )

        pdf.setFont(
            GS_FONT_NAME,
            GS_FONT_SIZE,
        )

        pdf.drawCentredString(
            badge_x + (badge_width / 2),
            badge_y + BADGE_VERTICAL_PADDING,
            gs_paper,
        )

        # Category aligned to GS badge left edge
        if category:
            category_paragraph.drawOn(
                pdf,
                badge_x,
                category_y,
            )

    finally:
        pdf.restoreState()


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — ISSUE HEADER")
    print("=" * 60)
    print("✓ Rounded issue-number box enabled")
    print("✓ Category aligned below GS badge")
    print("✓ One-line and two-line titles supported")
    print("=" * 60)