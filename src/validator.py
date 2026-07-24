"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir
Dataset Validator
===========================================================

Validates the structured dataset after it has been parsed
by src/reader.py.

This file does not read files and does not generate PDFs.
"""

from datetime import datetime
from typing import Any

from src.config import (
    DATE_FORMAT,
    MIN_ISSUE_RATING,
    SELECTED_ISSUES,
)


# ===========================================================
# VALIDATION RESULT
# ===========================================================

def create_validation_result() -> dict[str, Any]:
    """
    Creates the standard validation result structure.
    """

    return {
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }


def add_error(
    result: dict[str, Any],
    message: str,
) -> None:
    """
    Adds an error and marks the dataset as invalid.
    """

    result["is_valid"] = False
    result["errors"].append(message)


def add_warning(
    result: dict[str, Any],
    message: str,
) -> None:
    """
    Adds a warning without marking the dataset as invalid.
    """

    result["warnings"].append(message)


# ===========================================================
# GENERAL HELPERS
# ===========================================================

def is_blank(value: Any) -> bool:
    """
    Returns True when a value is missing or contains only spaces.
    """

    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def count_words(value: str) -> int:
    """
    Counts words in a text value.
    """

    if not value:
        return 0

    return len(value.split())


def parse_rating(value: Any) -> float | None:
    """
    Converts ratings such as:

        4.5
        4.5/5
        5 / 5

    into a float.
    """

    if value is None:
        return None

    rating_text = str(value).strip()

    if not rating_text:
        return None

    if "/" in rating_text:
        rating_text = rating_text.split(
            "/",
            maxsplit=1,
        )[0].strip()

    try:
        return float(rating_text)
    except ValueError:
        return None


def parse_issue_number(value: Any) -> int | None:
    """
    Converts an issue number into an integer.
    """

    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ===========================================================
# DOCUMENT VALIDATION
# ===========================================================

def validate_paper(
    dataset: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """
    Validates the paper/source field.
    """

    paper = dataset.get("paper", "")

    if is_blank(paper):
        add_error(
            result,
            "PAPER is missing.",
        )


def validate_date(
    dataset: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """
    Validates the dataset date using config.DATE_FORMAT.
    """

    date_value = dataset.get("date", "")

    if is_blank(date_value):
        add_error(
            result,
            "DATE is missing.",
        )
        return

    try:
        datetime.strptime(
            str(date_value).strip(),
            DATE_FORMAT,
        )
    except ValueError:
        add_error(
            result,
            f"DATE must use the format {DATE_FORMAT}. "
            f"Received: {date_value}",
        )


def validate_issue_count(
    dataset: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """

     Confirms that three or four selected issues are present.
    """

    issues = dataset.get("issues", [])

    if not isinstance(issues, list):
        add_error(
            result,
            "ISSUES must be stored as a list.",
        )
        return

    issue_count = len(issues)

    if issue_count not in (3, 4):
        add_error(
        result,
        f"Three or four issues are required. Detected: {issue_count}."
    )


# ===========================================================
# ISSUE FIELD VALIDATION
# ===========================================================

def validate_required_text_field(
    issue: dict[str, Any],
    field_name: str,
    display_name: str,
    issue_position: int,
    result: dict[str, Any],
) -> None:
    """
    Validates a required text field.
    """

    value = issue.get(field_name, "")

    if is_blank(value):
        add_error(
            result,
            f"Issue {issue_position}: {display_name} is missing.",
        )


def validate_issue_number(
    issue: dict[str, Any],
    issue_position: int,
    result: dict[str, Any],
) -> int | None:
    """
    Validates the issue number and returns it when valid.
    """

    number = parse_issue_number(
        issue.get("issue_number")
    )

    if number is None:
        add_error(
            result,
            f"Issue {issue_position}: ISSUE NUMBER is invalid.",
        )
        return None

    if number < 1:
        add_error(
            result,
            f"Issue {issue_position}: ISSUE NUMBER must be positive.",
        )

    return number


def validate_rating(
    issue: dict[str, Any],
    issue_position: int,
    result: dict[str, Any],
) -> None:
    """
    Validates the UPSC relevance rating.
    """

    rating = parse_rating(
        issue.get("rating")
    )

    if rating is None:
        add_error(
            result,
            f"Issue {issue_position}: RATING is missing or invalid.",
        )
        return

    if rating < MIN_ISSUE_RATING:
        add_error(
            result,
            f"Issue {issue_position}: RATING must be at least "
            f"{MIN_ISSUE_RATING}/5. Received: {rating}/5.",
        )

    if rating > 5:
        add_error(
            result,
            f"Issue {issue_position}: RATING cannot exceed 5.",
        )


def validate_recall_questions(
    issue: dict[str, Any],
    issue_position: int,
    result: dict[str, Any],
) -> None:
    """
    Confirm that exactly one recall question is present.
    """

    questions = issue.get(
        "recall_questions",
        [],
    )

    if not isinstance(
        questions,
        list,
    ):
        add_error(
            result,
            f"Issue {issue_position}: "
            "RECALL QUESTIONS must be a list.",
        )
        return

    valid_questions = [
        question.strip()
        for question in questions
        if (
            isinstance(question, str)
            and question.strip()
        )
    ]

    if len(valid_questions) != 1:
        add_error(
            result,
            f"Issue {issue_position}: Exactly one recall question "
            f"are required. Detected: {len(valid_questions)}.",
        )
        return

    for question_number, question in enumerate(
        valid_questions,
        start=1,
    ):
        if not question.endswith("?"):
            add_warning(
                result,
                f"Issue {issue_position}: Recall Question "
                f"{question_number} does not end with a question mark.",
            )


def validate_quick_facts(
    issue: dict[str, Any],
    issue_position: int,
    result: dict[str, Any],
) -> None:
    """
    Confirms that exactly five non-empty Quick Facts are present.
    """

    facts = issue.get(
        "quick_facts",
        [],
    )

    if not isinstance(
        facts,
        list,
    ):
        add_error(
            result,
            f"Issue {issue_position}: QUICK FACTS must be a list.",
        )
        return

    valid_facts = [
        str(fact).strip()
        for fact in facts
        if str(fact).strip()
    ]

    if len(valid_facts) != 4:
        add_error(
            result,
            f"Issue {issue_position}: Exactly 4 Quick Facts "
            f"are required. Detected: {len(valid_facts)}.",
        )


def validate_text_length(
    issue: dict[str, Any],
    field_name: str,
    display_name: str,
    issue_position: int,
    result: dict[str, Any],
    minimum_words: int,
    maximum_words: int,
) -> None:
    """
    Checks whether a text field stays within a preferred word range.

    Word-length problems are warnings because final layout fitting
    will also be checked by the PDF engine.
    """

    value = issue.get(
        field_name,
        "",
    )

    if is_blank(value):
        return

    word_count = count_words(
        str(value)
    )

    if word_count < minimum_words:
        add_warning(
            result,
            f"Issue {issue_position}: {display_name} has "
            f"{word_count} words. Preferred minimum: {minimum_words}.",
        )

    if word_count > maximum_words:
        add_warning(
            result,
            f"Issue {issue_position}: {display_name} has "
            f"{word_count} words. Preferred maximum: {maximum_words}.",
        )


# ===========================================================
# COMPLETE ISSUE VALIDATION
# ===========================================================

def validate_issue(
    issue: dict[str, Any],
    issue_position: int,
    result: dict[str, Any],
) -> int | None:
    """
    Validates one complete UPSC issue.
    """

    if not isinstance(
        issue,
        dict,
    ):
        add_error(
            result,
            f"Issue {issue_position} is not a valid issue object.",
        )
        return None

    issue_number = validate_issue_number(
        issue,
        issue_position,
        result,
    )

    required_text_fields = {
        "issue_title": "ISSUE TITLE",
        "gs_paper": "GS PAPER",
        "subject": "SUBJECT",
        "current_context": "CURRENT CONTEXT",
        "why_it_matters": "WHY IT MATTERS FOR UPSC",
        "core_concept": "CORE CONCEPT",
        "challenges": "CHALLENGES",
        "way_forward": "WAY FORWARD",
        "what_upsc_asks": "WHAT UPSC ASKS",
        "key_takeaway": "KEY TAKEAWAY",
    }

    for (
        field_name,
        display_name,
    ) in required_text_fields.items():
        validate_required_text_field(
            issue,
            field_name,
            display_name,
            issue_position,
            result,
        )

    validate_rating(
        issue,
        issue_position,
        result,
    )

    validate_recall_questions(
        issue,
        issue_position,
        result,
    )

    validate_quick_facts(
        issue,
        issue_position,
        result,
    )

    preferred_lengths = {
        "current_context": (
            "CURRENT CONTEXT",
            20,
            70,
        ),
        "why_it_matters": (
            "WHY IT MATTERS FOR UPSC",
            20,
            70,
        ),
        "core_concept": (
            "CORE CONCEPT",
            20,
            90,
        ),
        "challenges": (
            "CHALLENGES",
            20,
            90,
        ),
        "way_forward": (
            "WAY FORWARD",
            20,
            90,
        ),
        "what_upsc_asks": (
            "WHAT UPSC ASKS",
            10,
            60,
        ),
        "key_takeaway": (
            "KEY TAKEAWAY",
            12,
            40,
        ),
    }

    for (
        field_name,
        settings,
    ) in preferred_lengths.items():
        (
            display_name,
            minimum_words,
            maximum_words,
        ) = settings

        validate_text_length(
            issue,
            field_name,
            display_name,
            issue_position,
            result,
            minimum_words,
            maximum_words,
        )

    return issue_number


# ===========================================================
# COMPLETE DATASET VALIDATION
# ===========================================================

def validate_dataset(
    dataset: dict[str, Any],
) -> dict[str, Any]:
    """
    Validates the complete parsed dataset.

    Returns:

        {
            "is_valid": True or False,
            "errors": [...],
            "warnings": [...]
        }
    """

    result = create_validation_result()

    if not isinstance(
        dataset,
        dict,
    ):
        add_error(
            result,
            "Dataset must be a dictionary.",
        )
        return result

    validate_paper(
        dataset,
        result,
    )

    validate_date(
        dataset,
        result,
    )

    validate_issue_count(
        dataset,
        result,
    )

    issues = dataset.get(
        "issues",
        [],
    )

    if not isinstance(
        issues,
        list,
    ):
        return result

    detected_numbers: list[int] = []

    for (
        issue_position,
        issue,
    ) in enumerate(
        issues,
        start=1,
    ):
        issue_number = validate_issue(
            issue,
            issue_position,
            result,
        )

        if issue_number is not None:
            detected_numbers.append(
                issue_number
            )

    if len(detected_numbers) != len(
        set(detected_numbers)
    ):
        add_error(
            result,
            "Duplicate ISSUE NUMBER values were detected.",
        )

    expected_numbers = list(
        range(
            1,
            len(issues) + 1,
        )
    )

    if (
        detected_numbers
        and sorted(detected_numbers)
        != expected_numbers
    ):
        add_warning(
            result,
            "Issue numbers are not sequential. "
            f"Expected: {expected_numbers}. "
            f"Detected: {sorted(detected_numbers)}.",
        )

    return result


# ===========================================================
# CONSOLE REPORT
# ===========================================================

def print_validation_report(
    result: dict[str, Any],
) -> None:
    """
    Prints a readable validation report.
    """

    print("=" * 60)
    print("DATASET VALIDATION")
    print("=" * 60)

    if result["is_valid"]:
        print("✓ Dataset structure is valid")
    else:
        print("✗ Dataset validation failed")

    if result["errors"]:
        print("\nERRORS")
        print("-" * 60)

        for error in result["errors"]:
            print(f"✗ {error}")

    if result["warnings"]:
        print("\nWARNINGS")
        print("-" * 60)

        for warning in result["warnings"]:
            print(f"⚠ {warning}")

    if (
        not result["errors"]
        and not result["warnings"]
    ):
        print(
            "✓ No errors or warnings detected"
        )

    print("=" * 60)


# ===========================================================
# DEVELOPMENT TEST
# ===========================================================

if __name__ == "__main__":

    from src.reader import read_today_dataset

    try:
        data = read_today_dataset()
        validation = validate_dataset(data)
        print_validation_report(validation)

    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        print("\nERROR")
        print("-" * 60)
        print(error)