"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION PATHS
Created by Sudhir
============================================================

PURPOSE

Provides every path required by the Version 3.0 orchestration
layer.

The path system is intentionally separate from Version 2.1 so
that existing stable modules remain unchanged.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ==========================================================
# VERSION 3.0 ROOT PATHS
# ==========================================================

PRODUCTION_ROOT = PROJECT_ROOT / "production"
PRODUCTION_TEMPLATES_DIR = PRODUCTION_ROOT / "templates"
PRODUCTION_SESSIONS_DIR = PRODUCTION_ROOT / "sessions"


# ==========================================================
# VERSION 3.0 TEMPLATE FILES
# ==========================================================

ISSUE_SELECTION_TEMPLATE = (
    PRODUCTION_TEMPLATES_DIR
    / "issue_selection_prompt.md"
)

FINAL_CONTENT_TEMPLATE = (
    PRODUCTION_TEMPLATES_DIR
    / "final_content_prompt.md"
)

CANONICAL_SCHEMA_FILE = (
    PRODUCTION_TEMPLATES_DIR
    / "generated_content_schema.json"
)


# ==========================================================
# VERSION 2.1 PATHS
# ==========================================================

DAILY_WORK_DIR = PROJECT_ROOT / "Daily_Work"
DAILY_WORK_INPUT_DIR = DAILY_WORK_DIR / "input"
DAILY_WORK_GENERATED_DIR = DAILY_WORK_DIR / "generated"

V21_SELECTED_ISSUES_FILE = (
    DAILY_WORK_INPUT_DIR
    / "selected_issues.json"
)

V21_EDITORIALS_FILE = (
    DAILY_WORK_INPUT_DIR
    / "todays_editorials.txt"
)

REPOSITORY_DIR = PROJECT_ROOT / "Repository"
OUTPUT_DIR = PROJECT_ROOT / "output"


# ==========================================================
# HELPERS
# ==========================================================

def normalize_production_date(
    value: date | str,
) -> date:
    """
    Convert a date or ISO-format date string into a date object.

    Accepted string format:
        YYYY-MM-DD
    """

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise TypeError(
            "Production date must be a date object or "
            "an ISO date string."
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "Production date must use YYYY-MM-DD format. "
            f"Received: {value!r}"
        ) from exc


# ==========================================================
# DAILY SESSION PATHS
# ==========================================================

