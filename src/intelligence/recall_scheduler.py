"""
============================================================
TODAY'S UPSC ISSUES
SPACED RECALL SCHEDULER
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Creates and manages spaced-revision schedules for repository
issues.

DEFAULT REVIEW INTERVALS

Day 1
Day 3
Day 7
Day 15
Day 30

The scheduler:

1. Reads permanent issue records.
2. Creates future recall dates.
3. Stores one schedule per issue.
4. Returns recall sets due on a selected date.
5. Tracks pending and completed reviews.
6. Avoids duplicate schedule entries.
7. Keeps the Version 2.0 next-day recall workflow compatible.
============================================================
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT MODULES
# ============================================================

from src.intelligence.repository_search import (  # noqa: E402
    RepositorySearchError,
    list_issue_summaries,
    load_all_issue_records,
    load_issue_record,
)


# ============================================================
# PROJECT PATHS
# ============================================================

REPOSITORY_ROOT = PROJECT_ROOT / "Repository"
INDEX_ROOT = REPOSITORY_ROOT / "index"

SPACED_RECALL_INDEX_FILE = (
    INDEX_ROOT
    / "spaced_recall_index.json"
)


# ============================================================
# DEFAULT REVIEW INTERVALS
# ============================================================

DEFAULT_REVIEW_INTERVALS = (
    1,
    3,
    7,
    15,
    30,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class RecallSchedulerError(Exception):
    """Base exception for recall-scheduler errors."""


class InvalidRecallIssueError(RecallSchedulerError):
    """Raised when an issue cannot be scheduled."""


class RecallIndexError(RecallSchedulerError):
    """Raised when the recall index is invalid."""


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass(frozen=True, slots=True)
class RecallReview:
    """One scheduled recall review."""

    issue_id: str
    issue_title: str
    publication_date: str
    interval_day: int
    review_date: str
    questions: tuple[str, str]
    status: str
    completed_on: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert the review into a dictionary."""

        return {
            "issue_id": self.issue_id,
            "issue_title": self.issue_title,
            "publication_date": self.publication_date,
            "interval_day": self.interval_day,
            "review_date": self.review_date,
            "questions": list(self.questions),
            "status": self.status,
            "completed_on": self.completed_on,
        }


