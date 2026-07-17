"""
===========================================================
Today's UPSC Issues
Portrait Layout Development Test
Version : 1.0
Created By : Sudhir
===========================================================

This file generates a temporary PDF showing:

- Real page header
- Two equal issue areas
- Compact issue header box
- Six-content-points box
- Recall questions box
- Quick facts box
- Key takeaway box
- Temporary footer placeholder

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


# Import project modules only after PROJECT_ROOT is added.
from src.components.takeaway import draw_takeaway
from src.components.quick_facts import draw_quick_facts
from src.components.content_section import draw_content_sections  # noqa: E402
from src.components.recall_questions import draw_recall_questions  # noqa: E402
from src.components.issue_header import draw_issue_header
from src.components.footer import draw_footer  # noqa: E402
from src.components.header import draw_header  # noqa: E402
from src.layout import (  # noqa: E402
    BOX_RADIUS,
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
    Draw one temporary rounded layout box with a label.
    """

    pdf.saveState()

    pdf.setStrokeColor(border_colour)
    pdf.setLineWidth(line_width)

    if dashed:
        pdf.setDash(3, 2)

    pdf.roundRect(
        box.x,
        box.y,
        box.width,
        box.height,
        BOX_RADIUS,
        stroke=1,
        fill=0,
    )

    pdf.setDash()
    pdf.setFillColor(LABEL_COLOUR)
    pdf.setFont("Helvetica-Bold", label_size)

    pdf.drawString(
        box.x + 4,
        box.y + box.height - 10,
        label,
    )

    pdf.restoreState()


