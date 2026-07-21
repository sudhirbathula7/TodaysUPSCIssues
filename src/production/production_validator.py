"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION VALIDATOR
Created by Sudhir
============================================================

PURPOSE

Validates generated_content.json before it is allowed to enter
the stable Version 2.1 production pipeline.

VALIDATION LEVELS

1. JSON syntax
2. Canonical structure
3. Production metadata
4. Issue completeness
5. Cross-reference consistency
6. Version 2.1 compatibility

The validator does not modify the canonical input.
============================================================
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.production.models import current_timestamp
from src.production.paths import (
    CANONICAL_SCHEMA_FILE,
    ProductionPaths,
)


# ==========================================================
# CONSTANTS
# ==========================================================

SCHEMA_VERSION = "3.0"
PUBLICATION_NAME = "Today's UPSC Issues"

MIN_ISSUES = 1
MAX_ISSUES = 8

MIN_RATING = 4.5
MAX_RATING = 5.0

VALID_GS_PAPERS = {
    "GS I",
    "GS II",
    "GS III",
    "GS IV",
    "Prelims",
    "Essay",
    "GS II & GS III",
    "GS I & GS II",
    "GS III & Essay",
    "Multi-GS",
}

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "production",
    "source_editorials",
    "issues",
    "publication",
}

REQUIRED_PRODUCTION_FIELDS = {
    "production_date",
    "edition_code",
    "publication_name",
    "issue_count",
}

REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "newspaper",
    "editorial_title",
}

REQUIRED_ISSUE_FIELDS = {
    "issue_number",
    "issue_id",
    "title",
    "slug",
    "gs_paper",
    "syllabus_tags",
    "rating",
    "source_ids",
    "content",
    "recall",
    "telegram",
    "youtube",
    "website",
}

REQUIRED_CONTENT_FIELDS = {
    "current_context",
    "why_it_matters",
    "core_concept",
    "challenges",
    "way_forward",
    "quick_facts",
    "what_upsc_asks",
    "key_takeaway",
}

REQUIRED_RECALL_FIELDS = {
    "questions",
    "anchors",
}

REQUIRED_TELEGRAM_FIELDS = {
    "card_title",
    "card_points",
    "recall_prompt",
}

REQUIRED_YOUTUBE_FIELDS = {
    "hook",
    "script",
    "closing_question",
}

REQUIRED_WEBSITE_ISSUE_FIELDS = {
    "short_heading",
    "summary",
}

REQUIRED_PUBLICATION_FIELDS = {
    "website",
    "telegram",
    "youtube",
}

REQUIRED_WEBSITE_PUBLICATION_FIELDS = {
    "daily_heading",
    "daily_summary",
}

REQUIRED_TELEGRAM_PUBLICATION_FIELDS = {
    "daily_intro",
    "daily_closing",
}

REQUIRED_YOUTUBE_PUBLICATION_FIELDS = {
    "daily_title",
    "daily_description",
}

ISSUE_ID_PATTERN = re.compile(
    r"^TUI-[0-9]{6}-[0-9]{2}-[A-Z0-9-]+$"
)

EDITION_CODE_PATTERN = re.compile(
    r"^TUI-[0-9]{6}$"
)

SLUG_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)


# ==========================================================
# VALIDATION MESSAGE
# ==========================================================

@dataclass(frozen=True)
class ValidationMessage:
    """
    One validator error or warning.
    """

    level: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


# ==========================================================
# VALIDATION RESULT
# ==========================================================

@dataclass
class ValidationResult:
    """
    Complete validation result for one canonical file.
    """

    source_file: str
    production_date: str | None = None
    edition_code: str | None = None
    issue_count: int | None = None

    errors: list[ValidationMessage] = field(
        default_factory=list
    )

    warnings: list[ValidationMessage] = field(
        default_factory=list
    )

    validated_at: str = field(
        default_factory=current_timestamp
    )

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add_error(
        self,
        code: str,
        path: str,
        message: str,
    ) -> None:
        self.errors.append(
            ValidationMessage(
                level="error",
                code=code,
                path=path,
                message=message,
            )
        )

    def add_warning(
        self,
        code: str,
        path: str,
        message: str,
    ) -> None:
        self.warnings.append(
            ValidationMessage(
                level="warning",
                code=code,
                path=path,
                message=message,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_version": "3.0",
            "validated_at": self.validated_at,
            "source_file": self.source_file,
            "is_valid": self.is_valid,
            "production_date": self.production_date,
            "edition_code": self.edition_code,
            "issue_count": self.issue_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                item.to_dict()
                for item in self.errors
            ],
            "warnings": [
                item.to_dict()
                for item in self.warnings
            ],
        }

    def to_text(self) -> str:
        lines = [
            "=" * 72,
            "TODAY'S UPSC ISSUES — PRODUCTION VALIDATION REPORT",
            "=" * 72,
            f"Source file     : {self.source_file}",
            f"Validated at    : {self.validated_at}",
            f"Production date : {self.production_date or 'Unknown'}",
            f"Edition code    : {self.edition_code or 'Unknown'}",
            f"Issue count     : {self.issue_count if self.issue_count is not None else 'Unknown'}",
            f"Result          : {'PASSED' if self.is_valid else 'FAILED'}",
            f"Errors          : {len(self.errors)}",
            f"Warnings        : {len(self.warnings)}",
            "-" * 72,
        ]

        if self.errors:
            lines.append("ERRORS")

            for index, item in enumerate(
                self.errors,
                start=1,
            ):
                lines.extend(
                    [
                        (
                            f"{index}. [{item.code}] "
                            f"{item.path}"
                        ),
                        f"   {item.message}",
                    ]
                )

            lines.append("-" * 72)

        if self.warnings:
            lines.append("WARNINGS")

            for index, item in enumerate(
                self.warnings,
                start=1,
            ):
                lines.extend(
                    [
                        (
                            f"{index}. [{item.code}] "
                            f"{item.path}"
                        ),
                        f"   {item.message}",
                    ]
                )

            lines.append("-" * 72)

        if self.is_valid:
            lines.append(
                "✓ Canonical production data is valid."
            )
            lines.append(
                "✓ Data may proceed to the Version 2.1 adapter."
            )
        else:
            lines.append(
                "✗ Production must stop until all errors are corrected."
            )

        lines.append("=" * 72)

        return "\n".join(lines) + "\n"


