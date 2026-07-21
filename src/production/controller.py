"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION CONTROLLER
Created by Sudhir
============================================================

PURPOSE

Coordinates the Version 3.0 production workflow above the
stable Version 2.1 modules.

WORKFLOW

1. Create/load production session
2. Generate Issue Selection Prompt
3. Save selected issue numbers
4. Generate Final Content Prompt
5. Import ChatGPT JSON response
6. Validate canonical data
7. Convert canonical data to Version 2.1 input
8. Run the existing Version 2.1 daily runner
============================================================
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.production.models import SessionStatus
from src.production.paths import (
    CANONICAL_SCHEMA_FILE,
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
# CONSTANTS
# ==========================================================

MASTER_PROMPT_FILE = (
    PROJECT_ROOT
    / "production"
    / "01_Master_Production_Prompt.md"
)

V21_DAILY_RUNNER = (
    PROJECT_ROOT
    / "src"
    / "daily_runner.py"
)


# ==========================================================
# EXCEPTIONS
# ==========================================================

class ProductionControllerError(RuntimeError):
    """Raised when Version 3.0 production cannot continue."""


# ==========================================================
# CONTROLLER
# ==========================================================

class ProductionController:
    """
    Coordinate one daily Version 3.0 production session.
    """

    def __init__(
        self,
        production_date: str,
    ) -> None:
        self.production_date = production_date
        self.paths = ProductionPaths.for_date(
            production_date
        )
        self.manager = ProductionSessionManager(
            production_date
        )
        self.validator = ProductionValidator(
            expected_production_date=(
                production_date
            )
        )
        self.adapter = V21Adapter(
            expected_production_date=(
                production_date
            )
        )

    # ------------------------------------------------------
    # DISPLAY
    # ------------------------------------------------------

    @staticmethod
    def _heading(title: str) -> None:
        print("=" * 72)
        print("TODAY'S UPSC ISSUES")
        print(title)
        print("=" * 72)

    @staticmethod
    def _success(message: str) -> None:
        print(f"✓ {message}")

    # ------------------------------------------------------
    # COMMON READERS
    # ------------------------------------------------------

    @staticmethod
    def _read_required_text(
        path: Path,
        description: str,
    ) -> str:
        if not path.exists():
            raise ProductionControllerError(
                f"{description} was not found:\n{path}"
            )

        text = path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            raise ProductionControllerError(
                f"{description} is empty:\n{path}"
            )

        return text

    def _read_master_prompt(self) -> str:
        return self._read_required_text(
            MASTER_PROMPT_FILE,
            "Master production prompt",
        )

    def _read_schema_text(self) -> str:
        return self._read_required_text(
            CANONICAL_SCHEMA_FILE,
            "Canonical JSON schema",
        )

        # ------------------------------------------------------
    # SESSION PREPARATION
    # ------------------------------------------------------

    def prepare_session(
        self,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Create or load the daily session and generate Prompt 1.
        """

        self._heading(
            "VERSION 3.0 — PREPARE PRODUCTION SESSION"
        )

        if self.manager.exists and not overwrite:
            session = self.manager.load_session()

            self._success(
                "Existing production session loaded"
            )

            if not self.paths.editorials_file.exists():
                source_path = self.manager.copy_editorials(
                    overwrite=False
                )

                session.metadata["editorials_copied"] = True
                session.metadata["editorials_source"] = str(
                    source_path
                )
                session.metadata["editorials_file"] = str(
                    self.paths.editorials_file
                )

                self.manager.save_session(session)

                self._success(
                    "Editorial input copied into session"
                )

        else:
            session = self.manager.create_session(
                overwrite=overwrite,
                copy_editorials=True,
            )

            self._success(
                "New production session created"
            )

        prompt_path = self.build_selection_prompt(
            overwrite=overwrite
        )

        session = self.manager.mark_stage_completed(
            "selection_prompt",
            status=(
                SessionStatus.SELECTION_PROMPT_READY
            ),
            metadata={
                "issue_selection_prompt": str(
                    prompt_path
                )
            },
        )

        self._success(
            "Issue Selection Prompt generated"
        )

        print("-" * 72)
        print(f"Date    : {session.production_date}")
        print(f"Edition : {session.edition_code}")
        print(f"Prompt  : {prompt_path}")
        print("-" * 72)
        print("NEXT STEP")
        print()
        print("1. Open the prompt file.")
        print("2. Paste it into ChatGPT.")
        print("3. Review the shortlisted issues.")
        print("4. Run:")
        print()
        print(
            f"python production.py "
            f"{self.production_date} "
            f"--select 1 2 3"
        )
        print("=" * 72)

        return prompt_path

    # ------------------------------------------------------
    # PROMPT 1
    # ------------------------------------------------------

    def build_selection_prompt(
        self,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Generate the Issue Selection Prompt.
        """

        editorials = self.manager.read_editorials()
        master_prompt = self._read_master_prompt()

        output_path = (
            self.paths.issue_selection_prompt_file
        )

        if output_path.exists() and not overwrite:
            return output_path

        prompt = f"""
{master_prompt}

============================================================
VERSION 3.0 — STAGE 1 EXECUTION
============================================================

PRODUCTION DATE
{self.production_date}

TASK
Perform only the EDITORIAL CURATOR stage.

Read every editorial below completely.

Identify a maximum of four strong, independent UPSC issues.
Publish fewer than four when fewer issues deserve publication.
Reject every issue rated below 4.5 out of 5.
Merge overlapping issues.
Do not generate the final issue datasets yet.

OUTPUT
Display only these columns:

Issue Number
Issue Title
GS Paper
Subject
Rating
Source Editorial(s)
Reason for Selection

Stop after the shortlist and wait for the selected issue numbers.

============================================================
TODAY'S EDITORIALS
============================================================

{editorials}

============================================================
END OF EDITORIAL INPUT
============================================================
""".strip() + "\n"

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            prompt,
            encoding="utf-8",
        )

        return output_path

    # ------------------------------------------------------
    # ISSUE SELECTION
    # ------------------------------------------------------

    def select_issues(
        self,
        issue_numbers: list[int],
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Save selected issue numbers and generate Prompt 2.
        """

        self._heading(
            "VERSION 3.0 — SAVE ISSUE SELECTION"
        )

        session = (
            self.manager.save_selected_issue_numbers(
                issue_numbers,
                overwrite=overwrite,
            )
        )

        self._success(
            "Selected issue numbers saved"
        )

        prompt_path = self.build_content_prompt(
            overwrite=overwrite
        )

        session = self.manager.mark_stage_completed(
            "content_prompt",
            status=(
                SessionStatus.CONTENT_PROMPT_READY
            ),
            metadata={
                "final_content_prompt": str(
                    prompt_path
                )
            },
        )

        selected_text = ", ".join(
            str(number)
            for number in session.selected_issue_numbers
        )

        self._success(
            "Final Content Prompt generated"
        )

        print("-" * 72)
        print(f"Selected issues : {selected_text}")
        print(f"Prompt          : {prompt_path}")
        print("-" * 72)
        print("NEXT STEP")
        print()
        print("1. Open the Final Content Prompt.")
        print("2. Paste it into ChatGPT.")
        print("3. Copy the complete JSON response into:")
        print()
        print(f"   {self.paths.final_ai_response_file}")
        print()
        print("4. Run:")
        print()
        print(
            f"python production.py "
            f"{self.production_date} --run"
        )
        print("=" * 72)

        return prompt_path

    # ------------------------------------------------------
    # PROMPT 2
    # ------------------------------------------------------

    def build_content_prompt(
        self,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Generate the Final Content Prompt.
        """

        editorials = self.manager.read_editorials()
        selected_numbers = (
            self.manager.load_selected_issue_numbers()
        )
        master_prompt = self._read_master_prompt()
        schema_text = self._read_schema_text()

        output_path = (
            self.paths.final_content_prompt_file
        )

        if output_path.exists() and not overwrite:
            return output_path

        selected_text = ", ".join(
            str(number)
            for number in selected_numbers
        )

        prompt = f"""
{master_prompt}

============================================================
VERSION 3.0 — STAGE 2 EXECUTION
============================================================

PRODUCTION DATE
{self.production_date}

SELECTED ISSUE NUMBERS
{selected_text}

TASK
Generate content only for the selected issue numbers.

Use the editorials as the primary source.
Produce original UPSC educational content.
Do not copy newspaper wording or sentence structure.

IMPORTANT VERSION 3.0 OUTPUT RULE
The old plain-text parser format does not apply to this run.

Return exactly one valid JSON object matching the canonical
schema provided below.

Do not use markdown.
Do not use JSON code fences.
Do not include any introduction, explanation, validation
message, notes or concluding text.

The response must begin with {{ and end with }}.

CONTENT REQUIREMENTS
- Exactly two recall questions for every issue.
- Exactly four Quick Facts for every issue.
- Rating must be numeric and at least 4.5.
- issue_count must match the number of generated issues.
- Issue numbers must begin at 1 and remain sequential in the
  generated JSON.
- Use production date {self.production_date}.
- Use edition code {self.paths.production_date.strftime("TUI-%y%m%d")}.
- Include Telegram, YouTube and website content.
- Include every mandatory field from the schema.
- Use only source IDs declared in source_editorials.

============================================================
CANONICAL JSON SCHEMA
============================================================

{schema_text}

============================================================
TODAY'S EDITORIALS
============================================================

{editorials}

============================================================
FINAL INSTRUCTION
============================================================

Return only the complete canonical JSON object.
""".strip() + "\n"

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            prompt,
            encoding="utf-8",
        )

        return output_path

    # ------------------------------------------------------
    # AI RESPONSE IMPORT
    # ------------------------------------------------------

    @staticmethod
    def _extract_json_text(
        raw_text: str,
    ) -> str:
        """
        Extract one JSON object from a ChatGPT response.
        """

        text = raw_text.strip()

        if text.startswith("```"):
            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )

            text = re.sub(
                r"\s*```$",
                "",
                text,
            )

            text = text.strip()

        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise ProductionControllerError(
                    "No complete JSON object was found in "
                    "final_ai_response.txt."
                )

            text = text[start:end + 1]

            try:
                decoded = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ProductionControllerError(
                    "The AI response contains invalid JSON at "
                    f"line {exc.lineno}, column {exc.colno}: "
                    f"{exc.msg}"
                ) from exc

        if not isinstance(decoded, dict):
            raise ProductionControllerError(
                "The canonical AI response must be one "
                "JSON object."
            )

        return (
            json.dumps(
                decoded,
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )

    def import_ai_response(
        self,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Import final_ai_response.txt as generated_content.json.
        """

        self._heading(
            "VERSION 3.0 — IMPORT AI RESPONSE"
        )

        raw_path = (
            self.paths.final_ai_response_file
        )

        raw_text = self._read_required_text(
            raw_path,
            "Final AI response",
        )

        canonical_path = (
            self.paths.generated_content_file
        )

        if canonical_path.exists() and not overwrite:
            existing = canonical_path.read_text(
                encoding="utf-8"
            )

            extracted = self._extract_json_text(
                raw_text
            )

            if existing != extracted:
                raise ProductionControllerError(
                    "generated_content.json already exists "
                    "with different content. Use --overwrite "
                    "only when intentionally replacing it."
                )

            self._success(
                "Existing canonical JSON is unchanged"
            )

            return canonical_path

        self.paths.raw_response_archive_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.paths.raw_response_archive_file.write_text(
            raw_text.rstrip() + "\n",
            encoding="utf-8",
        )

        extracted_json = self._extract_json_text(
            raw_text
        )

        canonical_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        canonical_path.write_text(
            extracted_json,
            encoding="utf-8",
        )

        self.manager.mark_stage_completed(
            "response_imported",
            status=SessionStatus.RESPONSE_IMPORTED,
            metadata={
                "generated_content_file": str(
                    canonical_path
                )
            },
        )

        self._success(
            "AI response imported"
        )
        self._success(
            "Canonical generated_content.json created"
        )

        print(f"Canonical file: {canonical_path}")
        print("=" * 72)

        return canonical_path

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    def validate_canonical(self) -> None:
        """
        Validate generated_content.json and save reports.
        """

        self._heading(
            "VERSION 3.0 — VALIDATE CANONICAL CONTENT"
        )

        canonical_path = (
            self.paths.generated_content_file
        )

        result = self.validator.validate_file(
            canonical_path
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

        print(result.to_text())

        if not result.is_valid:
            self.manager.mark_failed(
                "canonical_validation",
                (
                    f"Canonical validation failed with "
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
                "validation_report": str(
                    self.paths
                    .validation_report_json_file
                )
            },
        )

        self._success(
            "Canonical production content validated"
        )

    # ------------------------------------------------------
    # VERSION 2.1 ADAPTER
    # ------------------------------------------------------

    def create_v21_input(
        self,
        *,
        overwrite: bool = False,
    ) -> None:
        """
        Create Daily_Work/input/selected_issues.json.
        """

        self._heading(
            "VERSION 3.0 — CREATE VERSION 2.1 INPUT"
        )

        result = self.adapter.convert_file(
            canonical_file=(
                self.paths.generated_content_file
            ),
            source_files=[
                str(self.paths.editorials_file)
            ],
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
        Run the existing Version 2.1 daily runner.
        """

        self._heading(
            "VERSION 3.0 — RUN VERSION 2.1 PIPELINE"
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
            command.append("--overwrite")

        if open_pdf:
            command.append("--open-pdf")

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
                    f"with code {completed.returncode}."
                ),
            )

            raise ProductionControllerError(
                "Version 2.1 production pipeline failed."
            )

        self.manager.mark_stage_completed(
            "v21_pipeline",
            status=SessionStatus.PRODUCTION_COMPLETED,
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
    # COMPLETE RUN
    # ------------------------------------------------------

    def run(
        self,
        *,
        overwrite: bool = False,
        open_pdf: bool = False,
    ) -> None:
        """
        Import, validate, adapt and run production.
        """

        self._heading(
            "VERSION 3.0 — COMPLETE PRODUCTION RUN"
        )

        try:
            self.import_ai_response(
                overwrite=overwrite
            )

            self.validate_canonical()

            self.create_v21_input(
                overwrite=overwrite
            )

            self.run_v21_pipeline(
                overwrite=overwrite,
                open_pdf=open_pdf,
            )

        except Exception as error:
            print()
            print("=" * 72)
            print("PRODUCTION FAILED")
            print("=" * 72)
            print(str(error))
            print("=" * 72)
            raise

        print()
        print("=" * 72)
        print("TODAY'S UPSC ISSUES")
        print("VERSION 3.0 PRODUCTION COMPLETED SUCCESSFULLY")
        print("=" * 72)
        print(f"Date       : {self.production_date}")
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

    def print_status(self) -> None:
        """
        Display the current production session status.
        """

        if not self.manager.exists:
            self._heading(
                "VERSION 3.0 — SESSION STATUS"
            )
            print(
                "No production session exists for "
                f"{self.production_date}."
            )
            print()
            print("Run:")
            print(
                f"python production.py "
                f"{self.production_date} --prepare"
            )
            print("=" * 72)
            return

        self.manager.print_summary()