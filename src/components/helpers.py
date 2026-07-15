"""
============================================================
Today's UPSC Issues
PDF Helper Functions
Created by Sudhir
============================================================
"""

from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph

from src.styles import BORDERS, COLOURS, FONTS, SPACING


# ==========================================================
# ROUNDED BOX
# ==========================================================

def draw_rounded_box(
    canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill_color=None,
    stroke_color=None,
    radius: float | None = None,
    line_width: float | None = None,
) -> None:
    """
    Draw a printer-friendly rounded rectangle.
    """

    fill_color = fill_color or COLOURS.box_background
    stroke_color = stroke_color or COLOURS.border
    radius = BORDERS.radius if radius is None else radius
    line_width = BORDERS.normal if line_width is None else line_width

    canvas.saveState()
    canvas.setFillColor(fill_color)
    canvas.setStrokeColor(stroke_color)
    canvas.setLineWidth(line_width)

    canvas.roundRect(
        x,
        y,
        width,
        height,
        radius,
        fill=1,
        stroke=1,
    )

    canvas.restoreState()


# ==========================================================
# HORIZONTAL LINE
# ==========================================================

def draw_horizontal_line(
    canvas,
    x1: float,
    y: float,
    x2: float,
    colour=None,
    thickness: float | None = None,
) -> None:
    """
    Draw a horizontal divider line.
    """

    colour = colour or COLOURS.divider
    thickness = BORDERS.thin if thickness is None else thickness

    canvas.saveState()
    canvas.setStrokeColor(colour)
    canvas.setLineWidth(thickness)
    canvas.line(x1, y, x2, y)
    canvas.restoreState()


# ==========================================================
# PAGE BORDER
# ==========================================================

def draw_page_border(
    canvas,
    page_width: float,
    page_height: float,
    margin: float = 19.0,
) -> None:
    """
    Draw the outer printable page border.

    The larger margin protects content during printing,
    trimming and binding.
    """

    canvas.saveState()
    canvas.setStrokeColor(COLOURS.border)
    canvas.setLineWidth(BORDERS.thin)

    canvas.rect(
        margin,
        margin,
        page_width - (2 * margin),
        page_height - (2 * margin),
        fill=0,
        stroke=1,
    )

    canvas.restoreState()


# ==========================================================
# LOGO
# ==========================================================

def draw_logo(
    canvas,
    filepath: str | Path,
    x: float,
    y: float,
    width: float,
    height: float,
) -> bool:
    """
    Draw a logo while preserving its aspect ratio.

    Returns True when the logo is drawn.
    Returns False when the file does not exist.
    """

    logo_path = Path(filepath)

    if not logo_path.is_file():
        return False

    canvas.drawImage(
        ImageReader(str(logo_path)),
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )

    return True


# ==========================================================
# SMALL LABEL
# ==========================================================

def draw_small_label(
    canvas,
    text: str,
    x: float,
    y: float,
    colour=None,
) -> None:
    """
    Draw a small bold metadata label.
    """

    font = FONTS.gs_badge
    colour = colour or COLOURS.primary

    canvas.saveState()
    canvas.setFillColor(colour)
    canvas.setFont(font.name, font.size)
    canvas.drawString(x, y, text)
    canvas.restoreState()


# ==========================================================
# SECTION TITLE
# ==========================================================

def draw_section_title(
    canvas,
    text: str,
    x: float,
    y: float,
    colour=None,
) -> None:
    """
    Draw a standard section heading.
    """

    font = FONTS.section_heading
    colour = colour or COLOURS.primary

    canvas.saveState()
    canvas.setFillColor(colour)
    canvas.setFont(font.name, font.size)
    canvas.drawString(x, y, text)
    canvas.restoreState()


# ==========================================================
# PARAGRAPH STYLE
# ==========================================================

def create_paragraph_style(
    name: str = "body",
    font_name: str | None = None,
    font_size: float | None = None,
    leading: float | None = None,
    text_color=None,
    alignment: int = 0,
) -> ParagraphStyle:
    """
    Create a reusable ReportLab paragraph style.
    """

    body_font = FONTS.body

    return ParagraphStyle(
        name=name,
        fontName=font_name or body_font.name,
        fontSize=font_size or body_font.size,
        leading=leading or body_font.leading,
        textColor=text_color or COLOURS.text,
        alignment=alignment,
        spaceBefore=0,
        spaceAfter=0,
    )


# ==========================================================
# BODY TEXT
# ==========================================================

def draw_body_text(
    canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_name: str | None = None,
    font_size: float | None = None,
    leading: float | None = None,
    text_color=None,
) -> float:
    """
    Draw wrapped text below the supplied top coordinate.

    Returns the height occupied by the paragraph.
    """

    style = create_paragraph_style(
        name="body_text",
        font_name=font_name,
        font_size=font_size,
        leading=leading,
        text_color=text_color,
    )

    paragraph = Paragraph(text or "", style)
    _, height = paragraph.wrap(width, 1000)

    paragraph.drawOn(canvas, x, y - height)

    return height


# ==========================================================
# TEXT HEIGHT
# ==========================================================

def measure_text_height(
    text: str,
    width: float,
    font_name: str | None = None,
    font_size: float | None = None,
    leading: float | None = None,
) -> float:
    """
    Calculate the height of wrapped paragraph text.
    """

    style = create_paragraph_style(
        name="measure_text",
        font_name=font_name,
        font_size=font_size,
        leading=leading,
    )

    paragraph = Paragraph(text or "", style)
    _, height = paragraph.wrap(width, 1000)

    return height


# ==========================================================
# TEXT WIDTH
# ==========================================================

def measure_text_width(
    text: str,
    font_name: str | None = None,
    font_size: float | None = None,
) -> float:
    """
    Calculate the width of a single line of text.
    """

    font = FONTS.body

    return stringWidth(
        text or "",
        font_name or font.name,
        font_size or font.size,
    )


# ==========================================================
# DEVELOPMENT TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — PDF HELPERS")
    print("=" * 60)
    print(f"Body font     : {FONTS.body.name}")
    print(f"Body size     : {FONTS.body.size}")
    print(f"Body leading  : {FONTS.body.leading}")
    print(f"Primary colour: {COLOURS.primary}")
    print("-" * 60)
    print("✓ PDF helper functions loaded successfully")
    print("=" * 60)