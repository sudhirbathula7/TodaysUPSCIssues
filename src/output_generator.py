"""
============================================================
TODAY'S UPSC ISSUES
OUTPUT GENERATOR
Version 2.0
Created by Sudhir
============================================================

PURPOSE

Reads the dated repository package and prepares all daily
publication outputs through one coordinated process.

The Output Generator:

1. Loads the repository package for a selected date.
2. Validates all required repository files.
3. Creates a dated publication-output folder.
4. Exports the PDF dataset.
5. Exports YouTube Shorts scripts and anchors.
6. Exports Telegram card content.
7. Exports the website heading.
8. Exports the recall schedule.
9. Creates human-readable TXT files for daily use.
10. Creates a final output manifest.

This module does not yet draw the final PDF or Telegram images.
Those specialised generators will be connected later.
============================================================
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from copy import deepcopy
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
# PROJECT PATHS
# ============================================================

REPOSITORY_ROOT = PROJECT_ROOT / "Repository"
DAILY_REPOSITORY_ROOT = REPOSITORY_ROOT / "daily"

OUTPUT_ROOT = PROJECT_ROOT / "output"
DAILY_OUTPUT_ROOT = OUTPUT_ROOT / "daily"


# ============================================================
# REPOSITORY FILE NAMES
# ============================================================

SELECTED_ISSUES_FILE = "selected_issues.json"
PDF_DATASET_FILE = "pdf_dataset.json"
YOUTUBE_SHORTS_FILE = "youtube_shorts.json"
TELEGRAM_CARDS_FILE = "telegram_cards.json"
WEBSITE_CONTENT_FILE = "website_content.json"
RECALL_SCHEDULE_FILE = "recall_schedule.json"
REPOSITORY_MANIFEST_FILE = "manifest.json"


# ============================================================
# OUTPUT FILE NAMES
# ============================================================

OUTPUT_PDF_DATASET_FILE = "pdf_dataset.json"
OUTPUT_YOUTUBE_FILE = "youtube_shorts.json"
OUTPUT_TELEGRAM_FILE = "telegram_cards.json"
OUTPUT_WEBSITE_FILE = "website_content.json"
OUTPUT_RECALL_FILE = "recall_schedule.json"

YOUTUBE_SCRIPT_TEXT_FILE = "youtube_shorts.txt"
TELEGRAM_TEXT_FILE = "telegram_cards.txt"
WEBSITE_TEXT_FILE = "website_heading.txt"
RECALL_TEXT_FILE = "recall_schedule.txt"
PUBLICATION_SUMMARY_FILE = "publication_summary.txt"
OUTPUT_MANIFEST_FILE = "output_manifest.json"


# ============================================================
# EXCEPTIONS
# ============================================================

class OutputGeneratorError(Exception):
    """Base exception for output-generator errors."""


class OutputValidationError(OutputGeneratorError):
    """Raised when repository data is missing or invalid."""


class OutputPackageExistsError(OutputGeneratorError):
    """Raised when an output package already exists."""


# ============================================================
# RESULT DATA CLASS
# ============================================================

@dataclass(frozen=True)
class OutputResult:
    """Summary returned after the output package is created."""

    publication_date: str
    output_folder: Path
    issue_count: int
    youtube_short_count: int
    telegram_card_count: int
    created_files: tuple[Path, ...]

    def display(self) -> None:
        """Print a readable completion summary."""

        print("=" * 60)
        print("TODAY'S UPSC ISSUES")
        print("OUTPUT GENERATOR")
        print("=" * 60)
        print(f"Publication date : {self.publication_date}")
        print(f"Issues prepared  : {self.issue_count}")
        print(f"YouTube Shorts   : {self.youtube_short_count}")
        print(f"Telegram cards   : {self.telegram_card_count}")
        print(f"Output folder    : {self.output_folder}")
        print("-" * 60)

        for path in self.created_files:
            print(f"✓ {path.name}")

        print("-" * 60)
        print("✓ Daily output package generated successfully")
        print("=" * 60)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _normalise_text(value: Any) -> str:
    """Return clean single-spaced text."""

    if value is None:
        return ""

    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def _normalise_multiline_text(value: Any) -> str:
    """Clean text while preserving useful line breaks."""

    if value is None:
        return ""

    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    lines: list[str] = []

    for line in text.split("\n"):
        cleaned = re.sub(r"[ \t]+", " ", line).strip()

        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def _parse_date(value: str | date | datetime) -> date:
    """Convert supported date values into a date object."""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    cleaned = _normalise_text(value)

    supported_formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for format_string in supported_formats:
        try:
            return datetime.strptime(cleaned, format_string).date()
        except ValueError:
            continue

    raise OutputValidationError(
        "Unsupported publication date. "
        "Use YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY or a written date."
    )


def _timestamp() -> str:
    """Return a timezone-aware timestamp."""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> Any:
    """Read and validate a JSON file."""

    if not path.exists():
        raise OutputValidationError(
            f"Required repository file is missing:\n{path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise OutputValidationError(
            f"Invalid JSON file:\n{path}\n{error}"
        ) from error


def _write_json(path: Path, data: Any) -> None:
    """Write JSON safely using a temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(path)


