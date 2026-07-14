"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir
Dataset Reader
===========================================================

Reads the structured issue dataset created by ChatGPT.

This file only reads and parses data.
Validation will be handled separately by validator.py.
"""

import os
import re
from typing import Any

from config import INPUT_DIR, SELECTED_ISSUES


# ===========================================================
# SUPPORTED DATASET LABELS
# ===========================================================

DOCUMENT_LABELS = {
    "PAPER",
    "DATE",
}

ISSUE_LABELS = {
    "ISSUE NUMBER",
    "ISSUE TITLE",
    "GS PAPER",
    "SUBJECT",
    "RATING",
    "RECALL QUESTION 1",
    "RECALL QUESTION 2",
    "CURRENT CONTEXT",
    "WHY IT MATTERS FOR UPSC",
    "CORE CONCEPT",
    "CHALLENGES",
    "WAY FORWARD",
    "QUICK FACTS",
    "WHAT UPSC ASKS",
    "KEY TAKEAWAY",
}

ALL_LABELS = DOCUMENT_LABELS | ISSUE_LABELS


# ===========================================================
# TEXT CLEANING
# ===========================================================

def clean_text(value: str) -> str:
    """
    Cleans unnecessary whitespace while preserving readable text.
    """

    if not value:
        return ""

    value = value.strip()

    lines = [
        re.sub(r"\s+", " ", line.strip())
        for line in value.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


def normalise_label(value: str) -> str:
    """
    Converts a dataset label into a standard uppercase format.

    Example:
        Issue Title:  -> ISSUE TITLE
        issue_title   -> ISSUE TITLE
    """

    value = value.strip().rstrip(":")
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)

    return value.upper()


# ===========================================================
# FILE READING
# ===========================================================

def read_text_file(filepath: str) -> str:
    """
    Reads a UTF-8 text file and returns its contents.
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Input file not found:\n{filepath}"
        )

    if not os.path.isfile(filepath):
        raise ValueError(
            f"The supplied path is not a file:\n{filepath}"
        )

    try:
        with open(filepath, "r", encoding="utf-8-sig") as file:
            content = file.read()
    except UnicodeDecodeError as error:
        raise ValueError(
            f"Unable to read the file as UTF-8:\n{filepath}"
        ) from error

    if not content.strip():
        raise ValueError(
            f"Input file is empty:\n{filepath}"
        )

    return content


# ===========================================================
# LABEL DETECTION
# ===========================================================

def detect_label(line: str) -> str | None:
    """
    Checks whether a line is a supported dataset label.

    Labels may be written as:

        ISSUE TITLE:
        ISSUE TITLE
    """

    candidate = normalise_label(line)

    if candidate in ALL_LABELS:
        return candidate

    return None


# ===========================================================
# GENERIC LABEL PARSER
# ===========================================================

def parse_labelled_content(content: str) -> list[tuple[str, str]]:
    """
    Converts labelled text into ordered label-value pairs.

    Multi-line values are supported.
    """

    parsed_items: list[tuple[str, str]] = []

    current_label: str | None = None
    current_value_lines: list[str] = []

    def save_current_item() -> None:
        nonlocal current_label, current_value_lines

        if current_label is None:
            return

        value = clean_text("\n".join(current_value_lines))
        parsed_items.append((current_label, value))

        current_label = None
        current_value_lines = []

    for raw_line in content.splitlines():
        stripped_line = raw_line.strip()

        # Ignore visual separators.
        if stripped_line and set(stripped_line) <= {"=", "-", "_"}:
            continue

        detected_label = detect_label(stripped_line)

        if detected_label:
            save_current_item()
            current_label = detected_label
            continue

        if current_label is not None:
            current_value_lines.append(raw_line)

    save_current_item()

    return parsed_items


# ===========================================================
# ISSUE CREATION
# ===========================================================

