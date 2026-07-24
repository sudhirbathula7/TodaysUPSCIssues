"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.1 DAILY LAUNCHER
Created by Sudhir
============================================================

PURPOSE

Provides a clean daily production entry point.

DAILY WORKFLOW

1. Save the final ChatGPT JSON at:

       input/DAILY_INPUT.json

2. Run:

       python run_daily.py

The launcher automatically:

1. Reads the input JSON.
2. Extracts the production date.
3. Creates the internal production session.
4. Copies the canonical JSON into the session.
5. Runs the existing Version 3.1 production pipeline.

The Version 3.1 production engine remains unchanged.
============================================================
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from src.publishing.published_collector import (  # noqa: E402
    PublishedCollectorError,
    collect_published_files,
)

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ==========================================================
# PROJECT MODULES
# ==========================================================

from src.production.controller import (  # noqa: E402
    ProductionController,
    ProductionControllerError,
)
from src.production.paths import (  # noqa: E402
    ProductionPaths,
)
from src.production.session_manager import (  # noqa: E402
    ProductionSessionManager,
)


# ==========================================================
# USER INPUT
# ==========================================================

INPUT_ROOT = PROJECT_ROOT / "input"

DAILY_INPUT_FILE = (
    INPUT_ROOT
    / "DAILY_INPUT.json"
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class DailyLauncherError(RuntimeError):
    """Raised when Version 3.1 daily production cannot start."""


# ==========================================================
# DISPLAY HELPERS
# ==========================================================

def print_heading(
    title: str,
) -> None:
    """Print a standard launcher heading."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print(title)
    print("=" * 72)


def print_success(
    message: str,
) -> None:
    """Print a success message."""

    print(f"✓ {message}")


# ==========================================================
# INPUT LOADING
# ==========================================================

def load_daily_input() -> dict[str, Any]:
    """
    Load input/DAILY_INPUT.json.

    UTF-8 with or without a byte-order mark is accepted.
    """

    if not DAILY_INPUT_FILE.exists():
        raise DailyLauncherError(
            "Daily input file was not found:\n"
            f"{DAILY_INPUT_FILE}\n\n"
            "Copy today's final ChatGPT JSON into this file "
            "before running production."
        )

    if not DAILY_INPUT_FILE.is_file():
        raise DailyLauncherError(
            "The daily input path is not a file:\n"
            f"{DAILY_INPUT_FILE}"
        )

    try:
        content = DAILY_INPUT_FILE.read_text(
            encoding="utf-8-sig",
        )
    except OSError as error:
        raise DailyLauncherError(
            "The daily input file could not be read:\n"
            f"{DAILY_INPUT_FILE}\n"
            f"{error}"
        ) from error

    if not content.strip():
        raise DailyLauncherError(
            "The daily input file is empty:\n"
            f"{DAILY_INPUT_FILE}"
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise DailyLauncherError(
            "input/DAILY_INPUT.json contains invalid JSON.\n"
            f"Line   : {error.lineno}\n"
            f"Column : {error.colno}\n"
            f"Reason : {error.msg}"
        ) from error

    if not isinstance(data, dict):
        raise DailyLauncherError(
            "The daily input must contain one JSON object."
        )

    return data


# ==========================================================
# DATE EXTRACTION
# ==========================================================

def extract_production_date(
    data: dict[str, Any],
) -> str:
    """
    Extract production.production_date.

    DAILY_INPUT.json uses DD-MM-YYYY.
    The internal production controller uses YYYY-MM-DD.
    """

    production = data.get("production")

    if not isinstance(production, dict):
        raise DailyLauncherError(
            "The JSON does not contain a valid 'production' object."
        )

    production_date = str(
        production.get("production_date", "")
    ).strip()

    if not production_date:
        raise DailyLauncherError(
            "The JSON does not contain 'production.production_date'."
        )

    try:
        parsed_date = datetime.strptime(
            production_date,
            "%d-%m-%Y",
        ).date()
    except ValueError as error:
        raise DailyLauncherError(
            "production.production_date must use DD-MM-YYYY format.\n"
            f"Received: {production_date!r}"
        ) from error

    return parsed_date.isoformat()


# ==========================================================
# BASIC INPUT CHECKS
# ==========================================================

def validate_basic_input(
    data: dict[str, Any],
    production_date: str,
) -> None:
    """
    Perform launcher-level checks before Version 3.1 validation.

    Full validation remains the responsibility of
    ProductionValidator.
    """

    production = data.get("production")

    if not isinstance(production, dict):
        raise DailyLauncherError(
            "The JSON field 'production' must contain an object."
        )

    issues = data.get("issues")

    if not isinstance(issues, list):
        raise DailyLauncherError(
            "The JSON field 'issues' must contain a list."
        )

    if not issues:
        raise DailyLauncherError(
            "The JSON does not contain any selected issues."
        )

    declared_issue_count = production.get(
        "total_issues"
    )

    if declared_issue_count != len(issues):
        raise DailyLauncherError(
            "The production total_issues value does not match "
            "the number of issues in the JSON.\n"
            f"Declared : {declared_issue_count}\n"
            f"Actual   : {len(issues)}"
        )

    expected_schema_date = (
        production_date[8:10]
        + "-"
        + production_date[5:7]
        + "-"
        + production_date[0:4]
    )

    schema_date = str(
        production.get(
            "production_date",
            "",
        )
    ).strip()

    if schema_date != expected_schema_date:
        raise DailyLauncherError(
            "The production date inside DAILY_INPUT.json does "
            "not match the requested production date.\n"
            f"Expected : {expected_schema_date}\n"
            f"Received : {schema_date or 'missing'}"
        )

    expected_edition_code = (
        "TUI-"
        + production_date[2:4]
        + production_date[5:7]
        + production_date[8:10]
    )

    edition_code = str(
        production.get(
            "edition_code",
            "",
        )
    ).strip()

    if edition_code != expected_edition_code:
        raise DailyLauncherError(
            "The edition code does not match the "
            "production date.\n"
            f"Expected : {expected_edition_code}\n"
            f"Received : {edition_code or 'missing'}"
        )

    issue_numbers: list[int] = []

    for index, issue in enumerate(
        issues,
        start=1,
    ):
        if not isinstance(issue, dict):
            raise DailyLauncherError(
                f"Issue {index} must be a JSON object."
            )

        metadata = issue.get("metadata")

        if not isinstance(metadata, dict):
            raise DailyLauncherError(
                f"Issue {index} must contain a metadata object."
            )

        issue_number = metadata.get(
            "issue_number"
        )

        if (
            not isinstance(issue_number, int)
            or isinstance(issue_number, bool)
        ):
            raise DailyLauncherError(
                f"Issue {index} has an invalid metadata.issue_number."
            )

        issue_numbers.append(issue_number)

    expected_numbers = list(
        range(1, len(issues) + 1)
    )

    if sorted(issue_numbers) != expected_numbers:
        raise DailyLauncherError(
            "Issue numbers must be sequential from 1.\n"
            f"Expected : {expected_numbers}\n"
            f"Received : {sorted(issue_numbers)}"
        )

# ==========================================================
# SESSION PREPARATION
# ==========================================================

def prepare_internal_session(
    data: dict[str, Any],
    production_date: str,
) -> ProductionPaths:
    """
    Create the internal Version 3.1 session when required and
    copy the daily input into its canonical location.
    """

    paths = ProductionPaths.for_date(
        production_date
    )

    manager = ProductionSessionManager(
        production_date
    )

    if not manager.exists:
        manager.create_session(
            overwrite=True,
            copy_editorials=False,
        )

        print_success(
            "Internal production session created"
        )
    else:
        paths.create_directories()

        print_success(
            "Existing production session will be rebuilt"
        )

    paths.canonical_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    canonical_text = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )

    try:
        paths.generated_content_file.write_text(
            canonical_text + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        raise DailyLauncherError(
            "The canonical production file could not be written:\n"
            f"{paths.generated_content_file}\n"
            f"{error}"
        ) from error

    print_success(
        "Daily JSON copied to the canonical production session"
    )

    return paths


# ==========================================================
# PRODUCTION
# ==========================================================

def run_production(
    production_date: str,
) -> None:
    """
    Run all issues contained in the daily JSON through the
    existing Version 3.1 production controller.
    """

    controller = ProductionController(
        production_date
    )

    controller.build(
        issue_numbers=None,
        overwrite=True,
        open_pdf=True,
    )


# ==========================================================
# MAIN
# ==========================================================

def main() -> int:
    """Run Version 3.1 daily production."""

    print_heading(
        "VERSION 3.1 — ONE-FILE DAILY PRODUCTION"
    )

    print(
        f"Daily input:\n"
        f"{DAILY_INPUT_FILE}"
    )
    print("-" * 72)

    try:
        data = load_daily_input()

        print_success(
            "Daily input JSON loaded"
        )

        production_date = extract_production_date(
            data
        )

        print_success(
            f"Production date detected: {production_date}"
        )

        validate_basic_input(
            data=data,
            production_date=production_date,
        )

        print_success(
            "Basic launcher checks passed"
        )

        paths = prepare_internal_session(
            data=data,
            production_date=production_date,
        )

        print("-" * 72)
        print(
            "Starting the existing Version 3.1 "
            "production engine..."
        )
        print("-" * 72)

        run_production(
        production_date
        )

        print("-" * 72)
        print(
        "Collecting publication-ready files..."
        )
        print("-" * 72)

        published_result = collect_published_files(
        production_date=production_date,
        overwrite=True,
        )

        print_success(
         "Published folder created"
                )

        for published_file in (
          published_result.created_files
        ):
         print(
        f"  - {published_file.name}"
    )

        print()
        print_heading(
    "VERSION 3.1 DAILY PRODUCTION COMPLETED"
)

        print(
            f"Date       : {production_date}"
        )
        print(
            f"Canonical  : "
            f"{paths.generated_content_file}"
        )
        print(
            f"Repository : "
            f"{paths.repository_daily_dir}"
        )
        print(
            f"Published  : "
            f"{published_result.published_folder}"
        )

        print("=" * 72)

        return 0

    except (
        DailyLauncherError,
        ProductionControllerError,
        PublishedCollectorError,
        FileNotFoundError,
        FileExistsError,
        ValueError,
        OSError,
    ) as error:
        print()
        print_heading(
            "VERSION 3.1 DAILY PRODUCTION FAILED"
        )
        print(error)
        print("=" * 72)

        return 1

    except KeyboardInterrupt:
        print()
        print(
            "Daily production was interrupted by the user."
        )

        return 130


if __name__ == "__main__":
    raise SystemExit(
        main()
    )