def _write_text(path: Path, content: str) -> None:
    """Write a UTF-8 text file safely."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        file.write(content.rstrip())
        file.write("\n")

    temporary_path.replace(path)


def _copy_json_file(source: Path, destination: Path) -> None:
    """Copy an existing JSON file while preserving its content."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _relative_path(path: Path) -> str:
    """Return a project-relative path where possible."""

    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


# ============================================================
# REPOSITORY PACKAGE LOADING
# ============================================================

def get_repository_folder(
    publication_date: str | date | datetime,
) -> Path:
    """Return the dated repository folder using DD-MM-YY."""

    parsed_date = _parse_date(publication_date)
    return DAILY_REPOSITORY_ROOT / parsed_date.strftime("%d-%m-%y")


def get_output_folder(
    publication_date: str | date | datetime,
) -> Path:
    """Return the dated daily output folder using DD-MM-YY."""

    parsed_date = _parse_date(publication_date)
    return DAILY_OUTPUT_ROOT / parsed_date.strftime("%d-%m-%y")


def load_repository_package(
    publication_date: str | date | datetime,
) -> dict[str, Any]:
    """Load all required daily repository datasets."""

    parsed_date = _parse_date(publication_date)
    repository_folder = get_repository_folder(parsed_date)

    if not repository_folder.exists():
        raise OutputValidationError(
            "Repository package not found for "
            f"{parsed_date.isoformat()}:\n{repository_folder}"
        )

    paths = {
        "selected_issues": repository_folder / SELECTED_ISSUES_FILE,
        "pdf_dataset": repository_folder / PDF_DATASET_FILE,
        "youtube_shorts": repository_folder / YOUTUBE_SHORTS_FILE,
        "telegram_cards": repository_folder / TELEGRAM_CARDS_FILE,
        "website_content": repository_folder / WEBSITE_CONTENT_FILE,
        "recall_schedule": repository_folder / RECALL_SCHEDULE_FILE,
        "repository_manifest": repository_folder / REPOSITORY_MANIFEST_FILE,
    }

    package = {
        "publication_date": parsed_date.isoformat(),
        "repository_folder": repository_folder,
        "paths": paths,
    }

    for key, path in paths.items():
        package[key] = _read_json(path)

    validate_repository_package(package)

    return package


# ============================================================
# VALIDATION
# ============================================================

