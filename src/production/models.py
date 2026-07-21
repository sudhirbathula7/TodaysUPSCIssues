"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION MODELS
Created by Sudhir
============================================================

PURPOSE

Defines the production session state used by the Version 3.0
orchestration layer.

Every production date has one session.json file.
============================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


# ==========================================================
# VERSION
# ==========================================================

PRODUCTION_VERSION = "3.0"


# ==========================================================
# SESSION STATUS
# ==========================================================

class SessionStatus(StrEnum):
    """
    Valid lifecycle stages for one production session.
    """

    CREATED = "created"
    SELECTION_PROMPT_READY = "selection_prompt_ready"
    ISSUES_SELECTED = "issues_selected"
    CONTENT_PROMPT_READY = "content_prompt_ready"
    RESPONSE_IMPORTED = "response_imported"
    VALIDATED = "validated"
    REPOSITORY_COMPLETED = "repository_completed"
    INTELLIGENCE_COMPLETED = "intelligence_completed"
    OUTPUTS_COMPLETED = "outputs_completed"
    PDF_COMPLETED = "pdf_completed"
    PRODUCTION_COMPLETED = "production_completed"
    FAILED = "failed"


# ==========================================================
# TIME HELPERS
# ==========================================================

def current_timestamp() -> str:
    """
    Return a timezone-aware local timestamp.
    """

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def parse_production_date(value: str) -> date:
    """
    Parse a production date using YYYY-MM-DD format.
    """

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            "production_date must use YYYY-MM-DD format. "
            f"Received: {value!r}"
        ) from exc


# ==========================================================
# PRODUCTION SESSION
# ==========================================================

