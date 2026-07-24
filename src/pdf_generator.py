"""
============================================================
TODAY'S UPSC ISSUES
PDF GENERATOR
Version 3.1
Created by Sudhir
============================================================

PURPOSE

Generates the final portrait PDF from the Version 3.1 daily
PDF dataset.

WORKFLOW

1. Locate the dated pdf_dataset.json file.
2. Validate all issue content.
3. Load previous-day recall questions.
4. Fall back to current issue recall questions only when the
   previous-day recall schedule is unavailable during development.
5. Create an A4 portrait PDF.
6. Place two issues on every page.
7. Use the existing locked layout and drawing components.
8. Save the final PDF using DD-MM-YY naming.

DEFAULT COMMAND

python -m src.pdf_generator 2026-07-19

REBUILD COMMAND

python -m src.pdf_generator 2026-07-19 --overwrite

OPEN AFTER GENERATION

python -m src.pdf_generator 2026-07-19 --overwrite --open
============================================================
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from reportlab.pdfgen import canvas


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT COMPONENTS
# ============================================================

from src.components.content_section import (  # noqa: E402
    ContentSection,
    draw_content_sections,
)
from src.components.footer import draw_footer  # noqa: E402
from src.components.header import draw_header  # noqa: E402
from src.components.issue_header import draw_issue_header  # noqa: E402
from src.components.quick_facts import draw_quick_facts  # noqa: E402
from src.components.recall_questions import (  # noqa: E402
    draw_recall_questions,
)
from src.components.takeaway import draw_takeaway  # noqa: E402
from src.layout import (  # noqa: E402
    PAGE_HEIGHT,
    PAGE_WIDTH,
    IssueLayout,
    create_layout,
)


# ============================================================
# PROJECT PATHS
# ============================================================

OUTPUT_ROOT = PROJECT_ROOT / "output"
DAILY_OUTPUT_ROOT = OUTPUT_ROOT / "daily"

REPOSITORY_ROOT = PROJECT_ROOT / "Repository"
DAILY_REPOSITORY_ROOT = REPOSITORY_ROOT / "daily"


# ============================================================
# FILE NAMES
# ============================================================

PDF_DATASET_FILE = "pdf_dataset.json"
SELECTED_ISSUES_FILE = "selected_issues.json"

PDF_FILENAME_PREFIX = "Todays_UPSC_Issues"


# ============================================================
# EXCEPTIONS
# ============================================================

class PDFGeneratorError(Exception):
    """Base exception for final PDF generation errors."""


class PDFDatasetError(PDFGeneratorError):
    """Raised when the PDF dataset is missing or invalid."""


class PDFAlreadyExistsError(PDFGeneratorError):
    """Raised when the final PDF already exists."""


class PDFContentOverflowError(PDFGeneratorError):
    """Raised when issue content cannot fit in its allocated area."""


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class PDFResult:
    """Summary returned after final PDF generation."""

    publication_date: str
    pdf_path: Path
    issue_count: int
    page_count: int
    document_code: str

    def display(self) -> None:
        """Print a readable result summary."""

        print("=" * 64)
        print("TODAY'S UPSC ISSUES")
        print("FINAL PDF GENERATOR")
        print("=" * 64)
        print(f"Publication date : {self.publication_date}")
        print(f"Document code    : {self.document_code}")
        print(f"Issues rendered  : {self.issue_count}")
        print(f"Pages generated  : {self.page_count}")
        print(f"Final PDF        : {self.pdf_path}")
        print("-" * 64)
        print("✓ Final portrait PDF generated successfully")
        print("=" * 64)


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date(value: str | date | datetime) -> date:
    """Convert supported date values into a date object."""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    cleaned = str(value).strip()

    supported_formats = (
        "%Y-%m-%d",
        "%d-%m-%y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for format_string in supported_formats:
        try:
            return datetime.strptime(
                cleaned,
                format_string,
            ).date()
        except ValueError:
            continue

    raise PDFDatasetError(
        "Unsupported publication date. Use one of these formats:\n"
        "2026-07-19\n"
        "19-07-26\n"
        "19-07-2026\n"
        "19/07/2026\n"
        "19 July 2026"
    )


def _display_date(publication_date: date) -> str:
    """Return the locked display and folder date."""

    return publication_date.strftime("%d-%m-%y")


def _iso_date(publication_date: date) -> str:
    """Return the legacy ISO date used by earlier Version 2.0 files."""

    return publication_date.isoformat()


def _document_code(publication_date: date) -> str:
    """Return the locked document code."""

    return f"#TUI-{publication_date.strftime('%y%m%d')}"


# ============================================================
# JSON HELPERS
# ============================================================

def _read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file."""

    if not path.exists():
        raise PDFDatasetError(
            f"Required JSON file was not found:\n{path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise PDFDatasetError(
            f"Invalid JSON file:\n{path}\n"
            f"Line {error.lineno}, column {error.colno}: "
            f"{error.msg}"
        ) from error


