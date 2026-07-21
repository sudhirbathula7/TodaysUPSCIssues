"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION SESSION MANAGER
Created by Sudhir
============================================================

PURPOSE

Creates, loads, updates and protects Version 3.0 production
sessions.

Each production date has one session workspace located at:

production/sessions/YYYY-MM-DD/

The manager controls session.json and the daily session
directories. It does not modify the stable Version 2.1
production modules.
============================================================
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from src.production.models import (
    ProductionSession,
    SessionStatus,
    current_timestamp,
)
from src.production.paths import (
    V21_EDITORIALS_FILE,
    ProductionPaths,
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class SessionManagerError(RuntimeError):
    """
    Base exception for production session errors.
    """


class SessionAlreadyExistsError(SessionManagerError):
    """
    Raised when a new session would overwrite an existing one.
    """


class SessionNotFoundError(SessionManagerError):
    """
    Raised when an expected production session does not exist.
    """


class EditorialInputError(SessionManagerError):
    """
    Raised when editorial input cannot be prepared.
    """


# ==========================================================
# SESSION MANAGER
# ==========================================================

class ProductionSessionManager:
    """
    Manage one Version 3.0 daily production session.
    """

    def __init__(
        self,
        production_date: date | str,
    ) -> None:
        self.paths = ProductionPaths.for_date(
            production_date
        )

    # ------------------------------------------------------
    # SESSION STATE
    # ------------------------------------------------------

    @property
    def exists(self) -> bool:
        """
        Return True when session.json exists.
        """

        return self.paths.session_file.exists()

    @property
    def session_directory_exists(self) -> bool:
        """
        Return True when the daily session directory exists.
        """

        return self.paths.session_dir.exists()

    # ------------------------------------------------------
    # CREATE SESSION
    # ------------------------------------------------------

    def create_session(
        self,
        *,
        overwrite: bool = False,
        copy_editorials: bool = True,
        editorial_source: Path | None = None,
    ) -> ProductionSession:
        """
        Create a new daily production session.

        By default, the manager copies editorials from the
        existing Version 2.1 input location:

            Daily_Work/input/todays_editorials.txt

        Existing sessions are protected unless overwrite=True.
        """

        if self.exists and not overwrite:
            raise SessionAlreadyExistsError(
                "Production session already exists for "
                f"{self.paths.date_key}: "
                f"{self.paths.session_file}"
            )

        if (
            self.session_directory_exists
            and not self.exists
            and not overwrite
            and any(self.paths.session_dir.iterdir())
        ):
            raise SessionAlreadyExistsError(
                "A non-empty session directory already exists "
                "without session.json. Use overwrite=True only "
                "after confirming that its contents may be replaced: "
                f"{self.paths.session_dir}"
            )

        if overwrite and self.paths.session_dir.exists():
            shutil.rmtree(self.paths.session_dir)

        self.paths.create_directories()

        session = ProductionSession.create(
            self.paths.production_date
        )

        session.metadata.update(
            {
                "session_directory": str(
                    self.paths.session_dir
                ),
                "created_by": "production_session_manager",
                "editorials_copied": False,
            }
        )

        if copy_editorials:
            copied_from = self.copy_editorials(
                source=editorial_source,
                overwrite=overwrite,
            )

            session.metadata["editorials_copied"] = True
            session.metadata["editorials_source"] = str(
                copied_from
            )
            session.metadata["editorials_file"] = str(
                self.paths.editorials_file
            )

        session.save(
            self.paths.session_file,
            overwrite=True,
        )

        return session

    # ------------------------------------------------------
    # LOAD SESSION
    # ------------------------------------------------------

    def load_session(self) -> ProductionSession:
        """
        Load the existing session for this production date.
        """

        if not self.exists:
            raise SessionNotFoundError(
                "Production session not found for "
                f"{self.paths.date_key}: "
                f"{self.paths.session_file}"
            )

        return ProductionSession.load(
            self.paths.session_file
        )

    # ------------------------------------------------------
    # SAVE SESSION
    # ------------------------------------------------------

    def save_session(
        self,
        session: ProductionSession,
    ) -> None:
        """
        Validate and save the supplied production session.
        """

        if (
            session.production_date
            != self.paths.date_key
        ):
            raise SessionManagerError(
                "Session date does not match the manager date. "
                f"Manager: {self.paths.date_key}, "
                f"session: {session.production_date}"
            )

        session.updated_at = current_timestamp()

        session.save(
            self.paths.session_file,
            overwrite=True,
        )

    # ------------------------------------------------------
    # EDITORIAL INPUT
    # ------------------------------------------------------

    def copy_editorials(
        self,
        *,
        source: Path | None = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Copy editorial input into the session workspace.

        Default source:
            Daily_Work/input/todays_editorials.txt
        """

        source_path = (
            source
            if source is not None
            else V21_EDITORIALS_FILE
        )

        source_path = Path(source_path)

        if not source_path.exists():
            raise EditorialInputError(
                "Editorial input file was not found: "
                f"{source_path}"
            )

        if not source_path.is_file():
            raise EditorialInputError(
                "Editorial input path is not a file: "
                f"{source_path}"
            )

        try:
            editorial_text = source_path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError as exc:
            raise EditorialInputError(
                "Editorial input must be a UTF-8 text file: "
                f"{source_path}"
            ) from exc

        if not editorial_text.strip():
            raise EditorialInputError(
                "Editorial input file is empty: "
                f"{source_path}"
            )

        destination = self.paths.editorials_file

        if destination.exists() and not overwrite:
            existing_text = destination.read_text(
                encoding="utf-8"
            )

            if existing_text != editorial_text:
                raise EditorialInputError(
                    "The session already contains a different "
                    "editorial input file. Use overwrite=True "
                    "only when replacement is intentional: "
                    f"{destination}"
                )

            return source_path

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_text(
            editorial_text.rstrip() + "\n",
            encoding="utf-8",
        )

        return source_path

    def set_editorials_text(
        self,
        editorial_text: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Write editorial text directly into the session input.
        """

        if not isinstance(editorial_text, str):
            raise TypeError(
                "editorial_text must be a string."
            )

        clean_text = editorial_text.strip()

        if not clean_text:
            raise EditorialInputError(
                "Editorial text cannot be empty."
            )

        destination = self.paths.editorials_file

        if destination.exists() and not overwrite:
            existing_text = destination.read_text(
                encoding="utf-8"
            ).strip()

            if existing_text != clean_text:
                raise EditorialInputError(
                    "Editorial input already exists and differs "
                    "from the supplied text. Use overwrite=True "
                    "only when replacement is intentional."
                )

            return destination

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_text(
            clean_text + "\n",
            encoding="utf-8",
        )

        session = self.load_session()

        session.metadata["editorials_copied"] = True
        session.metadata["editorials_source"] = (
            "direct_text_input"
        )
        session.metadata["editorials_file"] = str(
            destination
        )

        self.save_session(session)

        return destination

    def read_editorials(self) -> str:
        """
        Read the session editorial input.
        """

        path = self.paths.editorials_file

        if not path.exists():
            raise EditorialInputError(
                "Session editorial input does not exist: "
                f"{path}"
            )

        text = path.read_text(
            encoding="utf-8"
        )

        if not text.strip():
            raise EditorialInputError(
                "Session editorial input is empty: "
                f"{path}"
            )

        return text

    # ------------------------------------------------------
    # ISSUE SELECTION
    # ------------------------------------------------------

    def save_selected_issue_numbers(
        self,
        issue_numbers: list[int],
        *,
        overwrite: bool = False,
    ) -> ProductionSession:
        """
        Save the user's final selected issue numbers.
        """

        session = self.load_session()

        if (
            self.paths.selected_issue_numbers_file.exists()
            and not overwrite
        ):
            existing_data = json.loads(
                self.paths.selected_issue_numbers_file.read_text(
                    encoding="utf-8"
                )
            )

            existing_numbers = existing_data.get(
                "selected_issue_numbers",
                [],
            )

            if existing_numbers != issue_numbers:
                raise SessionManagerError(
                    "Selected issue numbers already exist and "
                    "differ from the new selection. Use "
                    "overwrite=True only when the selection "
                    "must be replaced."
                )

        session.set_selected_issues(
            issue_numbers
        )

        selection_data = {
            "production_date": session.production_date,
            "edition_code": session.edition_code,
            "selected_issue_numbers": (
                session.selected_issue_numbers
            ),
            "selected_issue_count": len(
                session.selected_issue_numbers
            ),
            "saved_at": current_timestamp(),
        }

        self.paths.selected_issue_numbers_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.paths.selected_issue_numbers_file.write_text(
            json.dumps(
                selection_data,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        session.mark_stage_completed(
            "issues_selected",
            status=SessionStatus.ISSUES_SELECTED,
        )

        self.save_session(session)

        return session

    def load_selected_issue_numbers(
        self,
    ) -> list[int]:
        """
        Load selected issue numbers from the session.
        """

        path = self.paths.selected_issue_numbers_file

        if not path.exists():
            raise SessionManagerError(
                "Selected issue numbers file not found: "
                f"{path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise SessionManagerError(
                "Selected issue numbers file contains "
                f"invalid JSON: {path}"
            ) from exc

        values = data.get(
            "selected_issue_numbers"
        )

        if not isinstance(values, list):
            raise SessionManagerError(
                "selected_issue_numbers must be a list."
            )

        cleaned_values: list[int] = []

        for value in values:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise SessionManagerError(
                    "Every selected issue number must "
                    "be a positive integer."
                )

            if value in cleaned_values:
                raise SessionManagerError(
                    "Selected issue numbers contain "
                    "duplicate values."
                )

            cleaned_values.append(value)

        if not cleaned_values:
            raise SessionManagerError(
                "No selected issue numbers were found."
            )

        return cleaned_values

    # ------------------------------------------------------
    # STATUS MANAGEMENT
    # ------------------------------------------------------

    def update_status(
        self,
        status: SessionStatus,
    ) -> ProductionSession:
        """
        Update and save the current session status.
        """

        session = self.load_session()
        session.set_status(status)
        self.save_session(session)

        return session

    def mark_stage_completed(
        self,
        stage_name: str,
        *,
        status: SessionStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProductionSession:
        """
        Mark one production stage as complete.
        """

        session = self.load_session()

        session.mark_stage_completed(
            stage_name,
            status=status,
        )

        if metadata:
            session.metadata.update(metadata)

        self.save_session(session)

        return session

    def mark_failed(
        self,
        stage_name: str,
        error: Exception | str,
    ) -> ProductionSession:
        """
        Record a failed production stage.
        """

        session = self.load_session()

        error_message = (
            str(error)
            if isinstance(error, Exception)
            else error
        )

        session.mark_failed(
            stage_name,
            error_message,
        )

        self.save_session(session)

        return session

    # ------------------------------------------------------
    # FILE CHECKS
    # ------------------------------------------------------

    def required_session_files_status(
        self,
    ) -> dict[str, bool]:
        """
        Return the existence status of important session files.
        """

        return {
            "session": self.paths.session_file.exists(),
            "editorials": (
                self.paths.editorials_file.exists()
            ),
            "issue_selection_prompt": (
                self.paths.issue_selection_prompt_file.exists()
            ),
            "selected_issue_numbers": (
                self.paths
                .selected_issue_numbers_file
                .exists()
            ),
            "final_content_prompt": (
                self.paths.final_content_prompt_file.exists()
            ),
            "final_ai_response": (
                self.paths.final_ai_response_file.exists()
            ),
            "generated_content": (
                self.paths.generated_content_file.exists()
            ),
            "validation_report": (
                self.paths
                .validation_report_json_file
                .exists()
            ),
            "production_log": (
                self.paths.production_log_file.exists()
            ),
        }

    # ------------------------------------------------------
    # SESSION SUMMARY
    # ------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """
        Return a serialisable production session summary.
        """

        session = self.load_session()

        return {
            "version": session.version,
            "production_date": (
                session.production_date
            ),
            "edition_code": session.edition_code,
            "status": session.status.value,
            "selected_issue_numbers": (
                session.selected_issue_numbers
            ),
            "completed_stages": (
                session.completed_stages
            ),
            "failed_stage": session.failed_stage,
            "error_message": session.error_message,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "session_directory": str(
                self.paths.session_dir
            ),
            "files": (
                self.required_session_files_status()
            ),
        }

    def print_summary(self) -> None:
        """
        Print the current session summary.
        """

        summary = self.summary()

        print("=" * 68)
        print("TODAY'S UPSC ISSUES — PRODUCTION SESSION")
        print("=" * 68)
        print(
            f"Date          : "
            f"{summary['production_date']}"
        )
        print(
            f"Edition       : "
            f"{summary['edition_code']}"
        )
        print(
            f"Version       : "
            f"{summary['version']}"
        )
        print(
            f"Status        : "
            f"{summary['status']}"
        )

        selected_numbers = (
            summary["selected_issue_numbers"]
        )

        if selected_numbers:
            selected_text = ", ".join(
                str(value)
                for value in selected_numbers
            )
        else:
            selected_text = "None"

        print(
            f"Selected      : {selected_text}"
        )

        completed_stages = (
            summary["completed_stages"]
        )

        if completed_stages:
            completed_text = ", ".join(
                completed_stages
            )
        else:
            completed_text = "None"

        print(
            f"Completed     : {completed_text}"
        )

        if summary["failed_stage"]:
            print(
                f"Failed stage  : "
                f"{summary['failed_stage']}"
            )
            print(
                f"Error         : "
                f"{summary['error_message']}"
            )

        print("-" * 68)
        print("Session files")

        for name, exists in summary["files"].items():
            marker = "✓" if exists else "·"
            print(
                f"{marker} {name}"
            )

        print("-" * 68)
        print(
            f"Directory     : "
            f"{summary['session_directory']}"
        )
        print("=" * 68)


# ==========================================================
# SELF TEST
# ==========================================================

if __name__ == "__main__":
    manager = ProductionSessionManager(
        "2026-07-21"
    )

    manager.print_summary()