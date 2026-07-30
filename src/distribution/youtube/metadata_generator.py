"""
============================================================
TODAY'S UPSC ISSUES
YOUTUBE SHORTS METADATA EXPORTER
Distribution Engine V1.0
============================================================

PURPOSE

Creates ready-to-use YouTube Shorts metadata from DAILY_INPUT.json.

This module does not generate new educational content.

It uses:

    metadata.title
    metadata.issue_number
    metadata.issue_id
    metadata.gs_papers
    metadata.syllabus_tags
    description
    outputs.youtube_short.hook
    outputs.youtube_short.closing_question

OUTPUT

    output/distribution/DD-MM-YY/youtube_metadata.txt
============================================================
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class YouTubeMetadataError(RuntimeError):
    """Raised when YouTube metadata cannot be generated."""


# Words that should not become title-based hashtags.
HASHTAG_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "india",
    "indias",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "under",
    "with",
}


def clean_text(value: Any) -> str:
    """Return clean, single-spaced text."""

    if value is None:
        return ""

    return " ".join(str(value).strip().split())


def load_json(input_file: Path) -> dict[str, Any]:
    """Load and validate DAILY_INPUT.json."""

    if not input_file.exists():
        raise YouTubeMetadataError(
            f"Input file not found: {input_file}"
        )

    try:
        data = json.loads(
            input_file.read_text(encoding="utf-8-sig")
        )
    except json.JSONDecodeError as exc:
        raise YouTubeMetadataError(
            f"Invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise YouTubeMetadataError(
            "DAILY_INPUT.json root must be a JSON object."
        )

    return data


def find_default_input(project_root: Path) -> Path:
    """
    Find DAILY_INPUT.json using supported project locations.
    """

    possible_files = [
        project_root
        / "Daily_Work"
        / "input"
        / "DAILY_INPUT.json",

        project_root
        / "input"
        / "DAILY_INPUT.json",

        project_root
        / "DAILY_INPUT.json",
    ]

    for file_path in possible_files:
        if file_path.exists():
            return file_path

    # Return the preferred path so the error message is clear.
    return possible_files[0]


def get_production_date(data: dict[str, Any]) -> datetime:
    """Extract the production date from the JSON."""

    possible_values: list[Any] = []

    production = data.get("production")

    if isinstance(production, dict):
        possible_values.extend(
            [
                production.get("production_date"),
                production.get("date"),
            ]
        )

    metadata = data.get("metadata")

    if isinstance(metadata, dict):
        possible_values.extend(
            [
                metadata.get("production_date"),
                metadata.get("date"),
            ]
        )

    possible_values.append(data.get("date"))

    raw_date = ""

    for value in possible_values:
        cleaned = clean_text(value)

        if cleaned:
            raw_date = cleaned
            break

    if not raw_date:
        raise YouTubeMetadataError(
            "Production date was not found in DAILY_INPUT.json."
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

    raise YouTubeMetadataError(
        f"Unsupported production date format: {raw_date!r}"
    )


def get_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the validated issues list."""

    issues = data.get("issues")

    if not isinstance(issues, list) or not issues:
        raise YouTubeMetadataError(
            "DAILY_INPUT.json must contain a non-empty issues list."
        )

    validated_issues: list[dict[str, Any]] = []

    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            raise YouTubeMetadataError(
                f"Issue {index} must be a JSON object."
            )

        validated_issues.append(issue)

    return validated_issues


def camel_case_hashtag(value: str) -> str:
    """
    Convert text into a compact hashtag.

    Example:
        Public Examination Reforms
        -> #PublicExaminationReforms
    """

    words = re.findall(r"[A-Za-z0-9]+", value)

    if not words:
        return ""

    combined = "".join(
        word[:1].upper() + word[1:]
        for word in words
    )

    return f"#{combined}"