def validate_repository_package(package: dict[str, Any]) -> None:
    """Validate consistency across the repository files."""

    publication_date = _parse_date(
    package["publication_date"]
     ).strftime("%d-%m-%y")

    datasets = (
        "selected_issues",
        "pdf_dataset",
        "youtube_shorts",
        "telegram_cards",
        "website_content",
        "recall_schedule",
        "repository_manifest",
    )

    for dataset_name in datasets:
        dataset = package.get(dataset_name)

        if not isinstance(dataset, dict):
            raise OutputValidationError(
                f"{dataset_name} must contain a JSON object."
            )

        dataset_date = dataset.get("publication_date")

        if dataset_date and dataset_date != publication_date:
            raise OutputValidationError(
                f"Publication-date mismatch in {dataset_name}: "
                f"{dataset_date} instead of {publication_date}."
            )

    selected_issues = package["selected_issues"].get("issues", [])

    if not isinstance(selected_issues, list) or not selected_issues:
        raise OutputValidationError(
            "selected_issues.json does not contain any issues."
        )

    issue_count = package["selected_issues"].get(
        "issue_count",
        len(selected_issues),
    )

    if issue_count != len(selected_issues):
        raise OutputValidationError(
            "Issue count does not match the selected issue list."
        )

    selected_issue_ids = [
        issue.get("issue_id")
        for issue in selected_issues
    ]

    if any(not issue_id for issue_id in selected_issue_ids):
        raise OutputValidationError(
            "One or more selected issues do not contain an issue ID."
        )

    if len(selected_issue_ids) != len(set(selected_issue_ids)):
        raise OutputValidationError(
            "Duplicate issue IDs found in selected_issues.json."
        )

    _validate_platform_issue_ids(
        expected_ids=selected_issue_ids,
        records=package["pdf_dataset"].get("issues", []),
        dataset_name="pdf_dataset.json",
    )

    _validate_platform_issue_ids(
        expected_ids=selected_issue_ids,
        records=package["youtube_shorts"].get("shorts", []),
        dataset_name="youtube_shorts.json",
    )

    _validate_platform_issue_ids(
        expected_ids=selected_issue_ids,
        records=package["telegram_cards"].get("cards", []),
        dataset_name="telegram_cards.json",
    )

    _validate_platform_issue_ids(
        expected_ids=selected_issue_ids,
        records=package["website_content"].get("issues", []),
        dataset_name="website_content.json",
    )

    manifest_ids = package["repository_manifest"].get("issue_ids", [])

    if manifest_ids and manifest_ids != selected_issue_ids:
        raise OutputValidationError(
            "Issue IDs in manifest.json do not match selected_issues.json."
        )


def _validate_platform_issue_ids(
    expected_ids: list[str],
    records: Any,
    dataset_name: str,
) -> None:
    """Check that a platform dataset contains all selected issues."""

    if not isinstance(records, list):
        raise OutputValidationError(
            f"{dataset_name} must contain a list of issue records."
        )

    actual_ids = [
        record.get("issue_id")
        for record in records
        if isinstance(record, dict)
    ]

    if actual_ids != expected_ids:
        raise OutputValidationError(
            f"Issue order or IDs in {dataset_name} do not match "
            "selected_issues.json."
        )


# ============================================================
# HUMAN-READABLE OUTPUT BUILDERS
# ============================================================

def build_youtube_text(dataset: dict[str, Any]) -> str:
    """Create the daily YouTube Shorts working document."""

    publication_date = dataset.get("publication_date", "")
    shorts = dataset.get("shorts", [])

    lines = [
        "=" * 60,
        "TODAY'S UPSC ISSUES",
        "YOUTUBE SHORTS",
        f"DATE: {publication_date}",
        "=" * 60,
        "",
    ]

    for number, short in enumerate(shorts, start=1):
        title = _normalise_text(short.get("title"))
        issue_id = _normalise_text(short.get("issue_id"))
        script = _normalise_multiline_text(short.get("script"))
        anchors = short.get("anchors", [])
        recall_questions = short.get(
            "recall_questions_explained",
            [],
        )

        lines.extend(
            [
                f"SHORT {number}",
                f"ISSUE ID: {issue_id}",
                f"TITLE: {title}",
                "",
                "SCRIPT:",
                script or "[Script not available]",
                "",
                "VISUAL ANCHORS:",
            ]
        )

        if anchors:
            for anchor_number, anchor in enumerate(anchors, start=1):
                lines.append(
                    f"{anchor_number}. {_normalise_text(anchor)}"
                )
        else:
            lines.append("[Anchors not available]")

        lines.extend(
            [
                "",
                "RECALL QUESTIONS EXPLAINED:",
            ]
        )

        if recall_questions:
            for question_number, question in enumerate(
                recall_questions,
                start=1,
            ):
                lines.append(
                    f"{question_number}. {_normalise_text(question)}"
                )
        else:
            lines.append("[Recall questions not available]")

        lines.extend(
            [
                "",
                "-" * 60,
                "",
            ]
        )

    return "\n".join(lines)