def draw_issue_area_guide(
    pdf: canvas.Canvas,
    issue: IssueLayout,
    issue_number: int,
) -> None:
    """
    Draw a light dashed guide around the complete issue area.

    This guide is for development only and will not appear
    in the production PDF.
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
    Draw all five component boxes for one issue.
    """

    draw_issue_area_guide(
        pdf,
        issue,
        issue_number,
    )

    # ---------------------------------------------
    # Sample data for development testing
    # ---------------------------------------------

    if issue_number == 1:
        title = "Urban Flood Governance"
        gs_paper = "GS III"
        category = "Governance"

    else:
        title = (
            "Strengthening Parliamentary Committee "
            "Scrutiny for Better Governance"
        )
        gs_paper = "GS II"
        category = "Polity"

    draw_issue_header(
        pdf=pdf,
        box=issue.header,
        issue_number=issue_number,
        title=title,
        gs_paper=gs_paper,
        category=category,
    )

    if issue_number == 1:
     content_sections = [
        (
            "Core Issue",
            "Critical infrastructure cybersecurity must protect not only core systems, "
            "but also <b>contractors</b>, <b>vendors</b>, cloud services and connected supply chains.",
        ),
        (
            "What's Happening?",
            "A ransomware group reportedly leaked files linked to a contractor working on "
            "the Kudankulam nuclear power project, although the operational reactor network "
            "was stated to be unaffected.",
        ),
        (
            "Why It Matters",
            "Cyber incidents involving nuclear infrastructure can affect <b>national security</b>, "
            "public confidence, institutional credibility and the safety of strategic assets.",
        ),
        (
            "Key Challenges",
            "Delayed breach disclosure, weak incident response, poor vendor security, limited "
            "coordination and treating cybersecurity mainly as a compliance exercise reduce preparedness.",
        ),
        (
            "The Way Forward",
            "India needs stronger supply-chain security standards, timely disclosure, regular audits, "
            "better cyber hygiene and coordinated action by CERT-In, operators and private partners.",
        ),
    ]
    else:
     content_sections = [
        (
            "Core Issue",
            "Parliamentary committees improve legislative scrutiny by examining bills, budgets, "
            "ministries and public policies in greater detail than is possible during full House debates.",
        ),
        (
            "What's Happening?",
            "Concerns continue over weak committee referrals, limited discussion time and reduced "
            "institutional scrutiny of important legislation.",
        ),
        (
            "Why It Matters",
            "Strong committee oversight improves <b>accountability</b>, evidence-based lawmaking, "
            "executive control and the quality of parliamentary democracy.",
        ),
        (
            "Key Challenges",
            "Non-binding recommendations, limited research support, inconsistent referrals and "
            "political majorities can weaken committee effectiveness.",
        ),
        (
            "The Way Forward",
            "Important bills should receive regular committee scrutiny, research support must improve, "
            "and governments should provide reasoned responses to committee recommendations.",
        ),
    ]

    draw_content_sections(
    pdf=pdf,
    box=issue.content,
    sections=content_sections,
    )

    if issue_number == 1:
     recall_questions = (
        "Why do Indian cities continue to face severe urban flooding?",
        "What governance reforms can improve urban flood resilience?",
    )
    else:
     recall_questions = (
        "Why are parliamentary committees important for legislative scrutiny?",
        "What limits the effectiveness of committee oversight in India?",
    )

    draw_recall_questions(
    pdf=pdf,
    box=issue.recall,
    questions=recall_questions,
    )

    if issue_number == 1:

        quick_facts = [

        "CERT-In is India's national cyber incident response agency.",

        "Kudankulam is India's largest nuclear power project.",

        "Ransomware attacks may involve both encryption and data theft.",

        "Supply-chain attacks often target contractors instead of core systems.",

        "Critical infrastructure follows layered cyber-security architecture.",


        ]

    else:

        quick_facts = [

        "Department-related Standing Committees examine Bills in detail.",

        "Committee recommendations are advisory in nature.",

        "Parliamentary Committees improve legislative scrutiny.",

        "Committee reports strengthen executive accountability.",

        "Both Lok Sabha and Rajya Sabha have Standing Committees.",

    ]


    draw_quick_facts(
    pdf=pdf,
    box=issue.quick_facts,
    facts=quick_facts,
    )

    if issue_number == 1:

        takeaway = (
        "Cybersecurity for critical infrastructure must extend "
        "beyond reactors to <b>vendors</b>, <b>contractors</b> "
        "and digital supply chains through proactive protection "
        "and transparent incident response."
         )

    else:

        takeaway = (
        "Strong Parliamentary Committees improve "
        "<b>accountability</b>, legislative quality and "
        "executive oversight, making them essential to a "
        "healthy parliamentary democracy."
        )

    draw_takeaway(
    pdf=pdf,
    box=issue.takeaway,
    takeaway=takeaway,
)

# ===========================================================
# PDF GENERATION
# ===========================================================

def create_test_pdf() -> Path:
    """
    Generate the portrait layout test PDF.
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

    # Optional page-edge development guide
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

    # Real header component
    draw_header(
        pdf=pdf,
        box=layout.header,
        date_text="17 July 2026",
    )

    # Issue 1 placeholders
    draw_issue_boxes(
        pdf,
        layout.issue1,
        1,
    )

    # Issue 2 placeholders
    draw_issue_boxes(
        pdf,
        layout.issue2,
        2,
    )

    # Temporary footer placeholder
    draw_footer(
    pdf=pdf,
    box=layout.footer,
    document_code="#TUI-260717",
    page_number=1,
    total_pages=2,
    )

    pdf.showPage()
    pdf.save()

    return OUTPUT_FILE


# ===========================================================
# OPEN GENERATED PDF
# ===========================================================

def open_generated_pdf(pdf_path: Path) -> None:
    """
    Open the generated PDF with the Windows default viewer.
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
    Generate and automatically open the test PDF.
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
    print("PDF generated successfully:")
    print(generated_file.resolve())
    print("-" * 70)
    print("The PDF will now open automatically.")
    print("=" * 70)

    open_generated_pdf(generated_file)


if __name__ == "__main__":
    main()