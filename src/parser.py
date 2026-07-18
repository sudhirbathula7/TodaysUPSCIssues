"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir
Dataset Parser and Internal Data Models
===========================================================

Converts the validated dictionary returned by reader.py into
clean dataclass objects used by the PDF engine.

This file does not read input files directly and does not
generate PDFs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.config import DATE_FORMAT
from src.validator import (
    parse_issue_number,
    parse_rating,
    validate_dataset,
)


# ===========================================================
# EXCEPTIONS
# ===========================================================

class DatasetParsingError(ValueError):
    """
    Raised when a dataset cannot be safely converted into
    internal dataclass objects.
    """


# ===========================================================
# INTERNAL DATA MODELS
# ===========================================================

@dataclass(slots=True)
class Issue:
    """
    Represents one complete UPSC issue.
    """

    issue_number: int
    issue_title: str
    gs_paper: str
    subject: str
    rating: float

    recall_questions: list[str] = field(default_factory=list)

    current_context: str = ""
    why_it_matters: str = ""
    core_concept: str = ""
    challenges: str = ""
    way_forward: str = ""
    quick_facts: list[str] = field(default_factory=list)
    what_upsc_asks: str = ""
    key_takeaway: str = ""

    @property
    def display_rating(self) -> str:
        """
        Returns the rating in a user-friendly format.

        Example:
            4.8 -> 4.8/5
            5.0 -> 5/5
        """

        if self.rating.is_integer():
            return f"{int(self.rating)}/5"

        return f"{self.rating:.1f}/5"

    @property
    def display_number(self) -> str:
        """
        Returns the issue number as display text.
        """

        return str(self.issue_number)

    @property
    def recall_question_1(self) -> str:
        """
        Returns the first recall question.
        """

        if len(self.recall_questions) >= 1:
            return self.recall_questions[0]

        return ""

    @property
    def recall_question_2(self) -> str:
        """
        Returns the second recall question.
        """

        if len(self.recall_questions) >= 2:
            return self.recall_questions[1]

        return ""


@dataclass(slots=True)
class DailyIssueBook:
    """
    Represents the complete daily publication dataset.
    """

    paper: str
    publication_date: datetime
    issues: list[Issue] = field(default_factory=list)

    @property
    def date_text(self) -> str:
        """
        Returns the date using the configured input date format.
        """

        return self.publication_date.strftime(DATE_FORMAT)

    @property
    def formatted_date(self) -> str:
        """
        Returns a publication-friendly date.

        Example:
            14 July 2026
        """

        return self.publication_date.strftime("%d %B %Y")

    @property
    def issue_count(self) -> int:
        """
        Returns the number of issues in the publication.
        """

        return len(self.issues)

    @property
    def issue_numbers(self) -> list[int]:
        """
        Returns all issue numbers in publication order.
        """

        return [
            issue.issue_number
            for issue in self.issues
        ]


# ===========================================================
# TEXT NORMALISATION
# ===========================================================

