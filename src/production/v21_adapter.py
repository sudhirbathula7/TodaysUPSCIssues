"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.1 → VERSION 2.1 ADAPTER
Created by Sudhir
============================================================

PURPOSE

Converts the Version 3.1 DAILY_INPUT.json
contract into the flat selected_issues.json structure consumed
by the stable Version 2.1 repository generator.

The adapter performs only deterministic field translation.

It does not:

• Generate repository records
• Run intelligence analysis
• Generate publication outputs
• Generate PDFs
• Modify Version 2.1 modules
============================================================
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.production.paths import (
    V21_SELECTED_ISSUES_FILE,
)
from src.production.production_validator import (
    ProductionValidator,
    ValidationResult,
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class V21AdapterError(RuntimeError):
    """
    Base exception for Version 2.1 adapter failures.
    """


class CanonicalInputError(V21AdapterError):
    """
    Raised when canonical input cannot be read or validated.
    """


class AdapterOutputError(V21AdapterError):
    """
    Raised when Version 2.1 output cannot be created safely.
    """


# ==========================================================
# ADAPTER RESULT
# ==========================================================

@dataclass(frozen=True)
class V21AdapterResult:
    """
    Result of one canonical-to-Version-2.1 conversion.
    """

    production_date: str
    issue_count: int
    output_file: Path
    backup_file: Path | None
    selected_issues: tuple[dict[str, Any], ...]

    def display(self) -> None:
        """
        Print a readable adapter result.
        """

        print("=" * 72)
        print("TODAY'S UPSC ISSUES — VERSION 2.1 ADAPTER")
        print("=" * 72)
        print(
            f"Production date : {self.production_date}"
        )
        print(
            f"Issue count     : {self.issue_count}"
        )
        print(
            f"Output file     : {self.output_file}"
        )

        if self.backup_file is not None:
            print(
                f"Backup file     : {self.backup_file}"
            )
        else:
            print(
                "Backup file     : Not required"
            )

        print("-" * 72)
        print("Converted issues")

        for number, issue in enumerate(
            self.selected_issues,
            start=1,
        ):
            print(
                f"{number}. {issue['title']}"
            )

        print("-" * 72)
        print(
            "✓ Canonical data converted to "
            "Version 2.1 format"
        )
        print("=" * 72)


# ==========================================================
# HELPERS
# ==========================================================

def _clean_text(
    value: Any,
    *,
    field_name: str,
) -> str:
    """
    Return a required non-empty string.
    """

    if not isinstance(value, str):
        raise CanonicalInputError(
            f"{field_name} must be a string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise CanonicalInputError(
            f"{field_name} cannot be empty."
        )

    return cleaned


def _clean_string_list(
    value: Any,
    *,
    field_name: str,
    minimum: int = 1,
) -> list[str]:
    """
    Return a cleaned list of unique non-empty strings.
    """

    if not isinstance(value, list):
        raise CanonicalInputError(
            f"{field_name} must be a list."
        )

    cleaned_values: list[str] = []

    for index, item in enumerate(value):
        cleaned = _clean_text(
            item,
            field_name=(
                f"{field_name}[{index}]"
            ),
        )

        if cleaned not in cleaned_values:
            cleaned_values.append(cleaned)

    if len(cleaned_values) < minimum:
        raise CanonicalInputError(
            f"{field_name} must contain at least "
            f"{minimum} item(s)."
        )

    return cleaned_values


def _format_rating(value: Any) -> str:
    """
    Convert canonical numeric rating to Version 2.1 format.

    Example:
        4.8 → 4.8/5
        5.0 → 5/5
    """

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        raise CanonicalInputError(
            "Issue rating must be numeric."
        )

    numeric_value = float(value)

    if numeric_value.is_integer():
        rating_text = str(
            int(numeric_value)
        )
    else:
        rating_text = (
            f"{numeric_value:.2f}"
            .rstrip("0")
            .rstrip(".")
        )

    return f"{rating_text}/5"


def _build_category(
    syllabus_tags: list[str],
) -> str:
    """
    Build the optional Version 2.1 category value.

    Version 2.1 accepts a flat category string. The canonical
    schema stores structured syllabus tags.

    The first three unique tags are joined without changing
    their wording.
    """

    selected_tags = syllabus_tags[:3]

    return " | ".join(selected_tags)


def _build_youtube_script(
    youtube: dict[str, Any],
) -> str:
    """
    Build the Version 2.1 YouTube Shorts script.
    """

    hook = _clean_text(
        youtube.get("hook"),
        field_name="outputs.youtube_short.hook",
    )

    script = _clean_text(
        youtube.get("short_script"),
        field_name="outputs.youtube_short.short_script",
    )

    closing_question = _clean_text(
        youtube.get("closing_question"),
        field_name="outputs.youtube_short.closing_question",
    )

    return (
        f"{hook}\n\n"
        f"{script}\n\n"
        f"{closing_question}"
    )

def _build_telegram_caption(
    telegram: dict[str, Any],
) -> str:
    """
    Build the Version 2.1 Telegram caption.
    """

    return _clean_text(
        telegram.get("recall_prompt"),
        field_name="outputs.telegram_card.recall_prompt",
    )

def _build_website_heading(
    website: dict[str, Any],
) -> str:
    """
    Build the Version 2.1 website heading.
    """

    return _clean_text(
        website.get("heading"),
        field_name="outputs.website_article.heading",
    )


# ==========================================================
# ISSUE TRANSLATION# ==========================================================
# ISSUE TRANSLATION
# ==========================================================

def convert_issue_to_v21(
    issue: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one Version 3.1 issue into the Version 2.1 flat
    input structure.
    """

    if not isinstance(issue, dict):
        raise CanonicalInputError(
            "Each issue must be an object."
        )

    metadata = issue.get("metadata")
    pdf = issue.get("pdf")
    recall = issue.get("recall")
    outputs = issue.get("outputs")

    required_root_objects = {
        "metadata": metadata,
        "pdf": pdf,
        "recall": recall,
        "outputs": outputs,
    }

    for name, value in required_root_objects.items():
        if not isinstance(value, dict):
            raise CanonicalInputError(
                f"Issue {name} must be an object."
            )

    telegram = outputs.get("telegram_card")
    youtube = outputs.get("youtube_short")
    website = outputs.get("website_article")

    required_output_objects = {
        "outputs.telegram_card": telegram,
        "outputs.youtube_short": youtube,
        "outputs.website_article": website,
    }

    for name, value in required_output_objects.items():
        if not isinstance(value, dict):
            raise CanonicalInputError(
                f"Issue {name} must be an object."
            )

    syllabus_tags = _clean_string_list(
        metadata.get("syllabus_tags"),
        field_name="metadata.syllabus_tags",
        minimum=1,
    )

    gs_papers = _clean_string_list(
        metadata.get("gs_papers"),
        field_name="metadata.gs_papers",
        minimum=1,
    )

    quick_facts = _clean_string_list(
        pdf.get("quick_facts"),
        field_name="pdf.quick_facts",
        minimum=4,
    )

    recall_questions = _clean_string_list(
        recall.get("recall_questions"),
        field_name="recall.recall_questions",
        minimum=2,
    )

    anchors = _clean_string_list(
        recall.get("revision_anchors"),
        field_name="recall.revision_anchors",
        minimum=5,
    )

    if len(recall_questions) != 2:
        raise CanonicalInputError(
            "Version 2.1 requires exactly two "
            "recall questions per issue."
        )

    return {
        "title": _clean_text(metadata.get("title"), field_name="metadata.title"),
        "gs_paper": ", ".join(gs_papers),
        "category": _build_category(syllabus_tags),
        "rating": _format_rating(metadata.get("rating")),
        "current_context": _clean_text(pdf.get("current_context"), field_name="pdf.current_context"),
        "why_it_matters_for_upsc": _clean_text(pdf.get("why_it_matters"), field_name="pdf.why_it_matters"),
        "core_concept": _clean_text(pdf.get("core_concept"), field_name="pdf.core_concept"),
        "challenges": _clean_text(pdf.get("challenges"), field_name="pdf.challenges"),
        "way_forward": _clean_text(pdf.get("way_forward"), field_name="pdf.way_forward"),
        "quick_facts": quick_facts,
        "what_upsc_asks": _clean_text(pdf.get("what_upsc_asks"), field_name="pdf.what_upsc_asks"),
        "key_takeaway": _clean_text(pdf.get("key_takeaway"), field_name="pdf.key_takeaway"),
        "recall_questions": recall_questions,
        "youtube_short_script": _build_youtube_script(youtube),
        "anchors": anchors,
        "telegram_caption": _build_telegram_caption(telegram),
        "website_heading": _build_website_heading(website),
    }


# ==========================================================
# DATASET TRANSLATION# ==========================================================
# DATASET TRANSLATION
# ==========================================================

def convert_canonical_data_to_v21(
    canonical_data: dict[str, Any],
    *,
    source_files: list[str] | None = None,
) -> dict[str, Any]:
    """
    Convert complete canonical data into the Version 2.1
    selected_issues.json structure.
    """

    if not isinstance(canonical_data, dict):
        raise CanonicalInputError(
            "Canonical data must be an object."
        )

    production = canonical_data.get(
        "production"
    )

    issues = canonical_data.get(
        "issues"
    )

    if not isinstance(production, dict):
        raise CanonicalInputError(
            "Canonical production metadata is missing."
        )

    if not isinstance(issues, list):
        raise CanonicalInputError(
            "Canonical issues must be a list."
        )

    if not issues:
        raise CanonicalInputError(
            "Canonical input contains no issues."
        )

    publication_date = _clean_text(
        production.get("production_date"),
        field_name=(
            "production.production_date"
        ),
    )

    try:
        datetime.strptime(
            publication_date,
            "%d-%m-%Y",
        )
    except ValueError as exc:
        raise CanonicalInputError(
            "production.production_date must "
            "use DD-MM-YYYY."
        ) from exc

    converted_issues = [
        convert_issue_to_v21(issue)
        for issue in issues
    ]

    cleaned_source_files: list[str] = []

    if source_files is not None:
        if not isinstance(source_files, list):
            raise CanonicalInputError(
                "source_files must be a list."
            )

        for index, source_file in enumerate(
            source_files
        ):
            cleaned = _clean_text(
                source_file,
                field_name=(
                    f"source_files[{index}]"
                ),
            )

            if cleaned not in cleaned_source_files:
                cleaned_source_files.append(
                    cleaned
                )

    return {
        "publication_date": publication_date,
        "selected_issues": converted_issues,
        "source_files": cleaned_source_files,
    }


# ==========================================================
# ADAPTER
# ==========================================================

class V21Adapter:
    """
    Translate validated Version 3.0 canonical input into the
    stable Version 2.1 selected_issues.json format.
    """

    def __init__(
        self,
        *,
        expected_production_date: (
            date
            | str
            | None
        ) = None,
    ) -> None:
        self.validator = ProductionValidator(
            expected_production_date=(
                expected_production_date
            )
        )

    # ------------------------------------------------------
    # LOAD AND VALIDATE
    # ------------------------------------------------------

    def load_canonical_file(
        self,
        path: Path,
    ) -> tuple[
        dict[str, Any],
        ValidationResult,
    ]:
        """
        Load and validate one canonical file.
        """

        path = Path(path)

        result = self.validator.validate_file(
            path
        )

        if not result.is_valid:
            raise CanonicalInputError(
                "Canonical input failed production "
                "validation.\n\n"
                + result.to_text()
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise CanonicalInputError(
                f"Invalid canonical JSON: {path}"
            ) from exc

        if not isinstance(data, dict):
            raise CanonicalInputError(
                "Canonical root must be an object."
            )

        return data, result

    # ------------------------------------------------------
    # CONVERT
    # ------------------------------------------------------

    def convert_file(
        self,
        canonical_file: Path,
        *,
        output_file: Path | None = None,
        source_files: list[str] | None = None,
        overwrite: bool = False,
        create_backup: bool = True,
    ) -> V21AdapterResult:
        """
        Convert one canonical file and write the Version 2.1
        selected_issues.json file.

        The real Version 2.1 input path is used when output_file
        is omitted.
        """

        canonical_file = Path(
            canonical_file
        )

        destination = (
            Path(output_file)
            if output_file is not None
            else V21_SELECTED_ISSUES_FILE
        )

        canonical_data, validation_result = (
            self.load_canonical_file(
                canonical_file
            )
        )

        converted_data = (
            convert_canonical_data_to_v21(
                canonical_data,
                source_files=source_files,
            )
        )

        backup_file: Path | None = None

        if destination.exists():
            existing_text = destination.read_text(
                encoding="utf-8"
            )

            new_text = (
                json.dumps(
                    converted_data,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n"
            )

            if existing_text == new_text:
                return V21AdapterResult(
                    production_date=(
                        converted_data[
                            "publication_date"
                        ]
                    ),
                    issue_count=len(
                        converted_data[
                            "selected_issues"
                        ]
                    ),
                    output_file=destination,
                    backup_file=None,
                    selected_issues=tuple(
                        converted_data[
                            "selected_issues"
                        ]
                    ),
                )

            if not overwrite:
                raise AdapterOutputError(
                    "Version 2.1 input file already exists "
                    "with different content:\n"
                    f"{destination}\n"
                    "Use overwrite=True only when rebuilding "
                    "the production input intentionally."
                )

            if create_backup:
                backup_file = (
                    destination.with_name(
                        destination.stem
                        + ".backup"
                        + destination.suffix
                    )
                )

                shutil.copy2(
                    destination,
                    backup_file,
                )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_text(
            json.dumps(
                converted_data,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return V21AdapterResult(
            production_date=(
                validation_result.production_date
                or converted_data[
                    "publication_date"
                ]
            ),
            issue_count=len(
                converted_data[
                    "selected_issues"
                ]
            ),
            output_file=destination,
            backup_file=backup_file,
            selected_issues=tuple(
                converted_data[
                    "selected_issues"
                ]
            ),
        )


# ==========================================================
# COMMAND-LINE ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Convert Version 3.0 canonical content "
            "to Version 2.1 selected_issues.json."
        )
    )

    parser.add_argument(
        "canonical_file",
        type=Path,
        help="Path to DAILY_INPUT.json",
    )

    parser.add_argument(
        "--date",
        dest="production_date",
        help=(
            "Expected production date in "
            "DD-MM-YYYY format."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output path. Defaults to "
            "Daily_Work/input/selected_issues.json."
        ),
    )

    parser.add_argument(
        "--source-file",
        action="append",
        default=[],
        help=(
            "Source editorial file path. "
            "May be supplied more than once."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing output.",
    )

    arguments = parser.parse_args()

    adapter = V21Adapter(
        expected_production_date=(
            arguments.production_date
        )
    )

    adapter_result = adapter.convert_file(
        canonical_file=(
            arguments.canonical_file
        ),
        output_file=arguments.output,
        source_files=(
            arguments.source_file
        ),
        overwrite=arguments.overwrite,
    )

    adapter_result.display()