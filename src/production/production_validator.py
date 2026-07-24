"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.1 PRODUCTION VALIDATOR
Created by Sudhir
============================================================

Validates DAILY_INPUT.json against the frozen Version 3.1
issue-centric schema. The validator never modifies the input.
============================================================
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.production.models import current_timestamp
from src.production.paths import ProductionPaths

VALIDATOR_VERSION = "3.1"
MIN_ISSUES = 1
MAX_ISSUES = 8
MIN_RATING = 4.5
MAX_RATING = 5.0
VALID_GS_PAPERS = {"GS I", "GS II", "GS III", "GS IV", "Prelims", "Essay"}

REQUIRED_TOP_LEVEL_FIELDS = {"production", "issues"}
REQUIRED_PRODUCTION_FIELDS = {"production_date", "edition_code", "total_issues"}
REQUIRED_ISSUE_FIELDS = {"metadata", "description", "pdf", "recall", "outputs"}
REQUIRED_METADATA_FIELDS = {
    "issue_number", "issue_id", "title", "slug", "gs_papers",
    "syllabus_tags", "rating", "source_ids",
}
REQUIRED_PDF_FIELDS = {
    "current_context", "why_it_matters", "core_concept", "challenges",
    "way_forward", "quick_facts", "what_upsc_asks", "key_takeaway",
}
REQUIRED_RECALL_FIELDS = {"recall_questions", "revision_anchors"}
REQUIRED_OUTPUT_FIELDS = {"telegram_card", "youtube_short", "website_article"}
REQUIRED_TELEGRAM_FIELDS = {"card_title", "card_points", "recall_prompt"}
REQUIRED_YOUTUBE_FIELDS = {"hook", "short_script", "closing_question"}
REQUIRED_WEBSITE_FIELDS = {"heading", "summary"}

