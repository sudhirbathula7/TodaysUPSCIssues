"""
============================================================
TODAY'S UPSC ISSUES
ISSUE SIMILARITY ENGINE
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Compares two UPSC issue records and calculates a similarity
score from 0 to 100.

SCORING FACTORS

1. Title similarity
2. Weighted keyword similarity
3. Phrase similarity
4. Category similarity
5. GS paper match

This module only calculates similarity.
It does not decide whether an issue is a duplicate.
============================================================
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT MODULES
# ============================================================

from src.intelligence.keywords import (  # noqa: E402
    KeywordExtractionError,
    KeywordResult,
    extract_keywords,
)
from src.intelligence.repository_search import (  # noqa: E402
    RepositorySearchError,
    list_issue_summaries,
    load_issue_record,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class SimilarityError(Exception):
    """Base exception for similarity errors."""


class InvalidSimilarityIssueError(SimilarityError):
    """Raised when an issue cannot be compared."""


# ============================================================
# SCORE WEIGHTS
# ============================================================

TITLE_WEIGHT = 0.30
KEYWORD_WEIGHT = 0.35
PHRASE_WEIGHT = 0.20
CATEGORY_WEIGHT = 0.10
GS_PAPER_WEIGHT = 0.05

TOTAL_WEIGHT = (
    TITLE_WEIGHT
    + KEYWORD_WEIGHT
    + PHRASE_WEIGHT
    + CATEGORY_WEIGHT
    + GS_PAPER_WEIGHT
)

if abs(TOTAL_WEIGHT - 1.0) > 0.0001:
    raise ValueError(
        "Similarity weights must total 1.0."
    )


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """Complete comparison result for two issues."""

    issue_a_id: str
    issue_a_title: str

    issue_b_id: str
    issue_b_title: str

    overall_similarity: float
    title_similarity: float
    keyword_similarity: float
    phrase_similarity: float
    category_similarity: float
    gs_paper_similarity: float

    shared_keywords: tuple[str, ...]
    shared_phrases: tuple[str, ...]

    only_issue_a_keywords: tuple[str, ...]
    only_issue_b_keywords: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a serialisable dictionary."""

        return {
            "issue_a": {
                "issue_id": self.issue_a_id,
                "title": self.issue_a_title,
            },
            "issue_b": {
                "issue_id": self.issue_b_id,
                "title": self.issue_b_title,
            },
            "scores": {
                "overall_similarity": self.overall_similarity,
                "title_similarity": self.title_similarity,
                "keyword_similarity": self.keyword_similarity,
                "phrase_similarity": self.phrase_similarity,
                "category_similarity": self.category_similarity,
                "gs_paper_similarity": self.gs_paper_similarity,
            },
            "shared_keywords": list(
                self.shared_keywords
            ),
            "shared_phrases": list(
                self.shared_phrases
            ),
            "only_issue_a_keywords": list(
                self.only_issue_a_keywords
            ),
            "only_issue_b_keywords": list(
                self.only_issue_b_keywords
            ),
        }


# ============================================================
# TEXT HELPERS
# ============================================================

