"""
============================================================
TODAY'S UPSC ISSUES
TELEGRAM CAPTION GENERATOR
Distribution Engine V1.0
============================================================

PURPOSE

Generates the daily Telegram caption from:

    input/DAILY_INPUT.json

OUTPUT

    output/distribution/DD-MM-YY/telegram_caption.txt

The postcard image is generated separately by postcard_generator.py.
============================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TelegramCaptionError(RuntimeError):
    """Raised when the Telegram caption cannot be generated."""


def _clean_text(value: Any) -> str:
    """Convert a value into clean single-spaced text."""

    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def _parse_date(value: str) -> datetime:
    """Parse the supported production date formats."""

    value = value.strip()

    for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    raise TelegramCaptionError(
        "production.production_date must use YYYY-MM-DD, "
        "DD-MM-YYYY, or DD-MM-YY. "
        f"Received: {value!r}"
    )


def _load_json(input_file: Path) -> dict[str, Any]:
    """Load and validate the root DAILY_INPUT.json object."""

    if not input_file.exists():
        raise TelegramCaptionError(f"Input JSON not found: {input_file}")

    try:
        raw = json.loads(input_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise TelegramCaptionError(
            f"Invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(raw, dict):
        raise TelegramCaptionError(
            "DAILY_INPUT.json root must be a JSON object."
        )

    return raw


def _get_issue_title(issue: dict[str, Any], index: int) -> str:
    """
    Get the best available public-facing title.

    Supported fallbacks:
    1. outputs.telegram_card.title
    2. outputs.telegram.title
    3. metadata.title
    4. recall.recall_questions[0]
    """

    outputs = issue.get("outputs")
    if not isinstance(outputs, dict):
        outputs = {}

    telegram_card = outputs.get("telegram_card")
    if not isinstance(telegram_card, dict):
        telegram_card = {}

    telegram = outputs.get("telegram")
    if not isinstance(telegram, dict):
        telegram = {}

    metadata = issue.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    recall = issue.get("recall")
    if not isinstance(recall, dict):
        recall = {}

    questions = recall.get("recall_questions")
    if not isinstance(questions, list):
        questions = []

    candidates = [
        telegram_card.get("title"),
        telegram.get("title"),
        metadata.get("title"),
        questions[0] if questions else None,
    ]

    for candidate in candidates:
        cleaned = _clean_text(candidate)
        if cleaned:
            return cleaned

    raise TelegramCaptionError(
        f"Issue {index} does not contain a usable title."
    )


def _get_issue_number(issue: dict[str, Any], index: int) -> int:
    """Read issue_number from metadata, with sequential fallback."""

    metadata = issue.get("metadata")
    if not isinstance(metadata, dict):
        return index

    issue_number = metadata.get("issue_number")

    if isinstance(issue_number, int) and issue_number > 0:
        return issue_number

    return index


def _get_gs_label(issue: dict[str, Any]) -> str:
    """Return a compact GS paper label when available."""

    metadata = issue.get("metadata")
    if not isinstance(metadata, dict):
        return ""

    gs_papers = metadata.get("gs_papers")

    if isinstance(gs_papers, list):
        cleaned = [
            _clean_text(item)
            for item in gs_papers
            if _clean_text(item)
        ]
        return " & ".join(cleaned)

    return _clean_text(gs_papers)


def _get_custom_caption(raw: dict[str, Any]) -> str:
    """
    Read an optional complete Telegram caption already generated
    inside DAILY_INPUT.json.

    If present, it is preserved instead of rebuilding the caption.
    """

    publication = raw.get("publication")
    if not isinstance(publication, dict):
        return ""

    telegram = publication.get("telegram")
    if not isinstance(telegram, dict):
        return ""

    for key in ("caption", "post_caption", "text"):
        caption = str(telegram.get(key, "")).strip()
        if caption:
            return caption

    return ""


def build_telegram_caption(raw: dict[str, Any]) -> str:
    """Build the complete Telegram caption."""

    custom_caption = _get_custom_caption(raw)
    if custom_caption:
        return custom_caption.rstrip() + "\n"

    production = raw.get("production")
    issues = raw.get("issues")

    if not isinstance(production, dict):
        raise TelegramCaptionError(
            "Missing valid 'production' object."
        )

    if not isinstance(issues, list) or not issues:
        raise TelegramCaptionError(
            "Missing non-empty 'issues' list."
        )

    production_date_value = _clean_text(
        production.get("production_date")
    )

    if not production_date_value:
        raise TelegramCaptionError(
            "Missing production.production_date."
        )

    production_date = _parse_date(production_date_value)
    formatted_date = production_date.strftime("%d %B %Y").upper()

    declared_total = production.get("total_issues")

    if declared_total is not None and declared_total != len(issues):
        raise TelegramCaptionError(
            "Issue count mismatch: "
            f"production.total_issues={declared_total}, "
            f"actual issues={len(issues)}."
        )

    lines: list[str] = [
        "TODAY'S UPSC ISSUES",
        f"{formatted_date} | {len(issues)} TOPICS",
        "",
        "Small daily progress. Big UPSC success.",
        "",
    ]

    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            raise TelegramCaptionError(
                f"Issue {index} must be a JSON object."
            )

        issue_number = _get_issue_number(issue, index)
        title = _get_issue_title(issue, index)
        gs_label = _get_gs_label(issue)

        lines.append(f"{issue_number}. {title}")

        if gs_label:
            lines.append(f"   {gs_label}")

        lines.append("")

    lines.extend(
        [
            "Continue with today's PDF for:",
            "Current Context • Why It Matters • Core Concept • "
            "Challenges • Way Forward • Quick Facts • "
            "UPSC Practice Question",
            "",
            "Read. Recall. Revise.",
            "",
            "#UPSC #UPSCPreparation #CurrentAffairs "
            "#UPSCMains #UPSCIssues",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def generate_telegram_caption(
    input_file: Path,
    output_file: Path,
    overwrite: bool = True,
) -> Path:
    """Generate and save the Telegram caption text file."""

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_file}"
        )

    raw = _load_json(input_file)
    caption = build_telegram_caption(raw)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(caption, encoding="utf-8")

    return output_file


def main() -> int:
    """Run the Telegram caption generator directly."""

    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / "input" / "DAILY_INPUT.json"

    try:
        raw = _load_json(input_file)

        production = raw.get("production")
        if not isinstance(production, dict):
            raise TelegramCaptionError(
                "Missing valid 'production' object."
            )

        production_date = _parse_date(
            _clean_text(production.get("production_date"))
        )

        date_slug = production_date.strftime("%d-%m-%y")

        output_file = (
            project_root
            / "output"
            / "distribution"
            / date_slug
            / "telegram_caption.txt"
        )

        created = generate_telegram_caption(
            input_file=input_file,
            output_file=output_file,
            overwrite=True,
        )

        print("=" * 72)
        print("TODAY'S UPSC ISSUES — TELEGRAM CAPTION GENERATED")
        print("=" * 72)
        print(created)

        return 0

    except (
        TelegramCaptionError,
        FileNotFoundError,
        FileExistsError,
        OSError,
    ) as exc:
        print("=" * 72)
        print("TELEGRAM CAPTION GENERATION FAILED")
        print("=" * 72)
        print(exc)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())