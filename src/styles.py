"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir
PDF Visual Style System
===========================================================

Contains all visual rules used by the PDF engine:

- Font names
- Font sizes
- Colours
- Border widths
- Padding
- Line spacing
- Corner radius
- Component-specific visual settings

This file does not calculate layout coordinates and does not
draw anything on the PDF canvas.
"""

from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor


# ===========================================================
# STYLE DATA CLASSES
# ===========================================================

@dataclass(frozen=True, slots=True)
class FontStyle:
    """
    Defines one reusable font style.
    """

    name: str
    size: float
    leading: float


@dataclass(frozen=True, slots=True)
class ColourPalette:
    """
    Defines the complete colour system for the PDF.
    """

    primary: Color
    primary_dark: Color
    secondary: Color

    text: Color
    muted_text: Color

    border: Color
    divider: Color

    page_background: Color
    box_background: Color
    light_background: Color
    highlight_background: Color

    white: Color
    black: Color


@dataclass(frozen=True, slots=True)
class BorderStyle:
    """
    Defines reusable border settings.
    """

    thin: float
    normal: float
    strong: float
    radius: float


@dataclass(frozen=True, slots=True)
class SpacingStyle:
    """
    Defines internal component padding and text spacing.
    """

    page_inner_padding: float

    box_padding_small: float
    box_padding: float
    box_padding_large: float

    section_gap_small: float
    section_gap: float
    section_gap_large: float

    title_gap: float
    heading_gap: float
    paragraph_gap: float

    bullet_indent: float
    bullet_text_gap: float


@dataclass(frozen=True, slots=True)
class IconStyle:
    """
    Defines icon and marker sizes.
    """

    section_icon_size: float
    question_icon_size: float
    issue_number_size: float
    bullet_radius: float


@dataclass(frozen=True, slots=True)
class FontCollection:
    """
    Stores every font style used by the PDF.
    """

    brand_title: FontStyle
    header_meta: FontStyle

    recall_label: FontStyle
    recall_question: FontStyle

    issue_number: FontStyle
    issue_title: FontStyle
    issue_meta: FontStyle
    gs_badge: FontStyle

    section_heading: FontStyle
    body: FontStyle
    body_bold: FontStyle

    quick_fact_heading: FontStyle
    quick_fact: FontStyle

    upsc_heading: FontStyle
    upsc_text: FontStyle

    takeaway_heading: FontStyle
    takeaway_text: FontStyle

    footer: FontStyle
    footer_bold: FontStyle


@dataclass(frozen=True, slots=True)
class PDFStyles:
    """
    Complete visual style system used by PDF components.
    """

    fonts: FontCollection
    colours: ColourPalette
    borders: BorderStyle
    spacing: SpacingStyle
    icons: IconStyle


# ===========================================================
# FONT NAMES
# ===========================================================

REGULAR_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
ITALIC_FONT = "Helvetica-Oblique"
BOLD_ITALIC_FONT = "Helvetica-BoldOblique"


# ===========================================================
# COLOUR PALETTE
# ===========================================================

COLOURS = ColourPalette(
    # Main identity colours
    primary=HexColor("#183B63"),
    primary_dark=HexColor("#102A47"),
    secondary=HexColor("#4F6F52"),

    # Text colours
    text=HexColor("#202020"),
    muted_text=HexColor("#5F6368"),

    # Lines and borders
    border=HexColor("#C9CED4"),
    divider=HexColor("#E1E4E8"),

    # Backgrounds
    page_background=HexColor("#FFFFFF"),
    box_background=HexColor("#FFFFFF"),
    light_background=HexColor("#F7F8FA"),
    highlight_background=HexColor("#F1F5F9"),

    # Base colours
    white=HexColor("#FFFFFF"),
    black=HexColor("#000000"),
)


# ===========================================================
# FONT STYLES
# ===========================================================

FONTS = FontCollection(
    # Page header
    brand_title=FontStyle(
        name=BOLD_FONT,
        size=14.0,
        leading=16.0,
    ),
    header_meta=FontStyle(
        name=REGULAR_FONT,
        size=8.2,
        leading=10.0,
    ),

    # Recall questions
    recall_label=FontStyle(
        name=BOLD_FONT,
        size=8.4,
        leading=10.0,
    ),
    recall_question=FontStyle(
        name=BOLD_FONT,
        size=9.0,
        leading=11.0,
    ),

    # Issue heading
    issue_number=FontStyle(
        name=BOLD_FONT,
        size=14.0,
        leading=15.0,
    ),
    issue_title=FontStyle(
        name=BOLD_FONT,
        size=13.0,
        leading=15.0,
    ),
    issue_meta=FontStyle(
        name=REGULAR_FONT,
        size=7.8,
        leading=9.5,
    ),
    gs_badge=FontStyle(
        name=BOLD_FONT,
        size=8.2,
        leading=9.5,
    ),

    # Main content sections
    section_heading=FontStyle(
        name=BOLD_FONT,
        size=9.1,
        leading=11.0,
    ),
    body=FontStyle(
        name=REGULAR_FONT,
        size=8.4,
        leading=10.6,
    ),
    body_bold=FontStyle(
        name=BOLD_FONT,
        size=8.4,
        leading=10.6,
    ),

    # Quick facts
    quick_fact_heading=FontStyle(
        name=BOLD_FONT,
        size=9.2,
        leading=11.0,
    ),
    quick_fact=FontStyle(
        name=REGULAR_FONT,
        size=8.1,
        leading=10.1,
    ),

    # What UPSC Asks
    upsc_heading=FontStyle(
        name=BOLD_FONT,
        size=9.2,
        leading=11.0,
    ),
    upsc_text=FontStyle(
        name=BOLD_FONT,
        size=8.5,
        leading=10.5,
    ),

    # Key takeaway
    takeaway_heading=FontStyle(
        name=BOLD_FONT,
        size=9.2,
        leading=11.0,
    ),
    takeaway_text=FontStyle(
        name=BOLD_FONT,
        size=8.6,
        leading=10.7,
    ),

    # Footer
    footer=FontStyle(
        name=REGULAR_FONT,
        size=7.2,
        leading=8.5,
    ),
    footer_bold=FontStyle(
        name=BOLD_FONT,
        size=7.2,
        leading=8.5,
    ),
)


# ===========================================================
# BORDER STYLES
# ===========================================================

BORDERS = BorderStyle(
    thin=0.45,
    normal=0.75,
    strong=1.10,
    radius=4.0,
)


# ===========================================================
# SPACING STYLES
# ===========================================================

SPACING = SpacingStyle(
    page_inner_padding=8.0,

    box_padding_small=4.0,
    box_padding=6.0,
    box_padding_large=8.0,

    section_gap_small=3.0,
    section_gap=5.0,
    section_gap_large=8.0,

    title_gap=4.0,
    heading_gap=2.5,
    paragraph_gap=3.0,

    bullet_indent=8.0,
    bullet_text_gap=4.0,
)


# ===========================================================
# ICON AND MARKER STYLES
# ===========================================================

ICONS = IconStyle(
    section_icon_size=8.0,
    question_icon_size=8.0,
    issue_number_size=22.0,
    bullet_radius=1.6,
)


# ===========================================================
# COMPLETE STYLE OBJECT
# ===========================================================

STYLES = PDFStyles(
    fonts=FONTS,
    colours=COLOURS,
    borders=BORDERS,
    spacing=SPACING,
    icons=ICONS,
)


# ===========================================================
# COMPONENT-SPECIFIC SETTINGS
# ===========================================================

# Header
HEADER_BOTTOM_LINE_WIDTH = BORDERS.normal

# Recall questions
RECALL_BOX_RADIUS = BORDERS.radius
RECALL_BOX_BORDER_WIDTH = BORDERS.normal
RECALL_QUESTION_DIVIDER_WIDTH = BORDERS.thin

# Issue header
ISSUE_NUMBER_BORDER_WIDTH = BORDERS.strong
ISSUE_HEADER_DIVIDER_WIDTH = BORDERS.normal
GS_BADGE_BORDER_WIDTH = BORDERS.normal
GS_BADGE_HORIZONTAL_PADDING = 6.0
GS_BADGE_VERTICAL_PADDING = 3.0

# Main content
CONTENT_SECTION_DIVIDER_WIDTH = BORDERS.thin
SECTION_ICON_LINE_WIDTH = BORDERS.normal

# Quick facts
QUICK_FACTS_BORDER_WIDTH = BORDERS.normal
QUICK_FACTS_BOX_RADIUS = BORDERS.radius
QUICK_FACT_BULLET_RADIUS = ICONS.bullet_radius

# What UPSC Asks
UPSC_BOX_BORDER_WIDTH = BORDERS.normal
UPSC_BOX_RADIUS = BORDERS.radius

# Key takeaway
TAKEAWAY_BOX_BORDER_WIDTH = BORDERS.normal
TAKEAWAY_BOX_RADIUS = BORDERS.radius

# Footer
FOOTER_TOP_LINE_WIDTH = BORDERS.thin


# ===========================================================
# TEXT FITTING LIMITS
# ===========================================================

MIN_BODY_FONT_SIZE = 7.2
MIN_QUICK_FACT_FONT_SIZE = 7.0
MIN_QUESTION_FONT_SIZE = 7.8
MIN_TAKEAWAY_FONT_SIZE = 7.6

FONT_REDUCTION_STEP = 0.2


# ===========================================================
# DEVELOPMENT TEST
# ===========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — STYLE SYSTEM")
    print("=" * 60)

    print(f"Primary colour : {COLOURS.primary}")
    print(f"Body font      : {FONTS.body.name}")
    print(f"Body size      : {FONTS.body.size}")
    print(f"Body leading   : {FONTS.body.leading}")
    print(f"Box padding    : {SPACING.box_padding}")
    print(f"Border radius  : {BORDERS.radius}")

    print("-" * 60)
    print("✓ PDF style system loaded successfully")
    print("=" * 60)