EDITION_CODE_PATTERN = re.compile(r"^TUI-[0-9]{6}$")
ISSUE_ID_PATTERN = re.compile(r"^TUI-[0-9]{6}-[0-9]{3}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ValidationMessage:
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


@dataclass
class ValidationResult:
    source_file: str
    production_date: str | None = None
    edition_code: str | None = None
    issue_count: int | None = None
    errors: list[ValidationMessage] = field(default_factory=list)
    warnings: list[ValidationMessage] = field(default_factory=list)
    validated_at: str = field(default_factory=current_timestamp)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add_error(self, code: str, path: str, message: str) -> None:
        self.errors.append(ValidationMessage("error", code, path, message))

    def add_warning(self, code: str, path: str, message: str) -> None:
        self.warnings.append(ValidationMessage("warning", code, path, message))

    def to_dict(self) -> dict[str, Any]:
        return {
            "validator_version": VALIDATOR_VERSION,
            "validated_at": self.validated_at,
            "source_file": self.source_file,
            "is_valid": self.is_valid,
            "production_date": self.production_date,
            "edition_code": self.edition_code,
            "issue_count": self.issue_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [item.to_dict() for item in self.errors],
            "warnings": [item.to_dict() for item in self.warnings],
        }

    def to_text(self) -> str:
        lines = [
            "=" * 72,
            "TODAY'S UPSC ISSUES — VERSION 3.1 VALIDATION REPORT",
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
            for index, item in enumerate(self.errors, start=1):
                lines += [f"{index}. [{item.code}] {item.path}", f"   {item.message}"]
            lines.append("-" * 72)
        if self.warnings:
            lines.append("WARNINGS")
            for index, item in enumerate(self.warnings, start=1):
                lines += [f"{index}. [{item.code}] {item.path}", f"   {item.message}"]
            lines.append("-" * 72)
        lines.append(
            "✓ DAILY_INPUT.json is valid."
            if self.is_valid
            else "✗ Production must stop until all errors are corrected."
        )
        lines.append("=" * 72)
        return "\n".join(lines) + "\n"


class ProductionValidator:
    def __init__(self, *, expected_production_date: date | str | None = None) -> None:
        if isinstance(expected_production_date, date):
            self.expected_production_date = expected_production_date.strftime("%d-%m-%Y")
        else:
            self.expected_production_date = expected_production_date

    def validate_file(self, path: Path) -> ValidationResult:
        path = Path(path)
        result = ValidationResult(source_file=str(path))
        if not path.exists():
            result.add_error("FILE_NOT_FOUND", "$", f"Input file not found: {path}")
            return result
        if not path.is_file():
            result.add_error("NOT_A_FILE", "$", f"Input path is not a file: {path}")
            return result
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.add_error("INVALID_ENCODING", "$", "Input file must use UTF-8 encoding.")
            return result
        if not text.strip():
            result.add_error("EMPTY_FILE", "$", "Input file is empty.")
            return result
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            result.add_error(
                "INVALID_JSON", "$",
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
            return result
        return self.validate_data(data, source_file=str(path))

    def validate_data(self, data: Any, *, source_file: str = "<memory>") -> ValidationResult:
        result = ValidationResult(source_file=source_file)
        if not isinstance(data, dict):
            result.add_error("ROOT_NOT_OBJECT", "$", "DAILY_INPUT.json must contain one root object.")
            return result
        self._exact_fields(data, REQUIRED_TOP_LEVEL_FIELDS, "$", result, "MISSING_TOP_LEVEL_FIELD", "UNKNOWN_TOP_LEVEL_FIELD")
        production = data.get("production")
        if isinstance(production, dict):
            result.production_date = production.get("production_date")
            result.edition_code = production.get("edition_code")
            result.issue_count = production.get("total_issues")
        self._validate_production(production, result)
        self._validate_issues(data.get("issues"), result)
        self._validate_cross_consistency(data, result)
        return result

    @staticmethod
    def _is_string(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def _object(self, value: Any, path: str, result: ValidationResult) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            result.add_error("EXPECTED_OBJECT", path, "Expected a JSON object.")
            return None
        return value

    def _string(self, value: Any, path: str, result: ValidationResult) -> None:
        if not self._is_string(value):
            result.add_error("EMPTY_OR_INVALID_STRING", path, "Expected a non-empty string.")

    def _exact_fields(
        self,
        data: dict[str, Any],
        required: set[str],
        path: str,
        result: ValidationResult,
        missing_code: str,
        unknown_code: str,
    ) -> None:
        for name in sorted(required - set(data)):
            result.add_error(missing_code, f"{path}.{name}", f"Missing required field: {name}")
        for name in sorted(set(data) - required):
            result.add_error(unknown_code, f"{path}.{name}", f"Unexpected field: {name!r}.")

    def _string_list(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
        *,
        minimum: int = 1,
        exact: int | None = None,
    ) -> list[str]:
        if not isinstance(value, list):
            result.add_error("EXPECTED_LIST", path, "Expected a list.")
            return []
        if exact is not None and len(value) != exact:
            result.add_error("INVALID_ITEM_COUNT", path, f"Expected exactly {exact} item(s), received {len(value)}.")
        elif len(value) < minimum:
            result.add_error("TOO_FEW_ITEMS", path, f"Expected at least {minimum} item(s).")
        cleaned: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            if not self._is_string(item):
                result.add_error("INVALID_LIST_STRING", item_path, "Expected a non-empty string.")
                continue
            clean = item.strip()
            if clean in seen:
                result.add_warning("DUPLICATE_LIST_ITEM", item_path, f"Duplicate list item: {clean!r}.")
            seen.add(clean)
            cleaned.append(clean)
        return cleaned

    def _validate_production(self, value: Any, result: ValidationResult) -> None:
        path = "$.production"
        production = self._object(value, path, result)
        if production is None:
            return
        self._exact_fields(production, REQUIRED_PRODUCTION_FIELDS, path, result, "MISSING_PRODUCTION_FIELD", "UNKNOWN_PRODUCTION_FIELD")
        production_date = production.get("production_date")
        parsed_date: date | None = None
        if not self._is_string(production_date):
            result.add_error("INVALID_PRODUCTION_DATE", f"{path}.production_date", "Production date must use DD-MM-YYYY.")
        else:
            try:
                parsed_date = datetime.strptime(production_date, "%d-%m-%Y").date()
            except ValueError:
                result.add_error("INVALID_PRODUCTION_DATE", f"{path}.production_date", "Production date must be a real DD-MM-YYYY date.")
        if self.expected_production_date and production_date != self.expected_production_date:
            result.add_error("UNEXPECTED_PRODUCTION_DATE", f"{path}.production_date", f"Expected {self.expected_production_date!r}, received {production_date!r}.")
        edition_code = production.get("edition_code")
        if not isinstance(edition_code, str) or not EDITION_CODE_PATTERN.fullmatch(edition_code):
            result.add_error("INVALID_EDITION_CODE", f"{path}.edition_code", "Edition code must use TUI-YYMMDD format.")
        if parsed_date is not None and isinstance(edition_code, str):
            expected_code = "TUI-" + parsed_date.strftime("%y%m%d")
            if edition_code != expected_code:
                result.add_error("EDITION_DATE_MISMATCH", f"{path}.edition_code", f"Expected {expected_code!r}, received {edition_code!r}.")
        total_issues = production.get("total_issues")
        if not isinstance(total_issues, int) or isinstance(total_issues, bool) or not MIN_ISSUES <= total_issues <= MAX_ISSUES:
            result.add_error("INVALID_TOTAL_ISSUES", f"{path}.total_issues", f"total_issues must be an integer from {MIN_ISSUES} to {MAX_ISSUES}.")

    def _validate_issues(self, value: Any, result: ValidationResult) -> None:
        path = "$.issues"
        if not isinstance(value, list):
            result.add_error("ISSUES_NOT_LIST", path, "issues must be a list.")
            return
        if not MIN_ISSUES <= len(value) <= MAX_ISSUES:
            result.add_error("INVALID_ISSUES_LENGTH", path, f"issues must contain between {MIN_ISSUES} and {MAX_ISSUES} items.")
        numbers: set[int] = set()
        ids: set[str] = set()
        slugs: set[str] = set()
        for index, raw_issue in enumerate(value):
            issue_path = f"{path}[{index}]"
            issue = self._object(raw_issue, issue_path, result)
            if issue is None:
                continue
            self._exact_fields(issue, REQUIRED_ISSUE_FIELDS, issue_path, result, "MISSING_ISSUE_FIELD", "UNKNOWN_ISSUE_FIELD")
            metadata = self._validate_metadata(issue.get("metadata"), f"{issue_path}.metadata", result, numbers, ids, slugs)
            self._string(issue.get("description"), f"{issue_path}.description", result)
            self._validate_pdf(issue.get("pdf"), f"{issue_path}.pdf", result)
            self._validate_recall(issue.get("recall"), f"{issue_path}.recall", result)
            self._validate_outputs(issue.get("outputs"), f"{issue_path}.outputs", result)
            if metadata is not None:
                self._validate_issue_id_consistency(metadata, f"{issue_path}.metadata", result)

    def _validate_metadata(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
        numbers: set[int],
        ids: set[str],
        slugs: set[str],
    ) -> dict[str, Any] | None:
        metadata = self._object(value, path, result)
        if metadata is None:
            return None
        self._exact_fields(metadata, REQUIRED_METADATA_FIELDS, path, result, "MISSING_METADATA_FIELD", "UNKNOWN_METADATA_FIELD")
        number = metadata.get("issue_number")
        if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= MAX_ISSUES:
            result.add_error("INVALID_ISSUE_NUMBER", f"{path}.issue_number", f"issue_number must be an integer from 1 to {MAX_ISSUES}.")
        elif number in numbers:
            result.add_error("DUPLICATE_ISSUE_NUMBER", f"{path}.issue_number", f"Duplicate issue number: {number}.")
        else:
            numbers.add(number)
        issue_id = metadata.get("issue_id")
        if not isinstance(issue_id, str) or not ISSUE_ID_PATTERN.fullmatch(issue_id):
            result.add_error("INVALID_ISSUE_ID", f"{path}.issue_id", "issue_id must use TUI-YYMMDD-NNN format.")
        elif issue_id in ids:
            result.add_error("DUPLICATE_ISSUE_ID", f"{path}.issue_id", f"Duplicate issue_id: {issue_id!r}.")
        else:
            ids.add(issue_id)
        self._string(metadata.get("title"), f"{path}.title", result)
        slug = metadata.get("slug")
        if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
            result.add_error("INVALID_SLUG", f"{path}.slug", "Slug must use lowercase letters, numbers and single hyphens only.")
        elif slug in slugs:
            result.add_error("DUPLICATE_SLUG", f"{path}.slug", f"Duplicate slug: {slug!r}.")
        else:
            slugs.add(slug)
        gs_papers = self._string_list(metadata.get("gs_papers"), f"{path}.gs_papers", result)
        for item in gs_papers:
            if item not in VALID_GS_PAPERS:
                result.add_error("INVALID_GS_PAPER", f"{path}.gs_papers", f"Unsupported GS paper: {item!r}.")
        self._string_list(metadata.get("syllabus_tags"), f"{path}.syllabus_tags", result)
        rating = metadata.get("rating")
        if not isinstance(rating, (int, float)) or isinstance(rating, bool) or not MIN_RATING <= float(rating) <= MAX_RATING:
            result.add_error("INVALID_RATING", f"{path}.rating", f"rating must be between {MIN_RATING} and {MAX_RATING}.")
        self._string_list(metadata.get("source_ids"), f"{path}.source_ids", result)
        return metadata

    def _validate_issue_id_consistency(self, metadata: dict[str, Any], path: str, result: ValidationResult) -> None:
        issue_id = metadata.get("issue_id")
        number = metadata.get("issue_number")
        edition_code = result.edition_code
        if isinstance(issue_id, str) and isinstance(number, int) and isinstance(edition_code, str):
            expected = f"{edition_code}-{number:03d}"
            if issue_id != expected:
                result.add_error("ISSUE_ID_MISMATCH", f"{path}.issue_id", f"Expected {expected!r}, received {issue_id!r}.")

    def _validate_pdf(self, value: Any, path: str, result: ValidationResult) -> None:
        pdf = self._object(value, path, result)
        if pdf is None:
            return
        self._exact_fields(pdf, REQUIRED_PDF_FIELDS, path, result, "MISSING_PDF_FIELD", "UNKNOWN_PDF_FIELD")
        for name in REQUIRED_PDF_FIELDS - {"quick_facts"}:
            self._string(pdf.get(name), f"{path}.{name}", result)
        self._string_list(pdf.get("quick_facts"), f"{path}.quick_facts", result, exact=4)

    def _validate_recall(self, value: Any, path: str, result: ValidationResult) -> None:
        recall = self._object(value, path, result)
        if recall is None:
            return
        self._exact_fields(recall, REQUIRED_RECALL_FIELDS, path, result, "MISSING_RECALL_FIELD", "UNKNOWN_RECALL_FIELD")
        self._string_list(recall.get("recall_questions"), f"{path}.recall_questions", result, exact=1)
        self._string_list(recall.get("revision_anchors"), f"{path}.revision_anchors", result, exact=5)

    def _validate_outputs(self, value: Any, path: str, result: ValidationResult) -> None:
        outputs = self._object(value, path, result)
        if outputs is None:
            return
        self._exact_fields(outputs, REQUIRED_OUTPUT_FIELDS, path, result, "MISSING_OUTPUT_FIELD", "UNKNOWN_OUTPUT_FIELD")
        self._validate_simple_output(outputs.get("telegram_card"), f"{path}.telegram_card", result, REQUIRED_TELEGRAM_FIELDS, "TELEGRAM")
        telegram = outputs.get("telegram_card")
        if isinstance(telegram, dict):
            self._string_list(telegram.get("card_points"), f"{path}.telegram_card.card_points", result, exact=4)
        self._validate_simple_output(outputs.get("youtube_short"), f"{path}.youtube_short", result, REQUIRED_YOUTUBE_FIELDS, "YOUTUBE")
        self._validate_simple_output(outputs.get("website_article"), f"{path}.website_article", result, REQUIRED_WEBSITE_FIELDS, "WEBSITE")

    def _validate_simple_output(
        self,
        value: Any,
        path: str,
        result: ValidationResult,
        required: set[str],
        prefix: str,
    ) -> None:
        data = self._object(value, path, result)
        if data is None:
            return
        self._exact_fields(data, required, path, result, f"MISSING_{prefix}_FIELD", f"UNKNOWN_{prefix}_FIELD")
        for name in required:
            if name != "card_points":
                self._string(data.get(name), f"{path}.{name}", result)

    def _validate_cross_consistency(self, data: dict[str, Any], result: ValidationResult) -> None:
        production = data.get("production")
        issues = data.get("issues")
        if not isinstance(production, dict) or not isinstance(issues, list):
            return
        total = production.get("total_issues")
        if isinstance(total, int) and not isinstance(total, bool) and total != len(issues):
            result.add_error("ISSUE_COUNT_MISMATCH", "$.production.total_issues", f"total_issues is {total}, but issues contains {len(issues)} item(s).")
        numbers = []
        for issue in issues:
            if isinstance(issue, dict) and isinstance(issue.get("metadata"), dict):
                number = issue["metadata"].get("issue_number")
                if isinstance(number, int) and not isinstance(number, bool):
                    numbers.append(number)
        if numbers:
            expected = list(range(1, len(numbers) + 1))
            if sorted(numbers) != expected:
                result.add_error("NON_SEQUENTIAL_ISSUE_NUMBERS", "$.issues", f"Expected issue numbers {expected}, received {sorted(numbers)}.")

    @staticmethod
    def save_reports(result: ValidationResult, *, json_path: Path, text_path: Path) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        text_path.write_text(result.to_text(), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a Version 3.1 DAILY_INPUT.json file.")
    parser.add_argument("json_file", type=Path, help="Path to DAILY_INPUT.json")
    parser.add_argument("--date", dest="production_date", help="Expected date in DD-MM-YYYY format.")
    parser.add_argument("--save-session-reports", action="store_true")
    args = parser.parse_args()

    validator = ProductionValidator(expected_production_date=args.production_date)
    validation_result = validator.validate_file(args.json_file)
    print(validation_result.to_text())

    if args.save_session_reports:
        report_date = args.production_date or validation_result.production_date
        if not report_date:
            raise SystemExit("Cannot determine production date for report output.")
        parsed_date = datetime.strptime(report_date, "%d-%m-%Y").date()
        report_paths = ProductionPaths.for_date(parsed_date.isoformat())
        report_paths.create_directories()
        validator.save_reports(
            validation_result,
            json_path=report_paths.validation_report_json_file,
            text_path=report_paths.validation_report_text_file,
        )
        print("Validation reports saved:")
        print(f"  {report_paths.validation_report_json_file}")
        print(f"  {report_paths.validation_report_text_file}")

    raise SystemExit(0 if validation_result.is_valid else 1)