"""
============================================================
TODAY'S UPSC ISSUES
DUPLICATE AND RELATED ISSUE DETECTOR
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Compares a new issue against the permanent repository and
identifies:

1. Possible duplicates
2. Strongly related issues
3. Related issues
4. Distinct issues

CLASSIFICATION

90–100  Possible Duplicate
70–89   Strongly Related
50–69   Related
0–49    Distinct

The detector uses the similarity engine. It does not calculate
its own similarity scores.
============================================================
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# PROJECT IMPORT SUPPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT MODULES
# ============================================================

from src.intelligence.repository_search import (  # noqa: E402
    RepositorySearchError,
    list_issue_summaries,
    load_all_issue_records,
    load_issue_record,
)
from src.intelligence.similarity import (  # noqa: E402
    SimilarityError,
    SimilarityResult,
    compare_issues,
)


# ============================================================
# CLASSIFICATION THRESHOLDS
# ============================================================

POSSIBLE_DUPLICATE_THRESHOLD = 90.0
STRONGLY_RELATED_THRESHOLD = 70.0
RELATED_THRESHOLD = 50.0


# ============================================================
# EXCEPTIONS
# ============================================================

class DuplicateDetectorError(Exception):
    """Base exception for duplicate-detector errors."""


class InvalidCandidateIssueError(DuplicateDetectorError):
    """Raised when a candidate issue is invalid."""


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass(frozen=True, slots=True)
class DuplicateMatch:
    """One repository match for a candidate issue."""

    issue_id: str
    title: str
    publication_date: str
    similarity: float
    classification: str
    reason: str
    shared_keywords: tuple[str, ...]
    shared_phrases: tuple[str, ...]
    title_similarity: float
    keyword_similarity: float
    phrase_similarity: float
    category_similarity: float
    gs_paper_similarity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert the match into a serialisable dictionary."""

        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "publication_date": self.publication_date,
            "similarity": self.similarity,
            "classification": self.classification,
            "reason": self.reason,
            "shared_keywords": list(self.shared_keywords),
            "shared_phrases": list(self.shared_phrases),
            "scores": {
                "title": self.title_similarity,
                "keyword": self.keyword_similarity,
                "phrase": self.phrase_similarity,
                "category": self.category_similarity,
                "gs_paper": self.gs_paper_similarity,
            },
        }