def _clean_text(value: Any) -> str:
    """Return trimmed text."""

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# PATH RESOLUTION
# ============================================================

def _candidate_daily_folders(
    root: Path,
    publication_date: date,
) -> tuple[Path, Path]:
    """
    Return new and legacy dated folder candidates.

    Priority:
    1. DD-MM-YY
    2. YYYY-MM-DD
    """

    return (
        root / _display_date(publication_date),
        root / _iso_date(publication_date),
    )


def find_pdf_dataset_path(
    publication_date: str | date | datetime,
) -> Path:
    """Locate the prepared daily PDF dataset."""

    parsed_date = _parse_date(publication_date)

    for folder in _candidate_daily_folders(
        DAILY_OUTPUT_ROOT,
        parsed_date,
    ):
        path = folder / PDF_DATASET_FILE

        if path.exists():
            return path

    searched_paths = "\n".join(
        str(folder / PDF_DATASET_FILE)
        for folder in _candidate_daily_folders(
            DAILY_OUTPUT_ROOT,
            parsed_date,
        )
    )

    raise PDFDatasetError(
        "PDF dataset was not found. Searched:\n"
        f"{searched_paths}"
    )


def find_selected_issues_path(
    publication_date: date,
) -> Path | None:
    """
    Locate the repository selected-issues file.

    This file provides current recall questions as a development
    fallback when previous-day recall data is unavailable.
    """

    for folder in _candidate_daily_folders(
        DAILY_REPOSITORY_ROOT,
        publication_date,
    ):
        path = folder / SELECTED_ISSUES_FILE

        if path.exists():
            return path

    return None


def get_final_pdf_folder(
    publication_date: date,
) -> Path:
    """Return the locked DD-MM-YY final output folder."""

    return (
        DAILY_OUTPUT_ROOT
        / _display_date(publication_date)
    )


def get_final_pdf_path(
    publication_date: date,
) -> Path:
    """Return the locked final PDF path."""

    filename = (
        f"{PDF_FILENAME_PREFIX}_"
        f"{_display_date(publication_date)}.pdf"
    )

    return (
        get_final_pdf_folder(publication_date)
        / filename
    )


# ============================================================
# DATASET LOADING
# ============================================================

def load_pdf_dataset(
    publication_date: str | date | datetime,
) -> dict[str, Any]:
    """Load and validate the prepared daily PDF dataset."""

    parsed_date = _parse_date(publication_date)
    dataset_path = find_pdf_dataset_path(parsed_date)
    dataset = _read_json(dataset_path)

    if not isinstance(dataset, dict):
        raise PDFDatasetError(
            "pdf_dataset.json must contain a JSON object."
        )

    issues = dataset.get("issues")

    if not isinstance(issues, list):
        raise PDFDatasetError(
            'pdf_dataset.json must contain an "issues" list.'
        )

    if not issues:
        raise PDFDatasetError(
            "The PDF dataset does not contain any issues."
        )

    if len(issues) > 8:
        raise PDFDatasetError(
            "The final PDF supports a maximum of eight issues."
        )

    dataset["_dataset_path"] = dataset_path
    dataset["_parsed_date"] = parsed_date

    validate_pdf_dataset(dataset)

    return dataset


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_pdf_dataset(
    dataset: dict[str, Any],
) -> None:
    """Validate all issue fields required by the renderer."""

    issues = dataset["issues"]

    required_text_fields = (
        "title",
        "gs_paper",
        "current_context",
        "why_it_matters_for_upsc",
        "core_concept",
        "challenges",
        "way_forward",
        "key_takeaway",
    )

    for issue_number, issue in enumerate(
        issues,
        start=1,
    ):
        if not isinstance(issue, dict):
            raise PDFDatasetError(
                f"Issue {issue_number} must be a JSON object."
            )

        for field_name in required_text_fields:
            value = _clean_text(
                issue.get(field_name)
            )

            if not value:
                raise PDFDatasetError(
                    f"Issue {issue_number} is missing "
                    f"required field: {field_name}"
                )

        quick_facts = issue.get("quick_facts")

        if not isinstance(
            quick_facts,
            (list, tuple),
        ):
            raise PDFDatasetError(
                f"Issue {issue_number} Quick Facts "
                "must be a list."
            )

        if len(quick_facts) != 4:
            raise PDFDatasetError(
                f"Issue {issue_number} must contain "
                "exactly four Quick Facts."
            )

        if any(
            not _clean_text(fact)
            for fact in quick_facts
        ):
            raise PDFDatasetError(
                f"Issue {issue_number} contains an "
                "empty Quick Fact."
            )