@dataclass
class ProductionSession:
    """
    Persistent state for one daily production workflow.
    """

    production_date: str
    edition_code: str

    version: str = PRODUCTION_VERSION
    status: SessionStatus = SessionStatus.CREATED

    selected_issue_numbers: list[int] = field(
        default_factory=list
    )

    completed_stages: list[str] = field(
        default_factory=list
    )

    failed_stage: str | None = None
    error_message: str | None = None

    created_at: str = field(
        default_factory=current_timestamp
    )

    updated_at: str = field(
        default_factory=current_timestamp
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    # ------------------------------------------------------
    # CREATION
    # ------------------------------------------------------

    @classmethod
    def create(
        cls,
        production_date: date | str,
    ) -> "ProductionSession":
        """
        Create a new production session.
        """

        if isinstance(production_date, date):
            date_object = production_date
        elif isinstance(production_date, str):
            date_object = parse_production_date(
                production_date
            )
        else:
            raise TypeError(
                "production_date must be a date object "
                "or YYYY-MM-DD string."
            )

        date_text = date_object.isoformat()

        edition_code = (
            "TUI-"
            + date_object.strftime("%y%m%d")
        )

        return cls(
            production_date=date_text,
            edition_code=edition_code,
        )

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    def validate(self) -> None:
        """
        Validate the session model before saving.
        """

        parse_production_date(self.production_date)

        expected_code = (
            "TUI-"
            + date.fromisoformat(
                self.production_date
            ).strftime("%y%m%d")
        )

        if self.edition_code != expected_code:
            raise ValueError(
                "Invalid edition_code. "
                f"Expected {expected_code!r}, "
                f"received {self.edition_code!r}."
            )

        if self.version != PRODUCTION_VERSION:
            raise ValueError(
                "Invalid production version. "
                f"Expected {PRODUCTION_VERSION!r}, "
                f"received {self.version!r}."
            )

        if not isinstance(
            self.status,
            SessionStatus,
        ):
            try:
                self.status = SessionStatus(self.status)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid session status: "
                    f"{self.status!r}"
                ) from exc

        if len(
            self.selected_issue_numbers
        ) != len(
            set(self.selected_issue_numbers)
        ):
            raise ValueError(
                "selected_issue_numbers contains "
                "duplicate values."
            )

        for issue_number in self.selected_issue_numbers:
            if (
                not isinstance(issue_number, int)
                or isinstance(issue_number, bool)
                or issue_number < 1
            ):
                raise ValueError(
                    "Every selected issue number must "
                    "be a positive integer."
                )

    # ------------------------------------------------------
    # STATUS MANAGEMENT
    # ------------------------------------------------------

    def set_status(
        self,
        status: SessionStatus,
    ) -> None:
        """
        Update the current session status.
        """

        self.status = status
        self.updated_at = current_timestamp()

        if status != SessionStatus.FAILED:
            self.failed_stage = None
            self.error_message = None

    def mark_stage_completed(
        self,
        stage_name: str,
        *,
        status: SessionStatus | None = None,
    ) -> None:
        """
        Mark one production stage as completed.
        """

        clean_stage_name = stage_name.strip()

        if not clean_stage_name:
            raise ValueError(
                "stage_name cannot be empty."
            )

        if clean_stage_name not in self.completed_stages:
            self.completed_stages.append(
                clean_stage_name
            )

        if status is not None:
            self.status = status

        self.failed_stage = None
        self.error_message = None
        self.updated_at = current_timestamp()

    def mark_failed(
        self,
        stage_name: str,
        error_message: str,
    ) -> None:
        """
        Record a failed production stage.
        """

        self.status = SessionStatus.FAILED
        self.failed_stage = stage_name.strip()
        self.error_message = error_message.strip()
        self.updated_at = current_timestamp()

    def set_selected_issues(
        self,
        issue_numbers: list[int],
    ) -> None:
        """
        Store the user's final selected issue numbers.
        """

        cleaned_numbers: list[int] = []

        for value in issue_numbers:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(
                    "Selected issue numbers must be "
                    "positive integers."
                )

            if value not in cleaned_numbers:
                cleaned_numbers.append(value)

        if not cleaned_numbers:
            raise ValueError(
                "At least one issue must be selected."
            )

        self.selected_issue_numbers = cleaned_numbers
        self.status = SessionStatus.ISSUES_SELECTED
        self.updated_at = current_timestamp()

    # ------------------------------------------------------
    # SERIALISATION
    # ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the session to a JSON-compatible dictionary.
        """

        self.validate()

        return {
            "version": self.version,
            "production_date": self.production_date,
            "edition_code": self.edition_code,
            "status": self.status.value,
            "selected_issue_numbers": (
                self.selected_issue_numbers
            ),
            "completed_stages": self.completed_stages,
            "failed_stage": self.failed_stage,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ProductionSession":
        """
        Create a session from decoded JSON data.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Session data must be a dictionary."
            )

        required_fields = (
            "production_date",
            "edition_code",
        )

        missing_fields = [
            field_name
            for field_name in required_fields
            if field_name not in data
        ]

        if missing_fields:
            raise ValueError(
                "Session data is missing required fields: "
                + ", ".join(missing_fields)
            )

        try:
            status = SessionStatus(
                data.get(
                    "status",
                    SessionStatus.CREATED.value,
                )
            )
        except ValueError as exc:
            raise ValueError(
                "Session data contains an invalid status."
            ) from exc

        session = cls(
            version=data.get(
                "version",
                PRODUCTION_VERSION,
            ),
            production_date=data["production_date"],
            edition_code=data["edition_code"],
            status=status,
            selected_issue_numbers=list(
                data.get(
                    "selected_issue_numbers",
                    [],
                )
            ),
            completed_stages=list(
                data.get(
                    "completed_stages",
                    [],
                )
            ),
            failed_stage=data.get("failed_stage"),
            error_message=data.get("error_message"),
            created_at=data.get(
                "created_at",
                current_timestamp(),
            ),
            updated_at=data.get(
                "updated_at",
                current_timestamp(),
            ),
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        )

        session.validate()
        return session

    # ------------------------------------------------------
    # FILE OPERATIONS
    # ------------------------------------------------------

    def save(
        self,
        path: Path,
        *,
        overwrite: bool = True,
    ) -> None:
        """
        Save the session as formatted JSON.
        """

        if path.exists() and not overwrite:
            raise FileExistsError(
                f"Session file already exists: {path}"
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                self.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "ProductionSession":
        """
        Load a production session from a JSON file.
        """

        if not path.exists():
            raise FileNotFoundError(
                f"Session file not found: {path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid session JSON: {path}"
            ) from exc

        return cls.from_dict(data)


# ==========================================================
# SELF TEST
# ==========================================================

if __name__ == "__main__":
    session = ProductionSession.create(
        "2026-07-21"
    )

    session.set_selected_issues(
        [1, 3, 4]
    )

    session.mark_stage_completed(
        "issue_selection",
        status=SessionStatus.CONTENT_PROMPT_READY,
    )

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — V3.0 MODEL TEST")
    print("=" * 60)
    print(
        json.dumps(
            session.to_dict(),
            indent=2,
            ensure_ascii=False,
        )
    )
    print("-" * 60)
    print("✓ Production session model loaded successfully")
    print("=" * 60)