def title_keyword_hashtags(title: str) -> list[str]:
    """Create up to three useful hashtags from the issue title."""

    words = re.findall(r"[A-Za-z0-9]+", title)

    useful_words = [
        word
        for word in words
        if word.lower() not in HASHTAG_STOP_WORDS
        and len(word) >= 4
    ]

    hashtags: list[str] = []

    # Prefer a two-word subject hashtag.
    if len(useful_words) >= 2:
        combined = camel_case_hashtag(
            f"{useful_words[0]} {useful_words[1]}"
        )

        if combined:
            hashtags.append(combined)

    # Add one or two strong individual keywords.
    for word in useful_words:
        hashtag = camel_case_hashtag(word)

        if hashtag and hashtag not in hashtags:
            hashtags.append(hashtag)

        if len(hashtags) >= 3:
            break

    return hashtags


def syllabus_hashtag(
    syllabus_tags: list[Any],
) -> str:
    """Create one concise hashtag from the first syllabus tag."""

    if not syllabus_tags:
        return ""

    first_tag = clean_text(syllabus_tags[0])

    if not first_tag:
        return ""

    keyword_map = {
        "governance": "#Governance",
        "health": "#HealthGovernance",
        "international relations": "#InternationalRelations",
        "economy": "#IndianEconomy",
        "environment": "#Environment",
        "agriculture": "#Agriculture",
        "security": "#InternalSecurity",
        "judiciary": "#Judiciary",
        "executive": "#Governance",
        "science": "#ScienceAndTechnology",
        "technology": "#ScienceAndTechnology",
        "social justice": "#SocialJustice",
    }

    lower_tag = first_tag.lower()

    for keyword, hashtag in keyword_map.items():
        if keyword in lower_tag:
            return hashtag

    return ""


def unique_hashtags(
    values: list[str],
    maximum: int = 8,
) -> list[str]:
    """Remove duplicate hashtags while preserving order."""

    output: list[str] = []
    seen: set[str] = set()

    for value in values:
        hashtag = clean_text(value)

        if not hashtag or not hashtag.startswith("#"):
            continue

        comparison_key = hashtag.lower()

        if comparison_key in seen:
            continue

        seen.add(comparison_key)
        output.append(hashtag)

        if len(output) >= maximum:
            break

    return output


def build_youtube_title(title: str) -> str:
    """Create a readable YouTube Shorts title."""

    suffix = " | UPSC Current Affairs"

    maximum_title_length = 100
    available_length = maximum_title_length - len(suffix)

    if len(title) > available_length:
        title = title[: available_length - 1].rstrip() + "…"

    return f"{title}{suffix}"


def extract_metadata(
    issue: dict[str, Any],
    fallback_number: int,
    production_date: datetime,
) -> dict[str, Any]:
    """Extract and format metadata for one issue."""

    metadata = issue.get("metadata")
    outputs = issue.get("outputs")

    if not isinstance(metadata, dict):
        raise YouTubeMetadataError(
            f"Issue {fallback_number} is missing metadata."
        )

    if not isinstance(outputs, dict):
        raise YouTubeMetadataError(
            f"Issue {fallback_number} is missing outputs."
        )

    youtube_short = outputs.get("youtube_short")

    if not isinstance(youtube_short, dict):
        raise YouTubeMetadataError(
            f"Issue {fallback_number} is missing "
            "outputs.youtube_short."
        )

    issue_number = metadata.get(
        "issue_number",
        fallback_number,
    )

    if not isinstance(issue_number, int) or issue_number < 1:
        issue_number = fallback_number

    issue_id = clean_text(metadata.get("issue_id"))
    title = clean_text(metadata.get("title"))
    description = clean_text(issue.get("description"))
    hook = clean_text(youtube_short.get("hook"))
    closing_question = clean_text(
        youtube_short.get("closing_question")
    )

    gs_papers = metadata.get("gs_papers", [])
    syllabus_tags = metadata.get("syllabus_tags", [])

    if not isinstance(gs_papers, list):
        gs_papers = []

    if not isinstance(syllabus_tags, list):
        syllabus_tags = []

    if not title:
        raise YouTubeMetadataError(
            f"Issue {issue_number} is missing metadata.title."
        )

    if not description:
        description = hook

    if not description:
        raise YouTubeMetadataError(
            f"Issue {issue_number} has no description or hook."
        )

    gs_text = ", ".join(
        clean_text(item)
        for item in gs_papers
        if clean_text(item)
    )

    hashtags = unique_hashtags(
        [
            "#UPSC",
            "#UPSCPreparation",
            "#CurrentAffairs",
            syllabus_hashtag(syllabus_tags),
            *title_keyword_hashtags(title),
            "#TodaysUPSCIssues",
        ]
    )

    youtube_title = build_youtube_title(title)

    description_lines = [
        description,
        "",
    ]

    if closing_question:
        description_lines.extend(
            [
                f"Recall question: {closing_question}",
                "",
            ]
        )

    description_lines.extend(
        [
            f"Today's UPSC Issues | "
            f"{production_date.strftime('%d %B %Y')}",
        ]
    )

    if gs_text:
        description_lines.append(f"UPSC syllabus: {gs_text}")

    description_lines.extend(
        [
            "",
            "UPSC Issues by Kumar",
        ]
    )

    return {
        "issue_number": issue_number,
        "issue_id": issue_id,
        "youtube_title": youtube_title,
        "description": "\n".join(description_lines),
        "hashtags": hashtags,
    }


