"""
============================================================
TODAY'S UPSC ISSUES
YOUTUBE SHORTS SCRIPT EXPORTER
Distribution Engine V1.0
============================================================

PURPOSE

Extracts the pre-generated YouTube Shorts content from:

    input/DAILY_INPUT.json

The educational prompt already generates:

    outputs.youtube_short.hook
    outputs.youtube_short.short_script
    outputs.youtube_short.closing_question

This module does not rewrite or regenerate the content.
It validates and exports the scripts into one clean text file.

OUTPUT

    output/distribution/DD-MM-YY/youtube_shorts_scripts.txt
============================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ShortsScriptError(RuntimeError):
    """Raised when YouTube Shorts content cannot be exported."""


def clean_text(value: Any) -> str:
    """Return clean single-spaced text."""

    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def load_daily_input(input_file: Path) -> dict[str, Any]:
    """Load DAILY_INPUT.json."""

    if not input_file.exists():
        raise ShortsScriptError(f"Input file not found: {input_file}")

    try:
        data = json.loads(input_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ShortsScriptError(
            f"Invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ShortsScriptError(
            "DAILY_INPUT.json root must be a JSON object."
        )

    return data


def parse_production_date(data: dict[str, Any]) -> datetime:
    """Read and parse production.production_date."""

    production = data.get("production")

    if not isinstance(production, dict):
        raise ShortsScriptError(
            "Missing valid production object."
        )

    raw_date = clean_text(production.get("production_date"))

    if not raw_date:
        raise ShortsScriptError(
            "Missing production.production_date."
        )

    supported_formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d-%m-%y",
    )

    for date_format in supported_formats:
        try:
            return datetime.strptime(raw_date, date_format)
        except ValueError:
            continue

    raise ShortsScriptError(
        "Unsupported production date format: "
        f"{raw_date!r}"
    )


def get_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return and validate the issues list."""

    issues = data.get("issues")

    if not isinstance(issues, list) or not issues:
        raise ShortsScriptError(
            "DAILY_INPUT.json must contain a non-empty issues list."
        )

    validated: list[dict[str, Any]] = []

    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            raise ShortsScriptError(
                f"Issue {index} must be a JSON object."
            )

        validated.append(issue)

    return validated


def extract_script(
    issue: dict[str, Any],
    fallback_number: int,
) -> dict[str, Any]:
    """Extract one complete YouTube Shorts script."""

    metadata = issue.get("metadata")
    outputs = issue.get("outputs")

    if not isinstance(metadata, dict):
        raise ShortsScriptError(
            f"Issue {fallback_number} is missing metadata."
        )

    if not isinstance(outputs, dict):
        raise ShortsScriptError(
            f"Issue {fallback_number} is missing outputs."
        )

    youtube_short = outputs.get("youtube_short")

    if not isinstance(youtube_short, dict):
        raise ShortsScriptError(
            f"Issue {fallback_number} is missing "
            "outputs.youtube_short."
        )

    issue_number = metadata.get("issue_number", fallback_number)

    if not isinstance(issue_number, int) or issue_number < 1:
        issue_number = fallback_number

    issue_id = clean_text(metadata.get("issue_id"))
    title = clean_text(metadata.get("title"))
    hook = clean_text(youtube_short.get("hook"))
    short_script = clean_text(
        youtube_short.get("short_script")
    )
    closing_question = clean_text(
        youtube_short.get("closing_question")
    )

    missing_fields: list[str] = []

    if not title:
        missing_fields.append("metadata.title")

    if not hook:
        missing_fields.append("outputs.youtube_short.hook")

    if not short_script:
        missing_fields.append(
            "outputs.youtube_short.short_script"
        )

    if not closing_question:
        missing_fields.append(
            "outputs.youtube_short.closing_question"
        )

    if missing_fields:
        raise ShortsScriptError(
            f"Issue {issue_number} is missing: "
            + ", ".join(missing_fields)
        )

    return {
        "issue_number": issue_number,
        "issue_id": issue_id,
        "title": title,
        "hook": hook,
        "short_script": short_script,
        "closing_question": closing_question,
    }


def build_scripts_document(
    data: dict[str, Any],
) -> str:
    """Build the complete text document for all issue scripts."""

    production_date = parse_production_date(data)
    issues = get_issues(data)

    lines: list[str] = [
        "=" * 72,
        "TODAY'S UPSC ISSUES",
        "YOUTUBE SHORTS SCRIPTS",
        production_date.strftime("%d %B %Y").upper(),
        "=" * 72,
        "",
    ]

    for index, issue in enumerate(issues, start=1):
        script = extract_script(issue, index)

        lines.extend(
            [
                "=" * 72,
                f"SHORT {script['issue_number']}",
                "=" * 72,
                "",
                f"ISSUE ID: {script['issue_id'] or 'Not provided'}",
                "",
                f"TITLE: {script['title']}",
                "",
                "HOOK:",
                script["hook"],
                "",
                "SCRIPT:",
                script["short_script"],
                "",
                "CLOSING QUESTION:",
                script["closing_question"],
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def generate_shorts_scripts(
    input_file: Path,
    output_file: Path,
    overwrite: bool = True,
) -> Path:
    """Generate the YouTube Shorts scripts output file."""

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_file}"
        )

    data = load_daily_input(input_file)
    document = build_scripts_document(data)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        document,
        encoding="utf-8",
    )

    return output_file


def main() -> int:
    """Run the exporter directly."""

    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / "input" / "DAILY_INPUT.json"

    try:
        data = load_daily_input(input_file)
        production_date = parse_production_date(data)
        date_slug = production_date.strftime("%d-%m-%y")

        output_file = (
            project_root
            / "output"
            / "distribution"
            / date_slug
            / "youtube_shorts_scripts.txt"
        )

        created = generate_shorts_scripts(
            input_file=input_file,
            output_file=output_file,
            overwrite=True,
        )

        print("=" * 72)
        print("YOUTUBE SHORTS SCRIPTS GENERATED")
        print("=" * 72)
        print(created)

        return 0

    except (
        ShortsScriptError,
        FileNotFoundError,
        FileExistsError,
        OSError,
    ) as exc:
        print("=" * 72)
        print("YOUTUBE SHORTS SCRIPT EXPORT FAILED")
        print("=" * 72)
        print(exc)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())