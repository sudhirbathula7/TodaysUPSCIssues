"""
===========================================================
Today's UPSC Issues
Portrait Layout Development Test
Version : 1.0
Created By : Sudhir
===========================================================

This file generates a temporary PDF showing only the page
layout and individual component boxes.

It is used to visually inspect:

- Page header
- Two equal issue areas
- Compact issue header box
- Six-content-points box
- Recall questions box
- Quick facts box
- Key takeaway box
- Page footer

The generated PDF opens automatically on Windows.
===========================================================
"""

import os
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


# ===========================================================
# PROJECT PATH SETUP
# ===========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import only after the project root is available to Python.
from src.layout import (  # noqa: E402
    PAGE_HEIGHT,
    PAGE_WIDTH,
    IssueLayout,
    Rectangle,
    create_layout,
)


# ===========================================================
# OUTPUT
# ===========================================================

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "portrait_layout_test.pdf"


# ===========================================================
# TEMPORARY TEST COLOURS
# ===========================================================

PAGE_BORDER_COLOUR = HexColor("#9AA0A6")
BOX_BORDER_COLOUR = HexColor("#70757A")
LABEL_COLOUR = HexColor("#202124")
AREA_GUIDE_COLOUR = HexColor("#C5CAD0")


# ===========================================================
# DRAWING HELPERS
# ===========================================================

def draw_box(
    pdf: canvas.Canvas,
    box: Rectangle,
    label: str,
    *,
    line_width: float = 0.7,
    border_colour=BOX_BORDER_COLOUR,
    label_size: float = 7.0,
    dashed: bool = False,
) -> None:
    """
    Draw one temporary layout box with a label.
    """

    pdf.saveState()

    pdf.setStrokeColor(border_colour)
    pdf.setLineWidth(line_width)

    if dashed:
        pdf.setDash(3, 2)

    pdf.rect(
        box.x,
        box.y,
        box.width,
        box.height,
        stroke=1,
        fill=0,
    )

    pdf.setDash()
    pdf.setFillColor(LABEL_COLOUR)
    pdf.setFont("Helvetica-Bold", label_size)

    label_x = box.x + 4
    label_y = box.y + box.height - 10

    pdf.drawString(
        label_x,
        label_y,
        label,
    )

    pdf.restoreState()


def draw_issue_area_guide(
    pdf: canvas.Canvas,
    issue: IssueLayout,
    issue_number: int,
) -> None:
    """
    Draw the complete issue area as a light dashed guide.

    This is only a development reference. The production PDF
    will not draw this outer guide.
    """

    draw_box(
        pdf,
        issue.area,
        f"ISSUE {issue_number} TOTAL AREA",
        line_width=0.45,
        border_colour=AREA_GUIDE_COLOUR,
        label_size=6.2,
        dashed=True,
    )


def draw_issue_boxes(
    pdf: canvas.Canvas,
    issue: IssueLayout,
    issue_number: int,
) -> None:
    """
    Draw all five independent boxes of one issue.
    """

    draw_issue_area_guide(
        pdf,
        issue,
        issue_number,
    )

    draw_box(
        pdf,
        issue.header,
        f"ISSUE {issue_number} HEADER",
        line_width=0.8,
    )

    draw_box(
        pdf,
        issue.content,
        "SIX CONTENT POINTS",
        line_width=0.8,
    )

    draw_box(
        pdf,
        issue.recall,
        "RECALL QUESTIONS",
        line_width=0.8,
    )

    draw_box(
        pdf,
        issue.quick_facts,
        "QUICK FACTS",
        line_width=0.8,
    )

    draw_box(
        pdf,
        issue.takeaway,
        "KEY TAKEAWAY",
        line_width=0.8,
    )


# ===========================================================
# PDF GENERATION
# ===========================================================

def create_test_pdf() -> Path:
    """
    Generate the portrait layout skeleton PDF.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    layout = create_layout()

    pdf = canvas.Canvas(
        str(OUTPUT_FILE),
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
    )

    pdf.setTitle(
        "Today's UPSC Issues - Portrait Layout Test"
    )
    pdf.setAuthor("Sudhir")
    pdf.setSubject(
        "Development test for portrait page geometry"
    )

    # White page background
    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(
        0,
        0,
        PAGE_WIDTH,
        PAGE_HEIGHT,
        stroke=0,
        fill=1,
    )

    # Optional page-edge guide
    page_guide = Rectangle(
        x=0.5,
        y=0.5,
        width=PAGE_WIDTH - 1,
        height=PAGE_HEIGHT - 1,
    )

    draw_box(
        pdf,
        page_guide,
        "A4 PORTRAIT PAGE",
        line_width=0.3,
        border_colour=PAGE_BORDER_COLOUR,
        label_size=5.8,
    )

    # Header
    draw_box(
        pdf,
        layout.header,
        "PAGE HEADER",
        line_width=1.0,
    )

    # Issue 1
    draw_issue_boxes(
        pdf,
        layout.issue1,
        1,
    )

    # Issue 2
    draw_issue_boxes(
        pdf,
        layout.issue2,
        2,
    )

    # Footer
    draw_box(
        pdf,
        layout.footer,
        "PAGE FOOTER",
        line_width=1.0,
    )

    pdf.showPage()
    pdf.save()

    return OUTPUT_FILE


# ===========================================================
# OPEN GENERATED PDF
# ===========================================================

def open_generated_pdf(pdf_path: Path) -> None:
    """
    Open the generated PDF using the Windows default viewer.
    """

    try:
        os.startfile(str(pdf_path))
    except AttributeError:
        print(
            "Automatic opening is available on Windows only."
        )
    except OSError as error:
        print(
            "PDF generated successfully, but it could not "
            f"be opened automatically: {error}"
        )


# ===========================================================
# MAIN
# ===========================================================

def main() -> None:
    """
    Generate and automatically open the layout test PDF.
    """

    try:
        generated_file = create_test_pdf()

    except Exception as error:
        print("=" * 70)
        print("PORTRAIT LAYOUT TEST FAILED")
        print("=" * 70)
        print(f"{type(error).__name__}: {error}")
        print("=" * 70)
        raise

    print("=" * 70)
    print("TODAY'S UPSC ISSUES - PORTRAIT LAYOUT TEST")
    print("=" * 70)
    print(f"PDF generated successfully:")
    print(generated_file.resolve())
    print("-" * 70)
    print("The PDF will now open automatically.")
    print("=" * 70)

    open_generated_pdf(generated_file)


if __name__ == "__main__":
    main()