def build_telegram_text(dataset: dict[str, Any]) -> str:
    """Create the Telegram card working document."""

    publication_date = dataset.get("publication_date", "")
    cards = dataset.get("cards", [])

    lines = [
        "=" * 60,
        "TODAY'S UPSC ISSUES",
        "TELEGRAM CARDS",
        f"DATE: {publication_date}",
        "=" * 60,
        "",
    ]

    for number, card in enumerate(cards, start=1):
        title = _normalise_text(card.get("title"))
        issue_id = _normalise_text(card.get("issue_id"))
        heading = _normalise_text(card.get("card_heading"))
        questions = card.get("recall_questions", [])
        anchors = card.get("anchors", [])
        caption = _normalise_multiline_text(card.get("caption"))

        lines.extend(
            [
                f"CARD {number}",
                f"ISSUE ID: {issue_id}",
                f"ISSUE: {title}",
                f"CARD HEADING: {heading}",
                "",
                "RECALL QUESTIONS:",
            ]
        )

        if questions:
            for question_number, question in enumerate(
                questions,
                start=1,
            ):
                lines.append(
                    f"{question_number}. {_normalise_text(question)}"
                )
        else:
            lines.append("[Recall questions not available]")

        lines.extend(
            [
                "",
                "CARD ANCHORS:",
            ]
        )

        if anchors:
            for anchor_number, anchor in enumerate(anchors, start=1):
                lines.append(
                    f"{anchor_number}. {_normalise_text(anchor)}"
                )
        else:
            lines.append("[Anchors not available]")

        lines.extend(
            [
                "",
                "CAPTION:",
                caption or "[Caption not available]",
                "",
                "-" * 60,
                "",
            ]
        )

    return "\n".join(lines)


def build_website_text(dataset: dict[str, Any]) -> str:
    """Create the website publishing note."""

    publication_date = dataset.get("publication_date", "")
    daily_heading = _normalise_multiline_text(
        dataset.get("daily_heading")
    )
    issues = dataset.get("issues", [])

    lines = [
        "=" * 60,
        "TODAY'S UPSC ISSUES",
        "WEBSITE CONTENT",
        f"DATE: {publication_date}",
        "=" * 60,
        "",
        "DAILY WEBSITE HEADING:",
        daily_heading or "[Daily heading not available]",
        "",
        "ISSUE HEADINGS:",
    ]

    for number, issue in enumerate(issues, start=1):
        lines.extend(
            [
                "",
                f"{number}. {_normalise_text(issue.get('title'))}",
                _normalise_multiline_text(issue.get("heading"))
                or "[Heading not available]",
            ]
        )

    lines.extend(
        [
            "",
            "PDF ACTION:",
            "Upload the final daily PDF to the website viewer.",
            "",
        ]
    )

    return "\n".join(lines)


def build_recall_text(dataset: dict[str, Any]) -> str:
    """Create the three-day recall working document."""

    publication_date = dataset.get("publication_date", "")

    lines = [
        "=" * 60,
        "TODAY'S UPSC ISSUES",
        "RECALL SCHEDULE",
        f"DATE: {publication_date}",
        "=" * 60,
        "",
    ]

    sections = (
        ("PREVIOUS DAY", dataset.get("previous_day", {})),
        ("PRESENT DAY", dataset.get("present_day", {})),
        ("NEXT DAY", dataset.get("next_day", {})),
    )

    for section_title, section in sections:
        lines.extend(
            [
                section_title,
                f"DATE: {_normalise_text(section.get('date'))}",
                f"PURPOSE: {_normalise_text(section.get('purpose'))}",
                "",
            ]
        )

        questions = section.get("questions", [])

        if not questions:
            lines.append("[No recall questions available]")
        else:
            for issue_number, issue in enumerate(
                questions,
                start=1,
            ):
                lines.append(
                    f"{issue_number}. "
                    f"{_normalise_text(issue.get('issue_title'))}"
                )

                for question_number, question in enumerate(
                    issue.get("questions", []),
                    start=1,
                ):
                    lines.append(
                        f"   Q{question_number}. "
                        f"{_normalise_text(question)}"
                    )

                lines.append("")

        lines.extend(
            [
                "-" * 60,
                "",
            ]
        )

    return "\n".join(lines)