def normalise_text(value: Any) -> str:
    """
    Converts a value to clean single-spaced text.

    Existing line breaks are preserved so that bullet-style
    content can still be rendered correctly later.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    cleaned_lines: list[str] = []

    for line in text.splitlines():
        cleaned_line = " ".join(line.strip().split())

        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    return "\n".join(cleaned_lines)


def normalise_questions(value: Any) -> list[str]:
    """
    Converts recall-question data into a clean list.
    """

    if not isinstance(value, list):
        return []

    questions: list[str] = []

    for question in value:
        cleaned_question = normalise_text(question)

        if cleaned_question:
            questions.append(cleaned_question)

    return questions

def normalise_quick_facts(value: Any) -> list[str]:
    """
    Converts quick facts into a clean list.
    """

    if not isinstance(value, list):
        return []

    facts: list[str] = []

    for fact in value:
        cleaned = normalise_text(fact)

        if cleaned:
            facts.append(cleaned)

    return facts

def normalise_gs_paper(value: Any) -> str:
    """
    Normalises common GS Paper formats.

    Examples:
        gs2       -> GS II
        GS 2      -> GS II
        paper iii -> GS III
        GS IV     -> GS IV
    """

    text = normalise_text(value).upper()

    replacements = {
        "GS1": "GS I",
        "GS 1": "GS I",
        "PAPER I": "GS I",
        "PAPER 1": "GS I",

        "GS2": "GS II",
        "GS 2": "GS II",
        "PAPER II": "GS II",
        "PAPER 2": "GS II",

        "GS3": "GS III",
        "GS 3": "GS III",
        "PAPER III": "GS III",
        "PAPER 3": "GS III",

        "GS4": "GS IV",
        "GS 4": "GS IV",
        "PAPER IV": "GS IV",
        "PAPER 4": "GS IV",
    }

    return replacements.get(text, text)


# ===========================================================
# DATE PARSING
# ===========================================================

def parse_publication_date(value: Any) -> datetime:
    """
    Converts the dataset date into a datetime object.
    """

    date_text = normalise_text(value)

    try:
        return datetime.strptime(date_text, DATE_FORMAT)
    except ValueError as error:
        raise DatasetParsingError(
            f"Unable to parse publication date: {date_text}"
        ) from error


# ===========================================================
# ISSUE PARSING
# ===========================================================

def parse_issue(raw_issue: dict[str, Any]) -> Issue:
    """
    Converts one validated issue dictionary into an Issue object.
    """

    issue_number = parse_issue_number(
        raw_issue.get("issue_number")
    )

    rating = parse_rating(
        raw_issue.get("rating")
    )

    if issue_number is None:
        raise DatasetParsingError(
            "Unable to parse ISSUE NUMBER."
        )

    if rating is None:
        raise DatasetParsingError(
            f"Issue {issue_number}: Unable to parse RATING."
        )

    return Issue(
        issue_number=issue_number,
        issue_title=normalise_text(
            raw_issue.get("issue_title")
        ),
        gs_paper=normalise_gs_paper(
            raw_issue.get("gs_paper")
        ),
        subject=normalise_text(
            raw_issue.get("subject")
        ),
        rating=rating,
        recall_questions=normalise_questions(
            raw_issue.get("recall_questions")
        ),
        current_context=normalise_text(
            raw_issue.get("current_context")
        ),
        why_it_matters=normalise_text(
            raw_issue.get("why_it_matters")
        ),
        core_concept=normalise_text(
            raw_issue.get("core_concept")
        ),
        challenges=normalise_text(
            raw_issue.get("challenges")
        ),
        way_forward=normalise_text(
            raw_issue.get("way_forward")
        ),
        quick_facts=normalise_quick_facts(
        raw_issue.get("quick_facts")
        ),
        what_upsc_asks=normalise_text(
            raw_issue.get("what_upsc_asks")
        ),
        key_takeaway=normalise_text(
            raw_issue.get("key_takeaway")
        ),
    )


# ===========================================================
# COMPLETE DATASET PARSING
# ===========================================================

def parse_validated_dataset(
    dataset: dict[str, Any],
) -> DailyIssueBook:
    """
    Converts a valid dataset dictionary into a DailyIssueBook.

    The dataset is validated again before conversion so that
    invalid data cannot silently reach the PDF engine.
    """

    validation_result = validate_dataset(dataset)

    if not validation_result["is_valid"]:
        error_message = "\n".join(
            f"- {error}"
            for error in validation_result["errors"]
        )

        raise DatasetParsingError(
            "Dataset parsing stopped because validation failed:\n"
            f"{error_message}"
        )

    raw_issues = dataset.get("issues", [])

    parsed_issues = [
        parse_issue(raw_issue)
        for raw_issue in raw_issues
    ]

    parsed_issues.sort(
        key=lambda issue: issue.issue_number
    )

    return DailyIssueBook(
        paper=normalise_text(
            dataset.get("paper")
        ),
        publication_date=parse_publication_date(
            dataset.get("date")
        ),
        issues=parsed_issues,
    )


# ===========================================================
# CONSOLE REPORT
# ===========================================================

def print_parsed_book(book: DailyIssueBook) -> None:
    """
    Prints a readable summary of the parsed publication.
    """

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — PARSER")
    print("=" * 60)

    print(f"Paper  : {book.paper}")
    print(f"Date   : {book.formatted_date}")
    print(f"Issues : {book.issue_count}")

    print("-" * 60)

    for issue in book.issues:
        print(
            f"{issue.issue_number}. "
            f"{issue.issue_title} "
            f"[{issue.gs_paper} | {issue.display_rating}]"
        )

    print("-" * 60)
    print("✓ Dataset converted into dataclass objects")
    print("=" * 60)


# ===========================================================
# DEVELOPMENT TEST
# ===========================================================

if __name__ == "__main__":

    from src.reader import read_today_dataset

    try:
        raw_dataset = read_today_dataset()
        issue_book = parse_validated_dataset(raw_dataset)
        print_parsed_book(issue_book)

    except (
        FileNotFoundError,
        ValueError,
        DatasetParsingError,
    ) as error:
        print("\nERROR")
        print("-" * 60)
        print(error)