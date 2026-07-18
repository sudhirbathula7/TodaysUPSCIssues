"""
============================================================
Today's UPSC Issues
Production PDF Generator
Version : 1.0
Created by Sudhir
============================================================

Generates the final two-page A4 portrait publication from a
validated DailyIssueBook dataset.

This module does not read the daily input file directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.pdfgen import canvas
from src.layout import ISSUE_GAP
from src.components.content_section import draw_content_sections
from src.components.footer import draw_footer
from src.components.header import draw_header
from src.components.helpers import draw_horizontal_line
from src.components.issue_header import draw_issue_header
from src.components.quick_facts import draw_quick_facts
from src.components.recall_questions import draw_recall_questions
from src.components.takeaway import draw_takeaway
from src.layout import (
    PAGE_HEIGHT,
    PAGE_WIDTH,
    IssueLayout,
    create_layout,
)
from src.parser import DailyIssueBook, Issue


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


# ==========================================================
# PUBLICATION SETTINGS
# ==========================================================

ISSUES_PER_PAGE = 2
TOTAL_ISSUES = 4
TOTAL_PAGES = 2

PDF_TITLE = "Today's UPSC Issues"
PDF_AUTHOR = "Sudhir"
PDF_SUBJECT = "Daily UPSC issue-based learning publication"


# ==========================================================
# OUTPUT HELPERS
# ==========================================================

def build_document_code(book: DailyIssueBook) -> str:
    """
    Build the footer document code.

    Example:
        18 July 2026 -> #TUI-260718
    """

    return (
        "#TUI-"
        + book.publication_date.strftime("%y%m%d")
    )


def build_default_output_path(
    book: DailyIssueBook,
) -> Path:
    """
    Build the standard output PDF path.

    Example:
        output/TUI_260718.pdf
    """

    filename = (
        "TUI_"
        + book.publication_date.strftime("%y%m%d")
        + ".pdf"
    )

    return DEFAULT_OUTPUT_DIR / filename


def _prepare_output_path(
    output_path: str | Path | None,
    book: DailyIssueBook,
) -> Path:
    """
    Resolve and create the output directory.
    """

    if output_path is None:
        resolved_path = build_default_output_path(
            book
        )
    else:
        resolved_path = Path(output_path)

    if resolved_path.suffix.lower() != ".pdf":
        resolved_path = resolved_path.with_suffix(
            ".pdf"
        )

    resolved_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return resolved_path


# ==========================================================
# DATA MAPPING
# ==========================================================

def _build_content_sections(
    issue: Issue,
) -> list[tuple[str, str]]:
    """
    Convert an Issue into the five locked left-column sections.
    """

    return [
        (
            "Core Issue",
            issue.core_concept,
        ),
        (
            "What's Happening?",
            issue.current_context,
        ),
        (
            "Why It Matters",
            issue.why_it_matters,
        ),
        (
            "Key Challenges",
            issue.challenges,
        ),
        (
            "The Way Forward",
            issue.way_forward,
        ),
    ]


def _validate_issue_for_drawing(
    issue: Issue,
) -> None:
    """
    Perform final drawing-level checks.
    """

    if len(issue.recall_questions) != 2:
        raise ValueError(
            f"Issue {issue.issue_number}: exactly "
            "2 recall questions are required."
        )

    if not isinstance(
        issue.quick_facts,
        (list, tuple),
    ):
        raise TypeError(
            f"Issue {issue.issue_number}: quick_facts "
            "must be a list or tuple."
        )

    if len(issue.quick_facts) != 4:
        raise ValueError(
            f"Issue {issue.issue_number}: exactly "
            "4 Quick Facts are required."
        )


# ==========================================================
# ISSUE DRAWING
# ==========================================================

def draw_issue(
    pdf: canvas.Canvas,
    layout: IssueLayout,
    issue: Issue,
) -> None:
    """
    Draw one complete issue inside its allocated layout.
    """

    _validate_issue_for_drawing(
        issue
    )

    draw_issue_header(
        pdf=pdf,
        box=layout.header,
        issue_number=issue.issue_number,
        title=issue.issue_title,
        gs_paper=issue.gs_paper,
        category=issue.subject,
        rating=issue.display_rating,
    )

    draw_content_sections(
        pdf=pdf,
        box=layout.content,
        sections=_build_content_sections(
            issue
        ),
    )

    draw_recall_questions(
        pdf=pdf,
        box=layout.recall,
        questions=issue.recall_questions,
    )

    draw_quick_facts(
        pdf=pdf,
        box=layout.quick_facts,
        facts=issue.quick_facts,
    )

    draw_takeaway(
        pdf=pdf,
        box=layout.takeaway,
        takeaway=issue.key_takeaway,
    )


# ==========================================================
# PAGE DRAWING
# ==========================================================

def _draw_page_background(
    pdf: canvas.Canvas,
) -> None:
    """
    Draw a clean white page background.
    """

    pdf.saveState()

    try:
        pdf.setFillColorRGB(
            1,
            1,
            1,
        )

        pdf.rect(
            0,
            0,
            PAGE_WIDTH,
            PAGE_HEIGHT,
            stroke=0,
            fill=1,
        )

    finally:
        pdf.restoreState()


def draw_publication_page(
    pdf: canvas.Canvas,
    book: DailyIssueBook,
    page_number: int,
    page_issues: list[Issue],
) -> None:
    """
    Draw one complete publication page.
    """

    if page_number < 1:
        raise ValueError(
            "Page number must be at least 1."
        )

    if len(page_issues) != ISSUES_PER_PAGE:
        raise ValueError(
            f"Page {page_number} requires exactly "
            f"{ISSUES_PER_PAGE} issues."
        )

    layout = create_layout()

    _draw_page_background(
        pdf
    )

    draw_header(
        pdf=pdf,
        box=layout.header,
        date_text=book.formatted_date,
    )

    draw_issue(
        pdf=pdf,
        layout=layout.issue1,
        issue=page_issues[0],
    )

    # Divider
    draw_horizontal_line(
        canvas=pdf,
        x1=layout.issue1.area.x,
        y=layout.issue2.area.top + (ISSUE_GAP / 2),
        x2=layout.issue1.area.right,
        thickness=0.6,
    )

    draw_issue(
        pdf=pdf,
        layout=layout.issue2,
        issue=page_issues[1],
    )

    draw_footer(
        pdf=pdf,
        box=layout.footer,
        document_code=build_document_code(
            book
        ),
        page_number=page_number,
        total_pages=TOTAL_PAGES,
    )


# ==========================================================
# PDF GENERATION
# ==========================================================

def generate_pdf(
    book: DailyIssueBook,
    output_path: str | Path | None = None,
) -> Path:
    """
    Generate the final two-page production PDF.

    Returns:
        Path to the generated PDF.
    """

    if not isinstance(
        book,
        DailyIssueBook,
    ):
        raise TypeError(
            "generate_pdf expects a DailyIssueBook object."
        )

    if book.issue_count != TOTAL_ISSUES:
        raise ValueError(
            f"Exactly {TOTAL_ISSUES} issues are required. "
            f"Detected: {book.issue_count}."
        )

    output_file = _prepare_output_path(
        output_path=output_path,
        book=book,
    )

    pdf = canvas.Canvas(
        str(output_file),
        pagesize=(
            PAGE_WIDTH,
            PAGE_HEIGHT,
        ),
    )

    pdf.setTitle(
        f"{PDF_TITLE} - {book.formatted_date}"
    )

    pdf.setAuthor(
        PDF_AUTHOR
    )

    pdf.setSubject(
        PDF_SUBJECT
    )

    pdf.setCreator(
        "Today's UPSC Issues Publishing System"
    )

    try:
        for page_index in range(
            TOTAL_PAGES
        ):
            start_index = (
                page_index
                * ISSUES_PER_PAGE
            )

            end_index = (
                start_index
                + ISSUES_PER_PAGE
            )

            page_issues = book.issues[
                start_index:end_index
            ]

            draw_publication_page(
                pdf=pdf,
                book=book,
                page_number=page_index + 1,
                page_issues=page_issues,
            )

            pdf.showPage()

        pdf.save()

    except Exception:
        # Do not leave a misleading partial output behind.
        try:
            pdf.save()
        except Exception:
            pass

        if output_file.exists():
            try:
                output_file.unlink()
            except OSError:
                pass

        raise

    if not output_file.exists():
        raise RuntimeError(
            "PDF generation finished without creating "
            "the output file."
        )

    if output_file.stat().st_size == 0:
        output_file.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            "Generated PDF is empty."
        )

    return output_file


# ==========================================================
# OPEN PDF
# ==========================================================

def open_generated_pdf(
    pdf_path: str | Path,
) -> None:
    """
    Open the generated PDF using the Windows default viewer.
    """

    path = Path(pdf_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Generated PDF not found:\n{path}"
        )

    if os.name != "nt":
        print(
            "Automatic PDF opening is available "
            "on Windows only."
        )
        return

    try:
        os.startfile(
            str(path)
        )

    except OSError as error:
        print(
            "PDF generated successfully, but it could "
            f"not be opened automatically: {error}"
        )


# ==========================================================
# DEVELOPMENT ENTRY POINT
# ==========================================================

def main() -> None:
    """
    Read, validate, parse and generate the current daily PDF.
    """

    from src.parser import parse_validated_dataset
    from src.reader import read_today_dataset
    from src.validator import (
        print_validation_report,
        validate_dataset,
    )

    raw_dataset = read_today_dataset()

    validation_result = validate_dataset(
        raw_dataset
    )

    print_validation_report(
        validation_result
    )

    if not validation_result["is_valid"]:
        raise ValueError(
            "PDF generation stopped because "
            "dataset validation failed."
        )

    book = parse_validated_dataset(
        raw_dataset
    )

    generated_file = generate_pdf(
        book
    )

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — PDF GENERATOR")
    print("=" * 60)
    print("PDF generated successfully:")
    print(generated_file.resolve())
    print("=" * 60)

    open_generated_pdf(
        generated_file
    )


if __name__ == "__main__":
    main()