@dataclass(frozen=True, slots=True)
class RecallScheduleResult:
    """Complete spaced-recall schedule for one issue."""

    issue_id: str
    issue_title: str
    publication_date: str
    reviews: tuple[RecallReview, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the schedule into a dictionary."""

        return {
            "issue_id": self.issue_id,
            "issue_title": self.issue_title,
            "publication_date": self.publication_date,
            "reviews": [
                review.to_dict()
                for review in self.reviews
            ],
        }


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

    raise RecallSchedulerError(
        "Unsupported date format.\n"
        "Examples:\n"
        "20-07-26\n"
        "2026-07-20\n"
        "20-07-2026"
    )


def _display_date(value: date) -> str:
    """Return the repository date format."""

    return value.strftime("%d-%m-%y")


def _timestamp() -> str:
    """Return a timezone-aware timestamp."""

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


# ============================================================
# JSON HELPERS
# ============================================================

def _default_index() -> dict[str, Any]:
    """Return the default spaced-recall index."""

    return {
        "recall_version": "2.1",
        "intervals": list(
            DEFAULT_REVIEW_INTERVALS
        ),
        "last_updated": None,
        "issues": {},
        "dates": {},
    }


def _read_json(
    path: Path,
    default: Any | None = None,
) -> Any:
    """Read a JSON file or return the supplied default."""

    if not path.exists():
        return deepcopy(default)

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RecallIndexError(
            f"Invalid JSON file:\n{path}\n"
            f"Line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error


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


def ensure_recall_index() -> None:
    """Create the spaced-recall index when missing."""

    INDEX_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not SPACED_RECALL_INDEX_FILE.exists():
        _write_json(
            SPACED_RECALL_INDEX_FILE,
            _default_index(),
        )


def load_recall_index() -> dict[str, Any]:
    """Load and validate the spaced-recall index."""

    ensure_recall_index()

    index = _read_json(
        SPACED_RECALL_INDEX_FILE,
        _default_index(),
    )

    if not isinstance(index, dict):
        raise RecallIndexError(
            "spaced_recall_index.json must contain "
            "a JSON object."
        )

    if not isinstance(
        index.get("issues"),
        dict,
    ):
        raise RecallIndexError(
            'spaced_recall_index.json must contain '
            'an "issues" object.'
        )

    if not isinstance(
        index.get("dates"),
        dict,
    ):
        raise RecallIndexError(
            'spaced_recall_index.json must contain '
            'a "dates" object.'
        )

    return index


# ============================================================
# ISSUE VALIDATION
# ============================================================

def _extract_recall_questions(
    issue: dict[str, Any],
) -> tuple[str, str]:
    """Extract exactly two recall questions."""

    recall = issue.get(
        "recall",
        {},
    )

    questions: Any = []

    if isinstance(recall, dict):
        questions = recall.get(
            "questions",
            [],
        )

    if not isinstance(
        questions,
        (list, tuple),
    ):
        raise InvalidRecallIssueError(
            "Recall questions must be a list or tuple."
        )

    if len(questions) != 2:
        raise InvalidRecallIssueError(
            "Each issue must contain exactly "
            "two recall questions."
        )

    question_1 = str(
        questions[0]
    ).strip()

    question_2 = str(
        questions[1]
    ).strip()

    if not question_1 or not question_2:
        raise InvalidRecallIssueError(
            "Recall questions cannot be empty."
        )

    return (
        question_1,
        question_2,
    )


def _validate_issue(
    issue: dict[str, Any],
) -> None:
    """Validate one issue for recall scheduling."""

    if not isinstance(issue, dict):
        raise InvalidRecallIssueError(
            "Issue must be a dictionary."
        )

    issue_id = str(
        issue.get(
            "issue_id",
            "",
        )
    ).strip()

    title = str(
        issue.get(
            "title",
            "",
        )
    ).strip()

    publication_date = str(
        issue.get(
            "publication_date",
            "",
        )
    ).strip()

    if not issue_id:
        raise InvalidRecallIssueError(
            "Issue does not contain issue_id."
        )

    if not title:
        raise InvalidRecallIssueError(
            "Issue does not contain title."
        )

    if not publication_date:
        raise InvalidRecallIssueError(
            "Issue does not contain publication_date."
        )

    _parse_date(
        publication_date
    )

    _extract_recall_questions(
        issue
    )


# ============================================================
# REVIEW CREATION
# ============================================================

def create_issue_schedule(
    issue: dict[str, Any],
    intervals: Iterable[int] = DEFAULT_REVIEW_INTERVALS,
) -> RecallScheduleResult:
    """Create the spaced-recall schedule for one issue."""

    _validate_issue(
        issue
    )

    issue_id = str(
        issue["issue_id"]
    )

    issue_title = str(
        issue["title"]
    )

    publication_date = _parse_date(
        issue["publication_date"]
    )

    questions = _extract_recall_questions(
        issue
    )

    cleaned_intervals = sorted(
        {
            int(interval)
            for interval in intervals
        }
    )

    if not cleaned_intervals:
        raise RecallSchedulerError(
            "At least one recall interval is required."
        )

    if any(
        interval < 1
        for interval in cleaned_intervals
    ):
        raise RecallSchedulerError(
            "Recall intervals must be positive integers."
        )

    reviews: list[RecallReview] = []

    for interval in cleaned_intervals:
        review_date = (
            publication_date
            + timedelta(days=interval)
        )

        reviews.append(
            RecallReview(
                issue_id=issue_id,
                issue_title=issue_title,
                publication_date=_display_date(
                    publication_date
                ),
                interval_day=interval,
                review_date=_display_date(
                    review_date
                ),
                questions=questions,
                status="pending",
                completed_on=None,
            )
        )

    return RecallScheduleResult(
        issue_id=issue_id,
        issue_title=issue_title,
        publication_date=_display_date(
            publication_date
        ),
        reviews=tuple(
            reviews
        ),
    )


# ============================================================
# INDEX REGISTRATION
# ============================================================

def register_issue_schedule(
    issue: dict[str, Any],
    intervals: Iterable[int] = DEFAULT_REVIEW_INTERVALS,
    overwrite: bool = False,
) -> RecallScheduleResult:
    """Register one issue in the spaced-recall index."""

    schedule = create_issue_schedule(
        issue=issue,
        intervals=intervals,
    )

    index = load_recall_index()

    issue_records = index.setdefault(
        "issues",
        {},
    )

    date_records = index.setdefault(
        "dates",
        {},
    )

    if (
        schedule.issue_id in issue_records
        and not overwrite
    ):
        existing = issue_records[
            schedule.issue_id
        ]

        existing_reviews = existing.get(
            "reviews",
            [],
        )

        return RecallScheduleResult(
            issue_id=schedule.issue_id,
            issue_title=str(
                existing.get(
                    "issue_title",
                    schedule.issue_title,
                )
            ),
            publication_date=str(
                existing.get(
                    "publication_date",
                    schedule.publication_date,
                )
            ),
            reviews=tuple(
                RecallReview(
                    issue_id=str(
                        review.get(
                            "issue_id",
                            schedule.issue_id,
                        )
                    ),
                    issue_title=str(
                        review.get(
                            "issue_title",
                            schedule.issue_title,
                        )
                    ),
                    publication_date=str(
                        review.get(
                            "publication_date",
                            schedule.publication_date,
                        )
                    ),
                    interval_day=int(
                        review.get(
                            "interval_day",
                            1,
                        )
                    ),
                    review_date=str(
                        review.get(
                            "review_date",
                            "",
                        )
                    ),
                    questions=tuple(
                        review.get(
                            "questions",
                            [],
                        )
                    ),
                    status=str(
                        review.get(
                            "status",
                            "pending",
                        )
                    ),
                    completed_on=review.get(
                        "completed_on"
                    ),
                )
                for review in existing_reviews
            ),
        )

    # Remove previous date references when overwriting.
    if (
        schedule.issue_id in issue_records
        and overwrite
    ):
        for date_entry in date_records.values():
            if not isinstance(
                date_entry,
                list,
            ):
                continue

            date_entry[:] = [
                entry
                for entry in date_entry
                if entry.get(
                    "issue_id"
                ) != schedule.issue_id
            ]

    issue_record = schedule.to_dict()

    issue_records[
        schedule.issue_id
    ] = issue_record

    for review in schedule.reviews:
        date_entry = date_records.setdefault(
            review.review_date,
            [],
        )

        review_data = review.to_dict()

        already_exists = any(
            entry.get("issue_id")
            == review.issue_id
            and entry.get("interval_day")
            == review.interval_day
            for entry in date_entry
            if isinstance(entry, dict)
        )

        if not already_exists:
            date_entry.append(
                review_data
            )

    index["intervals"] = sorted(
        {
            int(interval)
            for interval in intervals
        }
    )

    index["last_updated"] = _timestamp()

    _write_json(
        SPACED_RECALL_INDEX_FILE,
        index,
    )

    return schedule


def register_issue_id(
    issue_id: str,
    intervals: Iterable[int] = DEFAULT_REVIEW_INTERVALS,
    overwrite: bool = False,
) -> RecallScheduleResult:
    """Load a repository issue and register its schedule."""

    try:
        issue = load_issue_record(
            issue_id
        )

    except RepositorySearchError as error:
        raise RecallSchedulerError(
            str(error)
        ) from error

    return register_issue_schedule(
        issue=issue,
        intervals=intervals,
        overwrite=overwrite,
    )


def register_all_repository_issues(
    intervals: Iterable[int] = DEFAULT_REVIEW_INTERVALS,
    overwrite: bool = False,
) -> list[RecallScheduleResult]:
    """Register all repository issues."""

    try:
        issues = load_all_issue_records()

    except RepositorySearchError as error:
        raise RecallSchedulerError(
            str(error)
        ) from error

    results: list[RecallScheduleResult] = []

    for issue in issues:
        results.append(
            register_issue_schedule(
                issue=issue,
                intervals=intervals,
                overwrite=overwrite,
            )
        )

    return results


# ============================================================
# DUE REVIEWS
# ============================================================

def get_reviews_due(
    review_date: str | date | datetime,
    include_completed: bool = False,
) -> list[RecallReview]:
    """Return recall reviews due on one date."""

    target_date = _display_date(
        _parse_date(
            review_date
        )
    )

    index = load_recall_index()

    raw_reviews = index.get(
        "dates",
        {},
    ).get(
        target_date,
        [],
    )

    if not isinstance(
        raw_reviews,
        list,
    ):
        raise RecallIndexError(
            f"Recall date entry must be a list: "
            f"{target_date}"
        )

    reviews: list[RecallReview] = []

    for review in raw_reviews:
        if not isinstance(
            review,
            dict,
        ):
            continue

        status = str(
            review.get(
                "status",
                "pending",
            )
        )

        if (
            status == "completed"
            and not include_completed
        ):
            continue

        questions = review.get(
            "questions",
            [],
        )

        if (
            not isinstance(
                questions,
                (list, tuple),
            )
            or len(questions) != 2
        ):
            continue

        reviews.append(
            RecallReview(
                issue_id=str(
                    review.get(
                        "issue_id",
                        "",
                    )
                ),
                issue_title=str(
                    review.get(
                        "issue_title",
                        "",
                    )
                ),
                publication_date=str(
                    review.get(
                        "publication_date",
                        "",
                    )
                ),
                interval_day=int(
                    review.get(
                        "interval_day",
                        0,
                    )
                ),
                review_date=str(
                    review.get(
                        "review_date",
                        target_date,
                    )
                ),
                questions=(
                    str(questions[0]),
                    str(questions[1]),
                ),
                status=status,
                completed_on=review.get(
                    "completed_on"
                ),
            )
        )

    return sorted(
        reviews,
        key=lambda review: (
            review.interval_day,
            review.issue_title,
            review.issue_id,
        ),
    )


# ============================================================
# COMPLETION TRACKING
# ============================================================

def mark_review_completed(
    issue_id: str,
    interval_day: int,
    completed_on: (
        str
        | date
        | datetime
        | None
    ) = None,
) -> RecallReview:
    """Mark one spaced-recall review as completed."""

    issue_id = str(
        issue_id
    ).strip()

    if not issue_id:
        raise RecallSchedulerError(
            "Issue ID cannot be empty."
        )

    interval_day = int(
        interval_day
    )

    completion_date = (
        _parse_date(completed_on)
        if completed_on is not None
        else date.today()
    )

    completion_text = _display_date(
        completion_date
    )

    index = load_recall_index()

    issue_record = index.get(
        "issues",
        {},
    ).get(
        issue_id
    )

    if not isinstance(
        issue_record,
        dict,
    ):
        raise RecallSchedulerError(
            f"Issue schedule was not found:\n"
            f"{issue_id}"
        )

    reviews = issue_record.get(
        "reviews",
        [],
    )

    target_review: dict[str, Any] | None = None

    for review in reviews:
        if (
            isinstance(review, dict)
            and int(
                review.get(
                    "interval_day",
                    -1,
                )
            ) == interval_day
        ):
            target_review = review
            break

    if target_review is None:
        raise RecallSchedulerError(
            f"Day {interval_day} review was not found "
            f"for {issue_id}."
        )

    target_review["status"] = "completed"
    target_review["completed_on"] = completion_text

    review_date = str(
        target_review.get(
            "review_date",
            "",
        )
    )

    date_entries = index.get(
        "dates",
        {},
    ).get(
        review_date,
        [],
    )

    if isinstance(
        date_entries,
        list,
    ):
        for date_entry in date_entries:
            if (
                isinstance(date_entry, dict)
                and date_entry.get("issue_id")
                == issue_id
                and int(
                    date_entry.get(
                        "interval_day",
                        -1,
                    )
                ) == interval_day
            ):
                date_entry["status"] = "completed"
                date_entry["completed_on"] = (
                    completion_text
                )

    index["last_updated"] = _timestamp()

    _write_json(
        SPACED_RECALL_INDEX_FILE,
        index,
    )

    questions = target_review.get(
        "questions",
        [],
    )

    return RecallReview(
        issue_id=issue_id,
        issue_title=str(
            target_review.get(
                "issue_title",
                issue_record.get(
                    "issue_title",
                    "",
                ),
            )
        ),
        publication_date=str(
            target_review.get(
                "publication_date",
                issue_record.get(
                    "publication_date",
                    "",
                ),
            )
        ),
        interval_day=interval_day,
        review_date=review_date,
        questions=(
            str(questions[0]),
            str(questions[1]),
        ),
        status="completed",
        completed_on=completion_text,
    )


# ============================================================
# SUMMARY HELPERS
# ============================================================

def get_pending_review_count() -> int:
    """Return the total number of pending reviews."""

    index = load_recall_index()

    count = 0

    for issue_record in index.get(
        "issues",
        {},
    ).values():
        if not isinstance(
            issue_record,
            dict,
        ):
            continue

        for review in issue_record.get(
            "reviews",
            [],
        ):
            if (
                isinstance(review, dict)
                and review.get(
                    "status"
                ) == "pending"
            ):
                count += 1

    return count


def get_overdue_reviews(
    as_of_date: (
        str
        | date
        | datetime
        | None
    ) = None,
) -> list[RecallReview]:
    """Return pending reviews scheduled before a selected date."""

    reference_date = (
        _parse_date(as_of_date)
        if as_of_date is not None
        else date.today()
    )

    index = load_recall_index()

    overdue: list[RecallReview] = []

    for date_text in index.get(
        "dates",
        {},
    ):
        scheduled_date = _parse_date(
            date_text
        )

        if scheduled_date >= reference_date:
            continue

        overdue.extend(
            get_reviews_due(
                date_text,
                include_completed=False,
            )
        )

    return sorted(
        overdue,
        key=lambda review: (
            _parse_date(
                review.review_date
            ),
            review.interval_day,
            review.issue_title,
        ),
    )


# ============================================================
# REPORTING
# ============================================================

def print_schedule(
    schedule: RecallScheduleResult,
) -> None:
    """Print one issue's spaced-recall schedule."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("SPACED RECALL SCHEDULE")
    print("=" * 72)

    print(
        f"Issue : {schedule.issue_title}"
    )

    print(
        f"ID    : {schedule.issue_id}"
    )

    print(
        f"Date  : {schedule.publication_date}"
    )

    print("-" * 72)

    for review in schedule.reviews:
        print(
            f"Day {review.interval_day:<2} "
            f"→ {review.review_date} "
            f"[{review.status.upper()}]"
        )

    print("=" * 72)


def print_due_reviews(
    review_date: str | date | datetime,
) -> None:
    """Print recalls due on one date."""

    target_date = _display_date(
        _parse_date(
            review_date
        )
    )

    reviews = get_reviews_due(
        target_date
    )

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("RECALLS DUE")
    print("=" * 72)

    print(
        f"Review date : {target_date}"
    )

    print(
        f"Recall sets : {len(reviews)}"
    )

    print("-" * 72)

    if not reviews:
        print("No pending reviews are due.")
        print("=" * 72)
        return

    for number, review in enumerate(
        reviews,
        start=1,
    ):
        print(
            f"{number}. {review.issue_title}"
        )

        print(
            f"   Issue ID : {review.issue_id}"
        )

        print(
            f"   Interval : Day {review.interval_day}"
        )

        print(
            f"   Q1       : {review.questions[0]}"
        )

        print(
            f"   Q2       : {review.questions[1]}"
        )

        print()

    print("=" * 72)


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Register and display the latest repository issue."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("SPACED RECALL SCHEDULER — VERSION 2.1")
    print("=" * 72)

    summaries = list_issue_summaries()

    if not summaries:
        print("No repository issues are available.")
        print("=" * 72)
        return

    latest_issue_id = summaries[0].issue_id

    schedule = register_issue_id(
        issue_id=latest_issue_id,
        overwrite=True,
    )

    print_schedule(
        schedule
    )

    print(
        f"Pending reviews : "
        f"{get_pending_review_count()}"
    )

    print("-" * 72)
    print("✓ Day 1 scheduling enabled")
    print("✓ Day 3 scheduling enabled")
    print("✓ Day 7 scheduling enabled")
    print("✓ Day 15 scheduling enabled")
    print("✓ Day 30 scheduling enabled")
    print("✓ Due-date lookup enabled")
    print("✓ Completion tracking enabled")
    print("=" * 72)


if __name__ == "__main__":
    _development_test()