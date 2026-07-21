"""
============================================================
TODAY'S UPSC ISSUES
PUBLICATION USAGE TRACKER
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Tracks the publication status of every issue across:

1. PDF
2. YouTube
3. Telegram
4. Website

The tracker reads and updates the existing Version 2.0
usage index.

It can:

- Show prepared and published status
- Mark a platform as published
- Return pending platforms
- Identify fully published issues
- Summarize repository-wide publication status
============================================================
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
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
INDEX_ROOT = REPOSITORY_ROOT / "index"

USAGE_INDEX_FILE = (
    INDEX_ROOT
    / "usage_index.json"
)


# ============================================================
# SUPPORTED PLATFORMS
# ============================================================

SUPPORTED_PLATFORMS = (
    "pdf",
    "youtube",
    "telegram",
    "website",
)


# ============================================================
# EXCEPTIONS
# ============================================================

class UsageTrackerError(Exception):
    """Base exception for usage-tracker errors."""


class UsageIndexError(UsageTrackerError):
    """Raised when the usage index is unavailable or invalid."""


class UsageIssueError(UsageTrackerError):
    """Raised when an issue usage record is unavailable."""


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass(frozen=True, slots=True)
class PlatformUsage:
    """Publication status for one platform."""

    platform: str
    prepared: bool
    published: bool
    published_on: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "prepared": self.prepared,
            "published": self.published,
            "published_on": self.published_on,
        }


@dataclass(frozen=True, slots=True)
class IssueUsageStatus:
    """Complete publication status for one issue."""

    issue_id: str
    title: str
    publication_date: str
    platforms: tuple[PlatformUsage, ...]
    pending_platforms: tuple[str, ...]
    published_platforms: tuple[str, ...]
    fully_published: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "publication_date": self.publication_date,
            "platforms": [
                platform.to_dict()
                for platform in self.platforms
            ],
            "pending_platforms": list(
                self.pending_platforms
            ),
            "published_platforms": list(
                self.published_platforms
            ),
            "fully_published": self.fully_published,
        }


@dataclass(frozen=True, slots=True)
class UsageSummary:
    """Repository-wide publication summary."""

    total_issues: int
    fully_published_issues: int
    partially_published_issues: int
    unpublished_issues: int
    platform_published_counts: dict[str, int]
    platform_pending_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_issues": self.total_issues,
            "fully_published_issues": (
                self.fully_published_issues
            ),
            "partially_published_issues": (
                self.partially_published_issues
            ),
            "unpublished_issues": self.unpublished_issues,
            "platform_published_counts": dict(
                self.platform_published_counts
            ),
            "platform_pending_counts": dict(
                self.platform_pending_counts
            ),
        }


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date(
    value: str | date | datetime,
) -> date:
    """Convert supported date values into a date object."""

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

    raise UsageTrackerError(
        "Unsupported date format."
    )


def _display_date(value: date) -> str:
    """Return DD-MM-YY."""

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
    return {
        "repository_version": "2.0",
        "last_updated": None,
        "issues": {},
    }


def _read_json(
    path: Path,
    default: Any | None = None,
) -> Any:
    """Read JSON or return a default when missing."""

    if not path.exists():
        return deepcopy(default)

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise UsageIndexError(
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


def ensure_usage_index() -> None:
    """Create the usage index if missing."""

    INDEX_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not USAGE_INDEX_FILE.exists():
        _write_json(
            USAGE_INDEX_FILE,
            _default_index(),
        )


def load_usage_index() -> dict[str, Any]:
    """Load and validate usage_index.json."""

    ensure_usage_index()

    index = _read_json(
        USAGE_INDEX_FILE,
        _default_index(),
    )

    if not isinstance(index, dict):
        raise UsageIndexError(
            "usage_index.json must contain a JSON object."
        )

    if not isinstance(
        index.get("issues"),
        dict,
    ):
        raise UsageIndexError(
            'usage_index.json must contain an "issues" object.'
        )

    return index


# ============================================================
# PLATFORM HELPERS
# ============================================================

def _validate_platform(
    platform: str,
) -> str:
    """Validate and normalize a platform name."""

    value = str(
        platform
    ).strip().lower()

    if value not in SUPPORTED_PLATFORMS:
        raise UsageTrackerError(
            f"Unsupported platform: {platform}\n"
            f"Supported: {', '.join(SUPPORTED_PLATFORMS)}"
        )

    return value


def _platform_usage_from_record(
    platform: str,
    record: dict[str, Any],
) -> PlatformUsage:
    """Convert one platform record."""

    return PlatformUsage(
        platform=platform,
        prepared=bool(
            record.get(
                "prepared",
                False,
            )
        ),
        published=bool(
            record.get(
                "published",
                False,
            )
        ),
        published_on=(
            str(
                record.get(
                    "published_on"
                )
            )
            if record.get(
                "published_on"
            )
            else None
        ),
    )


# ============================================================
# ISSUE STATUS
# ============================================================

def get_issue_usage_status(
    issue_id: str,
) -> IssueUsageStatus:
    """Return complete usage status for one issue."""

    issue_id = str(
        issue_id
    ).strip()

    if not issue_id:
        raise UsageIssueError(
            "Issue ID cannot be empty."
        )

    index = load_usage_index()

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
        raise UsageIssueError(
            f"Usage record was not found:\n{issue_id}"
        )

    platforms: list[PlatformUsage] = []

    for platform in SUPPORTED_PLATFORMS:
        raw_platform = issue_record.get(
            platform,
            {},
        )

        if not isinstance(
            raw_platform,
            dict,
        ):
            raw_platform = {}

        platforms.append(
            _platform_usage_from_record(
                platform,
                raw_platform,
            )
        )

    published_platforms = tuple(
        platform.platform
        for platform in platforms
        if platform.published
    )

    pending_platforms = tuple(
        platform.platform
        for platform in platforms
        if not platform.published
    )

    return IssueUsageStatus(
        issue_id=issue_id,
        title=str(
            issue_record.get(
                "title",
                "",
            )
        ),
        publication_date=str(
            issue_record.get(
                "publication_date",
                "",
            )
        ),
        platforms=tuple(
            platforms
        ),
        pending_platforms=pending_platforms,
        published_platforms=published_platforms,
        fully_published=(
            len(pending_platforms) == 0
        ),
    )


def list_all_usage_statuses() -> list[IssueUsageStatus]:
    """Return usage status for every indexed issue."""

    index = load_usage_index()

    issue_ids = list(
        index.get(
            "issues",
            {},
        ).keys()
    )

    statuses = [
        get_issue_usage_status(
            issue_id
        )
        for issue_id in issue_ids
    ]

    return sorted(
        statuses,
        key=lambda status: (
            _parse_date(
                status.publication_date
            ),
            status.issue_id,
        ),
        reverse=True,
    )


# ============================================================
# STATUS UPDATES
# ============================================================

def mark_platform_prepared(
    issue_ids: str | Iterable[str],
    platform: str,
) -> None:
    """Mark one platform as prepared."""

    platform = _validate_platform(
        platform
    )

    if isinstance(
        issue_ids,
        str,
    ):
        issue_ids = [issue_ids]
    else:
        issue_ids = list(
            issue_ids
        )

    index = load_usage_index()

    for issue_id in issue_ids:
        issue_id = str(
            issue_id
        ).strip()

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
            raise UsageIssueError(
                f"Usage record was not found:\n{issue_id}"
            )

        platform_record = issue_record.setdefault(
            platform,
            {},
        )

        platform_record["prepared"] = True

        platform_record.setdefault(
            "published",
            False,
        )

        platform_record.setdefault(
            "published_on",
            None,
        )

        issue_record["updated_at"] = _timestamp()

    index["last_updated"] = _timestamp()

    _write_json(
        USAGE_INDEX_FILE,
        index,
    )


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

    platform = _validate_platform(
        platform
    )

    if isinstance(
        issue_ids,
        str,
    ):
        issue_ids = [issue_ids]
    else:
        issue_ids = list(
            issue_ids
        )

    publication_date = (
        _parse_date(
            published_on
        )
        if published_on is not None
        else date.today()
    )

    publication_text = _display_date(
        publication_date
    )

    index = load_usage_index()

    for issue_id in issue_ids:
        issue_id = str(
            issue_id
        ).strip()

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
            raise UsageIssueError(
                f"Usage record was not found:\n{issue_id}"
            )

        platform_record = issue_record.setdefault(
            platform,
            {},
        )

        platform_record["prepared"] = True
        platform_record["published"] = True
        platform_record["published_on"] = (
            publication_text
        )

        issue_record["updated_at"] = _timestamp()

    index["last_updated"] = _timestamp()

    _write_json(
        USAGE_INDEX_FILE,
        index,
    )


def mark_platform_unpublished(
    issue_ids: str | Iterable[str],
    platform: str,
) -> None:
    """Reset one platform to unpublished."""

    platform = _validate_platform(
        platform
    )

    if isinstance(
        issue_ids,
        str,
    ):
        issue_ids = [issue_ids]
    else:
        issue_ids = list(
            issue_ids
        )

    index = load_usage_index()

    for issue_id in issue_ids:
        issue_id = str(
            issue_id
        ).strip()

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
            raise UsageIssueError(
                f"Usage record was not found:\n{issue_id}"
            )

        platform_record = issue_record.setdefault(
            platform,
            {},
        )

        platform_record["published"] = False
        platform_record["published_on"] = None
        platform_record.setdefault(
            "prepared",
            True,
        )

        issue_record["updated_at"] = _timestamp()

    index["last_updated"] = _timestamp()

    _write_json(
        USAGE_INDEX_FILE,
        index,
    )


# ============================================================
# FILTERS
# ============================================================

def get_fully_published_issues() -> list[IssueUsageStatus]:
    """Return fully published issues."""

    return [
        status
        for status in list_all_usage_statuses()
        if status.fully_published
    ]


def get_partially_published_issues() -> list[IssueUsageStatus]:
    """Return issues published on some but not all platforms."""

    return [
        status
        for status in list_all_usage_statuses()
        if (
            status.published_platforms
            and status.pending_platforms
        )
    ]


def get_unpublished_issues() -> list[IssueUsageStatus]:
    """Return issues not published anywhere."""

    return [
        status
        for status in list_all_usage_statuses()
        if not status.published_platforms
    ]


def get_pending_for_platform(
    platform: str,
) -> list[IssueUsageStatus]:
    """Return issues pending publication on one platform."""

    platform = _validate_platform(
        platform
    )

    return [
        status
        for status in list_all_usage_statuses()
        if platform in status.pending_platforms
    ]


# ============================================================
# SUMMARY
# ============================================================

def build_usage_summary() -> UsageSummary:
    """Build a repository-wide usage summary."""

    statuses = list_all_usage_statuses()

    fully_published = 0
    partially_published = 0
    unpublished = 0

    published_counts = {
        platform: 0
        for platform in SUPPORTED_PLATFORMS
    }

    pending_counts = {
        platform: 0
        for platform in SUPPORTED_PLATFORMS
    }

    for status in statuses:
        if status.fully_published:
            fully_published += 1

        elif status.published_platforms:
            partially_published += 1

        else:
            unpublished += 1

        for platform in SUPPORTED_PLATFORMS:
            if platform in status.published_platforms:
                published_counts[
                    platform
                ] += 1
            else:
                pending_counts[
                    platform
                ] += 1

    return UsageSummary(
        total_issues=len(
            statuses
        ),
        fully_published_issues=fully_published,
        partially_published_issues=(
            partially_published
        ),
        unpublished_issues=unpublished,
        platform_published_counts=(
            published_counts
        ),
        platform_pending_counts=(
            pending_counts
        ),
    )


# ============================================================
# REPORTING
# ============================================================

def print_issue_usage(
    status: IssueUsageStatus,
) -> None:
    """Print one issue's publication status."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("ISSUE PUBLICATION STATUS")
    print("=" * 72)

    print(
        f"Issue : {status.title}"
    )

    print(
        f"ID    : {status.issue_id}"
    )

    print(
        f"Date  : {status.publication_date}"
    )

    print("-" * 72)

    for platform in status.platforms:
        prepared_text = (
            "YES"
            if platform.prepared
            else "NO"
        )

        published_text = (
            "YES"
            if platform.published
            else "NO"
        )

        print(
            f"{platform.platform.upper():<10} "
            f"Prepared: {prepared_text:<3} "
            f"Published: {published_text:<3} "
            f"Date: {platform.published_on or '-'}"
        )

    print("-" * 72)

    print(
        "Pending platforms : "
        + (
            ", ".join(
                status.pending_platforms
            )
            if status.pending_platforms
            else "None"
        )
    )

    print(
        "Fully published   : "
        + (
            "YES"
            if status.fully_published
            else "NO"
        )
    )

    print("=" * 72)