def _normalise_text(value: Any) -> str:
    """Return clean lowercase comparison text."""

    if value is None:
        return ""

    text = str(value).lower()

    text = (
        text.replace("’", "'")
        .replace("–", " ")
        .replace("—", " ")
        .replace("-", " ")
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\s']+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _normalise_title(value: Any) -> str:
    """Normalise issue titles for comparison."""

    text = _normalise_text(
        value
    )

    text = re.sub(
        r"\bindia'?s\b",
        " ",
        text,
    )

    text = re.sub(
        r"\bindian\b",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _token_set(value: Any) -> set[str]:
    """Convert text into a token set."""

    return {
        token
        for token in _normalise_text(value).split()
        if len(token) >= 3
    }


def _clamp_score(value: float) -> float:
    """Keep a score between 0 and 100."""

    return round(
        max(
            0.0,
            min(
                100.0,
                value,
            ),
        ),
        2,
    )


# ============================================================
# BASIC SIMILARITY METRICS
# ============================================================

def _sequence_similarity(
    text_a: str,
    text_b: str,
) -> float:
    """Calculate character-sequence similarity."""

    if not text_a or not text_b:
        return 0.0

    ratio = SequenceMatcher(
        None,
        text_a,
        text_b,
    ).ratio()

    return ratio * 100


def _jaccard_similarity(
    values_a: set[str],
    values_b: set[str],
) -> float:
    """Calculate set-based Jaccard similarity."""

    if not values_a and not values_b:
        return 100.0

    if not values_a or not values_b:
        return 0.0

    intersection = values_a & values_b
    union = values_a | values_b

    if not union:
        return 0.0

    return (
        len(intersection)
        / len(union)
        * 100
    )


def _weighted_jaccard_similarity(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
) -> float:
    """Calculate weighted Jaccard similarity."""

    all_keywords = (
        set(scores_a)
        | set(scores_b)
    )

    if not all_keywords:
        return 0.0

    minimum_total = 0.0
    maximum_total = 0.0

    for keyword in all_keywords:
        score_a = float(
            scores_a.get(
                keyword,
                0.0,
            )
        )

        score_b = float(
            scores_b.get(
                keyword,
                0.0,
            )
        )

        minimum_total += min(
            score_a,
            score_b,
        )

        maximum_total += max(
            score_a,
            score_b,
        )

    if maximum_total <= 0:
        return 0.0

    return (
        minimum_total
        / maximum_total
        * 100
    )


# ============================================================
# TITLE SIMILARITY
# ============================================================

def calculate_title_similarity(
    title_a: str,
    title_b: str,
) -> float:
    """
    Calculate title similarity using both sequence and
    token overlap.
    """

    normalised_a = _normalise_title(
        title_a
    )

    normalised_b = _normalise_title(
        title_b
    )

    if not normalised_a or not normalised_b:
        return 0.0

    sequence_score = _sequence_similarity(
        normalised_a,
        normalised_b,
    )

    token_score = _jaccard_similarity(
        _token_set(normalised_a),
        _token_set(normalised_b),
    )

    combined_score = (
        sequence_score * 0.55
        + token_score * 0.45
    )

    return _clamp_score(
        combined_score
    )


# ============================================================
# KEYWORD SIMILARITY
# ============================================================

def calculate_keyword_similarity(
    keywords_a: KeywordResult,
    keywords_b: KeywordResult,
) -> float:
    """Calculate weighted keyword similarity."""

    score = _weighted_jaccard_similarity(
        keywords_a.scores,
        keywords_b.scores,
    )

    return _clamp_score(
        score
    )


# ============================================================
# PHRASE SIMILARITY
# ============================================================

def calculate_phrase_similarity(
    keywords_a: KeywordResult,
    keywords_b: KeywordResult,
) -> float:
    """Calculate known-phrase overlap."""

    phrases_a = set(
        keywords_a.phrases
    )

    phrases_b = set(
        keywords_b.phrases
    )

    score = _jaccard_similarity(
        phrases_a,
        phrases_b,
    )

    return _clamp_score(
        score
    )


# ============================================================
# CATEGORY SIMILARITY
# ============================================================

def calculate_category_similarity(
    category_a: str,
    category_b: str,
) -> float:
    """
    Calculate category overlap.

    If both categories are empty, treat them as matching.
    If only one is empty, return zero.
    """

    tokens_a = _token_set(
        category_a
    )

    tokens_b = _token_set(
        category_b
    )

    if not tokens_a and not tokens_b:
        return 100.0

    if not tokens_a or not tokens_b:
        return 0.0

    score = _jaccard_similarity(
        tokens_a,
        tokens_b,
    )

    return _clamp_score(
        score
    )

# ============================================================
# GS PAPER SIMILARITY
# ============================================================

def calculate_gs_paper_similarity(
    gs_paper_a: str,
    gs_paper_b: str,
) -> float:
    """Return 100 when GS papers match exactly."""

    value_a = _normalise_text(
        gs_paper_a
    )

    value_b = _normalise_text(
        gs_paper_b
    )

    if not value_a or not value_b:
        return 0.0

    if value_a == value_b:
        return 100.0

    return 0.0


# ============================================================
# VALIDATION
# ============================================================

def _validate_issue(
    issue: dict[str, Any],
    label: str,
) -> None:
    """Validate one issue record."""

    if not isinstance(issue, dict):
        raise InvalidSimilarityIssueError(
            f"{label} must be a dictionary."
        )

    issue_id = str(
        issue.get(
            "issue_id",
            "",
        )
    ).strip()

    title = str(
        issue.get(
            "title",
            "",
        )
    ).strip()

    if not issue_id:
        raise InvalidSimilarityIssueError(
            f"{label} does not contain issue_id."
        )

    if not title:
        raise InvalidSimilarityIssueError(
            f"{label} does not contain title."
        )


# ============================================================
# MAIN COMPARISON
# ============================================================

def compare_issues(
    issue_a: dict[str, Any],
    issue_b: dict[str, Any],
) -> SimilarityResult:
    """Compare two complete issue records."""

    _validate_issue(
        issue_a,
        "Issue A",
    )

    _validate_issue(
        issue_b,
        "Issue B",
    )

    issue_a_id = str(
        issue_a["issue_id"]
    )

    issue_b_id = str(
        issue_b["issue_id"]
    )

    issue_a_title = str(
        issue_a["title"]
    )

    issue_b_title = str(
        issue_b["title"]
    )

    try:
        keywords_a = extract_keywords(
            issue_a
        )

        keywords_b = extract_keywords(
            issue_b
        )

    except KeywordExtractionError as error:
        raise SimilarityError(
            str(error)
        ) from error

    title_similarity = calculate_title_similarity(
        issue_a_title,
        issue_b_title,
    )

    keyword_similarity = calculate_keyword_similarity(
        keywords_a,
        keywords_b,
    )

    phrase_similarity = calculate_phrase_similarity(
        keywords_a,
        keywords_b,
    )

    category_similarity = calculate_category_similarity(
        str(
            issue_a.get(
                "category",
                "",
            )
        ),
        str(
            issue_b.get(
                "category",
                "",
            )
        ),
    )

    gs_paper_similarity = calculate_gs_paper_similarity(
        str(
            issue_a.get(
                "gs_paper",
                "",
            )
        ),
        str(
            issue_b.get(
                "gs_paper",
                "",
            )
        ),
    )

    overall_similarity = (
        title_similarity
        * TITLE_WEIGHT

        + keyword_similarity
        * KEYWORD_WEIGHT

        + phrase_similarity
        * PHRASE_WEIGHT

        + category_similarity
        * CATEGORY_WEIGHT

        + gs_paper_similarity
        * GS_PAPER_WEIGHT
    )

    shared_keywords = sorted(
        set(keywords_a.keywords)
        & set(keywords_b.keywords)
    )

    shared_phrases = sorted(
        set(keywords_a.phrases)
        & set(keywords_b.phrases)
    )

    only_issue_a_keywords = sorted(
        set(keywords_a.keywords)
        - set(keywords_b.keywords)
    )

    only_issue_b_keywords = sorted(
        set(keywords_b.keywords)
        - set(keywords_a.keywords)
    )

    return SimilarityResult(
        issue_a_id=issue_a_id,
        issue_a_title=issue_a_title,

        issue_b_id=issue_b_id,
        issue_b_title=issue_b_title,

        overall_similarity=_clamp_score(
            overall_similarity
        ),

        title_similarity=_clamp_score(
            title_similarity
        ),

        keyword_similarity=_clamp_score(
            keyword_similarity
        ),

        phrase_similarity=_clamp_score(
            phrase_similarity
        ),

        category_similarity=_clamp_score(
            category_similarity
        ),

        gs_paper_similarity=_clamp_score(
            gs_paper_similarity
        ),

        shared_keywords=tuple(
            shared_keywords
        ),

        shared_phrases=tuple(
            shared_phrases
        ),

        only_issue_a_keywords=tuple(
            only_issue_a_keywords
        ),

        only_issue_b_keywords=tuple(
            only_issue_b_keywords
        ),
    )


# ============================================================
# REPOSITORY COMPARISON
# ============================================================

def compare_issue_ids(
    issue_a_id: str,
    issue_b_id: str,
) -> SimilarityResult:
    """Load and compare two repository issues."""

    try:
        issue_a = load_issue_record(
            issue_a_id
        )

        issue_b = load_issue_record(
            issue_b_id
        )

    except RepositorySearchError as error:
        raise SimilarityError(
            str(error)
        ) from error

    return compare_issues(
        issue_a,
        issue_b,
    )


# ============================================================
# SELF COMPARISON
# ============================================================

def compare_issue_with_itself(
    issue_id: str,
) -> SimilarityResult:
    """Development helper for validating a perfect match."""

    issue = load_issue_record(
        issue_id
    )

    return compare_issues(
        issue,
        issue,
    )


# ============================================================
# DISPLAY
# ============================================================

def print_similarity_result(
    result: SimilarityResult,
) -> None:
    """Print a readable comparison report."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("ISSUE SIMILARITY REPORT")
    print("=" * 72)

    print(
        f"Issue A : {result.issue_a_title}"
    )

    print(
        f"ID      : {result.issue_a_id}"
    )

    print()

    print(
        f"Issue B : {result.issue_b_title}"
    )

    print(
        f"ID      : {result.issue_b_id}"
    )

    print("-" * 72)

    print(
        f"Overall similarity : "
        f"{result.overall_similarity:>6.2f}%"
    )

    print(
        f"Title similarity   : "
        f"{result.title_similarity:>6.2f}%"
    )

    print(
        f"Keyword similarity : "
        f"{result.keyword_similarity:>6.2f}%"
    )

    print(
        f"Phrase similarity  : "
        f"{result.phrase_similarity:>6.2f}%"
    )

    print(
        f"Category similarity: "
        f"{result.category_similarity:>6.2f}%"
    )

    print(
        f"GS paper similarity: "
        f"{result.gs_paper_similarity:>6.2f}%"
    )

    print("-" * 72)
    print("SHARED KEYWORDS")

    if result.shared_keywords:
        for keyword in result.shared_keywords:
            print(
                f"• {keyword}"
            )
    else:
        print("No shared keywords.")

    print("-" * 72)
    print("SHARED PHRASES")

    if result.shared_phrases:
        for phrase in result.shared_phrases:
            print(
                f"• {phrase}"
            )
    else:
        print("No shared phrases.")

    print("=" * 72)


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Run a self-comparison using the latest issue."""

    print("=" * 72)
    print("TODAY'S UPSC ISSUES")
    print("SIMILARITY ENGINE — VERSION 2.1")
    print("=" * 72)

    summaries = list_issue_summaries()

    if not summaries:
        print("No repository issues are available.")
        print("=" * 72)
        return

    latest_issue_id = summaries[0].issue_id

    result = compare_issue_with_itself(
        latest_issue_id
    )

    print_similarity_result(
        result
    )

    print("✓ Title comparison enabled")
    print("✓ Weighted keyword comparison enabled")
    print("✓ Phrase comparison enabled")
    print("✓ Category comparison enabled")
    print("✓ GS paper comparison enabled")
    print("✓ Overall weighted score enabled")
    print("=" * 72)


if __name__ == "__main__":
    _development_test()