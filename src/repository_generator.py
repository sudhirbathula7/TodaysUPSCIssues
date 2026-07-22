"""
============================================================
TODAY'S UPSC ISSUES
REPOSITORY GENERATOR
Version 2.0
Created by Sudhir
============================================================

PURPOSE

Creates and maintains the permanent issue repository.

DATE STANDARD

Display and dated folders:
    DD-MM-YY
    Example: 19-07-26

Document code:
    YYMMDD
    Example: TUI-260719

The generator:

1. Stores selected daily issues.
2. Creates permanent issue records.
3. Creates the dated daily repository folder.
4. Tracks PDF, YouTube, Telegram and website usage.
5. Tracks previous, present and next-day recall questions.
6. Maintains central issue, recall and usage indexes.
7. Prevents duplicate issue IDs.
8. Preserves source editorials.
============================================================
"""

from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = PROJECT_ROOT / "Repository"

ISSUES_ROOT = REPOSITORY_ROOT / "issues"
DAILY_ROOT = REPOSITORY_ROOT / "daily"
INDEX_ROOT = REPOSITORY_ROOT / "index"
SOURCE_EDITORIALS_ROOT = REPOSITORY_ROOT / "source_editorials"

ISSUE_INDEX_FILE = INDEX_ROOT / "issue_index.json"
RECALL_INDEX_FILE = INDEX_ROOT / "recall_index.json"
USAGE_INDEX_FILE = INDEX_ROOT / "usage_index.json"


# ============================================================
# FILE NAMES
# ============================================================

SELECTED_ISSUES_FILE = "selected_issues.json"
PDF_DATASET_FILE = "pdf_dataset.json"
YOUTUBE_SHORTS_FILE = "youtube_shorts.json"
TELEGRAM_CARDS_FILE = "telegram_cards.json"
WEBSITE_CONTENT_FILE = "website_content.json"
RECALL_SCHEDULE_FILE = "recall_schedule.json"
DAILY_MANIFEST_FILE = "manifest.json"


# ============================================================
# EXCEPTIONS
# ============================================================

class RepositoryError(Exception):
    """Base exception for repository-related errors."""


class RepositoryValidationError(RepositoryError):
    """Raised when issue data fails validation."""


class DuplicateIssueError(RepositoryError):
    """Raised when an issue ID already exists unexpectedly."""


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class RepositoryResult:
    """Result returned after repository generation."""

    publication_date: str
    daily_folder: Path
    issue_count: int
    issue_ids: tuple[str, ...]
    created_files: tuple[Path, ...]

    def display(self) -> None:
        """Print a readable repository summary."""

        print("=" * 60)
        print("TODAY'S UPSC ISSUES")
        print("REPOSITORY GENERATOR")
        print("=" * 60)
        print(f"Publication date : {self.publication_date}")
        print(f"Issues stored    : {self.issue_count}")
        print(f"Daily folder     : {self.daily_folder}")
        print("-" * 60)

        for issue_id in self.issue_ids:
            print(f"✓ {issue_id}")

        print("-" * 60)
        print("✓ Repository package generated successfully")
        print("=" * 60)


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
        "%Y-%m-%d",
        "%d-%m-%y",
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

    raise RepositoryValidationError(
        "Unsupported publication date.\n"
        "Examples:\n"
        "2026-07-19\n"
        "19-07-26\n"
        "19-07-2026\n"
        "19 July 2026"
    )


def _display_date(value: date) -> str:
    """Return the locked DD-MM-YY date."""

    return value.strftime("%d-%m-%y")

def _next_production_date(
    publication_date: date,
) -> date:
    """
    Return the next scheduled production date.

    Production runs from Monday to Saturday.
    Sunday is skipped, so Saturday recall is scheduled
    for Monday.
    """

    next_date = (
        publication_date
        + timedelta(days=1)
    )

    if next_date.weekday() == 6:
        next_date += timedelta(days=1)

    return next_date

def _document_code(value: date) -> str:
    """Return the compact TUI document code."""

    return f"TUI-{value.strftime('%y%m%d')}"


def _timestamp() -> str:
    """Return a timezone-aware timestamp."""

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


# ============================================================
# JSON HELPERS
# ============================================================