@dataclass(frozen=True)
class ProductionPaths:
    """
    Complete path map for one Version 3.0 production session.
    """

    production_date: date

    @classmethod
    def for_date(
        cls,
        value: date | str,
    ) -> "ProductionPaths":
        """
        Create a path map from a date object or YYYY-MM-DD string.
        """

        return cls(
            production_date=normalize_production_date(value)
        )

    # ------------------------------------------------------
    # SESSION ROOT
    # ------------------------------------------------------

    @property
    def date_key(self) -> str:
        """
        Canonical Version 3.0 session date key.
        """

        return self.production_date.isoformat()

    @property
    def legacy_date_key(self) -> str:
        """
        Existing Version 2.1 date-folder format.

        Example:
            21-07-26
        """

        return self.production_date.strftime("%d-%m-%y")

    @property
    def session_dir(self) -> Path:
        return PRODUCTION_SESSIONS_DIR / self.date_key

    # ------------------------------------------------------
    # SESSION DIRECTORIES
    # ------------------------------------------------------

    @property
    def input_dir(self) -> Path:
        return self.session_dir / "input"

    @property
    def prompts_dir(self) -> Path:
        return self.session_dir / "prompts"

    @property
    def selections_dir(self) -> Path:
        return self.session_dir / "selections"

    @property
    def responses_dir(self) -> Path:
        return self.session_dir / "responses"

    @property
    def canonical_dir(self) -> Path:
        return self.session_dir / "canonical"

    @property
    def validation_dir(self) -> Path:
        return self.session_dir / "validation"

    @property
    def logs_dir(self) -> Path:
        return self.session_dir / "logs"

    # ------------------------------------------------------
    # SESSION FILES
    # ------------------------------------------------------

    @property
    def session_file(self) -> Path:
        return self.session_dir / "session.json"

    @property
    def editorials_file(self) -> Path:
        return self.input_dir / "todays_editorials.txt"

    @property
    def issue_selection_prompt_file(self) -> Path:
        return (
            self.prompts_dir
            / "01_issue_selection_prompt.txt"
        )

    @property
    def final_content_prompt_file(self) -> Path:
        return (
            self.prompts_dir
            / "02_final_content_prompt.txt"
        )

    @property
    def selected_issue_numbers_file(self) -> Path:
        return (
            self.selections_dir
            / "selected_issue_numbers.json"
        )

    @property
    def issue_shortlist_file(self) -> Path:
        return (
            self.responses_dir
            / "issue_shortlist.txt"
        )

    @property
    def final_ai_response_file(self) -> Path:
        return (
            self.responses_dir
            / "final_ai_response.txt"
        )

    @property
    def raw_response_archive_file(self) -> Path:
        return (
            self.responses_dir
            / "raw_response_archive.txt"
        )

    @property
    def generated_content_file(self) -> Path:
        return (
            self.canonical_dir
            / "generated_content.json"
        )

    @property
    def validation_report_json_file(self) -> Path:
        return (
            self.validation_dir
            / "validation_report.json"
        )

    @property
    def validation_report_text_file(self) -> Path:
        return (
            self.validation_dir
            / "validation_report.txt"
        )

    @property
    def production_log_file(self) -> Path:
        return self.logs_dir / "production.log"

    # ------------------------------------------------------
    # VERSION 2.1 OUTPUT LOCATIONS
    # ------------------------------------------------------

    @property
    def repository_daily_dir(self) -> Path:
        return (
            REPOSITORY_DIR
            / "daily"
            / self.legacy_date_key
        )

    @property
    def intelligence_dir(self) -> Path:
        return (
            REPOSITORY_DIR
            / "intelligence"
            / self.legacy_date_key
        )

    @property
    def daily_output_dir(self) -> Path:
        return (
            OUTPUT_DIR
            / "daily"
            / self.legacy_date_key
        )

    # ------------------------------------------------------
    # DIRECTORY CREATION
    # ------------------------------------------------------

    def required_directories(self) -> tuple[Path, ...]:
        """
        Return every directory needed for a session.
        """

        return (
            PRODUCTION_ROOT,
            PRODUCTION_TEMPLATES_DIR,
            PRODUCTION_SESSIONS_DIR,
            self.session_dir,
            self.input_dir,
            self.prompts_dir,
            self.selections_dir,
            self.responses_dir,
            self.canonical_dir,
            self.validation_dir,
            self.logs_dir,
        )

    def create_directories(self) -> None:
        """
        Create all required Version 3.0 session directories.
        """

        for directory in self.required_directories():
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    # ------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------

    def as_dict(self) -> dict[str, str]:
        """
        Return important paths as serialisable strings.
        """

        return {
            "project_root": str(PROJECT_ROOT),
            "production_root": str(PRODUCTION_ROOT),
            "session_dir": str(self.session_dir),
            "input_dir": str(self.input_dir),
            "prompts_dir": str(self.prompts_dir),
            "selections_dir": str(self.selections_dir),
            "responses_dir": str(self.responses_dir),
            "canonical_dir": str(self.canonical_dir),
            "validation_dir": str(self.validation_dir),
            "logs_dir": str(self.logs_dir),
            "session_file": str(self.session_file),
            "editorials_file": str(self.editorials_file),
            "generated_content_file": str(
                self.generated_content_file
            ),
            "production_log_file": str(
                self.production_log_file
            ),
            "v21_selected_issues_file": str(
                V21_SELECTED_ISSUES_FILE
            ),
            "repository_daily_dir": str(
                self.repository_daily_dir
            ),
            "daily_output_dir": str(
                self.daily_output_dir
            ),
        }


# ==========================================================
# SELF TEST
# ==========================================================

if __name__ == "__main__":
    paths = ProductionPaths.for_date("2026-07-21")
    paths.create_directories()

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — V3.0 PATH TEST")
    print("=" * 60)

    for key, value in paths.as_dict().items():
        print(f"{key:<30}: {value}")

    print("-" * 60)
    print("✓ Production path system loaded successfully")
    print("=" * 60)