def build_publication_summary(
    package: dict[str, Any],
) -> str:
    """Create a concise overview of all daily outputs."""

    publication_date = package["publication_date"]
    selected_issues = package["selected_issues"].get("issues", [])
    daily_heading = package["website_content"].get(
        "daily_heading",
        "",
    )

    previous_questions = (
        package["recall_schedule"]
        .get("previous_day", {})
        .get("questions", [])
    )

    current_questions = (
        package["recall_schedule"]
        .get("present_day", {})
        .get("questions", [])
    )

    lines = [
        "=" * 60,
        "TODAY'S UPSC ISSUES",
        "DAILY PUBLICATION SUMMARY",
        f"DATE: {publication_date}",
        "=" * 60,
        "",
        f"DAILY CODE: TUI-{_parse_date(publication_date).strftime('%y%m%d')}",
        f"TOTAL ISSUES: {len(selected_issues)}",
        f"YOUTUBE SHORTS: {len(package['youtube_shorts'].get('shorts', []))}",
        f"TELEGRAM CARDS: {len(package['telegram_cards'].get('cards', []))}",
        f"PREVIOUS-DAY RECALL SETS: {len(previous_questions)}",
        f"NEXT-DAY RECALL SETS: {len(current_questions)}",
        "",
        "WEBSITE HEADING:",
        _normalise_multiline_text(daily_heading),
        "",
        "SELECTED ISSUES:",
    ]

    for number, issue in enumerate(selected_issues, start=1):
        lines.append(
            f"{number}. {issue.get('title', '')} "
            f"[{issue.get('issue_id', '')}]"
        )

    lines.extend(
        [
            "",
            "OUTPUT STATUS:",
            "✓ PDF dataset prepared",
            "✓ YouTube Shorts scripts prepared",
            "✓ YouTube anchors prepared",
            "✓ Telegram card content prepared",
            "✓ Website heading prepared",
            "✓ Recall schedule prepared",
            "",
        ]
    )

    return "\n".join(lines)


# ============================================================
# OUTPUT PACKAGE GENERATOR
# ============================================================

