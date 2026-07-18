"""
============================================================
Today's UPSC Issues
One-Click Production Runner
Version : 1.0
Created by Sudhir
============================================================

Daily workflow:

1. Read input/todays_issues.txt
2. Validate the dataset
3. Parse it into internal data models
4. Generate the final two-page PDF
5. Archive the input and PDF
6. Open the final PDF automatically
============================================================
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


# ==========================================================
# PROJECT PATH SETUP
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# Import project modules only after PROJECT_ROOT is available.
from src.parser import (  # noqa: E402
    DatasetParsingError,
    parse_validated_dataset,
)
from src.pdf_generator import (  # noqa: E402
    generate_pdf,
    open_generated_pdf,
)
from src.reader import (  # noqa: E402
    get_default_input_file,
    read_today_dataset,
)
from src.validator import (  # noqa: E402
    print_validation_report,
    validate_dataset,
)


# ==========================================================
# PROJECT DIRECTORIES
# ==========================================================

OUTPUT_DIR = PROJECT_ROOT / "output"
REPOSITORY_DIR = PROJECT_ROOT / "Repository"


# ==========================================================
# ARCHIVE HELPERS
# ==========================================================

def build_archive_directory(book) -> Path:
    """
    Build the dated archive folder.

    Example:
        Repository/2026/July/14
    """

    return (
        REPOSITORY_DIR
        / book.publication_date.strftime("%Y")
        / book.publication_date.strftime("%B")
        / book.publication_date.strftime("%d")
    )


def copy_with_overwrite(
    source: Path,
    destination: Path,
) -> Path:
    """
    Copy a file to the destination.

    Existing archive copies are replaced deliberately because
    rerunning the same edition should refresh that day's files.
    """

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )

    return destination


def archive_production_files(
    book,
    input_file: Path,
    generated_pdf: Path,
) -> tuple[Path, Path]:
    """
    Archive the daily input and generated PDF.
    """

    archive_dir = build_archive_directory(
        book
    )

    archive_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    archived_input = copy_with_overwrite(
        source=input_file,
        destination=(
            archive_dir
            / "todays_issues.txt"
        ),
    )

    archived_pdf = copy_with_overwrite(
        source=generated_pdf,
        destination=(
            archive_dir
            / generated_pdf.name
        ),
    )

    return (
        archived_input,
        archived_pdf,
    )


# ==========================================================
# CONSOLE DISPLAY
# ==========================================================

def print_banner() -> None:
    """
    Print the production-system banner.
    """

    print("=" * 68)
    print("TODAY'S UPSC ISSUES")
    print("ONE-CLICK DAILY PRODUCTION SYSTEM")
    print("Version 1.0 | Created by Sudhir")
    print("=" * 68)


def print_success_report(
    generated_pdf: Path,
    archived_input: Path,
    archived_pdf: Path,
) -> None:
    """
    Print the final production summary.
    """

    print()
    print("=" * 68)
    print("DAILY PRODUCTION COMPLETED SUCCESSFULLY")
    print("=" * 68)

    print("Final PDF")
    print(generated_pdf.resolve())

    print("-" * 68)

    print("Archived Input")
    print(archived_input.resolve())

    print("-" * 68)

    print("Archived PDF")
    print(archived_pdf.resolve())

    print("=" * 68)
    print("The final PDF will now open automatically.")
    print("=" * 68)


# ==========================================================
# PRODUCTION WORKFLOW
# ==========================================================

def run_production() -> Path:
    """
    Execute the complete daily production workflow.
    """

    print_banner()

    input_file = Path(
        get_default_input_file()
    )

    print()
    print("STEP 1: Reading daily dataset")
    print("-" * 68)

    raw_dataset = read_today_dataset()

    print(
        f"Input file: {input_file.resolve()}"
    )

    print()
    print("STEP 2: Validating dataset")
    print("-" * 68)

    validation_result = validate_dataset(
        raw_dataset
    )

    print_validation_report(
        validation_result
    )

    if not validation_result["is_valid"]:
        raise ValueError(
            "Production stopped because dataset validation failed."
        )

    print()
    print("STEP 3: Parsing dataset")
    print("-" * 68)

    book = parse_validated_dataset(
        raw_dataset
    )

    print(
        f"Date   : {book.formatted_date}"
    )

    print(
        f"Issues : {book.issue_count}"
    )

    print()
    print("STEP 4: Generating final PDF")
    print("-" * 68)

    generated_pdf = generate_pdf(
        book
    )

    print(
        f"Generated: {generated_pdf.resolve()}"
    )

    print()
    print("STEP 5: Archiving production files")
    print("-" * 68)

    (
        archived_input,
        archived_pdf,
    ) = archive_production_files(
        book=book,
        input_file=input_file,
        generated_pdf=generated_pdf,
    )

    print_success_report(
        generated_pdf=generated_pdf,
        archived_input=archived_input,
        archived_pdf=archived_pdf,
    )

    open_generated_pdf(
        generated_pdf
    )

    return generated_pdf


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    """
    Run production with a clear failure report.
    """

    try:
        run_production()

    except (
        FileNotFoundError,
        ValueError,
        TypeError,
        RuntimeError,
        DatasetParsingError,
    ) as error:
        print()
        print("=" * 68)
        print("DAILY PRODUCTION FAILED")
        print("=" * 68)
        print(
            f"{type(error).__name__}: {error}"
        )
        print("=" * 68)
        raise


if __name__ == "__main__":
    main()