@dataclass(frozen=True, slots=True)
class DuplicateScanResult:
    """Complete repository scan for one candidate issue."""

    candidate_issue_id: str
    candidate_title: str
    repository_issue_count: int
    compared_issue_count: int
    highest_similarity: float
    overall_classification: str
    possible_duplicate: bool
    matches: tuple[DuplicateMatch, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the scan result into a dictionary."""

        return {
            "candidate": {
                "issue_id": self.candidate_issue_id,
                "title": self.candidate_title,
            },
            "repository_issue_count": self.repository_issue_count,
            "compared_issue_count": self.compared_issue_count,
            "highest_similarity": self.highest_similarity,
            "overall_classification": self.overall_classification,
            "possible_duplicate": self.possible_duplicate,
            "matches": [
                match.to_dict()
                for match in self.matches
            ],
        }


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_similarity(score: float) -> str:
    """Convert a similarity score into a classification."""

    if score >= POSSIBLE_DUPLICATE_THRESHOLD:
        return "POSSIBLE DUPLICATE"

    if score >= STRONGLY_RELATED_THRESHOLD:
        return "STRONGLY RELATED"

    if score >= RELATED_THRESHOLD:
        return "RELATED"

    return "DISTINCT"


# ============================================================
# VALIDATION
# ============================================================

def _validate_candidate_issue(
    issue: dict[str, Any],
) -> None:
    """Validate a candidate issue before repository scanning."""

    if not isinstance(issue, dict):
        raise InvalidCandidateIssueError(
            "Candidate issue must be a dictionary."
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
        raise InvalidCandidateIssueError(
            "Candidate issue does not contain issue_id."
        )

    if not title:
        raise InvalidCandidateIssueError(
            "Candidate issue does not contain title."
        )


# ============================================================
# MATCH REASON
# ============================================================

def _build_match_reason(
    result: SimilarityResult,
) -> str:
    """Create a concise human-readable explanation."""

    reasons: list[str] = []

    if result.title_similarity >= 80:
        reasons.append("very similar titles")

    elif result.title_similarity >= 55:
        reasons.append("partly similar titles")

    shared_keyword_count = len(
        result.shared_keywords
    )

    shared_phrase_count = len(
        result.shared_phrases
    )

    if shared_keyword_count:
        reasons.append(
            f"{shared_keyword_count} shared keyword"
            + (
                "s"
                if shared_keyword_count != 1
                else ""
            )
        )

    if shared_phrase_count:
        reasons.append(
            f"{shared_phrase_count} shared phrase"
            + (
                "s"
                if shared_phrase_count != 1
                else ""
            )
        )

    if result.category_similarity >= 100:
        reasons.append("same category")

    elif result.category_similarity >= 50:
        reasons.append("overlapping category")

    if result.gs_paper_similarity >= 100:
        reasons.append("same GS paper")

    if not reasons:
        return "Limited thematic overlap"

    if len(reasons) == 1:
        return reasons[0].capitalize()

    return (
        ", ".join(reasons[:-1])
        + f" and {reasons[-1]}"
    ).capitalize()


# ============================================================
# RESULT CONVERSION
# ============================================================

def _to_duplicate_match(
    repository_issue: dict[str, Any],
    similarity_result: SimilarityResult,
) -> DuplicateMatch:
    """Convert a similarity result into a duplicate match."""

    similarity = similarity_result.overall_similarity

    return DuplicateMatch(
        issue_id=str(
            repository_issue.get(
                "issue_id",
                "",
            )
        ),
        title=str(
            repository_issue.get(
                "title",
                "",
            )
        ),
        publication_date=str(
            repository_issue.get(
                "publication_date",
                "",
            )
        ),
        similarity=similarity,
        classification=classify_similarity(
            similarity
        ),
        reason=_build_match_reason(
            similarity_result
        ),
        shared_keywords=(
            similarity_result.shared_keywords
        ),
        shared_phrases=(
            similarity_result.shared_phrases
        ),
        title_similarity=(
            similarity_result.title_similarity
        ),
        keyword_similarity=(
            similarity_result.keyword_similarity
        ),
        phrase_similarity=(
            similarity_result.phrase_similarity
        ),
        category_similarity=(
            similarity_result.category_similarity
        ),
        gs_paper_similarity=(
            similarity_result.gs_paper_similarity
        ),
    )


# ============================================================
# REPOSITORY SCAN
# ============================================================

def scan_repository_for_duplicates(
    candidate_issue: dict[str, Any],
    maximum_results: int = 10,
    minimum_similarity: float = 0.0,
    exclude_issue_ids: Iterable[str] | None = None,
) -> DuplicateScanResult:
    """
    Compare one candidate issue against the repository.

    Parameters
    ----------
    candidate_issue:
        Complete issue record being checked.

    maximum_results:
        Maximum number of ranked matches returned.

    minimum_similarity:
        Do not return matches below this score.

    exclude_issue_ids:
        Optional issue IDs that must not be compared.
    """

    _validate_candidate_issue(
        candidate_issue
    )

    if maximum_results < 1:
        raise DuplicateDetectorError(
            "maximum_results must be at least 1."
        )

    if not 0 <= minimum_similarity <= 100:
        raise DuplicateDetectorError(
            "minimum_similarity must be between 0 and 100."
        )

    excluded = {
        str(issue_id).strip()
        for issue_id in (
            exclude_issue_ids or []
        )
        if str(issue_id).strip()
    }

    candidate_issue_id = str(
        candidate_issue["issue_id"]
    )

    excluded.add(
        candidate_issue_id
    )

    try:
        repository_issues = load_all_issue_records()

    except RepositorySearchError as error:
        raise DuplicateDetectorError(
            str(error)
        ) from error

    matches: list[DuplicateMatch] = []
    compared_count = 0

    for repository_issue in repository_issues:
        repository_issue_id = str(
            repository_issue.get(
                "issue_id",
                "",
            )
        )

        if repository_issue_id in excluded:
            continue

        compared_count += 1

        try:
            similarity_result = compare_issues(
                candidate_issue,
                repository_issue,
            )

        except SimilarityError as error:
            raise DuplicateDetectorError(
                "Unable to compare candidate issue with "
                f"{repository_issue_id}:\n{error}"
            ) from error

        if (
            similarity_result.overall_similarity
            < minimum_similarity
        ):
            continue

        matches.append(
            _to_duplicate_match(
                repository_issue=repository_issue,
                similarity_result=similarity_result,
            )
        )

    matches.sort(
        key=lambda match: (
            match.similarity,
            match.title_similarity,
            match.keyword_similarity,
            match.issue_id,
        ),
        reverse=True,
    )

    selected_matches = matches[
        :maximum_results
    ]

    highest_similarity = (
        selected_matches[0].similarity
        if selected_matches
        else 0.0
    )

    overall_classification = classify_similarity(
        highest_similarity
    )

    return DuplicateScanResult(
        candidate_issue_id=candidate_issue_id,
        candidate_title=str(
            candidate_issue["title"]
        ),
        repository_issue_count=len(
            repository_issues
        ),
        compared_issue_count=compared_count,
        highest_similarity=highest_similarity,
        overall_classification=overall_classification,
        possible_duplicate=(
            highest_similarity
            >= POSSIBLE_DUPLICATE_THRESHOLD
        ),
        matches=tuple(
            selected_matches
        ),
    )


# ============================================================
# ISSUE-ID SCAN
# ============================================================

def scan_issue_id(
    issue_id: str,
    maximum_results: int = 10,
    minimum_similarity: float = 0.0,
) -> DuplicateScanResult:
    """Load one repository issue and compare it with all others."""

    try:
        candidate_issue = load_issue_record(
            issue_id
        )

    except RepositorySearchError as error:
        raise DuplicateDetectorError(
            str(error)
        ) from error

    return scan_repository_for_duplicates(
        candidate_issue=candidate_issue,
        maximum_results=maximum_results,
        minimum_similarity=minimum_similarity,
    )


# ============================================================
# BATCH SCAN
# ============================================================

def scan_multiple_issues(
    candidate_issues: Iterable[dict[str, Any]],
    maximum_results: int = 5,
    minimum_similarity: float = 0.0,
) -> list[DuplicateScanResult]:
    """Scan several candidate issues."""

    issues = list(
        candidate_issues
    )

    candidate_ids = {
        str(
            issue.get(
                "issue_id",
                "",
            )
        )
        for issue in issues
        if isinstance(issue, dict)
    }

    results: list[DuplicateScanResult] = []

    for issue in issues:
        results.append(
            scan_repository_for_duplicates(
                candidate_issue=issue,
                maximum_results=maximum_results,
                minimum_similarity=minimum_similarity,
                exclude_issue_ids=candidate_ids,
            )
        )

    return results


# ============================================================
# REPORTING
# ============================================================

def print_duplicate_scan(
    result: DuplicateScanResult,
) -> None:
    """Print a readable duplicate scan report."""

    print("=" * 76)
    print("TODAY'S UPSC ISSUES")
    print("DUPLICATE AND RELATED ISSUE REPORT")
    print("=" * 76)

    print(
        f"Candidate : {result.candidate_title}"
    )

    print(
        f"Issue ID  : {result.candidate_issue_id}"
    )

    print(
        f"Repository: {result.repository_issue_count} issue(s)"
    )

    print(
        f"Compared  : {result.compared_issue_count} issue(s)"
    )

    print("-" * 76)

    print(
        f"Highest similarity : "
        f"{result.highest_similarity:.2f}%"
    )

    print(
        f"Classification     : "
        f"{result.overall_classification}"
    )

    print(
        f"Possible duplicate : "
        f"{'YES' if result.possible_duplicate else 'NO'}"
    )

    print("-" * 76)

    if not result.matches:
        print("No repository matches found.")
        print("=" * 76)
        return

    print("TOP MATCHES")

    for number, match in enumerate(
        result.matches,
        start=1,
    ):
        print()
        print(
            f"{number}. {match.title}"
        )

        print(
            f"   ID             : {match.issue_id}"
        )

        print(
            f"   Date           : {match.publication_date}"
        )

        print(
            f"   Similarity     : {match.similarity:.2f}%"
        )

        print(
            f"   Classification : {match.classification}"
        )

        print(
            f"   Reason         : {match.reason}"
        )

        if match.shared_keywords:
            print(
                "   Shared keywords: "
                + ", ".join(
                    match.shared_keywords
                )
            )

        if match.shared_phrases:
            print(
                "   Shared phrases : "
                + ", ".join(
                    match.shared_phrases
                )
            )

    print("=" * 76)


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """
    Run a repository scan using the latest issue.

    If the repository contains only one issue, the issue is
    temporarily compared against itself to validate the full
    duplicate classification path.
    """

    print("=" * 76)
    print("TODAY'S UPSC ISSUES")
    print("DUPLICATE DETECTOR — VERSION 2.1")
    print("=" * 76)

    summaries = list_issue_summaries()

    if not summaries:
        print("No repository issues are available.")
        print("=" * 76)
        return

    latest_issue_id = summaries[0].issue_id
    candidate_issue = load_issue_record(
        latest_issue_id
    )

    if len(summaries) == 1:
        similarity_result = compare_issues(
            candidate_issue,
            candidate_issue,
        )

        self_match = _to_duplicate_match(
            repository_issue=candidate_issue,
            similarity_result=similarity_result,
        )

        result = DuplicateScanResult(
            candidate_issue_id=latest_issue_id,
            candidate_title=str(
                candidate_issue["title"]
            ),
            repository_issue_count=1,
            compared_issue_count=1,
            highest_similarity=(
                self_match.similarity
            ),
            overall_classification=(
                self_match.classification
            ),
            possible_duplicate=True,
            matches=(
                self_match,
            ),
        )

    else:
        result = scan_issue_id(
            latest_issue_id,
            maximum_results=5,
        )

    print_duplicate_scan(
        result
    )

    print("✓ Repository-wide comparison enabled")
    print("✓ Ranked matching enabled")
    print("✓ Duplicate classification enabled")
    print("✓ Related-issue classification enabled")
    print("✓ Match explanations enabled")
    print("=" * 76)


if __name__ == "__main__":
    _development_test()