def generate_output_package(
    publication_date: str | date | datetime,
    overwrite: bool = False,
) -> OutputResult:
    """
    Generate all daily platform-ready output files.

    Parameters
    ----------
    publication_date:
        Date of the repository package to process.

    overwrite:
        Replace the existing daily output package when True.
    """

    parsed_date = _parse_date(publication_date)
    package = load_repository_package(parsed_date)

    output_folder = get_output_folder(parsed_date)

    if output_folder.exists():
        if not overwrite:
            raise OutputPackageExistsError(
                "An output package already exists for "
                f"{parsed_date.isoformat()}:\n{output_folder}\n"
                "Use overwrite=True only when intentionally rebuilding it."
            )

        shutil.rmtree(output_folder)

    output_folder.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []

    json_exports = {
        OUTPUT_PDF_DATASET_FILE: package["pdf_dataset"],
        OUTPUT_YOUTUBE_FILE: package["youtube_shorts"],
        OUTPUT_TELEGRAM_FILE: package["telegram_cards"],
        OUTPUT_WEBSITE_FILE: package["website_content"],
        OUTPUT_RECALL_FILE: package["recall_schedule"],
    }

    for filename, content in json_exports.items():
        path = output_folder / filename
        _write_json(path, deepcopy(content))
        created_files.append(path)

    text_exports = {
        YOUTUBE_SCRIPT_TEXT_FILE: build_youtube_text(
            package["youtube_shorts"]
        ),
        TELEGRAM_TEXT_FILE: build_telegram_text(
            package["telegram_cards"]
        ),
        WEBSITE_TEXT_FILE: build_website_text(
            package["website_content"]
        ),
        RECALL_TEXT_FILE: build_recall_text(
            package["recall_schedule"]
        ),
        PUBLICATION_SUMMARY_FILE: build_publication_summary(
            package
        ),
    }

    for filename, content in text_exports.items():
        path = output_folder / filename
        _write_text(path, content)
        created_files.append(path)

    selected_issues = package["selected_issues"].get("issues", [])
    youtube_shorts = package["youtube_shorts"].get("shorts", [])
    telegram_cards = package["telegram_cards"].get("cards", [])

    output_manifest = {
        "output_version": "2.0",
        "publication_date": parsed_date.isoformat(),
        "daily_code": f"TUI-{parsed_date.strftime('%y%m%d')}",
        "source_repository_folder": _relative_path(
            package["repository_folder"]
        ),
        "output_folder": _relative_path(output_folder),
        "issue_count": len(selected_issues),
        "issue_ids": [
            issue.get("issue_id")
            for issue in selected_issues
        ],
        "outputs": {
            "pdf": {
                "dataset_ready": True,
                "final_pdf_generated": False,
                "file": OUTPUT_PDF_DATASET_FILE,
            },
            "youtube": {
                "ready": True,
                "short_count": len(youtube_shorts),
                "json_file": OUTPUT_YOUTUBE_FILE,
                "text_file": YOUTUBE_SCRIPT_TEXT_FILE,
            },
            "telegram": {
                "ready": True,
                "card_count": len(telegram_cards),
                "json_file": OUTPUT_TELEGRAM_FILE,
                "text_file": TELEGRAM_TEXT_FILE,
            },
            "website": {
                "ready": True,
                "json_file": OUTPUT_WEBSITE_FILE,
                "text_file": WEBSITE_TEXT_FILE,
                "pdf_upload_required": True,
            },
            "recall": {
                "ready": True,
                "json_file": OUTPUT_RECALL_FILE,
                "text_file": RECALL_TEXT_FILE,
            },
        },
        "files": [
            _relative_path(path)
            for path in created_files
        ],
        "generated_at": _timestamp(),
    }

    manifest_path = output_folder / OUTPUT_MANIFEST_FILE
    _write_json(manifest_path, output_manifest)
    created_files.append(manifest_path)

    return OutputResult(
        publication_date=parsed_date.isoformat(),
        output_folder=output_folder,
        issue_count=len(selected_issues),
        youtube_short_count=len(youtube_shorts),
        telegram_card_count=len(telegram_cards),
        created_files=tuple(created_files),
    )


# ============================================================
# COMMAND-LINE SUPPORT
# ============================================================

def _get_command_line_date() -> date:
    """
    Read an optional publication date from the command line.

    Examples:
        python src\\output_generator.py
        python src\\output_generator.py 2026-07-19
    """

    if len(sys.argv) >= 2:
        return _parse_date(sys.argv[1])

    return date.today()


def _command_requests_overwrite() -> bool:
    """
    Detect the optional overwrite flag.

    Example:
        python src\\output_generator.py 2026-07-19 --overwrite
    """

    return any(
        argument.strip().lower() in {
            "--overwrite",
            "-o",
        }
        for argument in sys.argv[1:]
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the daily output generator."""

    try:
        publication_date = _get_command_line_date()
        overwrite = _command_requests_overwrite()

        result = generate_output_package(
            publication_date=publication_date,
            overwrite=overwrite,
        )

        result.display()

    except OutputGeneratorError as error:
        print("=" * 60)
        print("TODAY'S UPSC ISSUES")
        print("OUTPUT GENERATOR ERROR")
        print("=" * 60)
        print(error)
        print("=" * 60)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()