# ============================================================
# RECALL QUESTION RESOLUTION
# ============================================================

RecallSet = dict[str, list[str]]


def _clean_string_list(
    value: Any,
    *,
    expected_count: int,
) -> list[str]:
    """Return a clean string list with the required item count."""

    if not isinstance(value, (list, tuple)):
        return []

    cleaned = [_clean_text(item) for item in value]

    if len(cleaned) != expected_count or not all(cleaned):
        return []

    return cleaned


def _build_recall_set(
    questions: Any,
    anchors: Any,
) -> RecallSet | None:
    """Build one valid Version 3.1 recall set."""

    cleaned_questions = _clean_string_list(
        questions,
        expected_count=1,
    )

    cleaned_anchors = _clean_string_list(
        anchors,
        expected_count=5,
    )

    if not cleaned_questions or not cleaned_anchors:
        return None

    return {
        "questions": cleaned_questions,
        "anchors": cleaned_anchors,
    }


def _extract_scheduled_recall_sets(
    dataset: dict[str, Any],
) -> list[RecallSet]:
    """Extract scheduled previous-day recall sets."""

    raw_recall = dataset.get("recall_questions", [])

    if not isinstance(raw_recall, list):
        return []

    recall_sets: list[RecallSet] = []

    for entry in raw_recall:
        if not isinstance(entry, dict):
            continue

        recall_set = _build_recall_set(
            questions=entry.get("questions", []),
            anchors=entry.get("anchors", []),
        )

        if recall_set is not None:
            recall_sets.append(recall_set)

    return recall_sets


def _extract_current_recall_sets(
    publication_date: date,
) -> list[RecallSet]:
    """Extract current-day recall sets for first-day fallback."""

    selected_issues_path = find_selected_issues_path(
        publication_date
    )

    if selected_issues_path is None:
        return []

    selected_dataset = _read_json(selected_issues_path)

    issues = selected_dataset.get(
        "selected_issues",
        selected_dataset.get("issues", []),
    )

    if not isinstance(issues, list):
        return []

    recall_sets: list[RecallSet] = []

    for issue in issues:
        if not isinstance(issue, dict):
            continue

        recall_set = _build_recall_set(
            questions=issue.get("recall_questions", []),
            anchors=issue.get("anchors", []),
        )

        if recall_set is not None:
            recall_sets.append(recall_set)
            continue

        recall = issue.get("recall", {})
        youtube = issue.get("youtube", {})
        telegram = issue.get("telegram", {})

        if not isinstance(recall, dict):
            recall = {}

        if not isinstance(youtube, dict):
            youtube = {}

        if not isinstance(telegram, dict):
            telegram = {}

        repository_questions = recall.get(
            "questions",
            [],
        )

        repository_anchors = (
            recall.get("anchors", [])
            or youtube.get("anchors", [])
            or telegram.get("anchors", [])
            or issue.get("anchors", [])
        )

        recall_set = _build_recall_set(
            questions=repository_questions,
            anchors=repository_anchors,
        )

        if recall_set is not None:
            recall_sets.append(recall_set)

    return recall_sets


def resolve_recall_sets(
    dataset: dict[str, Any],
    publication_date: date,
) -> list[RecallSet]:
    """
    Resolve one question-plus-anchor set for every rendered issue.

    Priority:
    1. Scheduled previous-day recall sets.
    2. Current-day sets only when scheduled data is insufficient.
    """

    issue_count = len(dataset["issues"])

    recall_sets = _extract_scheduled_recall_sets(dataset)

    if len(recall_sets) < issue_count:
        current_recall_sets = _extract_current_recall_sets(
            publication_date
        )

        for recall_set in current_recall_sets:
            if len(recall_sets) >= issue_count:
                break

            recall_sets.append(recall_set)

    if len(recall_sets) < issue_count:
        raise PDFDatasetError(
            "There are not enough recall sets for "
            f"{issue_count} issue(s).\n"
            f"Available recall sets: {len(recall_sets)}\n"
            "Each issue requires exactly one recall question "
            "and five revision anchors."
        )

    return recall_sets[:issue_count]