# ==========================================================
# VALIDATOR
# ==========================================================

class ProductionValidator:
    """
    Validate one Version 3.0 canonical production file.
    """

    def __init__(
        self,
        *,
        expected_production_date: date | str | None = None,
    ) -> None:
        if isinstance(expected_production_date, date):
            self.expected_production_date = (
                expected_production_date.isoformat()
            )
        else:
            self.expected_production_date = (
                expected_production_date
            )

    # ------------------------------------------------------
    # PUBLIC ENTRY POINTS
    # ------------------------------------------------------

    def validate_file(
        self,
        path: Path,
    ) -> ValidationResult:
        """
        Read and validate a canonical JSON file.
        """

        path = Path(path)

        result = ValidationResult(
            source_file=str(path)
        )

        if not path.exists():
            result.add_error(
                "FILE_NOT_FOUND",
                "$",
                f"Canonical file not found: {path}",
            )
            return result

        if not path.is_file():
            result.add_error(
                "NOT_A_FILE",
                "$",
                f"Canonical path is not a file: {path}",
            )
            return result

        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            result.add_error(
                "INVALID_ENCODING",
                "$",
                "Canonical file must use UTF-8 encoding.",
            )
            return result

        if not text.strip():
            result.add_error(
                "EMPTY_FILE",
                "$",
                "Canonical file is empty.",
            )
            return result

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            result.add_error(
                "INVALID_JSON",
                "$",
                (
                    "Invalid JSON syntax at "
                    f"line {exc.lineno}, column {exc.colno}: "
                    f"{exc.msg}"
                ),
            )
            return result

        return self.validate_data(
            data,
            source_file=str(path),
        )

    def validate_data(
        self,
        data: Any,
        *,
        source_file: str = "<memory>",
    ) -> ValidationResult:
        """
        Validate decoded canonical data.
        """

        result = ValidationResult(
            source_file=source_file
        )

        if not isinstance(data, dict):
            result.add_error(
                "ROOT_NOT_OBJECT",
                "$",
                "Canonical data must be a JSON object.",
            )
            return result

        self._validate_schema_file(result)
        self._validate_top_level(data, result)

        production = data.get("production")

        if isinstance(production, dict):
            result.production_date = production.get(
                "production_date"
            )
            result.edition_code = production.get(
                "edition_code"
            )
            result.issue_count = production.get(
                "issue_count"
            )

        self._validate_production(
            production,
            result,
        )

        source_editorials = data.get(
            "source_editorials"
        )

        source_ids = self._validate_sources(
            source_editorials,
            result,
        )

        issues = data.get("issues")

        self._validate_issues(
            issues,
            source_ids,
            result,
        )

        self._validate_publication(
            data.get("publication"),
            result,
        )

        self._validate_cross_consistency(
            data,
            result,
        )

        self._validate_v21_compatibility(
            data,
            result,
        )

        return result

    # ------------------------------------------------------
    # SCHEMA CONTRACT
    # ------------------------------------------------------

    def _validate_schema_file(
        self,
        result: ValidationResult,
    ) -> None:
        """
        Confirm that the locked schema file exists and is valid.
        """

        if not CANONICAL_SCHEMA_FILE.exists():
            result.add_error(
                "SCHEMA_FILE_MISSING",
                "$",
                (
                    "Locked canonical schema file is missing: "
                    f"{CANONICAL_SCHEMA_FILE}"
                ),
            )
            return

        try:
            schema_data = json.loads(
                CANONICAL_SCHEMA_FILE.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            result.add_error(
                "SCHEMA_FILE_INVALID",
                "$",
                (
                    "Locked canonical schema is invalid JSON: "
                    f"{exc.msg}"
                ),
            )
            return

        if schema_data.get("$id") != (
            "todays-upsc-issues-generated-content-v3.0"
        ):
            result.add_error(
                "SCHEMA_ID_MISMATCH",
                "$",
                "Unexpected canonical schema identifier.",
            )

    # ------------------------------------------------------
    # GENERIC HELPERS
    # ------------------------------------------------------

    @staticmethod
    def _is_non_empty_string(value: Any) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _missing_fields(
        data: dict[str, Any],
        required_fields: set[str],
    ) -> list[str]:
        return sorted(
            required_fields - set(data.keys())
        )

    def _require_object(
        self,
        value: Any,
        *,
        path: str,
        result: ValidationResult,
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            result.add_error(
                "EXPECTED_OBJECT",
                path,
                "Expected a JSON object.",
            )
            return None

        return value

    def _require_non_empty_string(
        self,
        value: Any,
        *,
        path: str,
        result: ValidationResult,
    ) -> None:
        if not self._is_non_empty_string(value):
            result.add_error(
                "EMPTY_OR_INVALID_STRING",
                path,
                "Expected a non-empty string.",
            )

    def _validate_string_list(
        self,
        value: Any,
        *,
        path: str,
        result: ValidationResult,
        minimum: int = 1,
        maximum: int | None = None,
    ) -> list[str]:
        if not isinstance(value, list):
            result.add_error(
                "EXPECTED_LIST",
                path,
                "Expected a list.",
            )
            return []

        if len(value) < minimum:
            result.add_error(
                "TOO_FEW_ITEMS",
                path,
                f"Expected at least {minimum} item(s).",
            )

        if (
            maximum is not None
            and len(value) > maximum
        ):
            result.add_error(
                "TOO_MANY_ITEMS",
                path,
                f"Expected no more than {maximum} item(s).",
            )

        cleaned_values: list[str] = []

        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"

            if not self._is_non_empty_string(item):
                result.add_error(
                    "INVALID_LIST_STRING",
                    item_path,
                    "Expected a non-empty string.",
                )
                continue

            clean_item = item.strip()

            if clean_item in cleaned_values:
                result.add_warning(
                    "DUPLICATE_LIST_ITEM",
                    item_path,
                    (
                        "Duplicate list item detected: "
                        f"{clean_item!r}"
                    ),
                )

            cleaned_values.append(clean_item)

        return cleaned_values

    # ------------------------------------------------------
    # TOP LEVEL
    # ------------------------------------------------------

    def _validate_top_level(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        missing = self._missing_fields(
            data,
            REQUIRED_TOP_LEVEL_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_TOP_LEVEL_FIELD",
                f"$.{field_name}",
                (
                    "Missing required top-level field: "
                    f"{field_name}"
                ),
            )

        allowed_fields = REQUIRED_TOP_LEVEL_FIELDS

        for field_name in sorted(
            set(data.keys()) - allowed_fields
        ):
            result.add_error(
                "UNKNOWN_TOP_LEVEL_FIELD",
                f"$.{field_name}",
                (
                    "Unexpected top-level field. "
                    "The canonical contract does not permit "
                    f"{field_name!r}."
                ),
            )

        schema_version = data.get(
            "schema_version"
        )

        if schema_version != SCHEMA_VERSION:
            result.add_error(
                "SCHEMA_VERSION_MISMATCH",
                "$.schema_version",
                (
                    f"Expected schema version "
                    f"{SCHEMA_VERSION!r}, received "
                    f"{schema_version!r}."
                ),
            )

    # ------------------------------------------------------
    # PRODUCTION METADATA
    # ------------------------------------------------------

    def _validate_production(
        self,
        value: Any,
        result: ValidationResult,
    ) -> None:
        production = self._require_object(
            value,
            path="$.production",
            result=result,
        )

        if production is None:
            return

        missing = self._missing_fields(
            production,
            REQUIRED_PRODUCTION_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_PRODUCTION_FIELD",
                f"$.production.{field_name}",
                (
                    "Missing required production field: "
                    f"{field_name}"
                ),
            )

        production_date = production.get(
            "production_date"
        )

        if not self._is_non_empty_string(
            production_date
        ):
            result.add_error(
                "INVALID_PRODUCTION_DATE",
                "$.production.production_date",
                "Production date must use YYYY-MM-DD.",
            )
            parsed_date = None
        else:
            try:
                parsed_date = date.fromisoformat(
                    production_date
                )
            except ValueError:
                parsed_date = None
                result.add_error(
                    "INVALID_PRODUCTION_DATE",
                    "$.production.production_date",
                    (
                        "Production date must use a real "
                        "YYYY-MM-DD calendar date."
                    ),
                )

        if (
            self.expected_production_date
            and production_date
            != self.expected_production_date
        ):
            result.add_error(
                "UNEXPECTED_PRODUCTION_DATE",
                "$.production.production_date",
                (
                    "Canonical production date does not match "
                    "the active session. Expected "
                    f"{self.expected_production_date!r}, "
                    f"received {production_date!r}."
                ),
            )

        edition_code = production.get(
            "edition_code"
        )

        if (
            not isinstance(edition_code, str)
            or not EDITION_CODE_PATTERN.fullmatch(
                edition_code
            )
        ):
            result.add_error(
                "INVALID_EDITION_CODE",
                "$.production.edition_code",
                (
                    "Edition code must use "
                    "TUI-YYMMDD format."
                ),
            )

        if (
            parsed_date is not None
            and isinstance(edition_code, str)
        ):
            expected_code = (
                "TUI-"
                + parsed_date.strftime("%y%m%d")
            )

            if edition_code != expected_code:
                result.add_error(
                    "EDITION_DATE_MISMATCH",
                    "$.production.edition_code",
                    (
                        f"Expected {expected_code!r} for "
                        f"{production_date}, received "
                        f"{edition_code!r}."
                    ),
                )

        publication_name = production.get(
            "publication_name"
        )

        if publication_name != PUBLICATION_NAME:
            result.add_error(
                "PUBLICATION_NAME_MISMATCH",
                "$.production.publication_name",
                (
                    f"Expected {PUBLICATION_NAME!r}, "
                    f"received {publication_name!r}."
                ),
            )

        issue_count = production.get(
            "issue_count"
        )

        if (
            not isinstance(issue_count, int)
            or isinstance(issue_count, bool)
            or not MIN_ISSUES
            <= issue_count
            <= MAX_ISSUES
        ):
            result.add_error(
                "INVALID_ISSUE_COUNT",
                "$.production.issue_count",
                (
                    f"Issue count must be an integer from "
                    f"{MIN_ISSUES} to {MAX_ISSUES}."
                ),
            )

        if "generated_by" in production:
            self._require_non_empty_string(
                production.get("generated_by"),
                path="$.production.generated_by",
                result=result,
            )

        allowed_fields = (
            REQUIRED_PRODUCTION_FIELDS
            | {"generated_by"}
        )

        for field_name in sorted(
            set(production.keys()) - allowed_fields
        ):
            result.add_error(
                "UNKNOWN_PRODUCTION_FIELD",
                f"$.production.{field_name}",
                (
                    "Unexpected production metadata field: "
                    f"{field_name!r}."
                ),
            )

    # ------------------------------------------------------
    # SOURCE EDITORIALS
    # ------------------------------------------------------

    def _validate_sources(
        self,
        value: Any,
        result: ValidationResult,
    ) -> set[str]:
        path = "$.source_editorials"

        if not isinstance(value, list):
            result.add_error(
                "SOURCES_NOT_LIST",
                path,
                "source_editorials must be a list.",
            )
            return set()

        if not value:
            result.add_error(
                "NO_SOURCE_EDITORIALS",
                path,
                "At least one source editorial is required.",
            )

        source_ids: set[str] = set()

        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"

            source = self._require_object(
                item,
                path=item_path,
                result=result,
            )

            if source is None:
                continue

            missing = self._missing_fields(
                source,
                REQUIRED_SOURCE_FIELDS,
            )

            for field_name in missing:
                result.add_error(
                    "MISSING_SOURCE_FIELD",
                    f"{item_path}.{field_name}",
                    (
                        "Missing required source field: "
                        f"{field_name}"
                    ),
                )

            for field_name in REQUIRED_SOURCE_FIELDS:
                self._require_non_empty_string(
                    source.get(field_name),
                    path=f"{item_path}.{field_name}",
                    result=result,
                )

            source_id = source.get("source_id")

            if self._is_non_empty_string(source_id):
                if source_id in source_ids:
                    result.add_error(
                        "DUPLICATE_SOURCE_ID",
                        f"{item_path}.source_id",
                        (
                            "Duplicate source_id: "
                            f"{source_id!r}"
                        ),
                    )

                source_ids.add(source_id)

            publication_date = source.get(
                "publication_date"
            )

            if publication_date is not None:
                if not isinstance(
                    publication_date,
                    str,
                ):
                    result.add_error(
                        "INVALID_SOURCE_DATE",
                        f"{item_path}.publication_date",
                        (
                            "publication_date must be a date "
                            "string or null."
                        ),
                    )
                else:
                    try:
                        date.fromisoformat(
                            publication_date
                        )
                    except ValueError:
                        result.add_error(
                            "INVALID_SOURCE_DATE",
                            (
                                f"{item_path}."
                                "publication_date"
                            ),
                            (
                                "Source publication date must "
                                "use YYYY-MM-DD."
                            ),
                        )

            author = source.get("author")

            if (
                author is not None
                and not self._is_non_empty_string(author)
            ):
                result.add_error(
                    "INVALID_SOURCE_AUTHOR",
                    f"{item_path}.author",
                    "Author must be a non-empty string or null.",
                )

            allowed_fields = (
                REQUIRED_SOURCE_FIELDS
                | {
                    "publication_date",
                    "author",
                }
            )

            for field_name in sorted(
                set(source.keys()) - allowed_fields
            ):
                result.add_error(
                    "UNKNOWN_SOURCE_FIELD",
                    f"{item_path}.{field_name}",
                    (
                        "Unexpected source field: "
                        f"{field_name!r}."
                    ),
                )

        return source_ids

    # ------------------------------------------------------
    # ISSUES
    # ------------------------------------------------------

    def _validate_issues(
        self,
        value: Any,
        source_ids: set[str],
        result: ValidationResult,
    ) -> None:
        path = "$.issues"

        if not isinstance(value, list):
            result.add_error(
                "ISSUES_NOT_LIST",
                path,
                "issues must be a list.",
            )
            return

        if not MIN_ISSUES <= len(value) <= MAX_ISSUES:
            result.add_error(
                "INVALID_ISSUES_LENGTH",
                path,
                (
                    f"issues must contain between "
                    f"{MIN_ISSUES} and {MAX_ISSUES} items."
                ),
            )

        issue_numbers: set[int] = set()
        issue_ids: set[str] = set()
        slugs: set[str] = set()

        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"

            issue = self._require_object(
                item,
                path=item_path,
                result=result,
            )

            if issue is None:
                continue

            missing = self._missing_fields(
                issue,
                REQUIRED_ISSUE_FIELDS,
            )

            for field_name in missing:
                result.add_error(
                    "MISSING_ISSUE_FIELD",
                    f"{item_path}.{field_name}",
                    (
                        "Missing required issue field: "
                        f"{field_name}"
                    ),
                )

            self._validate_issue_identity(
                issue,
                item_path,
                issue_numbers,
                issue_ids,
                slugs,
                result,
            )

            self._validate_string_list(
                issue.get("syllabus_tags"),
                path=f"{item_path}.syllabus_tags",
                result=result,
                minimum=1,
            )

            rating = issue.get("rating")

            if (
                not isinstance(rating, (int, float))
                or isinstance(rating, bool)
                or not MIN_RATING
                <= float(rating)
                <= MAX_RATING
            ):
                result.add_error(
                    "INVALID_RATING",
                    f"{item_path}.rating",
                    (
                        f"Rating must be between "
                        f"{MIN_RATING} and {MAX_RATING}."
                    ),
                )

            issue_source_ids = self._validate_string_list(
                issue.get("source_ids"),
                path=f"{item_path}.source_ids",
                result=result,
                minimum=1,
            )

            for source_id in issue_source_ids:
                if source_id not in source_ids:
                    result.add_error(
                        "UNKNOWN_SOURCE_REFERENCE",
                        f"{item_path}.source_ids",
                        (
                            f"Issue references unknown source "
                            f"{source_id!r}."
                        ),
                    )

            self._validate_issue_content(
                issue.get("content"),
                f"{item_path}.content",
                result,
            )

            self._validate_recall(
                issue.get("recall"),
                f"{item_path}.recall",
                result,
            )

            self._validate_telegram_issue(
                issue.get("telegram"),
                f"{item_path}.telegram",
                result,
            )

            self._validate_youtube_issue(
                issue.get("youtube"),
                f"{item_path}.youtube",
                result,
            )

            self._validate_website_issue(
                issue.get("website"),
                f"{item_path}.website",
                result,
            )

            for field_name in sorted(
                set(issue.keys())
                - REQUIRED_ISSUE_FIELDS
            ):
                result.add_error(
                    "UNKNOWN_ISSUE_FIELD",
                    f"{item_path}.{field_name}",
                    (
                        "Unexpected issue field: "
                        f"{field_name!r}."
                    ),
                )

    def _validate_issue_identity(
        self,
        issue: dict[str, Any],
        item_path: str,
        issue_numbers: set[int],
        issue_ids: set[str],
        slugs: set[str],
        result: ValidationResult,
    ) -> None:
        issue_number = issue.get(
            "issue_number"
        )

        if (
            not isinstance(issue_number, int)
            or isinstance(issue_number, bool)
            or not 1 <= issue_number <= MAX_ISSUES
        ):
            result.add_error(
                "INVALID_ISSUE_NUMBER",
                f"{item_path}.issue_number",
                (
                    "issue_number must be an integer "
                    f"from 1 to {MAX_ISSUES}."
                ),
            )
        elif issue_number in issue_numbers:
            result.add_error(
                "DUPLICATE_ISSUE_NUMBER",
                f"{item_path}.issue_number",
                (
                    "Duplicate issue number: "
                    f"{issue_number}"
                ),
            )
        else:
            issue_numbers.add(issue_number)

        issue_id = issue.get("issue_id")

        if (
            not isinstance(issue_id, str)
            or not ISSUE_ID_PATTERN.fullmatch(
                issue_id
            )
        ):
            result.add_error(
                "INVALID_ISSUE_ID",
                f"{item_path}.issue_id",
                (
                    "issue_id must use the format "
                    "TUI-YYMMDD-NN-UPPERCASE-TITLE."
                ),
            )
        elif issue_id in issue_ids:
            result.add_error(
                "DUPLICATE_ISSUE_ID",
                f"{item_path}.issue_id",
                f"Duplicate issue_id: {issue_id!r}",
            )
        else:
            issue_ids.add(issue_id)

        self._require_non_empty_string(
            issue.get("title"),
            path=f"{item_path}.title",
            result=result,
        )

        slug = issue.get("slug")

        if (
            not isinstance(slug, str)
            or not SLUG_PATTERN.fullmatch(slug)
        ):
            result.add_error(
                "INVALID_SLUG",
                f"{item_path}.slug",
                (
                    "Slug must contain lowercase letters, "
                    "numbers and single hyphens only."
                ),
            )
        elif slug in slugs:
            result.add_error(
                "DUPLICATE_SLUG",
                f"{item_path}.slug",
                f"Duplicate slug: {slug!r}",
            )
        else:
            slugs.add(slug)

        gs_paper = issue.get("gs_paper")

        if gs_paper not in VALID_GS_PAPERS:
            result.add_error(
                "INVALID_GS_PAPER",
                f"{item_path}.gs_paper",
                (
                    f"Unsupported gs_paper value: "
                    f"{gs_paper!r}."
                ),
            )

    # ------------------------------------------------------
    # ISSUE CONTENT
    # ------------------------------------------------------

    def _validate_issue_content(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        content = self._require_object(
            value,
            path=path,
            result=result,
        )

        if content is None:
            return

        missing = self._missing_fields(
            content,
            REQUIRED_CONTENT_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_CONTENT_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required issue content field: "
                    f"{field_name}"
                ),
            )

        text_fields = (
            REQUIRED_CONTENT_FIELDS
            - {"quick_facts"}
        )

        for field_name in text_fields:
            self._require_non_empty_string(
                content.get(field_name),
                path=f"{path}.{field_name}",
                result=result,
            )

        self._validate_string_list(
            content.get("quick_facts"),
            path=f"{path}.quick_facts",
            result=result,
            minimum=3,
            maximum=8,
        )

        for field_name in sorted(
            set(content.keys())
            - REQUIRED_CONTENT_FIELDS
        ):
            result.add_error(
                "UNKNOWN_CONTENT_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected issue content field: "
                    f"{field_name!r}."
                ),
            )

    def _validate_recall(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        recall = self._require_object(
            value,
            path=path,
            result=result,
        )

        if recall is None:
            return

        missing = self._missing_fields(
            recall,
            REQUIRED_RECALL_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_RECALL_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required recall field: "
                    f"{field_name}"
                ),
            )

        self._validate_string_list(
            recall.get("questions"),
            path=f"{path}.questions",
            result=result,
            minimum=2,
            maximum=2,
        )

        self._validate_string_list(
            recall.get("anchors"),
            path=f"{path}.anchors",
            result=result,
            minimum=2,
            maximum=6,
        )

        for field_name in sorted(
            set(recall.keys())
            - REQUIRED_RECALL_FIELDS
        ):
            result.add_error(
                "UNKNOWN_RECALL_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected recall field: "
                    f"{field_name!r}."
                ),
            )

    def _validate_telegram_issue(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        telegram = self._require_object(
            value,
            path=path,
            result=result,
        )

        if telegram is None:
            return

        missing = self._missing_fields(
            telegram,
            REQUIRED_TELEGRAM_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_TELEGRAM_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required Telegram field: "
                    f"{field_name}"
                ),
            )

        self._require_non_empty_string(
            telegram.get("card_title"),
            path=f"{path}.card_title",
            result=result,
        )

        self._validate_string_list(
            telegram.get("card_points"),
            path=f"{path}.card_points",
            result=result,
            minimum=2,
            maximum=6,
        )

        self._require_non_empty_string(
            telegram.get("recall_prompt"),
            path=f"{path}.recall_prompt",
            result=result,
        )

        for field_name in sorted(
            set(telegram.keys())
            - REQUIRED_TELEGRAM_FIELDS
        ):
            result.add_error(
                "UNKNOWN_TELEGRAM_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected Telegram field: "
                    f"{field_name!r}."
                ),
            )

    def _validate_youtube_issue(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        youtube = self._require_object(
            value,
            path=path,
            result=result,
        )

        if youtube is None:
            return

        missing = self._missing_fields(
            youtube,
            REQUIRED_YOUTUBE_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_YOUTUBE_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required YouTube field: "
                    f"{field_name}"
                ),
            )

        for field_name in REQUIRED_YOUTUBE_FIELDS:
            self._require_non_empty_string(
                youtube.get(field_name),
                path=f"{path}.{field_name}",
                result=result,
            )

        for field_name in sorted(
            set(youtube.keys())
            - REQUIRED_YOUTUBE_FIELDS
        ):
            result.add_error(
                "UNKNOWN_YOUTUBE_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected YouTube field: "
                    f"{field_name!r}."
                ),
            )

    def _validate_website_issue(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
    ) -> None:
        website = self._require_object(
            value,
            path=path,
            result=result,
        )

        if website is None:
            return

        missing = self._missing_fields(
            website,
            REQUIRED_WEBSITE_ISSUE_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_WEBSITE_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required website field: "
                    f"{field_name}"
                ),
            )

        for field_name in REQUIRED_WEBSITE_ISSUE_FIELDS:
            self._require_non_empty_string(
                website.get(field_name),
                path=f"{path}.{field_name}",
                result=result,
            )

        for field_name in sorted(
            set(website.keys())
            - REQUIRED_WEBSITE_ISSUE_FIELDS
        ):
            result.add_error(
                "UNKNOWN_WEBSITE_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected website field: "
                    f"{field_name!r}."
                ),
            )

    # ------------------------------------------------------
    # PUBLICATION CONTENT
    # ------------------------------------------------------

    def _validate_publication(
        self,
        value: Any,
        result: ValidationResult,
    ) -> None:
        path = "$.publication"

        publication = self._require_object(
            value,
            path=path,
            result=result,
        )

        if publication is None:
            return

        missing = self._missing_fields(
            publication,
            REQUIRED_PUBLICATION_FIELDS,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_PUBLICATION_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required publication field: "
                    f"{field_name}"
                ),
            )

        self._validate_simple_text_object(
            publication.get("website"),
            path=f"{path}.website",
            required_fields=(
                REQUIRED_WEBSITE_PUBLICATION_FIELDS
            ),
            result=result,
        )

        self._validate_simple_text_object(
            publication.get("telegram"),
            path=f"{path}.telegram",
            required_fields=(
                REQUIRED_TELEGRAM_PUBLICATION_FIELDS
            ),
            result=result,
        )

        self._validate_simple_text_object(
            publication.get("youtube"),
            path=f"{path}.youtube",
            required_fields=(
                REQUIRED_YOUTUBE_PUBLICATION_FIELDS
            ),
            result=result,
        )

        for field_name in sorted(
            set(publication.keys())
            - REQUIRED_PUBLICATION_FIELDS
        ):
            result.add_error(
                "UNKNOWN_PUBLICATION_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected publication field: "
                    f"{field_name!r}."
                ),
            )

    def _validate_simple_text_object(
        self,
        value: Any,
        *,
        path: str,
        required_fields: set[str],
        result: ValidationResult,
    ) -> None:
        data = self._require_object(
            value,
            path=path,
            result=result,
        )

        if data is None:
            return

        missing = self._missing_fields(
            data,
            required_fields,
        )

        for field_name in missing:
            result.add_error(
                "MISSING_PUBLICATION_TEXT_FIELD",
                f"{path}.{field_name}",
                (
                    "Missing required publication text "
                    f"field: {field_name}"
                ),
            )

        for field_name in required_fields:
            self._require_non_empty_string(
                data.get(field_name),
                path=f"{path}.{field_name}",
                result=result,
            )

        for field_name in sorted(
            set(data.keys()) - required_fields
        ):
            result.add_error(
                "UNKNOWN_PUBLICATION_TEXT_FIELD",
                f"{path}.{field_name}",
                (
                    "Unexpected publication text field: "
                    f"{field_name!r}."
                ),
            )

    # ------------------------------------------------------
    # CROSS-FIELD CONSISTENCY
    # ------------------------------------------------------

    def _validate_cross_consistency(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        production = data.get("production")
        issues = data.get("issues")

        if (
            isinstance(production, dict)
            and isinstance(issues, list)
        ):
            issue_count = production.get(
                "issue_count"
            )

            if (
                isinstance(issue_count, int)
                and not isinstance(issue_count, bool)
                and issue_count != len(issues)
            ):
                result.add_error(
                    "ISSUE_COUNT_MISMATCH",
                    "$.production.issue_count",
                    (
                        f"Production issue_count is "
                        f"{issue_count}, but issues contains "
                        f"{len(issues)} item(s)."
                    ),
                )

            production_date = production.get(
                "production_date"
            )

            edition_code = production.get(
                "edition_code"
            )

            if (
                isinstance(edition_code, str)
                and isinstance(production_date, str)
            ):
                date_fragment = edition_code.removeprefix(
                    "TUI-"
                )

                for index, issue in enumerate(issues):
                    if not isinstance(issue, dict):
                        continue

                    issue_id = issue.get("issue_id")

                    if (
                        isinstance(issue_id, str)
                        and not issue_id.startswith(
                            f"TUI-{date_fragment}-"
                        )
                    ):
                        result.add_error(
                            "ISSUE_ID_DATE_MISMATCH",
                            f"$.issues[{index}].issue_id",
                            (
                                "Issue ID does not match the "
                                "production edition date."
                            ),
                        )

                    issue_number = issue.get(
                        "issue_number"
                    )

                    if (
                        isinstance(issue_id, str)
                        and isinstance(issue_number, int)
                        and not isinstance(issue_number, bool)
                    ):
                        expected_fragment = (
                            f"TUI-{date_fragment}-"
                            f"{issue_number:02d}-"
                        )

                        if not issue_id.startswith(
                            expected_fragment
                        ):
                            result.add_error(
                                "ISSUE_ID_NUMBER_MISMATCH",
                                (
                                    f"$.issues[{index}]."
                                    "issue_id"
                                ),
                                (
                                    "Issue ID number does not "
                                    "match issue_number."
                                ),
                            )

        if isinstance(issues, list):
            valid_numbers = [
                item.get("issue_number")
                for item in issues
                if isinstance(item, dict)
                and isinstance(
                    item.get("issue_number"),
                    int,
                )
                and not isinstance(
                    item.get("issue_number"),
                    bool,
                )
            ]

            if valid_numbers:
                expected_numbers = list(
                    range(
                        1,
                        len(valid_numbers) + 1,
                    )
                )

                if sorted(valid_numbers) != expected_numbers:
                    result.add_error(
                        "NON_SEQUENTIAL_ISSUE_NUMBERS",
                        "$.issues",
                        (
                            "Issue numbers must form a "
                            "continuous sequence beginning at 1. "
                            f"Expected {expected_numbers}, "
                            f"received {sorted(valid_numbers)}."
                        ),
                    )

    # ------------------------------------------------------
    # VERSION 2.1 COMPATIBILITY
    # ------------------------------------------------------

    def _validate_v21_compatibility(
        self,
        data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """
        Confirm that canonical data has everything required
        to produce the Version 2.1 selected_issues.json file.
        """

        issues = data.get("issues")

        if not isinstance(issues, list):
            return

        for index, issue in enumerate(issues):
            if not isinstance(issue, dict):
                continue

            path = f"$.issues[{index}]"

            required_adapter_values = {
                "issue_number": issue.get(
                    "issue_number"
                ),
                "issue_id": issue.get("issue_id"),
                "title": issue.get("title"),
                "slug": issue.get("slug"),
                "gs_paper": issue.get("gs_paper"),
                "rating": issue.get("rating"),
                "content": issue.get("content"),
                "recall": issue.get("recall"),
                "telegram": issue.get("telegram"),
                "youtube": issue.get("youtube"),
                "website": issue.get("website"),
            }

            missing_adapter_values = [
                key
                for key, value
                in required_adapter_values.items()
                if value is None
            ]

            if missing_adapter_values:
                result.add_error(
                    "V21_ADAPTER_INPUT_INCOMPLETE",
                    path,
                    (
                        "Issue cannot be translated into the "
                        "Version 2.1 input format. Missing: "
                        + ", ".join(
                            missing_adapter_values
                        )
                    ),
                )

    # ------------------------------------------------------
    # REPORT OUTPUT
    # ------------------------------------------------------

    @staticmethod
    def save_reports(
        result: ValidationResult,
        *,
        json_path: Path,
        text_path: Path,
    ) -> None:
        """
        Save JSON and human-readable validation reports.
        """

        json_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        text_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_path.write_text(
            json.dumps(
                result.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        text_path.write_text(
            result.to_text(),
            encoding="utf-8",
        )


# ==========================================================
# COMMAND-LINE SELF TEST
# ==========================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Validate a Today's UPSC Issues "
            "Version 3.0 canonical JSON file."
        )
    )

    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to generated_content.json",
    )

    parser.add_argument(
        "--date",
        dest="production_date",
        help="Expected production date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--save-session-reports",
        action="store_true",
        help=(
            "Save reports inside the matching "
            "Version 3.0 session folder."
        ),
    )

    arguments = parser.parse_args()

    validator = ProductionValidator(
        expected_production_date=(
            arguments.production_date
        )
    )

    validation_result = validator.validate_file(
        arguments.json_file
    )

    print(validation_result.to_text())

    if arguments.save_session_reports:
        report_date = (
            arguments.production_date
            or validation_result.production_date
        )

        if not report_date:
            raise SystemExit(
                "Cannot determine the production date "
                "for session report output."
            )

        report_paths = ProductionPaths.for_date(
            report_date
        )

        report_paths.create_directories()

        validator.save_reports(
            validation_result,
            json_path=(
                report_paths
                .validation_report_json_file
            ),
            text_path=(
                report_paths
                .validation_report_text_file
            ),
        )

        print(
            "Validation reports saved:"
        )
        print(
            f"  {report_paths.validation_report_json_file}"
        )
        print(
            f"  {report_paths.validation_report_text_file}"
        )

    raise SystemExit(
        0 if validation_result.is_valid else 1
    )