def _write_json(
    path: Path,
    data: Any,
) -> None:
    """Write JSON safely using a temporary file."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temporary_path.replace(path)


def _read_json(
    path: Path,
    default: Any | None = None,
) -> Any:
    """Read JSON and return the default when missing."""

    if not path.exists():
        return deepcopy(default)

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RepositoryError(
            f"Invalid JSON file:\n{path}\n{error}"
        ) from error


def _create_json_if_missing(
    path: Path,
    default_data: Any,
) -> None:
    """Create a JSON file only when absent."""

    if not path.exists():
        _write_json(
            path,
            default_data,
        )


# ============================================================
# REPOSITORY STRUCTURE
# ============================================================

def ensure_repository_structure() -> None:
    """Create permanent repository folders and indexes."""

    for folder in (
        REPOSITORY_ROOT,
        ISSUES_ROOT,
        DAILY_ROOT,
        INDEX_ROOT,
        SOURCE_EDITORIALS_ROOT,
    ):
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

    _create_json_if_missing(
        ISSUE_INDEX_FILE,
        _default_issue_index(),
    )

    _create_json_if_missing(
        RECALL_INDEX_FILE,
        _default_recall_index(),
    )

    _create_json_if_missing(
        USAGE_INDEX_FILE,
        _default_usage_index(),
    )


# ============================================================
# DEFAULT INDEXES
# ============================================================

def _default_issue_index() -> dict[str, Any]:
    return {
        "repository_version": "2.0",
        "last_updated": None,
        "total_issues": 0,
        "issues": {},
    }


def _default_recall_index() -> dict[str, Any]:
    """Return the default recall queue and tracking index."""

    return {
        "repository_version": "2.0",
        "last_updated": None,
        "next_recall_number": 1,
        "recalls": {},
        "dates": {},
        "questions": {},
    }


def _default_usage_index() -> dict[str, Any]:
    return {
        "repository_version": "2.0",
        "last_updated": None,
        "issues": {},
    }


# ============================================================
# TEXT HELPERS
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

    text = (
        str(value)
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .strip()
    )

    paragraphs: list[str] = []

    for paragraph in text.split("\n"):
        cleaned = re.sub(
            r"[ \t]+",
            " ",
            paragraph,
        ).strip()

        if cleaned:
            paragraphs.append(cleaned)

    return "\n".join(paragraphs)


def _normalise_list(value: Any) -> list[str]:
    """Convert supported values into a clean string list."""

    if value is None:
        return []

    if isinstance(value, str):
        value = [value]

    if (
        not isinstance(value, Iterable)
        or isinstance(value, dict)
    ):
        value = [value]

    items: list[str] = []

    for item in value:
        cleaned = _normalise_text(item)

        if cleaned:
            items.append(cleaned)

    return items


def _slugify(
    value: str,
    maximum_length: int = 60,
) -> str:
    """Create a safe filename slug."""

    value = _normalise_text(value).lower()

    value = (
        value
        .replace("’", "")
        .replace("'", "")
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    ).strip("-")

    if not value:
        value = "issue"

    return value[
        :maximum_length
    ].rstrip("-")


def _get_first_available(
    source: dict[str, Any],
    *field_names: str,
    default: Any = "",
) -> Any:
    """Return the first non-empty matching field."""

    for field_name in field_names:
        if (
            field_name in source
            and source[field_name] not in (None, "")
        ):
            return source[field_name]

    return default


# ============================================================
# ISSUE FIELD EXTRACTION
# ============================================================

def _extract_recall_questions(
    issue: dict[str, Any],
) -> list[str]:
    """Extract exactly two recall questions."""

    value = _get_first_available(
        issue,
        "recall_questions",
        "recall",
        "questions",
        default=[],
    )

    if isinstance(value, dict):
        value = [
            value.get("question_1", ""),
            value.get("question_2", ""),
        ]

    questions = _normalise_list(value)

    if not questions:
        questions = _normalise_list(
            [
                _get_first_available(
                    issue,
                    "recall_question_1",
                    "question_1",
                    default="",
                ),
                _get_first_available(
                    issue,
                    "recall_question_2",
                    "question_2",
                    default="",
                ),
            ]
        )

    return questions[:2]


def _extract_quick_facts(
    issue: dict[str, Any],
) -> list[str]:
    """Extract Quick Facts."""

    return _normalise_list(
        _get_first_available(
            issue,
            "quick_facts",
            "facts",
            default=[],
        )
    )


def _extract_anchors(
    issue: dict[str, Any],
) -> list[str]:
    """Extract visual anchors."""

    return _normalise_list(
        _get_first_available(
            issue,
            "anchors",
            "visual_anchors",
            "youtube_anchors",
            default=[],
        )
    )


# ============================================================
# ISSUE ID
# ============================================================

def create_issue_id(
    publication_date: date,
    sequence_number: int,
    title: str,
) -> str:
    """Create a stable issue ID."""

    date_code = publication_date.strftime(
        "%y%m%d"
    )

    title_code = _slugify(
        title,
        maximum_length=35,
    ).upper()

    return (
        f"TUI-{date_code}-"
        f"{sequence_number:02d}-"
        f"{title_code}"
    )


# ============================================================
# ISSUE NORMALISATION
# ============================================================

def normalise_issue(
    issue: dict[str, Any],
    publication_date: date,
    sequence_number: int,
) -> dict[str, Any]:
    """Convert incoming issue data into Version 2.0 format."""

    if not isinstance(issue, dict):
        raise RepositoryValidationError(
            f"Issue {sequence_number} must be a dictionary."
        )

    title = _normalise_text(
        _get_first_available(
            issue,
            "title",
            "issue_title",
            "issue",
            default="",
        )
    )

    if not title:
        raise RepositoryValidationError(
            f"Issue {sequence_number} does not contain a title."
        )

    issue_id = _normalise_text(
        _get_first_available(
            issue,
            "issue_id",
            "id",
            default="",
        )
    )

    if not issue_id:
        issue_id = create_issue_id(
            publication_date=publication_date,
            sequence_number=sequence_number,
            title=title,
        )

    recall_questions = _extract_recall_questions(
        issue
    )

    if len(recall_questions) != 2:
        raise RepositoryValidationError(
            f"{issue_id} must contain exactly "
            "two recall questions."
        )

    quick_facts = _extract_quick_facts(
        issue
    )

    if len(quick_facts) != 4:
        raise RepositoryValidationError(
            f"{issue_id} must contain exactly "
            "four Quick Facts."
        )

    publication_date_text = _display_date(
        publication_date
    )

    next_day_text = _display_date(
     _next_production_date(
        publication_date
     )
    )
    timestamp = _timestamp()

    normalised = {
        "repository_version": "2.0",
        "issue_id": issue_id,
        "publication_date": publication_date_text,
        "sequence_number": sequence_number,
        "title": title,
        "slug": _slugify(title),
        "gs_paper": _normalise_text(
            _get_first_available(
                issue,
                "gs_paper",
                "gs",
                default="",
            )
        ),
        "category": _normalise_text(
            _get_first_available(
                issue,
                "category",
                "subject",
                default="",
            )
        ),
        "rating": _normalise_text(
            _get_first_available(
                issue,
                "rating",
                "upsc_rating",
                default="",
            )
        ),
        "source": {
            "newspaper": _normalise_text(
                _get_first_available(
                    issue,
                    "newspaper",
                    "source_newspaper",
                    default="",
                )
            ),
            "editorial_title": _normalise_text(
                _get_first_available(
                    issue,
                    "editorial_title",
                    "source_editorial",
                    default="",
                )
            ),
            "source_file": _normalise_text(
                _get_first_available(
                    issue,
                    "source_file",
                    default="",
                )
            ),
        },
        "pdf_content": {
            "current_context": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "current_context",
                    "context",
                    default="",
                )
            ),
            "why_it_matters_for_upsc": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "why_it_matters_for_upsc",
                    "why_it_matters",
                    "upsc_relevance",
                    default="",
                )
            ),
            "core_concept": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "core_concept",
                    "concept",
                    default="",
                )
            ),
            "challenges": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "challenges",
                    default="",
                )
            ),
            "way_forward": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "way_forward",
                    "solutions",
                    default="",
                )
            ),
            "what_upsc_asks": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "what_upsc_asks",
                    "upsc_asks",
                    default="",
                )
            ),
            "quick_facts": quick_facts,
            "key_takeaway": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "key_takeaway",
                    "takeaway",
                    default="",
                )
            ),
        },
        "recall": {
            "questions": recall_questions,
            "explained_on": publication_date_text,
            "scheduled_for_pdf_on": next_day_text,
            "status": "scheduled",
        },
        "youtube": {
            "short_script": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "youtube_short_script",
                    "youtube_script",
                    "short_script",
                    default="",
                )
            ),
            "anchors": _extract_anchors(issue),
            "status": "prepared",
        },
        "telegram": {
            "card_heading": _normalise_text(
                _get_first_available(
                    issue,
                    "telegram_card_heading",
                    "telegram_heading",
                    default=title,
                )
            ),
            "recall_questions": recall_questions,
            "anchors": _extract_anchors(issue),
            "caption": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "telegram_caption",
                    default="",
                )
            ),
            "status": "prepared",
        },
        "website": {
            "heading": _normalise_multiline_text(
                _get_first_available(
                    issue,
                    "website_heading",
                    default=title,
                )
            ),
            "pdf_visible": True,
            "status": "prepared",
        },
        "usage": {
            "pdf": False,
            "youtube": False,
            "telegram": False,
            "website": False,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    validate_normalised_issue(
        normalised
    )

    return normalised


def validate_normalised_issue(
    issue: dict[str, Any],
) -> None:
    """Validate the normalised issue structure."""

    required_fields = (
        "issue_id",
        "publication_date",
        "title",
        "pdf_content",
        "recall",
        "youtube",
        "telegram",
        "website",
        "usage",
    )

    missing = [
        field
        for field in required_fields
        if field not in issue
    ]

    if missing:
        raise RepositoryValidationError(
            f"{issue.get('issue_id', 'Issue')} "
            f"is missing: {', '.join(missing)}"
        )

    if len(
        issue["recall"].get(
            "questions",
            [],
        )
    ) != 2:
        raise RepositoryValidationError(
            f"{issue['issue_id']} must contain "
            "two recall questions."
        )

    if len(
        issue["pdf_content"].get(
            "quick_facts",
            [],
        )
    ) != 4:
        raise RepositoryValidationError(
            f"{issue['issue_id']} must contain "
            "four Quick Facts."
        )


# ============================================================
# DAILY DATASET BUILDERS
# ============================================================

def build_pdf_dataset(
    publication_date: date,
    issues: list[dict[str, Any]],
    previous_day_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build the final PDF source dataset using the latest
    pending recall sets.
    """

    recall_source_dates = sorted(
        {
            str(
                recall.get(
                    "explained_on",
                    "",
                )
            ).strip()
            for recall in previous_day_questions
            if str(
                recall.get(
                    "explained_on",
                    "",
                )
            ).strip()
        },
        key=_parse_date,
        reverse=True,
    )

    return {
        "repository_version": "2.0",
        "publication_date": _display_date(
            publication_date
        ),
        "daily_code": _document_code(
            publication_date
        ),
        "recall_questions_from": (
            ", ".join(recall_source_dates)
            if recall_source_dates
            else None
        ),
        "recall_questions": previous_day_questions,
        "issues": [
            {
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "gs_paper": issue["gs_paper"],
                "category": issue["category"],
                "rating": issue["rating"],
                **deepcopy(
                    issue["pdf_content"]
                ),
            }
            for issue in issues
        ],
        "generated_at": _timestamp(),
    }


