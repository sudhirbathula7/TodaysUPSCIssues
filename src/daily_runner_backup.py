"""
============================================================
TODAY'S UPSC ISSUES
DAILY PRODUCTION RUNNER
Version 2.0
Created by Sudhir
============================================================

PURPOSE

Runs the complete daily production workflow through one command.

PRODUCTION STAGES

1. Read and validate the selected daily issues.
2. Generate the permanent repository package.
3. Generate platform-ready publication outputs.
4. Generate the final portrait PDF.
5. Display the complete production summary.

DEFAULT INPUT FILE

Daily_Work/input/selected_issues.json

NORMAL COMMAND

python src/daily_runner.py 2026-07-19

REBUILD COMMAND

python src/daily_runner.py 2026-07-19 --overwrite

REBUILD AND OPEN PDF

python src/daily_runner.py 2026-07-19 --overwrite --open-pdf
============================================================
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT MODULES
# ============================================================

from src.output_generator import (  # noqa: E402
    OutputGeneratorError,
    OutputResult,
    generate_output_package,
)
from src.pdf_generator import (  # noqa: E402
    PDFGeneratorError,
    PDFResult,
    generate_final_pdf,
)
from src.repository_generator import (  # noqa: E402
    RepositoryError,
    RepositoryResult,
    generate_repository_package,
)


# ============================================================
# PROJECT PATHS
# ============================================================

DAILY_WORK_ROOT = PROJECT_ROOT / "Daily_Work"
INPUT_ROOT = DAILY_WORK_ROOT / "input"

DEFAULT_SELECTED_ISSUES_FILE = (
    INPUT_ROOT
    / "selected_issues.json"
)


# ============================================================
# EXCEPTIONS
# ============================================================

class DailyRunnerError(Exception):
    """Base exception for daily-runner errors."""


class DailyInputError(DailyRunnerError):
    """Raised when the selected issue input is invalid."""


# ============================================================
# FINAL RESULT
# ============================================================

@dataclass(frozen=True)
class DailyRunResult:
    """Combined result of the complete daily production run."""

    publication_date: str
    input_file: Path
    repository_result: RepositoryResult
    output_result: OutputResult
    pdf_result: PDFResult

    def display(self) -> None:
        """Display the final professional production summary."""

        print()
        print("=" * 68)
        print("TODAY'S UPSC ISSUES")
        print("VERSION 2.0 — DAILY PRODUCTION COMPLETED")
        print("=" * 68)

        print(
            f"Publication date : "
            f"{self.pdf_result.publication_date}"
        )

        print(
            f"Document code    : "
            f"{self.pdf_result.document_code}"
        )

        print(
            f"Input file       : "
            f"{self.input_file}"
        )

        print(
            f"Issues processed : "
            f"{self.repository_result.issue_count}"
        )

        print(
            f"Pages generated  : "
            f"{self.pdf_result.page_count}"
        )

        print("-" * 68)

        print("PRODUCTION STATUS")
        print("✓ Repository package generated")
        print("✓ Issue index updated")
        print("✓ Recall schedule updated")
        print("✓ Usage index updated")
        print("✓ PDF dataset prepared")
        print("✓ YouTube Shorts content prepared")
        print("✓ Telegram card content prepared")
        print("✓ Website content prepared")
        print("✓ Publication summary prepared")
        print("✓ Final portrait PDF generated")

        print("-" * 68)

        print("REPOSITORY")
        print(
            self.repository_result.daily_folder
        )

        print()
        print("PLATFORM OUTPUTS")
        print(
            self.output_result.output_folder
        )

        print()
        print("FINAL PDF")
        print(
            self.pdf_result.pdf_path
        )

        print("-" * 68)
        print("✓ DAILY EDITION READY FOR PUBLICATION")
        print("=" * 68)


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date(
    value: str | date | datetime,
) -> date:
    """Convert supported values into a date object."""

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

    raise DailyInputError(
        "Unsupported publication date.\n"
        "Use one of these formats:\n"
        "2026-07-19\n"
        "19-07-26\n"
        "19-07-2026\n"
        "19/07/2026\n"
        "19 July 2026"
    )


def _display_date(
    publication_date: date,
) -> str:
    """Return the locked DD-MM-YY display format."""

    return publication_date.strftime(
        "%d-%m-%y"
    )


# ============================================================
# JSON HELPERS
# ============================================================

def _read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file."""

    if not path.exists():
        raise DailyInputError(
            "Selected issue input file was not found:\n"
            f"{path}"
        )

    if not path.is_file():
        raise DailyInputError(
            "Selected issue input path is not a file:\n"
            f"{path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise DailyInputError(
            "Invalid JSON in selected issue input file:\n"
            f"{path}\n"
            f"Line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error


# ============================================================
# PATH HELPERS
# ============================================================

def _resolve_input_path(
    value: str | Path | None,
) -> Path:
    """Resolve the selected issue input path."""

    if value is None:
        return (
            DEFAULT_SELECTED_ISSUES_FILE
            .resolve()
        )

    path = Path(value).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def _resolve_source_path(
    value: str | Path,
    input_file: Path,
) -> Path:
    """
    Resolve an optional editorial source path.

    Relative paths are checked against:

    1. The selected-issues file folder.
    2. The project root.
    """

    source_path = Path(
        value
    ).expanduser()

    if source_path.is_absolute():
        return source_path.resolve()

    relative_to_input = (
        input_file.parent
        / source_path
    )

    if relative_to_input.exists():
        return relative_to_input.resolve()

    return (
        PROJECT_ROOT
        / source_path
    ).resolve()


# ============================================================
# DAILY INPUT LOADING
# ============================================================

def load_daily_input(
    input_file: str | Path | None = None,
) -> dict[str, Any]:
    """
    Load the selected daily issue input.

    Supported JSON structures:

    Structure 1:
    {
      "publication_date": "2026-07-19",
      "selected_issues": [...]
    }

    Structure 2:
    {
      "publication_date": "2026-07-19",
      "issues": [...]
    }

    Structure 3:
    [
      {...},
      {...}
    ]
    """

    resolved_path = _resolve_input_path(
        input_file
    )

    raw_data = _read_json(
        resolved_path
    )

    publication_date_value: str | None = None
    selected_issues: Any = None
    source_files: Any = []

    if isinstance(raw_data, list):
        selected_issues = raw_data

    elif isinstance(raw_data, dict):
        publication_date_value = (
            raw_data.get(
                "publication_date"
            )
        )

        selected_issues = (
            raw_data.get(
                "selected_issues"
            )
        )

        if selected_issues is None:
            selected_issues = (
                raw_data.get(
                    "issues"
                )
            )

        source_files = raw_data.get(
            "source_files",
            [],
        )

        if not source_files:
            source_files = raw_data.get(
                "source_editorials",
                [],
            )

    else:
        raise DailyInputError(
            "The selected issue input must contain "
            "either a JSON object or a JSON list."
        )

    if not isinstance(
        selected_issues,
        list,
    ):
        raise DailyInputError(
            "The input file must contain an issue list "
            'under either "selected_issues" or "issues".'
        )

    if not selected_issues:
        raise DailyInputError(
            "The selected issue list is empty."
        )

    if len(selected_issues) > 8:
        raise DailyInputError(
            "The daily input contains more than eight "
            "issues. The Version 2.0 maximum is eight."
        )

    for issue_number, issue in enumerate(
        selected_issues,
        start=1,
    ):
        if not isinstance(issue, dict):
            raise DailyInputError(
                f"Issue {issue_number} must be "
                "a JSON object."
            )

        title = (
            issue.get("title")
            or issue.get("issue_title")
            or issue.get("issue")
        )

        if not str(
            title or ""
        ).strip():
            raise DailyInputError(
                f"Issue {issue_number} does not "
                "contain a title."
            )

        quick_facts = issue.get(
            "quick_facts",
            [],
        )

        if not isinstance(
            quick_facts,
            list,
        ):
            raise DailyInputError(
                f"Issue {issue_number} Quick Facts "
                "must be a list."
            )

        if len(quick_facts) != 4:
            raise DailyInputError(
                f"Issue {issue_number} must contain "
                "exactly four Quick Facts."
            )

        recall_questions = issue.get(
            "recall_questions",
            [],
        )

        if not isinstance(
            recall_questions,
            list,
        ):
            raise DailyInputError(
                f"Issue {issue_number} recall questions "
                "must be a list."
            )

        if len(recall_questions) != 2:
            raise DailyInputError(
                f"Issue {issue_number} must contain "
                "exactly two Recall Questions."
            )

    if source_files is None:
        source_files = []

    if isinstance(
        source_files,
        (str, Path),
    ):
        source_files = [
            source_files
        ]

    if not isinstance(
        source_files,
        list,
    ):
        raise DailyInputError(
            '"source_files" must be a list '
            "of file paths."
        )

    resolved_source_files = [
        _resolve_source_path(
            value=source_file,
            input_file=resolved_path,
        )
        for source_file in source_files
    ]

    return {
        "input_file": resolved_path,
        "publication_date": (
            publication_date_value
        ),
        "selected_issues": (
            selected_issues
        ),
        "source_files": (
            resolved_source_files
        ),
    }


# ============================================================
# DATE RESOLUTION
# ============================================================

def resolve_publication_date(
    command_line_date: str | None,
    input_date: str | None,
) -> date:
    """
    Resolve the final publication date.

    Priority:

    1. Command-line date.
    2. Date inside selected_issues.json.
    3. Today's date.
    """

    if command_line_date:
        parsed_command_date = _parse_date(
            command_line_date
        )

        if input_date:
            parsed_input_date = _parse_date(
                input_date
            )

            if (
                parsed_command_date
                != parsed_input_date
            ):
                raise DailyInputError(
                    "Publication-date mismatch:\n"
                    f"Command line : "
                    f"{_display_date(parsed_command_date)}\n"
                    f"Input file   : "
                    f"{_display_date(parsed_input_date)}"
                )

        return parsed_command_date

    if input_date:
        return _parse_date(
            input_date
        )

    return date.today()


# ============================================================
# COMPLETE DAILY WORKFLOW
# ============================================================

def run_daily_production(
    publication_date: (
        str
        | date
        | datetime
        | None
    ) = None,
    input_file: str | Path | None = None,
    overwrite: bool = False,
    open_pdf: bool = False,
) -> DailyRunResult:
    """
    Run the complete Version 2.0 production workflow.

    Stages:

    1. Repository generation.
    2. Platform output generation.
    3. Final PDF generation.
    """

    daily_input = load_daily_input(
        input_file
    )

    if isinstance(
        publication_date,
        datetime,
    ):
        command_date = (
            publication_date
            .date()
            .isoformat()
        )

    elif isinstance(
        publication_date,
        date,
    ):
        command_date = (
            publication_date
            .isoformat()
        )

    else:
        command_date = publication_date

    parsed_date = resolve_publication_date(
        command_line_date=command_date,
        input_date=(
            daily_input[
                "publication_date"
            ]
        ),
    )

    display_date = _display_date(
        parsed_date
    )

    print("=" * 68)
    print("TODAY'S UPSC ISSUES")
    print("VERSION 2.0 — DAILY PRODUCTION")
    print("=" * 68)

    print(
        f"Publication date : "
        f"{display_date}"
    )

    print(
        f"Selected issues  : "
        f"{len(daily_input['selected_issues'])}"
    )

    print(
        f"Input file       : "
        f"{daily_input['input_file']}"
    )

    print(
        f"Source files     : "
        f"{len(daily_input['source_files'])}"
    )

    print(
        f"Overwrite mode   : "
        f"{'ON' if overwrite else 'OFF'}"
    )

    print("-" * 68)

    # --------------------------------------------------------
    # STAGE 1 — REPOSITORY
    # --------------------------------------------------------

    print("STAGE 1 / 3")
    print("REPOSITORY GENERATION")

    repository_result = (
        generate_repository_package(
            publication_date=parsed_date,
            selected_issues=(
                daily_input[
                    "selected_issues"
                ]
            ),
            source_files=(
                daily_input[
                    "source_files"
                ]
            ),
            overwrite_daily=overwrite,
        )
    )

    print(
        "✓ Repository package generated "
        f"for {repository_result.issue_count} "
        "issue(s)"
    )

    print("-" * 68)

    # --------------------------------------------------------
    # STAGE 2 — PLATFORM OUTPUTS
    # --------------------------------------------------------

    print("STAGE 2 / 3")
    print("PUBLICATION OUTPUT GENERATION")

    output_result = (
        generate_output_package(
            publication_date=parsed_date,
            overwrite=overwrite,
        )
    )

    print(
        "✓ Publication output package generated"
    )

    print(
        f"✓ YouTube Shorts prepared: "
        f"{output_result.youtube_short_count}"
    )

    print(
        f"✓ Telegram cards prepared: "
        f"{output_result.telegram_card_count}"
    )

    print("-" * 68)

    # --------------------------------------------------------
    # STAGE 3 — FINAL PDF
    # --------------------------------------------------------

    print("STAGE 3 / 3")
    print("FINAL PDF GENERATION")

    pdf_result = generate_final_pdf(
        publication_date=parsed_date,
        overwrite=overwrite,
        open_after_generation=open_pdf,
    )

    print(
        f"✓ Final PDF generated with "
        f"{pdf_result.page_count} page(s)"
    )

    print("-" * 68)

    return DailyRunResult(
        publication_date=display_date,
        input_file=(
            daily_input["input_file"]
        ),
        repository_result=(
            repository_result
        ),
        output_result=(
            output_result
        ),
        pdf_result=pdf_result,
    )


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create the daily-runner command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate the complete Today's UPSC Issues "
            "Version 2.0 daily edition."
        )
    )

    parser.add_argument(
        "publication_date",
        nargs="?",
        help=(
            "Publication date. Examples: "
            "2026-07-19 or 19-07-26. "
            "Optional when the input file contains "
            "publication_date."
        ),
    )

    parser.add_argument(
        "--input",
        "-i",
        dest="input_file",
        default=None,
        help=(
            "Selected issue JSON file. "
            "Default: "
            "Daily_Work/input/selected_issues.json"
        ),
    )

    parser.add_argument(
        "--overwrite",
        "-o",
        action="store_true",
        help=(
            "Replace existing repository, output "
            "and PDF files for the selected date."
        ),
    )

    parser.add_argument(
        "--open-pdf",
        action="store_true",
        help=(
            "Open the final PDF after successful "
            "daily production."
        ),
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the complete daily production workflow."""

    parser = create_argument_parser()
    arguments = parser.parse_args()

    try:
        result = run_daily_production(
            publication_date=(
                arguments.publication_date
            ),
            input_file=(
                arguments.input_file
            ),
            overwrite=(
                arguments.overwrite
            ),
            open_pdf=(
                arguments.open_pdf
            ),
        )

        result.display()

    except (
        DailyRunnerError,
        RepositoryError,
        OutputGeneratorError,
        PDFGeneratorError,
    ) as error:
        print()
        print("=" * 68)
        print("TODAY'S UPSC ISSUES")
        print("DAILY PRODUCTION ERROR")
        print("=" * 68)
        print(error)
        print("=" * 68)

        raise SystemExit(1) from error

    except KeyboardInterrupt:
        print()
        print("Daily production was cancelled.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()