# ============================================================
# ISSUE MAPPING
# ============================================================

def build_content_sections(
    issue: dict[str, Any],
) -> tuple[ContentSection, ...]:
    """Map Version 2.0 dataset fields to locked PDF headings."""

    return (
        ContentSection(
            heading="Current Context",
            text=_clean_text(
                issue["current_context"]
            ),
        ),
        ContentSection(
            heading="Why It Matters for UPSC",
            text=_clean_text(
                issue["why_it_matters_for_upsc"]
            ),
        ),
        ContentSection(
            heading="Core Concept",
            text=_clean_text(
                issue["core_concept"]
            ),
        ),
        ContentSection(
            heading="Challenges",
            text=_clean_text(
                issue["challenges"]
            ),
        ),
        ContentSection(
            heading="Way Forward",
            text=_clean_text(
                issue["way_forward"]
            ),
        ),
    )


# ============================================================
# ISSUE RENDERER
# ============================================================

def render_issue(
    pdf: canvas.Canvas,
    issue_layout: IssueLayout,
    issue: dict[str, Any],
    issue_number: int,
    recall_set: RecallSet,
) -> None:
    """Render one complete issue using existing components."""

    recall_questions = recall_set.get("questions", [])
    recall_anchors = recall_set.get("anchors", [])

    try:
        draw_issue_header(
            pdf=pdf,
            box=issue_layout.header,
            issue_number=issue_number,
            title=_clean_text(issue["title"]),
            gs_paper=_clean_text(issue["gs_paper"]),
            category=_clean_text(issue.get("category", "")),
            rating=_clean_text(issue.get("rating", "")),
        )

        draw_content_sections(
            pdf=pdf,
            box=issue_layout.content,
            sections=build_content_sections(issue),
        )

        draw_recall_questions(
            pdf=pdf,
            box=issue_layout.recall,
            questions=recall_questions,
            anchors=recall_anchors,
        )

        draw_quick_facts(
            pdf=pdf,
            box=issue_layout.quick_facts,
            facts=issue["quick_facts"],
        )

        draw_takeaway(
            pdf=pdf,
            box=issue_layout.takeaway,
            takeaway=_clean_text(issue["key_takeaway"]),
        )

    except ValueError as error:
        raise PDFContentOverflowError(
            f"Unable to render Issue {issue_number}: "
            f"{issue.get('title', 'Untitled Issue')}\n"
            f"{error}"
        ) from error


# ============================================================
# PAGE RENDERER
# ============================================================

def render_page(
    pdf: canvas.Canvas,
    issues_on_page: list[dict[str, Any]],
    recall_sets_on_page: list[RecallSet],
    first_issue_number: int,
    publication_date: date,
    page_number: int,
    total_pages: int,
) -> None:
    """Render one portrait page containing one or two issues."""

    page_layout = create_layout()

    draw_header(
        pdf=pdf,
        box=page_layout.header,
        date_text=_display_date(
            publication_date
        ),
    )

    draw_footer(
        pdf=pdf,
        box=page_layout.footer,
        document_code=_document_code(
            publication_date
        ),
        page_number=page_number,
        total_pages=total_pages,
    )

    issue_slots = (
        page_layout.issue1,
        page_layout.issue2,
    )

    for local_index, issue in enumerate(
        issues_on_page
    ):
        render_issue(
            pdf=pdf,
            issue_layout=issue_slots[local_index],
            issue=issue,
            issue_number=(
                first_issue_number
                + local_index
            ),
            recall_set=(
                recall_sets_on_page[
                    local_index
                ]
            ),
        )


# ============================================================
# PDF GENERATION
# ============================================================