def print_usage_summary(
    summary: UsageSummary,
) -> None:
    """Print the repository-wide publication summary."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("PUBLICATION USAGE SUMMARY")
    print("=" * 72)

    print(
        f"Total issues              : "
        f"{summary.total_issues}"
    )

    print(
        f"Fully published issues    : "
        f"{summary.fully_published_issues}"
    )

    print(
        f"Partially published issues: "
        f"{summary.partially_published_issues}"
    )

    print(
        f"Unpublished issues        : "
        f"{summary.unpublished_issues}"
    )

    print("-" * 72)

    for platform in SUPPORTED_PLATFORMS:
        print(
            f"{platform.upper():<10} "
            f"Published: "
            f"{summary.platform_published_counts[platform]:<4} "
            f"Pending: "
            f"{summary.platform_pending_counts[platform]}"
        )

    print("=" * 72)


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Display the latest issue and repository summary."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("USAGE TRACKER — VERSION 2.1")
    print("=" * 72)

    statuses = list_all_usage_statuses()

    if not statuses:
        print("No usage records are available.")
        print("=" * 72)
        return

    latest_status = statuses[0]

    print_issue_usage(
        latest_status
    )

    summary = build_usage_summary()

    print_usage_summary(
        summary
    )

    print("✓ Platform preparation tracking enabled")
    print("✓ Platform publication tracking enabled")
    print("✓ Pending-platform lookup enabled")
    print("✓ Fully published detection enabled")
    print("✓ Repository-wide summary enabled")
    print("=" * 72)


if __name__ == "__main__":
    _development_test()