"""
============================================================
TODAY'S UPSC ISSUES
KNOWLEDGE ENGINE
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Provides one unified entry point for repository intelligence.

The Knowledge Engine combines:

1. Repository search
2. Keyword extraction
3. Similarity analysis
4. Duplicate detection
5. Related issue recommendations
6. Reusable Quick Facts
7. Reusable Recall Questions
8. Reusable examples and anchors
9. GS paper and category cross-links
10. Spaced recall scheduling
11. Publication usage status

This module coordinates existing intelligence modules.
It does not duplicate their internal logic.
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

from src.intelligence.duplicate_detector import (  # noqa: E402
    DuplicateDetectorError,
    DuplicateMatch,
    DuplicateScanResult,
    scan_repository_for_duplicates,
)
from src.intelligence.keywords import (  # noqa: E402
    KeywordExtractionError,
    KeywordResult,
    extract_keywords,
)
from src.intelligence.recall_scheduler import (  # noqa: E402
    RecallScheduleResult,
    RecallSchedulerError,
    register_issue_schedule,
)
from src.intelligence.repository_search import (  # noqa: E402
    RepositorySearchError,
    load_all_issue_records,
    load_issue_record,
)
from src.intelligence.usage_tracker import (  # noqa: E402
    IssueUsageStatus,
    UsageTrackerError,
    get_issue_usage_status,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class KnowledgeEngineError(Exception):
    """Base exception for knowledge-engine errors."""


class InvalidKnowledgeIssueError(KnowledgeEngineError):
    """Raised when an issue cannot be analysed."""


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_RELATED_THRESHOLD = 50.0
DEFAULT_MAXIMUM_RELATED_ISSUES = 5
DEFAULT_MAXIMUM_REUSABLE_ITEMS = 10


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass(frozen=True, slots=True)
class ReusableFact:
    """One reusable Quick Fact from a related issue."""

    source_issue_id: str
    source_issue_title: str
    source_publication_date: str
    similarity: float
    fact: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_issue_id": self.source_issue_id,
            "source_issue_title": self.source_issue_title,
            "source_publication_date": (
                self.source_publication_date
            ),
            "similarity": self.similarity,
            "fact": self.fact,
        }


@dataclass(frozen=True, slots=True)
class ReusableRecallQuestion:
    """One reusable recall question."""

    source_issue_id: str
    source_issue_title: str
    source_publication_date: str
    similarity: float
    question: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_issue_id": self.source_issue_id,
            "source_issue_title": self.source_issue_title,
            "source_publication_date": (
                self.source_publication_date
            ),
            "similarity": self.similarity,
            "question": self.question,
        }


@dataclass(frozen=True, slots=True)
class ReusableAnchor:
    """One reusable visual or conceptual anchor."""

    source_issue_id: str
    source_issue_title: str
    source_publication_date: str
    similarity: float
    anchor: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_issue_id": self.source_issue_id,
            "source_issue_title": self.source_issue_title,
            "source_publication_date": (
                self.source_publication_date
            ),
            "similarity": self.similarity,
            "anchor": self.anchor,
        }


@dataclass(frozen=True, slots=True)
class RelatedIssue:
    """One recommended related repository issue."""

    issue_id: str
    title: str
    publication_date: str
    similarity: float
    classification: str
    reason: str
    shared_keywords: tuple[str, ...]
    shared_phrases: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "publication_date": self.publication_date,
            "similarity": self.similarity,
            "classification": self.classification,
            "reason": self.reason,
            "shared_keywords": list(
                self.shared_keywords
            ),
            "shared_phrases": list(
                self.shared_phrases
            ),
        }


@dataclass(frozen=True, slots=True)
class KnowledgeAnalysis:
    """Complete knowledge analysis for one issue."""

    issue_id: str
    title: str
    publication_date: str
    gs_paper: str
    category: str

    keyword_result: KeywordResult
    duplicate_scan: DuplicateScanResult
    related_issues: tuple[RelatedIssue, ...]

    reusable_facts: tuple[ReusableFact, ...]
    reusable_recall_questions: tuple[
        ReusableRecallQuestion,
        ...
    ]
    reusable_anchors: tuple[ReusableAnchor, ...]

    related_gs_papers: tuple[str, ...]
    related_categories: tuple[str, ...]

    recall_schedule: RecallScheduleResult | None
    usage_status: IssueUsageStatus | None

    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue": {
                "issue_id": self.issue_id,
                "title": self.title,
                "publication_date": (
                    self.publication_date
                ),
                "gs_paper": self.gs_paper,
                "category": self.category,
            },
            "keywords": self.keyword_result.to_dict(),
            "duplicate_scan": (
                self.duplicate_scan.to_dict()
            ),
            "related_issues": [
                issue.to_dict()
                for issue in self.related_issues
            ],
            "reusable_facts": [
                fact.to_dict()
                for fact in self.reusable_facts
            ],
            "reusable_recall_questions": [
                question.to_dict()
                for question
                in self.reusable_recall_questions
            ],
            "reusable_anchors": [
                anchor.to_dict()
                for anchor in self.reusable_anchors
            ],
            "related_gs_papers": list(
                self.related_gs_papers
            ),
            "related_categories": list(
                self.related_categories
            ),
            "recall_schedule": (
                self.recall_schedule.to_dict()
                if self.recall_schedule
                else None
            ),
            "usage_status": (
                self.usage_status.to_dict()
                if self.usage_status
                else None
            ),
            "recommendations": list(
                self.recommendations
            ),
        }


# ============================================================
# VALIDATION
# ============================================================

def _validate_issue(
    issue: dict[str, Any],
) -> None:
    """Validate one issue before knowledge analysis."""

    if not isinstance(issue, dict):
        raise InvalidKnowledgeIssueError(
            "Issue must be a dictionary."
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
        raise InvalidKnowledgeIssueError(
            "Issue does not contain issue_id."
        )

    if not title:
        raise InvalidKnowledgeIssueError(
            "Issue does not contain title."
        )


# ============================================================
# GENERAL HELPERS
# ============================================================

def _clean_text(value: Any) -> str:
    """Return clean text."""

    if value is None:
        return ""

    return str(value).strip()


def _normalise_identity_text(
    value: Any,
) -> str:
    """Normalize text for duplicate-item removal."""

    return " ".join(
        _clean_text(value)
        .lower()
        .split()
    )


def _unique_text_values(
    values: Iterable[str],
) -> list[str]:
    """Return unique non-empty values preserving order."""

    selected: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_text(
            value
        )

        identity = _normalise_identity_text(
            cleaned
        )

        if not cleaned or not identity:
            continue

        if identity in seen:
            continue

        seen.add(identity)
        selected.append(cleaned)

    return selected


# ============================================================
# RELATED ISSUE CONVERSION
# ============================================================

def _to_related_issue(
    match: DuplicateMatch,
) -> RelatedIssue:
    """Convert a duplicate match into a recommendation."""

    return RelatedIssue(
        issue_id=match.issue_id,
        title=match.title,
        publication_date=match.publication_date,
        similarity=match.similarity,
        classification=match.classification,
        reason=match.reason,
        shared_keywords=match.shared_keywords,
        shared_phrases=match.shared_phrases,
    )


# ============================================================
# RELATED RECORD LOADING
# ============================================================

def _load_related_issue_records(
    related_issues: Iterable[RelatedIssue],
) -> list[
    tuple[
        RelatedIssue,
        dict[str, Any],
    ]
]:
    """Load complete records for related issues."""

    loaded: list[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ] = []

    for related_issue in related_issues:
        try:
            issue_record = load_issue_record(
                related_issue.issue_id
            )

        except RepositorySearchError:
            continue

        loaded.append(
            (
                related_issue,
                issue_record,
            )
        )

    return loaded


# ============================================================
# REUSABLE FACTS
# ============================================================

def _collect_reusable_facts(
    related_records: Iterable[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ],
    maximum_items: int,
) -> tuple[ReusableFact, ...]:
    """Collect reusable Quick Facts."""

    results: list[ReusableFact] = []
    seen: set[str] = set()

    for related_issue, record in related_records:
        pdf_content = record.get(
            "pdf_content",
            {},
        )

        if not isinstance(
            pdf_content,
            dict,
        ):
            continue

        facts = pdf_content.get(
            "quick_facts",
            [],
        )

        if not isinstance(
            facts,
            (list, tuple),
        ):
            continue

        for fact in facts:
            cleaned = _clean_text(
                fact
            )

            identity = _normalise_identity_text(
                cleaned
            )

            if not cleaned or identity in seen:
                continue

            seen.add(identity)

            results.append(
                ReusableFact(
                    source_issue_id=(
                        related_issue.issue_id
                    ),
                    source_issue_title=(
                        related_issue.title
                    ),
                    source_publication_date=(
                        related_issue
                        .publication_date
                    ),
                    similarity=(
                        related_issue.similarity
                    ),
                    fact=cleaned,
                )
            )

            if len(results) >= maximum_items:
                return tuple(results)

    return tuple(results)


# ============================================================
# REUSABLE RECALL QUESTIONS
# ============================================================

def _collect_reusable_recall_questions(
    related_records: Iterable[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ],
    maximum_items: int,
) -> tuple[ReusableRecallQuestion, ...]:
    """Collect reusable recall questions."""

    results: list[
        ReusableRecallQuestion
    ] = []

    seen: set[str] = set()

    for related_issue, record in related_records:
        recall = record.get(
            "recall",
            {},
        )

        if not isinstance(
            recall,
            dict,
        ):
            continue

        questions = recall.get(
            "questions",
            [],
        )

        if not isinstance(
            questions,
            (list, tuple),
        ):
            continue

        for question in questions:
            cleaned = _clean_text(
                question
            )

            identity = _normalise_identity_text(
                cleaned
            )

            if not cleaned or identity in seen:
                continue

            seen.add(identity)

            results.append(
                ReusableRecallQuestion(
                    source_issue_id=(
                        related_issue.issue_id
                    ),
                    source_issue_title=(
                        related_issue.title
                    ),
                    source_publication_date=(
                        related_issue
                        .publication_date
                    ),
                    similarity=(
                        related_issue.similarity
                    ),
                    question=cleaned,
                )
            )

            if len(results) >= maximum_items:
                return tuple(results)

    return tuple(results)


# ============================================================
# REUSABLE ANCHORS
# ============================================================

def _collect_reusable_anchors(
    related_records: Iterable[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ],
    maximum_items: int,
) -> tuple[ReusableAnchor, ...]:
    """Collect reusable visual and conceptual anchors."""

    results: list[ReusableAnchor] = []
    seen: set[str] = set()

    for related_issue, record in related_records:
        youtube = record.get(
            "youtube",
            {},
        )

        if not isinstance(
            youtube,
            dict,
        ):
            continue

        anchors = youtube.get(
            "anchors",
            [],
        )

        if not isinstance(
            anchors,
            (list, tuple),
        ):
            continue

        for anchor in anchors:
            cleaned = _clean_text(
                anchor
            )

            identity = _normalise_identity_text(
                cleaned
            )

            if not cleaned or identity in seen:
                continue

            seen.add(identity)

            results.append(
                ReusableAnchor(
                    source_issue_id=(
                        related_issue.issue_id
                    ),
                    source_issue_title=(
                        related_issue.title
                    ),
                    source_publication_date=(
                        related_issue
                        .publication_date
                    ),
                    similarity=(
                        related_issue.similarity
                    ),
                    anchor=cleaned,
                )
            )

            if len(results) >= maximum_items:
                return tuple(results)

    return tuple(results)


# ============================================================
# RELATED GS PAPERS AND CATEGORIES
# ============================================================

def _collect_related_gs_papers(
    related_records: Iterable[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ],
) -> tuple[str, ...]:
    """Collect related GS papers."""

    values = [
        _clean_text(
            record.get(
                "gs_paper",
                "",
            )
        )
        for _, record in related_records
    ]

    return tuple(
        _unique_text_values(
            values
        )
    )


def _collect_related_categories(
    related_records: Iterable[
        tuple[
            RelatedIssue,
            dict[str, Any],
        ]
    ],
) -> tuple[str, ...]:
    """Collect related categories."""

    values = [
        _clean_text(
            record.get(
                "category",
                "",
            )
        )
        for _, record in related_records
    ]

    return tuple(
        _unique_text_values(
            values
        )
    )


# ============================================================
# RECOMMENDATION TEXT
# ============================================================

def _build_recommendations(
    duplicate_scan: DuplicateScanResult,
    related_issues: tuple[RelatedIssue, ...],
    reusable_facts: tuple[ReusableFact, ...],
    reusable_questions: tuple[
        ReusableRecallQuestion,
        ...
    ],
    reusable_anchors: tuple[
        ReusableAnchor,
        ...
    ],
) -> tuple[str, ...]:
    """Build concise editorial recommendations."""

    recommendations: list[str] = []

    if duplicate_scan.possible_duplicate:
        recommendations.append(
            "Review the highest-scoring repository issue "
            "before publishing because the candidate may "
            "duplicate previously covered content."
        )

    elif (
        duplicate_scan.highest_similarity
        >= 70
    ):
        recommendations.append(
            "Treat the closest repository match as a "
            "continuation or update rather than repeating "
            "the earlier issue."
        )

    elif related_issues:
        recommendations.append(
            "Cross-link the related repository issues to "
            "strengthen continuity and revision value."
        )

    if reusable_facts:
        recommendations.append(
            f"Review {len(reusable_facts)} reusable Quick "
            "Fact suggestion(s) and retain only those still "
            "accurate in the current context."
        )

    if reusable_questions:
        recommendations.append(
            f"Review {len(reusable_questions)} previous "
            "Recall Question suggestion(s) for continuity "
            "and spaced revision."
        )

    if reusable_anchors:
        recommendations.append(
            f"Reuse or adapt {len(reusable_anchors)} visual "
            "anchor suggestion(s) for YouTube and Telegram."
        )

    if not recommendations:
        recommendations.append(
            "No substantial repository overlap was found. "
            "Treat this as a distinct issue."
        )

    return tuple(
        recommendations
    )


# ============================================================
# MAIN KNOWLEDGE ANALYSIS
# ============================================================

def analyze_issue(
    issue: dict[str, Any],
    maximum_related_issues: int = (
        DEFAULT_MAXIMUM_RELATED_ISSUES
    ),
    minimum_related_similarity: float = (
        DEFAULT_RELATED_THRESHOLD
    ),
    maximum_reusable_items: int = (
        DEFAULT_MAXIMUM_REUSABLE_ITEMS
    ),
    register_recall: bool = True,
    overwrite_recall_schedule: bool = False,
) -> KnowledgeAnalysis:
    """
    Run complete repository intelligence for one issue.
    """

    _validate_issue(
        issue
    )

    if maximum_related_issues < 1:
        raise KnowledgeEngineError(
            "maximum_related_issues must be at least 1."
        )

    if not 0 <= minimum_related_similarity <= 100:
        raise KnowledgeEngineError(
            "minimum_related_similarity must be between "
            "0 and 100."
        )

    if maximum_reusable_items < 1:
        raise KnowledgeEngineError(
            "maximum_reusable_items must be at least 1."
        )

    try:
        keyword_result = extract_keywords(
            issue
        )

        duplicate_scan = (
            scan_repository_for_duplicates(
                candidate_issue=issue,
                maximum_results=(
                    maximum_related_issues
                ),
                minimum_similarity=(
                    minimum_related_similarity
                ),
            )
        )

    except (
        KeywordExtractionError,
        DuplicateDetectorError,
    ) as error:
        raise KnowledgeEngineError(
            str(error)
        ) from error

    related_issues = tuple(
        _to_related_issue(match)
        for match in duplicate_scan.matches
    )

    related_records = (
        _load_related_issue_records(
            related_issues
        )
    )

    reusable_facts = (
        _collect_reusable_facts(
            related_records=related_records,
            maximum_items=(
                maximum_reusable_items
            ),
        )
    )

    reusable_questions = (
        _collect_reusable_recall_questions(
            related_records=related_records,
            maximum_items=(
                maximum_reusable_items
            ),
        )
    )

    reusable_anchors = (
        _collect_reusable_anchors(
            related_records=related_records,
            maximum_items=(
                maximum_reusable_items
            ),
        )
    )

    related_gs_papers = (
        _collect_related_gs_papers(
            related_records
        )
    )

    related_categories = (
        _collect_related_categories(
            related_records
        )
    )

    recall_schedule: (
        RecallScheduleResult
        | None
    ) = None

    if register_recall:
        try:
            recall_schedule = (
                register_issue_schedule(
                    issue=issue,
                    overwrite=(
                        overwrite_recall_schedule
                    ),
                )
            )

        except RecallSchedulerError as error:
            raise KnowledgeEngineError(
                str(error)
            ) from error

    usage_status: IssueUsageStatus | None = None

    try:
        usage_status = get_issue_usage_status(
            str(
                issue["issue_id"]
            )
        )

    except UsageTrackerError:
        usage_status = None

    recommendations = _build_recommendations(
        duplicate_scan=duplicate_scan,
        related_issues=related_issues,
        reusable_facts=reusable_facts,
        reusable_questions=(
            reusable_questions
        ),
        reusable_anchors=reusable_anchors,
    )

    return KnowledgeAnalysis(
        issue_id=str(
            issue["issue_id"]
        ),
        title=str(
            issue["title"]
        ),
        publication_date=_clean_text(
            issue.get(
                "publication_date",
                "",
            )
        ),
        gs_paper=_clean_text(
            issue.get(
                "gs_paper",
                "",
            )
        ),
        category=_clean_text(
            issue.get(
                "category",
                "",
            )
        ),
        keyword_result=keyword_result,
        duplicate_scan=duplicate_scan,
        related_issues=related_issues,
        reusable_facts=reusable_facts,
        reusable_recall_questions=(
            reusable_questions
        ),
        reusable_anchors=reusable_anchors,
        related_gs_papers=(
            related_gs_papers
        ),
        related_categories=(
            related_categories
        ),
        recall_schedule=recall_schedule,
        usage_status=usage_status,
        recommendations=recommendations,
    )


# ============================================================
# ISSUE-ID ANALYSIS
# ============================================================

def analyze_issue_id(
    issue_id: str,
    maximum_related_issues: int = (
        DEFAULT_MAXIMUM_RELATED_ISSUES
    ),
    minimum_related_similarity: float = (
        DEFAULT_RELATED_THRESHOLD
    ),
    maximum_reusable_items: int = (
        DEFAULT_MAXIMUM_REUSABLE_ITEMS
    ),
    register_recall: bool = True,
    overwrite_recall_schedule: bool = False,
) -> KnowledgeAnalysis:
    """Load and analyse one repository issue."""

    try:
        issue = load_issue_record(
            issue_id
        )

    except RepositorySearchError as error:
        raise KnowledgeEngineError(
            str(error)
        ) from error

    return analyze_issue(
        issue=issue,
        maximum_related_issues=(
            maximum_related_issues
        ),
        minimum_related_similarity=(
            minimum_related_similarity
        ),
        maximum_reusable_items=(
            maximum_reusable_items
        ),
        register_recall=register_recall,
        overwrite_recall_schedule=(
            overwrite_recall_schedule
        ),
    )


# ============================================================
# BATCH ANALYSIS
# ============================================================

def analyze_repository(
    maximum_related_issues: int = 5,
    minimum_related_similarity: float = 50.0,
    register_recall: bool = True,
) -> list[KnowledgeAnalysis]:
    """Analyse every permanent repository issue."""

    try:
        issues = load_all_issue_records()

    except RepositorySearchError as error:
        raise KnowledgeEngineError(
            str(error)
        ) from error

    results: list[KnowledgeAnalysis] = []

    for issue in issues:
        results.append(
            analyze_issue(
                issue=issue,
                maximum_related_issues=(
                    maximum_related_issues
                ),
                minimum_related_similarity=(
                    minimum_related_similarity
                ),
                register_recall=(
                    register_recall
                ),
            )
        )

    return results


# ============================================================
# REPORTING
# ============================================================

def print_knowledge_analysis(
    analysis: KnowledgeAnalysis,
) -> None:
    """Print a readable knowledge-engine report."""

    print("=" * 78)
    print("TODAY'S UPSC ISSUES")
    print("KNOWLEDGE ENGINE REPORT")
    print("=" * 78)

    print(
        f"Issue : {analysis.title}"
    )

    print(
        f"ID    : {analysis.issue_id}"
    )

    print(
        f"Date  : {analysis.publication_date}"
    )

    print(
        f"GS    : {analysis.gs_paper}"
    )

    print(
        f"Topic : {analysis.category or '-'}"
    )

    print("-" * 78)

    print(
        f"Highest repository similarity : "
        f"{analysis.duplicate_scan.highest_similarity:.2f}%"
    )

    print(
        f"Duplicate classification       : "
        f"{analysis.duplicate_scan.overall_classification}"
    )

    print(
        f"Possible duplicate             : "
        f"{'YES' if analysis.duplicate_scan.possible_duplicate else 'NO'}"
    )

    print("-" * 78)
    print("KEYWORDS")

    for keyword in analysis.keyword_result.keywords:
        print(
            f"• {keyword}"
        )

    print("-" * 78)
    print("RELATED ISSUES")

    if analysis.related_issues:
        for number, issue in enumerate(
            analysis.related_issues,
            start=1,
        ):
            print(
                f"{number}. {issue.title}"
            )

            print(
                f"   Date       : "
                f"{issue.publication_date}"
            )

            print(
                f"   Similarity : "
                f"{issue.similarity:.2f}%"
            )

            print(
                f"   Status     : "
                f"{issue.classification}"
            )

            print(
                f"   Reason     : "
                f"{issue.reason}"
            )
    else:
        print("No related repository issues found.")

    print("-" * 78)
    print("REUSABLE QUICK FACTS")

    if analysis.reusable_facts:
        for number, item in enumerate(
            analysis.reusable_facts,
            start=1,
        ):
            print(
                f"{number}. {item.fact}"
            )

            print(
                f"   Source: "
                f"{item.source_issue_title} "
                f"({item.source_publication_date})"
            )
    else:
        print("No reusable Quick Facts found.")

    print("-" * 78)
    print("REUSABLE RECALL QUESTIONS")

    if analysis.reusable_recall_questions:
        for number, item in enumerate(
            analysis.reusable_recall_questions,
            start=1,
        ):
            print(
                f"{number}. {item.question}"
            )

            print(
                f"   Source: "
                f"{item.source_issue_title} "
                f"({item.source_publication_date})"
            )
    else:
        print("No reusable Recall Questions found.")

    print("-" * 78)
    print("REUSABLE ANCHORS")

    if analysis.reusable_anchors:
        for number, item in enumerate(
            analysis.reusable_anchors,
            start=1,
        ):
            print(
                f"{number}. {item.anchor}"
            )

            print(
                f"   Source: "
                f"{item.source_issue_title} "
                f"({item.source_publication_date})"
            )
    else:
        print("No reusable anchors found.")

    print("-" * 78)
    print("RECOMMENDATIONS")

    for number, recommendation in enumerate(
        analysis.recommendations,
        start=1,
    ):
        print(
            f"{number}. {recommendation}"
        )

    print("=" * 78)


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Analyse the latest repository issue."""

    print("=" * 78)
    print("TODAY'S UPSC ISSUES")
    print("KNOWLEDGE ENGINE — VERSION 2.1")
    print("=" * 78)

    try:
        issues = load_all_issue_records()

    except RepositorySearchError as error:
        print(error)
        print("=" * 78)
        return

    if not issues:
        print("No repository issues are available.")
        print("=" * 78)
        return

    latest_issue = sorted(
        issues,
        key=lambda issue: (
            _clean_text(
                issue.get(
                    "publication_date",
                    "",
                )
            ),
            _clean_text(
                issue.get(
                    "issue_id",
                    "",
                )
            ),
        ),
        reverse=True,
    )[0]

    analysis = analyze_issue(
        issue=latest_issue,
        register_recall=True,
    )

    print_knowledge_analysis(
        analysis
    )

    print("✓ Unified repository intelligence enabled")
    print("✓ Duplicate analysis enabled")
    print("✓ Related issue recommendations enabled")
    print("✓ Quick Fact reuse enabled")
    print("✓ Recall Question reuse enabled")
    print("✓ Anchor reuse enabled")
    print("✓ Recall scheduling integrated")
    print("✓ Usage tracking integrated")
    print("=" * 78)


if __name__ == "__main__":
    _development_test()