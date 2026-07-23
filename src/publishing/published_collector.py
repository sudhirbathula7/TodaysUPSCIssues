"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.1 PUBLISHED OUTPUT COLLECTOR
Created by Sudhir
============================================================

PURPOSE

Creates one clean publication-ready folder for each daily
edition.

SOURCE

output/daily/DD-MM-YY/

DESTINATION

Published/DD-MM-YY/

PHASE 4 FILES

1. Final PDF
2. YouTube Shorts script
3. Website heading

Telegram_Post.png and YouTube_Post.png will be added during
Version 3.1 Phase 6.
============================================================
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ==========================================================
# PROJECT IMPORTS
# ==========================================================

from src.production.paths import (
    PROJECT_ROOT,
    ProductionPaths,
)


# ==========================================================
# PATHS
# ==========================================================

PUBLISHED_ROOT = PROJECT_ROOT / "Published"


# ==========================================================
# SOURCE FILE NAMES
# ==========================================================

YOUTUBE_SCRIPT_SOURCE_FILE = "youtube_shorts.txt"
WEBSITE_HEADING_SOURCE_FILE = "website_heading.txt"


# ==========================================================
# DESTINATION FILE NAMES
# ==========================================================

YOUTUBE_SCRIPT_PUBLISHED_FILE = (
    "YouTube_Shorts_Script.txt"
)

WEBSITE_HEADING_PUBLISHED_FILE = (
    "Website_Heading.txt"
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class PublishedCollectorError(RuntimeError):
    """Raised when publication-ready files cannot be collected."""


# ==========================================================
# RESULT MODEL
# ==========================================================

@dataclass(frozen=True, slots=True)
class PublishedCollectionResult:
    """Result of one published-output collection."""

    production_date: str
    published_folder: Path
    pdf_file: Path
    youtube_script_file: Path
    website_heading_file: Path

    @property
    def created_files(self) -> tuple[Path, ...]:
        """Return all publication-ready files created."""

        return (
            self.pdf_file,
            self.youtube_script_file,
            self.website_heading_file,
        )


# ==========================================================
# HELPERS
# ==========================================================

def _require_source_file(
    path: Path,
    description: str,
) -> Path:
    """Ensure one required source file exists."""

    if not path.exists():
        raise PublishedCollectorError(
            f"{description} was not found:\n{path}"
        )

    if not path.is_file():
        raise PublishedCollectorError(
            f"{description} is not a file:\n{path}"
        )

    return path


def _copy_file(
    source: Path,
    destination: Path,
) -> Path:
    """Copy one file while preserving metadata."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        shutil.copy2(
            source,
            destination,
        )
    except OSError as error:
        raise PublishedCollectorError(
            "A publication file could not be copied.\n"
            f"Source      : {source}\n"
            f"Destination : {destination}\n"
            f"Reason      : {error}"
        ) from error

    return destination


# ==========================================================
# COLLECTOR
# ==========================================================

def collect_published_files(
    production_date: str | date,
    *,
    overwrite: bool = True,
) -> PublishedCollectionResult:
    """
    Create the clean daily Published folder.

    Parameters
    ----------
    production_date:
        Production date in YYYY-MM-DD format or as a date object.

    overwrite:
        When True, replace the existing dated Published folder.
    """

    paths = ProductionPaths.for_date(
        production_date
    )

    source_folder = paths.daily_output_dir

    if not source_folder.exists():
        raise PublishedCollectorError(
            "The daily output folder was not found:\n"
            f"{source_folder}\n\n"
            "Run the production pipeline before collecting "
            "publication files."
        )

    legacy_date = paths.legacy_date_key

    source_pdf = _require_source_file(
        source_folder
        / f"Todays_UPSC_Issues_{legacy_date}.pdf",
        "Final PDF",
    )

    source_youtube_script = _require_source_file(
        source_folder
        / YOUTUBE_SCRIPT_SOURCE_FILE,
        "YouTube Shorts script",
    )

    source_website_heading = _require_source_file(
        source_folder
        / WEBSITE_HEADING_SOURCE_FILE,
        "Website heading",
    )

    published_folder = (
        PUBLISHED_ROOT
        / legacy_date
    )

    if published_folder.exists():
        if not overwrite:
            raise PublishedCollectorError(
                "The dated Published folder already exists:\n"
                f"{published_folder}"
            )

        try:
            shutil.rmtree(
                published_folder
            )
        except OSError as error:
            raise PublishedCollectorError(
                "The existing Published folder could not be "
                "replaced:\n"
                f"{published_folder}\n"
                f"Reason: {error}"
            ) from error

    published_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    published_pdf = _copy_file(
        source_pdf,
        published_folder
        / f"Todays_UPSC_Issues_{legacy_date}.pdf",
    )

    published_youtube_script = _copy_file(
        source_youtube_script,
        published_folder
        / YOUTUBE_SCRIPT_PUBLISHED_FILE,
    )

    published_website_heading = _copy_file(
        source_website_heading,
        published_folder
        / WEBSITE_HEADING_PUBLISHED_FILE,
    )

    return PublishedCollectionResult(
        production_date=(
            paths.production_date.isoformat()
        ),
        published_folder=published_folder,
        pdf_file=published_pdf,
        youtube_script_file=(
            published_youtube_script
        ),
        website_heading_file=(
            published_website_heading
        ),
    )