def create_empty_issue() -> dict[str, Any]:
    """
    Returns the standard internal structure for one issue.
    """

    return {
        "issue_number": "",
        "issue_title": "",
        "gs_paper": "",
        "subject": "",
        "rating": "",
        "recall_questions": [],
        "current_context": "",
        "why_it_matters": "",
        "core_concept": "",
        "challenges": "",
        "way_forward": "",
        "quick_facts": "",
        "what_upsc_asks": "",
        "key_takeaway": "",
    }


def assign_issue_value(
    issue: dict[str, Any],
    label: str,
    value: str,
) -> None:
    """
    Assigns a parsed value to the correct internal issue field.
    """

    field_mapping = {
        "ISSUE NUMBER": "issue_number",
        "ISSUE TITLE": "issue_title",
        "GS PAPER": "gs_paper",
        "SUBJECT": "subject",
        "RATING": "rating",
        "CURRENT CONTEXT": "current_context",
        "WHY IT MATTERS FOR UPSC": "why_it_matters",
        "CORE CONCEPT": "core_concept",
        "CHALLENGES": "challenges",
        "WAY FORWARD": "way_forward",
        "QUICK FACTS": "quick_facts",
        "WHAT UPSC ASKS": "what_upsc_asks",
        "KEY TAKEAWAY": "key_takeaway",
    }

    if label == "RECALL QUESTION 1":
        issue["recall_questions"].append(value)
        return

    if label == "RECALL QUESTION 2":
        issue["recall_questions"].append(value)
        return

    field_name = field_mapping.get(label)

    if field_name:
        issue[field_name] = value


# ===========================================================
# COMPLETE DATASET PARSER
# ===========================================================

def parse_dataset(content: str) -> dict[str, Any]:
    """
    Parses the complete daily dataset.

    Returns:

        {
            "paper": "...",
            "date": "...",
            "issues": [...]
        }
    """

    parsed_items = parse_labelled_content(content)

    dataset: dict[str, Any] = {
        "paper": "",
        "date": "",
        "issues": [],
    }

    current_issue: dict[str, Any] | None = None

    for label, value in parsed_items:

        if label == "PAPER":
            dataset["paper"] = value
            continue

        if label == "DATE":
            dataset["date"] = value
            continue

        if label == "ISSUE NUMBER":
            if current_issue is not None:
                dataset["issues"].append(current_issue)

            current_issue = create_empty_issue()
            assign_issue_value(current_issue, label, value)
            continue

        if current_issue is not None:
            assign_issue_value(current_issue, label, value)

    if current_issue is not None:
        dataset["issues"].append(current_issue)

    return dataset


# ===========================================================
# PUBLIC READER FUNCTION
# ===========================================================

def read_dataset(filepath: str) -> dict[str, Any]:
    """
    Reads and parses one structured daily dataset file.
    """

    content = read_text_file(filepath)
    dataset = parse_dataset(content)

    return dataset


def get_default_input_file() -> str:
    """
    Returns the standard daily dataset input path.
    """

    return os.path.join(INPUT_DIR, "todays_issues.txt")


def read_today_dataset() -> dict[str, Any]:
    """
    Reads input/todays_issues.txt using the standard project path.
    """

    return read_dataset(get_default_input_file())


# ===========================================================
# DEVELOPMENT TEST
# ===========================================================

if __name__ == "__main__":

    try:
        data = read_today_dataset()

        print("=" * 60)
        print("TODAY'S UPSC ISSUES — DATASET READER")
        print("=" * 60)

        print(f"Paper  : {data['paper'] or 'Not found'}")
        print(f"Date   : {data['date'] or 'Not found'}")
        print(f"Issues : {len(data['issues'])}")

        print("-" * 60)

        for index, issue in enumerate(data["issues"], start=1):
            title = issue["issue_title"] or "Untitled issue"
            print(f"{index}. {title}")

        print("-" * 60)

        if len(data["issues"]) == SELECTED_ISSUES:
            print(f"✓ Expected {SELECTED_ISSUES} issues detected")
        else:
            print(
                f"⚠ Expected {SELECTED_ISSUES} issues, "
                f"but detected {len(data['issues'])}"
            )

        print("=" * 60)

    except (FileNotFoundError, ValueError) as error:
        print("\nERROR")
        print("-" * 60)
        print(error)