def generate_final_pdf(
    publication_date: str | date | datetime,
    overwrite: bool = False,
    open_after_generation: bool = False,
) -> PDFResult:
    """Generate the complete final portrait PDF."""

    parsed_date = _parse_date(
        publication_date
    )

    dataset = load_pdf_dataset(
        parsed_date
    )

    issues = dataset["issues"]

    recall_sets = resolve_recall_sets(
        dataset=dataset,
        publication_date=parsed_date,
    )

    issue_count = len(issues)
    page_count = (
        issue_count + 1
    ) // 2

    final_pdf_path = get_final_pdf_path(
        parsed_date
    )

    if final_pdf_path.exists() and not overwrite:
        raise PDFAlreadyExistsError(
            "The final PDF already exists:\n"
            f"{final_pdf_path}\n"
            "Use --overwrite when intentionally rebuilding it."
        )

    final_pdf_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_pdf_path = (
        final_pdf_path.with_suffix(".pdf.tmp")
    )

    if temporary_pdf_path.exists():
        temporary_pdf_path.unlink()

    pdf = canvas.Canvas(
        str(temporary_pdf_path),
        pagesize=(
            PAGE_WIDTH,
            PAGE_HEIGHT,
        ),
        pageCompression=1,
    )

    pdf.setTitle(
        "Today's UPSC Issues"
    )

    pdf.setAuthor(
        "UPSC Issues by Kumar"
    )

    pdf.setSubject(
        f"Daily UPSC Issues — "
        f"{_display_date(parsed_date)}"
    )

    pdf.setCreator(
        "Today's UPSC Issues Version 3.1"
    )

    try:
        for page_index in range(page_count):
            start_index = page_index * 2
            end_index = start_index + 2

            issues_on_page = issues[
                start_index:end_index
            ]

            recall_sets_on_page = recall_sets[
                start_index:end_index
            ]

            render_page(
                pdf=pdf,
                issues_on_page=issues_on_page,
                recall_sets_on_page=recall_sets_on_page,
                first_issue_number=(
                    start_index + 1
                ),
                publication_date=parsed_date,
                page_number=(
                    page_index + 1
                ),
                total_pages=page_count,
            )

            pdf.showPage()

        pdf.save()

    except Exception:
        try:
            pdf.save()
        except Exception:
            pass

        if temporary_pdf_path.exists():
            temporary_pdf_path.unlink()

        raise

    if final_pdf_path.exists():
        final_pdf_path.unlink()

    temporary_pdf_path.replace(
        final_pdf_path
    )

    result = PDFResult(
        publication_date=_display_date(
            parsed_date
        ),
        pdf_path=final_pdf_path,
        issue_count=issue_count,
        page_count=page_count,
        document_code=_document_code(
            parsed_date
        ),
    )

    if open_after_generation:
        open_pdf(final_pdf_path)

    return result


# ============================================================
# OPEN PDF
# ============================================================

def open_pdf(pdf_path: Path) -> None:
    """Open the generated PDF using the operating system."""

    if not pdf_path.exists():
        raise PDFGeneratorError(
            f"Cannot open missing PDF:\n{pdf_path}"
        )

    try:
        if os.name == "nt":
            os.startfile(pdf_path)  # type: ignore[attr-defined]

        elif sys.platform == "darwin":
            os.system(
                f'open "{pdf_path}"'
            )

        else:
            os.system(
                f'xdg-open "{pdf_path}"'
            )

    except OSError as error:
        raise PDFGeneratorError(
            f"PDF generated, but could not be opened:\n"
            f"{pdf_path}\n{error}"
        ) from error


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate the final Today's UPSC Issues "
            "portrait PDF."
        )
    )

    parser.add_argument(
        "publication_date",
        nargs="?",
        default=date.today().isoformat(),
        help=(
            "Publication date. Examples: "
            "2026-07-19 or 19-07-26"
        ),
    )

    parser.add_argument(
        "--overwrite",
        "-o",
        action="store_true",
        help="Replace an existing final PDF.",
    )

    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_after_generation",
        help="Open the PDF after successful generation.",
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the final PDF generator."""

    parser = create_argument_parser()
    arguments = parser.parse_args()

    try:
        result = generate_final_pdf(
            publication_date=arguments.publication_date,
            overwrite=arguments.overwrite,
            open_after_generation=(
                arguments.open_after_generation
            ),
        )

        result.display()

    except PDFGeneratorError as error:
        print("=" * 64)
        print("TODAY'S UPSC ISSUES")
        print("FINAL PDF GENERATION ERROR")
        print("=" * 64)
        print(error)
        print("=" * 64)
        raise SystemExit(1) from error

    except KeyboardInterrupt:
        print()
        print("PDF generation was cancelled.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()