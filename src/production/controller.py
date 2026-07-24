"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.1 PRODUCTION CONTROLLER
Created by Sudhir
============================================================

SIMPLIFIED WORKFLOW

DAILY_INPUT.json
        ↓
Optional issue selection
        ↓
Validation
        ↓
Version 2.1 Adapter
        ↓
Existing Daily Runner
        ↓
Repository + Intelligence + Outputs + PDF
============================================================
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.production.models import SessionStatus
from src.production.paths import (
    PROJECT_ROOT,
    ProductionPaths,
)
from src.production.production_validator import (
    ProductionValidator,
)
from src.production.session_manager import (
    ProductionSessionManager,
)
from src.production.v21_adapter import V21Adapter


# ==========================================================
# VERSION 2.1 ENTRY POINT
# ==========================================================

V21_DAILY_RUNNER = (
    PROJECT_ROOT
    / "src"
    / "daily_runner.py"
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class ProductionControllerError(RuntimeError):
    """
    Raised when Version 3.1 production cannot continue.
    """


# ==========================================================
# PRODUCTION CONTROLLER
# ==========================================================

class ProductionController:
    """
    Run the simplified Version 3.1 production workflow.
    """

    def __init__(
        self,
        production_date: str,
    ) -> None:
        self.production_date = production_date

        try:
            parsed_date = datetime.strptime(
                production_date,
                "%Y-%m-%d",
            )
        except ValueError as exc:
            raise ProductionControllerError(
                "production_date must use YYYY-MM-DD."
            ) from exc

        schema_date = parsed_date.strftime(
            "%d-%m-%Y"
        )

        self.paths = ProductionPaths.for_date(
            production_date
        )

        self.manager = ProductionSessionManager(
            production_date
        )

        self.validator = ProductionValidator(
            expected_production_date=schema_date
        )

        self.adapter = V21Adapter(
            expected_production_date=schema_date
        )

    # ------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------

    @staticmethod
    def _heading(
        title: str,
    ) -> None:
        print("=" * 72)
        print("TODAY'S UPSC ISSUES")
        print(title)
        print("=" * 72)

    @staticmethod
    def _success(
        message: str,
    ) -> None:
        print(f"✓ {message}")

    # ------------------------------------------------------
    # SESSION
    # ------------------------------------------------------

    def ensure_session(self) -> None:
        """
        Ensure the production session and directories exist.
        """

        if not self.manager.exists:
            self.manager.create_session(
                copy_editorials=False,
            )

            self._success(
                "Production session created"
            )
        else:
            self.paths.create_directories()

    # ------------------------------------------------------
    # LOAD CANONICAL DATA
    # ------------------------------------------------------

    def _load_canonical_data(
        self,
    ) -> dict:
        """
        Load the session copy of DAILY_INPUT.json.
        """

        canonical_file = (
            self.paths.generated_content_file
        )

        if not canonical_file.exists():
            raise ProductionControllerError(
                "DAILY_INPUT.json session copy was not found:\n"
                f"{canonical_file}"
            )

        try:
            data = json.loads(
                canonical_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ProductionControllerError(
                "DAILY_INPUT.json contains invalid JSON "
                f"at line {exc.lineno}, column {exc.colno}: "
                f"{exc.msg}"
            ) from exc

        if not isinstance(data, dict):
            raise ProductionControllerError(
                "DAILY_INPUT.json must be a JSON object."
            )

        return data

    # ------------------------------------------------------
    # ISSUE SELECTION
    # ------------------------------------------------------

    def prepare_selected_canonical(
        self,
        issue_numbers: list[int] | None,
    ) -> Path:
        """
        Create the Version 3.1 file used for the current build.
        """

        self.ensure_session()
        canonical_data = self._load_canonical_data()
        all_issues = canonical_data.get("issues")

        if not isinstance(all_issues, list) or not all_issues:
            raise ProductionControllerError(
                "DAILY_INPUT.json contains no issues."
            )

        issue_lookup: dict[int, dict] = {}

        for issue in all_issues:
            if not isinstance(issue, dict):
                continue

            metadata = issue.get("metadata")

            if not isinstance(metadata, dict):
                continue

            issue_number = metadata.get("issue_number")

            if (
                isinstance(issue_number, int)
                and not isinstance(issue_number, bool)
            ):
                issue_lookup[issue_number] = issue

        if not issue_lookup:
            raise ProductionControllerError(
                "Issues do not contain valid "
                "metadata.issue_number values."
            )

        if issue_numbers:
            cleaned_numbers: list[int] = []

            for number in issue_numbers:
                if (
                    not isinstance(number, int)
                    or isinstance(number, bool)
                    or number < 1
                ):
                    raise ProductionControllerError(
                        "Selected issue numbers must be "
                        "positive integers."
                    )

                if number not in cleaned_numbers:
                    cleaned_numbers.append(number)

            unavailable_numbers = [
                number
                for number in cleaned_numbers
                if number not in issue_lookup
            ]

            if unavailable_numbers:
                available_text = ", ".join(
                    str(number)
                    for number in sorted(issue_lookup)
                )
                unavailable_text = ", ".join(
                    str(number)
                    for number in unavailable_numbers
                )

                raise ProductionControllerError(
                    "The following selected issue numbers are "
                    "not present in DAILY_INPUT.json: "
                    f"{unavailable_text}\n"
                    f"Available issue numbers: {available_text}"
                )
        else:
            cleaned_numbers = sorted(issue_lookup)

        selected_issues = [
            copy.deepcopy(issue_lookup[number])
            for number in cleaned_numbers
        ]

        if not selected_issues:
            raise ProductionControllerError(
                "No issues were selected for production."
            )

        production = canonical_data.get("production")

        if not isinstance(production, dict):
            raise ProductionControllerError(
                "Production metadata is missing."
            )

        edition_code = str(
            production.get("edition_code", "")
        ).strip()

        if not edition_code:
            raise ProductionControllerError(
                "production.edition_code is missing."
            )

        for new_number, issue in enumerate(
            selected_issues,
            start=1,
        ):
            metadata = issue.get("metadata")

            if not isinstance(metadata, dict):
                raise ProductionControllerError(
                    "Selected issue metadata is missing."
                )

            metadata["issue_number"] = new_number
            metadata["issue_id"] = (
                f"{edition_code}-{new_number:03d}"
            )

        selected_data = copy.deepcopy(canonical_data)
        selected_data["issues"] = selected_issues
        selected_data["production"]["total_issues"] = len(
            selected_issues
        )

        selected_file = (
            self.paths.canonical_dir
            / "selected_generated_content.json"
        )

        selected_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        selected_file.write_text(
            json.dumps(
                selected_data,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        self.manager.mark_stage_completed(
            "issues_selected_for_build",
            metadata={
                "selected_issue_numbers": cleaned_numbers,
                "selected_issue_count": len(selected_issues),
                "selected_canonical_file": str(selected_file),
            },
        )

        selected_text = ", ".join(
            str(number)
            for number in cleaned_numbers
        )

        self._success(
            f"{len(selected_issues)} issue(s) "
            f"selected for production: "
            f"{selected_text}"
        )

        return selected_file

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    def validate_canonical(
        self,
        canonical_file: Path | None = None,
    ) -> None:
        """
        Validate canonical content and save reports.
        """

        self.ensure_session()

        self._heading(
            "VERSION 3.1 — VALIDATE CANONICAL CONTENT"
        )

        validation_file = (
            canonical_file
            if canonical_file is not None
            else self.paths.generated_content_file
        )

        result = self.validator.validate_file(
            validation_file
        )

        self.validator.save_reports(
            result,
            json_path=(
                self.paths
                .validation_report_json_file
            ),
            text_path=(
                self.paths
                .validation_report_text_file
            ),
        )

        print(
            result.to_text()
        )

        if not result.is_valid:
            self.manager.mark_failed(
                "canonical_validation",
                (
                    "Canonical validation failed with "
                    f"{len(result.errors)} error(s)."
                ),
            )

            raise ProductionControllerError(
                "Canonical validation failed. Review:\n"
                f"{self.paths.validation_report_text_file}"
            )

        self.manager.mark_stage_completed(
            "canonical_validation",
            status=SessionStatus.VALIDATED,
            metadata={
                "validated_canonical_file": str(
                    validation_file
                ),
                "validation_report": str(
                    self.paths
                    .validation_report_json_file
                ),
            },
        )

        self._success(
            "Canonical production content validated"
        )

    # ------------------------------------------------------
    # SOURCE FILES
    # ------------------------------------------------------

    def source_files(
        self,
    ) -> list[str]:
        """
        Return usable editorial source files for archiving.
        """

        editorial_file = (
            self.paths.editorials_file
        )

        if not editorial_file.exists():
            return []

        if not editorial_file.is_file():
            return []

        try:
            editorial_text = (
                editorial_file.read_text(
                    encoding="utf-8"
                )
            )
        except UnicodeDecodeError:
            return []

        if not editorial_text.strip():
            return []

        return [
            str(editorial_file)
        ]

    # ------------------------------------------------------
    # VERSION 2.1 ADAPTER
    # ------------------------------------------------------

    def create_v21_input(
        self,
        *,
        canonical_file: Path | None = None,
        overwrite: bool = False,
    ) -> None:
        """
        Convert canonical JSON into selected_issues.json.
        """

        self._heading(
            "VERSION 3.1 — CREATE VERSION 2.1 INPUT"
        )

        adapter_file = (
            canonical_file
            if canonical_file is not None
            else self.paths.generated_content_file
        )

        result = self.adapter.convert_file(
            canonical_file=adapter_file,
            source_files=self.source_files(),
            overwrite=overwrite,
            create_backup=True,
        )

        result.display()

        self.manager.mark_stage_completed(
            "v21_adapter",
            metadata={
                "v21_input_file": str(
                    result.output_file
                ),
                "v21_issue_count": (
                    result.issue_count
                ),
            },
        )

    # ------------------------------------------------------
    # VERSION 2.1 PIPELINE
    # ------------------------------------------------------

    def run_v21_pipeline(
        self,
        *,
        overwrite: bool = False,
        open_pdf: bool = False,
    ) -> None:
        """
        Run the existing stable Version 2.1 daily runner.
        """

        self._heading(
            "VERSION 3.1 — RUN VERSION 2.1 PIPELINE"
        )

        if not V21_DAILY_RUNNER.exists():
            raise ProductionControllerError(
                "Version 2.1 daily runner was not found:\n"
                f"{V21_DAILY_RUNNER}"
            )

        command = [
            sys.executable,
            str(V21_DAILY_RUNNER),
            self.production_date,
        ]

        if overwrite:
            command.append(
                "--overwrite"
            )

        if open_pdf:
            command.append(
                "--open-pdf"
            )

        print("Command:")
        print(" ".join(command))
        print("-" * 72)

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        )

        if completed.returncode != 0:
            self.manager.mark_failed(
                "v21_pipeline",
                (
                    "Version 2.1 daily runner exited "
                    f"with code "
                    f"{completed.returncode}."
                ),
            )

            raise ProductionControllerError(
                "Version 2.1 production pipeline failed."
            )

        self.manager.mark_stage_completed(
            "v21_pipeline",
            status=(
                SessionStatus.PRODUCTION_COMPLETED
            ),
            metadata={
                "repository_daily_dir": str(
                    self.paths.repository_daily_dir
                ),
                "daily_output_dir": str(
                    self.paths.daily_output_dir
                ),
            },
        )

        self._success(
            "Version 2.1 pipeline completed"
        )

    # ------------------------------------------------------
    # COMPLETE BUILD
    # ------------------------------------------------------

    def build(
        self,
        *,
        issue_numbers: list[int] | None = None,
        overwrite: bool = False,
        open_pdf: bool = False,
    ) -> None:
        """
        Select issues, validate, adapt and run production.
        """

        self._heading(
            "VERSION 3.1 — COMPLETE PRODUCTION BUILD"
        )

        try:
            selected_canonical_file = (
                self.prepare_selected_canonical(
                    issue_numbers
                )
            )

            self.validate_canonical(
                selected_canonical_file
            )

            self.create_v21_input(
                canonical_file=(
                    selected_canonical_file
                ),
                overwrite=overwrite,
            )

            self.run_v21_pipeline(
                overwrite=overwrite,
                open_pdf=open_pdf,
            )

        except Exception as error:
            print()
            print("=" * 72)
            print(
                "VERSION 3.1 PRODUCTION FAILED"
            )
            print("=" * 72)
            print(str(error))
            print("=" * 72)
            raise

        selected_count = len(
            issue_numbers
        ) if issue_numbers else "ALL"

        print()
        print("=" * 72)
        print("TODAY'S UPSC ISSUES")
        print(
            "VERSION 3.1 PRODUCTION "
            "COMPLETED SUCCESSFULLY"
        )
        print("=" * 72)
        print(
            f"Date       : "
            f"{self.production_date}"
        )
        print(
            f"Issues     : "
            f"{selected_count}"
        )
        print(
            f"Repository : "
            f"{self.paths.repository_daily_dir}"
        )
        print(
            f"Outputs    : "
            f"{self.paths.daily_output_dir}"
        )
        print("=" * 72)

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    def print_status(
        self,
    ) -> None:
        """
        Display simplified production readiness.
        """

        self._heading(
            "VERSION 3.1 — PRODUCTION STATUS"
        )

        canonical_exists = (
            self.paths
            .generated_content_file
            .exists()
        )

        validation_exists = (
            self.paths
            .validation_report_json_file
            .exists()
        )

        print(
            f"Date      : "
            f"{self.production_date}"
        )

        print(
            f"Session   : "
            f"{'YES' if self.manager.exists else 'NO'}"
        )

        print(
            f"Editorials: "
            f"{'YES' if self.paths.editorials_file.exists() else 'NO'}"
        )

        print(
            f"Canonical : "
            f"{'YES' if canonical_exists else 'NO'}"
        )

        print(
            f"Validation: "
            f"{'YES' if validation_exists else 'NO'}"
        )

        print("-" * 72)

        print(
            "Canonical file:"
        )

        print(
            self.paths.generated_content_file
        )

        print("-" * 72)

        if canonical_exists:
            try:
                canonical_data = (
                    self._load_canonical_data()
                )

                issues = canonical_data.get(
                    "issues",
                    [],
                )

                available_numbers = [
                    issue.get(
                        "metadata",
                        {},
                    ).get(
                        "issue_number"
                    )
                    for issue in issues
                    if isinstance(issue, dict)
                    and isinstance(
                        issue.get("metadata"),
                        dict,
                    )
                ]

                available_numbers = [
                    number
                    for number in available_numbers
                    if isinstance(
                        number,
                        int,
                    )
                    and not isinstance(
                        number,
                        bool,
                    )
                ]

                if available_numbers:
                    number_text = " ".join(
                        str(number)
                        for number in sorted(
                            available_numbers
                        )
                    )

                    print(
                        "Available issues:"
                    )

                    print(
                        number_text
                    )

                    print("-" * 72)

            except ProductionControllerError:
                pass

            print("Build all issues:")

            print(
                f"python production.py "
                f"{self.production_date} "
                f"--build --overwrite --open-pdf"
            )

            print()

            print(
                "Build selected issues:"
            )

            print(
                f"python production.py "
                f"{self.production_date} "
                f"--build --issues 1 2 3 "
                f"--overwrite --open-pdf"
            )

        else:
            print(
                "Run run_daily.py with DAILY_INPUT.json. "
                "the canonical file location "
                "before building."
            )

        print("=" * 72)