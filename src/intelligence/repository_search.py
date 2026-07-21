"""
============================================================
TODAY'S UPSC ISSUES
REPOSITORY SEARCH
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Provides a read-only search layer for the permanent issue
repository.

SUPPORTED SEARCHES

1. Find an issue by issue ID.
2. Find issues by title text.
3. Find issues by keyword.
4. Find issues by GS paper.
5. Find issues by category.
6. Find issues by publication date.
7. Find issues within a date range.
8. Load complete permanent issue records.
9. List all repository issues.
10. Return concise search summaries.

This module does not modify repository files.
============================================================
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT PATHS
# ============================================================

REPOSITORY_ROOT = PROJECT_ROOT / "Repository"

ISSUES_ROOT = REPOSITORY_ROOT / "issues"
INDEX_ROOT = REPOSITORY_ROOT / "index"

ISSUE_INDEX_FILE = INDEX_ROOT / "issue_index.json"


# ============================================================
# EXCEPTIONS
# ============================================================

class RepositorySearchError(Exception):
    """Base exception for repository-search errors."""


class RepositoryIndexError(RepositorySearchError):
    """Raised when the central issue index is unavailable."""


class IssueRecordError(RepositorySearchError):
    """Raised when a permanent issue record cannot be loaded."""


# ============================================================
# SEARCH RESULT
# ============================================================

@dataclass(frozen=True, slots=True)
class IssueSearchResult:
    """Concise search result for one issue."""

    issue_id: str
    title: str
    publication_date: str
    gs_paper: str
    category: str
    rating: str
    record_path: Path

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a serialisable dictionary."""

        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "publication_date": self.publication_date,
            "gs_paper": self.gs_paper,
            "category": self.category,
            "rating": self.rating,
            "record_path": str(self.record_path),
        }


# ============================================================
# TEXT HELPERS
# ============================================================

def _normalise_text(value: Any) -> str:
    """Return clean single-spaced lowercase text."""

    if value is None:
        return ""

    text = str(value).strip().lower()
    return re.sub(r"\s+", " ", text)


def _normalise_search_terms(
    value: str | Iterable[str],
) -> list[str]:
    """Convert one or more values into clean search terms."""

    if isinstance(value, str):
        values = [value]
    else:
        values = list(value)

    terms: list[str] = []

    for item in values:
        cleaned = _normalise_text(item)

        if cleaned:
            terms.append(cleaned)

    return terms


def _contains_all_terms(
    text: str,
    terms: list[str],
) -> bool:
    """Return True when all terms are present."""

    normalised_text = _normalise_text(text)

    return all(
        term in normalised_text
        for term in terms
    )