def build_youtube_dataset(
    publication_date: date,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the YouTube Shorts dataset."""

    return {
        "repository_version": "2.0",
        "publication_date": _display_date(
            publication_date
        ),
        "shorts": [
            {
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "script": (
                    issue["youtube"]["short_script"]
                ),
                "anchors": (
                    issue["youtube"]["anchors"]
                ),
                "recall_questions_explained": (
                    issue["recall"]["questions"]
                ),
            }
            for issue in issues
        ],
        "generated_at": _timestamp(),
    }


def build_telegram_dataset(
    publication_date: date,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build Telegram card data."""

    return {
        "repository_version": "2.0",
        "publication_date": _display_date(
            publication_date
        ),
        "cards": [
            {
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "card_heading": (
                    issue["telegram"]["card_heading"]
                ),
                "recall_questions": (
                    issue["telegram"]["recall_questions"]
                ),
                "anchors": (
                    issue["telegram"]["anchors"]
                ),
                "caption": (
                    issue["telegram"]["caption"]
                ),
            }
            for issue in issues
        ],
        "generated_at": _timestamp(),
    }


def create_daily_website_heading(
    issues: list[dict[str, Any]],
) -> str:
    """Create a fallback combined website heading."""

    titles = [
        issue["title"]
        for issue in issues
        if issue.get("title")
    ]

    if not titles:
        return "Today’s important UPSC issues"

    if len(titles) == 1:
        return titles[0]

    if len(titles) == 2:
        return (
            f"{titles[0]} and {titles[1]}"
        )

    return (
        ", ".join(titles[:-1])
        + f", and {titles[-1]}"
    )


def build_website_dataset(
    publication_date: date,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build website publication content."""

    return {
        "repository_version": "2.0",
        "publication_date": _display_date(
            publication_date
        ),
        "daily_heading": (
            create_daily_website_heading(
                issues
            )
        ),
        "issues": [
            {
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "heading": (
                    issue["website"]["heading"]
                ),
            }
            for issue in issues
        ],
        "pdf_upload_required": True,
        "generated_at": _timestamp(),
    }


def build_recall_schedule(
    publication_date: date,
    previous_day_questions: list[dict[str, Any]],
    current_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build latest-pending, present-day and future recall tracking.

    The previous_day key is retained for compatibility, but
    its questions are the latest pending recalls selected for
    today's PDF.
    """

    next_production_date = _next_production_date(
        publication_date
    )

    recall_source_dates = sorted(
        {
            str(
                recall.get(
                    "explained_on",
                    "",
                )
            ).strip()
            for recall in previous_day_questions
            if str(
                recall.get(
                    "explained_on",
                    "",
                )
            ).strip()
        },
        key=_parse_date,
        reverse=True,
    )

    recall_source_text = (
        ", ".join(recall_source_dates)
        if recall_source_dates
        else None
    )

    present_questions = [
        {
            "issue_id": issue["issue_id"],
            "issue_title": issue["title"],
            "questions": deepcopy(
                issue["recall"]["questions"]
            ),
            "anchors": deepcopy(
                issue.get(
                    "youtube",
                    {},
                ).get(
                    "anchors",
                    [],
                )
            ),
            "youtube_explanation_date": (
                _display_date(
                    publication_date
                )
            ),
        }
        for issue in current_issues
    ]

    return {
        "repository_version": "2.0",
        "publication_date": _display_date(
            publication_date
        ),
        "previous_day": {
            "date": recall_source_text,
            "purpose": (
                "Latest pending recall sets used in today's PDF"
            ),
            "questions": previous_day_questions,
        },
        "present_day": {
            "date": _display_date(
                publication_date
            ),
            "purpose": (
                "Explained through today's YouTube Shorts "
                "and Telegram cards"
            ),
            "questions": present_questions,
        },
        "next_day": {
            "date": _display_date(
                next_production_date
            ),
            "purpose": (
                "Today's recalls become eligible from the "
                "next production day and remain pending until used"
            ),
            "questions": present_questions,
        },
        "generated_at": _timestamp(),
    }
# ============================================================
# RECALL LOOKUP
# ============================================================

def get_latest_pending_recall_questions(
    publication_date: date,
    required_count: int,
) -> list[dict[str, Any]]:
    """
    Return the latest pending recall sets for today's PDF.

    One issue produces one recall set. The number returned
    should match today's issue count whenever enough pending
    recalls exist.

    Recalls generated on the current publication date are
    excluded because they belong to today's YouTube and
    Telegram outputs, not today's PDF recall section.
    """

    if required_count <= 0:
        return []

    recall_index = _read_json(
        RECALL_INDEX_FILE,
        _default_recall_index(),
    )

    recalls = recall_index.setdefault(
        "recalls",
        {},
    )

    target_date = publication_date

    eligible_recalls: list[dict[str, Any]] = []

    for recall in recalls.values():
        if not isinstance(recall, dict):
            continue

        if recall.get("status") != "pending":
            continue

        explained_on = str(
            recall.get(
                "explained_on",
                "",
            )
        ).strip()

        eligible_on = str(
            recall.get(
                "eligible_for_pdf_on",
                recall.get(
                    "scheduled_for_pdf_on",
                    "",
                ),
            )
        ).strip()

        if not explained_on:
            continue

        try:
            explained_date = _parse_date(
                explained_on
            )
        except RepositoryError:
            continue

        if explained_date >= target_date:
            continue

        if eligible_on:
            try:
                eligible_date = _parse_date(
                    eligible_on
                )
            except RepositoryError:
                continue

            if eligible_date > target_date:
                continue

        eligible_recalls.append(
            deepcopy(recall)
        )

    eligible_recalls.sort(
        key=lambda recall: (
            _parse_date(
                recall["explained_on"]
            ),
            int(
                recall.get(
                    "recall_number",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    return eligible_recalls[
        :required_count
    ]


# ============================================================
# ISSUE RECORD STORAGE
# ============================================================

def get_issue_record_path(
    issue: dict[str, Any],
) -> Path:
    """Return the permanent issue-record path."""

    issue_date = _parse_date(
        issue["publication_date"]
    )

    issue_folder = (
        ISSUES_ROOT
        / issue_date.strftime("%Y")
        / issue_date.strftime("%m")
    )

    filename = (
        f"{issue['issue_id']}_"
        f"{issue['slug']}.json"
    )

    return issue_folder / filename


def save_issue_record(
    issue: dict[str, Any],
    overwrite: bool = False,
) -> Path:
    """Save one permanent issue record."""

    path = get_issue_record_path(
        issue
    )

    if path.exists() and not overwrite:
        existing = _read_json(path)

        if existing == issue:
            return path

        raise DuplicateIssueError(
            f"Issue record already exists:\n{path}"
        )

    _write_json(
        path,
        issue,
    )

    return path


# ============================================================
# INDEX UPDATES
# ============================================================

def update_issue_index(
    issues: list[dict[str, Any]],
) -> None:
    """Update the central issue index."""

    index = _read_json(
        ISSUE_INDEX_FILE,
        _default_issue_index(),
    )

    records = index.setdefault(
        "issues",
        {},
    )

    for issue in issues:
        records[issue["issue_id"]] = {
            "issue_id": issue["issue_id"],
            "title": issue["title"],
            "publication_date": (
                issue["publication_date"]
            ),
            "gs_paper": issue["gs_paper"],
            "category": issue["category"],
            "rating": issue["rating"],
            "slug": issue["slug"],
            "record_path": str(
                get_issue_record_path(
                    issue
                ).relative_to(
                    PROJECT_ROOT
                )
            ),
            "recall_pdf_date": (
                issue["recall"][
                    "scheduled_for_pdf_on"
                ]
            ),
            "usage": deepcopy(
                issue["usage"]
            ),
            "updated_at": _timestamp(),
        }

    index["total_issues"] = len(
        records
    )

    index["last_updated"] = _timestamp()

    _write_json(
        ISSUE_INDEX_FILE,
        index,
    )


def update_recall_index(
    publication_date: date,
    issues: list[dict[str, Any]],
) -> None:
    """
    Add today's issue recalls to the pending recall queue.

    One issue creates one numbered recall set. The recall
    becomes eligible on the next production day and remains
    pending until selected for a future PDF.
    """

    index = _read_json(
        RECALL_INDEX_FILE,
        _default_recall_index(),
    )

    dates = index.setdefault(
        "dates",
        {},
    )

    questions_index = index.setdefault(
        "questions",
        {},
    )

    recalls_index = index.setdefault(
        "recalls",
        {},
    )

    next_recall_number = int(
        index.get(
            "next_recall_number",
            1,
        )
    )

    publication_text = _display_date(
        publication_date
    )

    eligible_date = _next_production_date(
        publication_date
    )

    eligible_text = _display_date(
        eligible_date
    )

    entries: list[dict[str, Any]] = []

    for issue in issues:
        issue_id = issue["issue_id"]

        existing_recall = next(
            (
                recall
                for recall in recalls_index.values()
                if isinstance(recall, dict)
                and recall.get("issue_id") == issue_id
            ),
            None,
        )

        if existing_recall:
            recall_id = str(
                existing_recall["recall_id"]
            )

            recall_number = int(
                existing_recall.get(
                    "recall_number",
                    0,
                )
            )

            recall_status = str(
                existing_recall.get(
                    "status",
                    "pending",
                )
            )

            used_in_pdf_on = (
                existing_recall.get(
                    "used_in_pdf_on"
                )
            )
        else:
            recall_number = next_recall_number
            recall_id = (
                f"R-{recall_number:06d}"
            )
            recall_status = "pending"
            used_in_pdf_on = None
            next_recall_number += 1

        recall_entry = {
            "recall_id": recall_id,
            "recall_number": recall_number,
            "issue_id": issue_id,
            "issue_title": issue["title"],
            "questions": deepcopy(
                issue["recall"]["questions"]
            ),
            "anchors": deepcopy(
                issue.get(
                    "youtube",
                    {},
                ).get(
                    "anchors",
                    [],
                )
            ),
            "explained_on": publication_text,
            "eligible_for_pdf_on": eligible_text,
            "scheduled_for_pdf_on": eligible_text,
            "used_in_pdf_on": used_in_pdf_on,
            "status": recall_status,
        }

        recalls_index[recall_id] = deepcopy(
            recall_entry
        )

        entries.append(
            deepcopy(recall_entry)
        )

        for number, question in enumerate(
            issue["recall"]["questions"],
            start=1,
        ):
            question_id = (
                f"{issue_id}-RQ{number}"
            )

            existing_question = questions_index.get(
                question_id,
                {},
            )

            questions_index[question_id] = {
                "question_id": question_id,
                "recall_id": recall_id,
                "recall_number": recall_number,
                "issue_id": issue_id,
                "issue_title": issue["title"],
                "question_number": number,
                "question": question,
                "explained_on": publication_text,
                "eligible_for_pdf_on": eligible_text,
                "scheduled_for_pdf_on": eligible_text,
                "used_in_pdf_on": (
                    existing_question.get(
                        "used_in_pdf_on"
                    )
                ),
                "status": existing_question.get(
                    "status",
                    "pending",
                ),
            }

    dates.setdefault(
        publication_text,
        {},
    )["explained_on_youtube"] = deepcopy(
        entries
    )

    dates.setdefault(
        eligible_text,
        {},
    )["eligible_for_pdf"] = deepcopy(
        entries
    )

    # Retained for compatibility with existing readers.
    dates.setdefault(
        eligible_text,
        {},
    )["scheduled_for_pdf"] = deepcopy(
        entries
    )

    index["next_recall_number"] = (
        next_recall_number
    )

    index["last_updated"] = _timestamp()

    _write_json(
        RECALL_INDEX_FILE,
        index,
    )

def mark_recall_questions_used(
    publication_date: date,
    selected_recalls: list[dict[str, Any]],
) -> None:
    """
    Mark only the recall sets selected for today's PDF as used.

    Any pending recalls not selected remain available for a
    future production day.
    """

    if not selected_recalls:
        return

    index = _read_json(
        RECALL_INDEX_FILE,
        _default_recall_index(),
    )

    recalls_index = index.setdefault(
        "recalls",
        {},
    )

    questions_index = index.setdefault(
        "questions",
        {},
    )

    publication_text = _display_date(
        publication_date
    )

    used_entries: list[dict[str, Any]] = []

    for selected in selected_recalls:
        recall_id = str(
            selected.get(
                "recall_id",
                "",
            )
        ).strip()

        issue_id = str(
            selected.get(
                "issue_id",
                "",
            )
        ).strip()

        if (
            recall_id
            and recall_id in recalls_index
        ):
            recalls_index[
                recall_id
            ]["used_in_pdf_on"] = publication_text

            recalls_index[
                recall_id
            ]["status"] = "used"

            used_entry = deepcopy(
                recalls_index[recall_id]
            )
        else:
            used_entry = deepcopy(
                selected
            )

            used_entry[
                "used_in_pdf_on"
            ] = publication_text

            used_entry["status"] = "used"

        used_entries.append(
            used_entry
        )

        for number in (1, 2):
            question_id = (
                f"{issue_id}-RQ{number}"
            )

            if question_id in questions_index:
                questions_index[
                    question_id
                ]["used_in_pdf_on"] = publication_text

                questions_index[
                    question_id
                ]["status"] = "used"

    index.setdefault(
        "dates",
        {},
    ).setdefault(
        publication_text,
        {},
    )["used_in_pdf"] = deepcopy(
        used_entries
    )

    index["last_updated"] = _timestamp()

    _write_json(
        RECALL_INDEX_FILE,
        index,
    )


def update_usage_index(
    issues: list[dict[str, Any]],
) -> None:
    """Create or update platform usage records."""

    index = _read_json(
        USAGE_INDEX_FILE,
        _default_usage_index(),
    )

    records = index.setdefault(
        "issues",
        {},
    )

    for issue in issues:
        existing = records.get(
            issue["issue_id"],
            {},
        )

        records[issue["issue_id"]] = {
            "issue_id": issue["issue_id"],
            "title": issue["title"],
            "publication_date": (
                issue["publication_date"]
            ),
            "pdf": existing.get(
                "pdf",
                {
                    "prepared": True,
                    "published": False,
                    "published_on": None,
                },
            ),
            "youtube": existing.get(
                "youtube",
                {
                    "prepared": True,
                    "published": False,
                    "published_on": None,
                },
            ),
            "telegram": existing.get(
                "telegram",
                {
                    "prepared": True,
                    "published": False,
                    "published_on": None,
                },
            ),
            "website": existing.get(
                "website",
                {
                    "prepared": True,
                    "published": False,
                    "published_on": None,
                },
            ),
            "updated_at": _timestamp(),
        }

    index["last_updated"] = _timestamp()

    _write_json(
        USAGE_INDEX_FILE,
        index,
    )


# ============================================================
# SOURCE EDITORIAL ARCHIVE
# ============================================================

def archive_source_editorials(
    publication_date: date,
    source_files: Iterable[str | Path] | None,
) -> list[Path]:
    """Archive source editorial files by DD-MM-YY."""

    if not source_files:
        return []

    destination_folder = (
        SOURCE_EDITORIALS_ROOT
        / _display_date(
            publication_date
        )
    )

    destination_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    archived: list[Path] = []

    for source_file in source_files:
        source_path = (
            Path(source_file)
            .expanduser()
            .resolve()
        )

        if not source_path.exists():
            raise RepositoryError(
                "Source editorial file does not exist:\n"
                f"{source_path}"
            )

        destination_path = (
            destination_folder
            / source_path.name
        )

        if source_path != destination_path:
            shutil.copy2(
                source_path,
                destination_path,
            )

        archived.append(
            destination_path
        )

    return archived


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_repository_package(
    publication_date: str | date | datetime,
    selected_issues: list[dict[str, Any]],
    source_files: Iterable[str | Path] | None = None,
    overwrite_daily: bool = False,
) -> RepositoryResult:
    """Generate the complete daily repository package."""

    ensure_repository_structure()

    parsed_date = _parse_date(
        publication_date
    )

    display_date = _display_date(
        parsed_date
    )

    if not isinstance(
        selected_issues,
        list,
    ):
        raise RepositoryValidationError(
            "selected_issues must be a list."
        )

    if not selected_issues:
        raise RepositoryValidationError(
            "At least one selected issue is required."
        )

    normalised_issues = [
        normalise_issue(
            issue=issue,
            publication_date=parsed_date,
            sequence_number=index,
        )
        for index, issue in enumerate(
            selected_issues,
            start=1,
        )
    ]

    issue_ids = [
        issue["issue_id"]
        for issue in normalised_issues
    ]

    if len(issue_ids) != len(
        set(issue_ids)
    ):
        raise DuplicateIssueError(
            "Duplicate issue IDs found in the input."
        )

    daily_folder = (
        DAILY_ROOT
        / display_date
    )

    if daily_folder.exists() and not overwrite_daily:
        if (
            daily_folder
            / DAILY_MANIFEST_FILE
        ).exists():
            raise RepositoryError(
                "A repository package already exists "
                f"for {display_date}.\n"
                "Use overwrite_daily=True only when "
                "intentionally rebuilding it."
            )

    daily_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    previous_day_questions = (
    get_latest_pending_recall_questions(
        publication_date=parsed_date,
        required_count=len(
            normalised_issues
        ),
      )
    )

    selected_dataset = {
        "repository_version": "2.0",
        "publication_date": display_date,
        "issue_count": len(
            normalised_issues
        ),
        "issues": normalised_issues,
        "generated_at": _timestamp(),
    }

    daily_files = {
        SELECTED_ISSUES_FILE: (
            selected_dataset
        ),
        PDF_DATASET_FILE: build_pdf_dataset(
            publication_date=parsed_date,
            issues=normalised_issues,
            previous_day_questions=(
                previous_day_questions
            ),
        ),
        YOUTUBE_SHORTS_FILE: (
            build_youtube_dataset(
                publication_date=parsed_date,
                issues=normalised_issues,
            )
        ),
        TELEGRAM_CARDS_FILE: (
            build_telegram_dataset(
                publication_date=parsed_date,
                issues=normalised_issues,
            )
        ),
        WEBSITE_CONTENT_FILE: (
            build_website_dataset(
                publication_date=parsed_date,
                issues=normalised_issues,
            )
        ),
        RECALL_SCHEDULE_FILE: (
            build_recall_schedule(
                publication_date=parsed_date,
                previous_day_questions=(
                    previous_day_questions
                ),
                current_issues=(
                    normalised_issues
                ),
            )
        ),
    }

    created_files: list[Path] = []

    for filename, content in daily_files.items():
        path = (
            daily_folder
            / filename
        )

        _write_json(
            path,
            content,
        )

        created_files.append(path)

    for issue in normalised_issues:
        issue_path = save_issue_record(
            issue,
            overwrite=overwrite_daily,
        )

        created_files.append(
            issue_path
        )

    archived_editorials = (
        archive_source_editorials(
            publication_date=parsed_date,
            source_files=source_files,
        )
    )

    created_files.extend(
        archived_editorials
    )

    update_issue_index(
        normalised_issues
    )

    update_usage_index(
        normalised_issues
    )

    mark_recall_questions_used(
        publication_date=parsed_date,
        previous_day_questions=(
            previous_day_questions
        ),
    )

    update_recall_index(
        publication_date=parsed_date,
        issues=normalised_issues,
    )

    manifest = {
        "repository_version": "2.0",
        "publication_date": display_date,
        "daily_code": _document_code(
            parsed_date
        ),
        "issue_count": len(
            normalised_issues
        ),
        "issue_ids": issue_ids,
        "previous_day_recall_count": len(
            previous_day_questions
        ),
        "source_editorials": [
            str(
                path.relative_to(
                    PROJECT_ROOT
                )
            )
            for path in archived_editorials
        ],
        "files": [
            str(
                path.relative_to(
                    PROJECT_ROOT
                )
            )
            for path in created_files
        ],
        "status": {
            "repository_created": True,
            "pdf_dataset_prepared": True,
            "youtube_dataset_prepared": True,
            "telegram_dataset_prepared": True,
            "website_dataset_prepared": True,
            "recall_schedule_prepared": True,
        },
        "generated_at": _timestamp(),
    }

    manifest_path = (
        daily_folder
        / DAILY_MANIFEST_FILE
    )

    _write_json(
        manifest_path,
        manifest,
    )

    created_files.append(
        manifest_path
    )

    return RepositoryResult(
        publication_date=display_date,
        daily_folder=daily_folder,
        issue_count=len(
            normalised_issues
        ),
        issue_ids=tuple(
            issue_ids
        ),
        created_files=tuple(
            created_files
        ),
    )


# ============================================================
# PUBLICATION STATUS
# ============================================================

def mark_platform_published(
    issue_ids: str | Iterable[str],
    platform: str,
    published_on: (
        str
        | date
        | datetime
        | None
    ) = None,
) -> None:
    """Mark one or more issues as published."""

    supported_platforms = {
        "pdf",
        "youtube",
        "telegram",
        "website",
    }

    platform = _normalise_text(
        platform
    ).lower()

    if platform not in supported_platforms:
        raise RepositoryValidationError(
            f"Unsupported platform: {platform}"
        )

    if isinstance(issue_ids, str):
        issue_ids = [issue_ids]
    else:
        issue_ids = list(issue_ids)

    publication_date = (
        _parse_date(published_on)
        if published_on is not None
        else date.today()
    )

    publication_text = _display_date(
        publication_date
    )

    usage_index = _read_json(
        USAGE_INDEX_FILE,
        _default_usage_index(),
    )

    issue_index = _read_json(
        ISSUE_INDEX_FILE,
        _default_issue_index(),
    )

    for issue_id in issue_ids:
        if issue_id not in usage_index.get(
            "issues",
            {},
        ):
            raise RepositoryError(
                "Issue not found in usage index:\n"
                f"{issue_id}"
            )

        platform_record = (
            usage_index["issues"][
                issue_id
            ][platform]
        )

        platform_record["prepared"] = True
        platform_record["published"] = True
        platform_record[
            "published_on"
        ] = publication_text

        usage_index["issues"][
            issue_id
        ]["updated_at"] = _timestamp()

        if issue_id in issue_index.get(
            "issues",
            {},
        ):
            issue_index["issues"][
                issue_id
            ]["usage"][platform] = True

            issue_index["issues"][
                issue_id
            ]["updated_at"] = _timestamp()

    usage_index["last_updated"] = _timestamp()
    issue_index["last_updated"] = _timestamp()

    _write_json(
        USAGE_INDEX_FILE,
        usage_index,
    )

    _write_json(
        ISSUE_INDEX_FILE,
        issue_index,
    )


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Run a one-issue repository test."""

    sample_issues = [
        {
            "title": "India's Semiconductor Ecosystem",
            "gs_paper": "GS III",
            "category": "Economy | Technology",
            "rating": "4.9/5",
            "current_context": (
                "India is expanding semiconductor "
                "manufacturing, design and packaging."
            ),
            "why_it_matters_for_upsc": (
                "The issue connects industrial policy, "
                "national security and global supply chains."
            ),
            "core_concept": (
                "A semiconductor ecosystem includes design, "
                "fabrication, packaging, testing and skills."
            ),
            "challenges": (
                "High capital requirements, imported "
                "technology and limited expertise are barriers."
            ),
            "way_forward": (
                "India must strengthen research, skills, "
                "domestic design and supply-chain resilience."
            ),
            "quick_facts": [
                "Semiconductors are essential electronic components.",
                "Chip fabrication requires specialised facilities.",
                "The value chain includes design, fabrication and testing.",
                "Advanced plants require large capital investment.",
            ],
            "what_upsc_asks": (
                "Examine the importance of semiconductor "
                "manufacturing for technological self-reliance."
            ),
            "key_takeaway": (
                "India needs a complete semiconductor ecosystem "
                "rather than isolated fabrication investments."
            ),
            "recall_questions": [
                "What constitutes a semiconductor ecosystem?",
                "What limits India's domestic chip capacity?",
            ],
            "youtube_short_script": (
                "India needs an integrated chip ecosystem "
                "covering design, manufacturing and skills."
            ),
            "anchors": [
                "Chip design",
                "Fabrication plant",
                "Supply-chain resilience",
            ],
            "telegram_caption": (
                "Recall today's semiconductor issue."
            ),
            "website_heading": (
                "India's semiconductor push and the challenge "
                "of building a complete domestic ecosystem"
            ),
        }
    ]

    result = generate_repository_package(
        publication_date=date.today(),
        selected_issues=sample_issues,
        overwrite_daily=True,
    )

    result.display()


if __name__ == "__main__":
    _development_test()