def build_metadata_document(
    data: dict[str, Any],
) -> tuple[str, datetime, int]:
    """Build the complete YouTube metadata document."""

    production_date = get_production_date(data)
    issues = get_issues(data)

    lines: list[str] = [
        "=" * 72,
        "TODAY'S UPSC ISSUES",
        "YOUTUBE SHORTS METADATA",
        production_date.strftime("%d %B %Y").upper(),
        "=" * 72,
        "",
    ]

    for index, issue in enumerate(issues, start=1):
        metadata = extract_metadata(
            issue=issue,
            fallback_number=index,
            production_date=production_date,
        )

        lines.extend(
            [
                "=" * 72,
                f"SHORT {metadata['issue_number']}",
                "=" * 72,
                "",
                f"ISSUE ID: "
                f"{metadata['issue_id'] or 'Not provided'}",
                "",
                "TITLE",
                metadata["youtube_title"],
                "",
                "DESCRIPTION",
                metadata["description"],
                "",
                "HASHTAGS",
                " ".join(metadata["hashtags"]),
                "",
            ]
        )

    document = "\n".join(lines).rstrip() + "\n"

    return document, production_date, len(issues)


def generate_youtube_metadata(
    input_file: Path,
    output_file: Path,
    overwrite: bool = True,
) -> tuple[Path, int]:
    """Generate the YouTube Shorts metadata file."""

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_file}"
        )

    data = load_json(input_file)

    document, _, issue_count = build_metadata_document(data)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        document,
        encoding="utf-8",
    )

    return output_file, issue_count


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Export YouTube Shorts metadata from "
            "DAILY_INPUT.json."
        )
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Optional path to DAILY_INPUT.json.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path.",
    )

    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not replace an existing output file.",
    )

    return parser.parse_args()


def main() -> int:
    """Run the metadata exporter."""

    args = parse_arguments()

    project_root = Path(__file__).resolve().parents[3]

    input_file = (
        args.input_file
        if args.input_file
        else find_default_input(project_root)
    )

    try:
        data = load_json(input_file)
        production_date = get_production_date(data)

        default_output = (
            project_root
            / "output"
            / "distribution"
            / production_date.strftime("%d-%m-%y")
            / "youtube_metadata.txt"
        )

        output_file = args.output or default_output

        created_file, issue_count = generate_youtube_metadata(
            input_file=input_file,
            output_file=output_file,
            overwrite=not args.no_overwrite,
        )

        print("=" * 72)
        print("YOUTUBE SHORTS METADATA GENERATED")
        print("=" * 72)
        print(f"Input  : {input_file}")
        print(f"Output : {created_file}")
        print(f"Shorts : {issue_count}")

        return 0

    except (
        YouTubeMetadataError,
        FileExistsError,
        OSError,
    ) as exc:
        print("=" * 72)
        print("YOUTUBE METADATA EXPORT FAILED")
        print("=" * 72)
        print(exc)

        return 1


if __name__ == "__main__":
    sys.exit(main())