def _contains_any_term(
    text: str,
    terms: list[str],
) -> bool:
    """Return True when at least one term is present."""

    normalised_text = _normalise_text(text)

    return any(
        term in normalised_text
        for term in terms
    )


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date(
    value: str | date | datetime,
) -> date:
    """Convert supported date formats into a date object."""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    cleaned = str(value).strip()

    supported_formats = (
        "%d-%m-%y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d/%m/%y",
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

    raise RepositorySearchError(
        "Unsupported date format.\n"
        "Examples:\n"
        "20-07-26\n"
        "2026-07-20\n"
        "20-07-2026"
    )


def _display_date(value: date) -> str:
    """Return the repository date format."""

    return value.strftime("%d-%m-%y")


# ============================================================
# JSON HELPERS
# ============================================================

def _read_json(path: Path) -> Any:
    """Read a UTF-8 JSON file."""

    if not path.exists():
        raise RepositoryIndexError(
            f"Repository file was not found:\n{path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RepositoryIndexError(
            f"Invalid JSON file:\n{path}\n"
            f"Line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error


# ============================================================
# INDEX LOADING
# ============================================================

def load_issue_index() -> dict[str, Any]:
    """Load and validate the central issue index."""

    index = _read_json(
        ISSUE_INDEX_FILE
    )

    if not isinstance(index, dict):
        raise RepositoryIndexError(
            "issue_index.json must contain a JSON object."
        )

    issues = index.get("issues")

    if not isinstance(issues, dict):
        raise RepositoryIndexError(
            'issue_index.json must contain an "issues" object.'
        )

    return index


def get_issue_index_records() -> dict[str, dict[str, Any]]:
    """Return the indexed issue metadata records."""

    index = load_issue_index()
    records = index["issues"]

    return {
        str(issue_id): record
        for issue_id, record in records.items()
        if isinstance(record, dict)
    }


# ============================================================
# PATH RESOLUTION
# ============================================================

def _resolve_record_path(
    record_path: str | Path,
) -> Path:
    """Resolve a project-relative permanent record path."""

    path = Path(
        record_path
    ).expanduser()

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def _get_record_path_from_index(
    issue_id: str,
) -> Path:
    """Get the permanent record path for an issue ID."""

    records = get_issue_index_records()

    if issue_id not in records:
        raise IssueRecordError(
            f"Issue ID was not found:\n{issue_id}"
        )

    record_path = records[
        issue_id
    ].get("record_path")

    if not record_path:
        raise IssueRecordError(
            f"No record path is stored for:\n{issue_id}"
        )

    return _resolve_record_path(
        record_path
    )


# ============================================================
# RECORD LOADING
# ============================================================

def load_issue_record(
    issue_id: str,
) -> dict[str, Any]:
    """Load one complete permanent issue record."""

    issue_id = str(
        issue_id
    ).strip()

    if not issue_id:
        raise IssueRecordError(
            "Issue ID cannot be empty."
        )

    record_path = _get_record_path_from_index(
        issue_id
    )

    if not record_path.exists():
        raise IssueRecordError(
            "Permanent issue record is missing:\n"
            f"{record_path}"
        )

    record = _read_json(
        record_path
    )

    if not isinstance(record, dict):
        raise IssueRecordError(
            f"Issue record must contain a JSON object:\n"
            f"{record_path}"
        )

    if record.get("issue_id") != issue_id:
        raise IssueRecordError(
            "Issue ID mismatch between the index and "
            f"record file:\n{record_path}"
        )

    return record


def load_issue_records(
    issue_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Load several permanent issue records."""

    records: list[dict[str, Any]] = []

    for issue_id in issue_ids:
        records.append(
            load_issue_record(
                str(issue_id)
            )
        )

    return records


def load_all_issue_records() -> list[dict[str, Any]]:
    """Load every indexed permanent issue record."""

    issue_ids = list(
        get_issue_index_records().keys()
    )

    return load_issue_records(
        issue_ids
    )


# ============================================================
# SEARCH RESULT CONVERSION
# ============================================================

def _to_search_result(
    issue_id: str,
    record: dict[str, Any],
) -> IssueSearchResult:
    """Convert index metadata into IssueSearchResult."""

    record_path_value = record.get(
        "record_path",
        ""
    )

    record_path = (
        _resolve_record_path(
            record_path_value
        )
        if record_path_value
        else Path()
    )

    return IssueSearchResult(
        issue_id=issue_id,
        title=str(
            record.get(
                "title",
                "",
            )
        ),
        publication_date=str(
            record.get(
                "publication_date",
                "",
            )
        ),
        gs_paper=str(
            record.get(
                "gs_paper",
                "",
            )
        ),
        category=str(
            record.get(
                "category",
                "",
            )
        ),
        rating=str(
            record.get(
                "rating",
                "",
            )
        ),
        record_path=record_path,
    )


def list_issue_summaries() -> list[IssueSearchResult]:
    """Return summaries for all indexed issues."""

    records = get_issue_index_records()

    results = [
        _to_search_result(
            issue_id=issue_id,
            record=record,
        )
        for issue_id, record in records.items()
    ]

    return sorted(
        results,
        key=lambda result: (
            _parse_date(
                result.publication_date
            ),
            result.issue_id,
        ),
        reverse=True,
    )


# ============================================================
# ID SEARCH
# ============================================================

def find_by_issue_id(
    issue_id: str,
    load_full_record: bool = True,
) -> dict[str, Any] | IssueSearchResult | None:
    """Find one issue by exact issue ID."""

    issue_id = str(
        issue_id
    ).strip()

    records = get_issue_index_records()

    record = records.get(
        issue_id
    )

    if record is None:
        return None

    if load_full_record:
        return load_issue_record(
            issue_id
        )

    return _to_search_result(
        issue_id=issue_id,
        record=record,
    )


# ============================================================
# TITLE SEARCH
# ============================================================

def search_by_title(
    query: str | Iterable[str],
    match_all: bool = True,
    load_full_records: bool = False,
) -> list[
    IssueSearchResult
    | dict[str, Any]
]:
    """Search indexed issue titles."""

    terms = _normalise_search_terms(
        query
    )

    if not terms:
        return []

    results: list[
        IssueSearchResult
        | dict[str, Any]
    ] = []

    records = get_issue_index_records()

    for issue_id, record in records.items():
        title = str(
            record.get(
                "title",
                "",
            )
        )

        matched = (
            _contains_all_terms(
                title,
                terms,
            )
            if match_all
            else _contains_any_term(
                title,
                terms,
            )
        )

        if matched:
            if load_full_records:
                results.append(
                    load_issue_record(
                        issue_id
                    )
                )
            else:
                results.append(
                    _to_search_result(
                        issue_id,
                        record,
                    )
                )

    return results


# ============================================================
# GS PAPER SEARCH
# ============================================================

def search_by_gs_paper(
    gs_paper: str,
    load_full_records: bool = False,
) -> list[
    IssueSearchResult
    | dict[str, Any]
]:
    """Find all issues for one GS paper."""

    target = _normalise_text(
        gs_paper
    )

    if not target:
        return []

    results: list[
        IssueSearchResult
        | dict[str, Any]
    ] = []

    records = get_issue_index_records()

    for issue_id, record in records.items():
        record_gs = _normalise_text(
            record.get(
                "gs_paper",
                "",
            )
        )

        if record_gs == target:
            if load_full_records:
                results.append(
                    load_issue_record(
                        issue_id
                    )
                )
            else:
                results.append(
                    _to_search_result(
                        issue_id,
                        record,
                    )
                )

    return results


# ============================================================
# CATEGORY SEARCH
# ============================================================

def search_by_category(
    query: str | Iterable[str],
    match_all: bool = False,
    load_full_records: bool = False,
) -> list[
    IssueSearchResult
    | dict[str, Any]
]:
    """Search issues by category text."""

    terms = _normalise_search_terms(
        query
    )

    if not terms:
        return []

    results: list[
        IssueSearchResult
        | dict[str, Any]
    ] = []

    records = get_issue_index_records()

    for issue_id, record in records.items():
        category = str(
            record.get(
                "category",
                "",
            )
        )

        matched = (
            _contains_all_terms(
                category,
                terms,
            )
            if match_all
            else _contains_any_term(
                category,
                terms,
            )
        )

        if matched:
            if load_full_records:
                results.append(
                    load_issue_record(
                        issue_id
                    )
                )
            else:
                results.append(
                    _to_search_result(
                        issue_id,
                        record,
                    )
                )

    return results


# ============================================================
# DATE SEARCH
# ============================================================

def search_by_date(
    publication_date: str | date | datetime,
    load_full_records: bool = False,
) -> list[
    IssueSearchResult
    | dict[str, Any]
]:
    """Find all issues for one publication date."""

    target_date = _display_date(
        _parse_date(
            publication_date
        )
    )

    results: list[
        IssueSearchResult
        | dict[str, Any]
    ] = []

    records = get_issue_index_records()

    for issue_id, record in records.items():
        record_date = str(
            record.get(
                "publication_date",
                "",
            )
        )

        if record_date == target_date:
            if load_full_records:
                results.append(
                    load_issue_record(
                        issue_id
                    )
                )
            else:
                results.append(
                    _to_search_result(
                        issue_id,
                        record,
                    )
                )

    return results


def search_by_date_range(
    start_date: str | date | datetime,
    end_date: str | date | datetime,
    load_full_records: bool = False,
) -> list[
    IssueSearchResult
    | dict[str, Any]
]:
    """Find issues within an inclusive date range."""

    parsed_start = _parse_date(
        start_date
    )

    parsed_end = _parse_date(
        end_date
    )

    if parsed_start > parsed_end:
        raise RepositorySearchError(
            "Start date cannot be after end date."
        )

    results: list[
        IssueSearchResult
        | dict[str, Any]
    ] = []

    records = get_issue_index_records()

    for issue_id, record in records.items():
        publication_text = record.get(
            "publication_date"
        )

        if not publication_text:
            continue

        record_date = _parse_date(
            publication_text
        )

        if (
            parsed_start
            <= record_date
            <= parsed_end
        ):
            if load_full_records:
                results.append(
                    load_issue_record(
                        issue_id
                    )
                )
            else:
                results.append(
                    _to_search_result(
                        issue_id,
                        record,
                    )
                )

    return results


# ============================================================
# FULL-TEXT KEYWORD SEARCH
# ============================================================

def _flatten_issue_text(
    issue: dict[str, Any],
) -> str:
    """Combine searchable issue fields into one text block."""

    parts: list[str] = [
        str(
            issue.get(
                "title",
                "",
            )
        ),
        str(
            issue.get(
                "gs_paper",
                "",
            )
        ),
        str(
            issue.get(
                "category",
                "",
            )
        ),
    ]

    pdf_content = issue.get(
        "pdf_content",
        {},
    )

    if isinstance(pdf_content, dict):
        for value in pdf_content.values():
            if isinstance(value, list):
                parts.extend(
                    str(item)
                    for item in value
                )
            else:
                parts.append(
                    str(value)
                )

    recall = issue.get(
        "recall",
        {},
    )

    if isinstance(recall, dict):
        questions = recall.get(
            "questions",
            [],
        )

        if isinstance(
            questions,
            list,
        ):
            parts.extend(
                str(question)
                for question in questions
            )

    youtube = issue.get(
        "youtube",
        {},
    )

    if isinstance(youtube, dict):
        parts.append(
            str(
                youtube.get(
                    "short_script",
                    "",
                )
            )
        )

        anchors = youtube.get(
            "anchors",
            [],
        )

        if isinstance(
            anchors,
            list,
        ):
            parts.extend(
                str(anchor)
                for anchor in anchors
            )

    return " ".join(parts)


def search_by_keyword(
    query: str | Iterable[str],
    match_all: bool = False,
) -> list[dict[str, Any]]:
    """Search complete permanent issue records by keyword."""

    terms = _normalise_search_terms(
        query
    )

    if not terms:
        return []

    matches: list[
        dict[str, Any]
    ] = []

    for issue in load_all_issue_records():
        searchable_text = _flatten_issue_text(
            issue
        )

        matched = (
            _contains_all_terms(
                searchable_text,
                terms,
            )
            if match_all
            else _contains_any_term(
                searchable_text,
                terms,
            )
        )

        if matched:
            matches.append(
                issue
            )

    return matches


# ============================================================
# GENERAL SEARCH
# ============================================================

def search_repository(
    query: str | Iterable[str],
    match_all: bool = False,
) -> list[dict[str, Any]]:
    """Run a full-text repository search."""

    return search_by_keyword(
        query=query,
        match_all=match_all,
    )


# ============================================================
# DEVELOPMENT DISPLAY
# ============================================================

def _print_results(
    results: Iterable[
        IssueSearchResult
        | dict[str, Any]
    ],
) -> None:
    """Print concise search results."""

    results = list(results)

    if not results:
        print("No matching issues found.")
        return

    for number, result in enumerate(
        results,
        start=1,
    ):
        if isinstance(
            result,
            IssueSearchResult,
        ):
            issue_id = result.issue_id
            title = result.title
            publication_date = (
                result.publication_date
            )
            gs_paper = result.gs_paper
        else:
            issue_id = str(
                result.get(
                    "issue_id",
                    "",
                )
            )
            title = str(
                result.get(
                    "title",
                    "",
                )
            )
            publication_date = str(
                result.get(
                    "publication_date",
                    "",
                )
            )
            gs_paper = str(
                result.get(
                    "gs_paper",
                    "",
                )
            )

        print(
            f"{number}. {title}\n"
            f"   ID   : {issue_id}\n"
            f"   Date : {publication_date}\n"
            f"   GS   : {gs_paper}"
        )


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Test repository loading and basic searches."""

    print("=" * 68)
    print("TODAY'S UPSC ISSUES")
    print("REPOSITORY SEARCH — VERSION 2.1")
    print("=" * 68)

    summaries = list_issue_summaries()

    print(
        f"Indexed issues : {len(summaries)}"
    )

    print("-" * 68)

    if summaries:
        print("LATEST ISSUES")
        _print_results(
            summaries[:5]
        )
    else:
        print("No indexed issues are available.")

    print("-" * 68)
    print("✓ Issue index loaded")
    print("✓ Permanent records accessible")
    print("✓ Title search enabled")
    print("✓ GS paper search enabled")
    print("✓ Category search enabled")
    print("✓ Date search enabled")
    print("✓ Full-text keyword search enabled")
    print("=" * 68)


if __name__ == "__main__":
    _development_test()