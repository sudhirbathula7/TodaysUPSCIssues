"""
============================================================
TODAY'S UPSC ISSUES
KEYWORD EXTRACTOR
Version 2.1
Created by Sudhir
============================================================

PURPOSE

Extracts deterministic, reusable UPSC keywords from a
permanent issue record.

KEYWORD SOURCES

1. Issue title
2. Category
3. GS paper
4. Current Context
5. Why It Matters for UPSC
6. Core Concept
7. Challenges
8. Way Forward
9. Quick Facts
10. Recall Questions
11. YouTube anchors

DESIGN

- No AI or external API
- Repeatable output
- Stop-word filtering
- Phrase preservation
- UPSC vocabulary normalization
- Frequency-based ranking
- Suitable for similarity and duplicate detection
============================================================
"""

from __future__ import annotations

import re
import sys
from collections import Counter
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
    load_issue_record,
)


# ============================================================
# EXCEPTIONS
# ============================================================

class KeywordExtractionError(Exception):
    """Base exception for keyword extraction errors."""


class InvalidIssueRecordError(KeywordExtractionError):
    """Raised when the issue record is invalid."""


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True, slots=True)
class KeywordResult:
    """Keyword extraction result for one issue."""

    issue_id: str
    title: str
    keywords: tuple[str, ...]
    phrases: tuple[str, ...]
    scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a serialisable dictionary."""

        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "keywords": list(self.keywords),
            "phrases": list(self.phrases),
            "scores": dict(self.scores),
        }


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "a",
    "about",
    "above",
    "across",
    "after",
    "again",
    "against",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "do",
    "does",
    "doing",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "may",
    "me",
    "might",
    "more",
    "most",
    "must",
    "my",
    "myself",
    "need",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",

    # Generic content words
    "issue",
    "issues",
    "current",
    "context",
    "important",
    "importance",
    "matter",
    "matters",
    "challenge",
    "challenges",
    "forward",
    "way",
    "fact",
    "facts",
    "question",
    "questions",
    "takeaway",
    "examine",
    "discuss",
    "analyse",
    "analyze",
    "explain",
    "role",
    "major",
    "key",
    "remain",
    "remains",
    "requires",
    "required",
    "including",
    "include",
    "includes",
    "covering",
    "related",

    # Generic India references
    "india",
    "indian",
    "country",
    "national",
}


# ============================================================
# TOKEN NORMALISATION
# ============================================================

TOKEN_ALIASES = {
    "chips": "chip",
    "semiconductors": "semiconductor",
    "technologies": "technology",
    "industries": "industry",
    "policies": "policy",
    "economies": "economy",
    "systems": "system",
    "institutions": "institution",
    "governments": "government",
    "manufacturers": "manufacturer",
    "manufacturing": "manufacturing",
    "investments": "investment",
    "capabilities": "capability",
    "skills": "skill",
    "workers": "worker",
    "supply-chains": "supply chain",
    "supplychains": "supply chain",
    "supply": "supply",
    "chains": "chain",
    "electronics": "electronics",
    "federal": "federalism",
    "judicial": "judiciary",
    "courts": "court",
    "farmers": "farmer",
    "agricultural": "agriculture",
    "climatic": "climate",
    "environmental": "environment",
    "security-related": "security",
    "regulations": "regulation",
    "regulatory": "regulation",
    "digitalisation": "digitalization",
}


# ============================================================
# UPSC PHRASES
# ============================================================

KNOWN_PHRASES = (
    "semiconductor ecosystem",
    "chip manufacturing",
    "chip design",
    "supply chain",
    "supply chain resilience",
    "national security",
    "technological self reliance",
    "technological self-reliance",
    "industrial policy",
    "industry academia collaboration",
    "industry-academia collaboration",
    "public health",
    "climate change",
    "urban governance",
    "disaster management",
    "parliamentary committee",
    "social justice",
    "internal security",
    "food security",
    "energy security",
    "data protection",
    "digital governance",
    "artificial intelligence",
    "machine learning",
    "fiscal federalism",
    "cooperative federalism",
    "judicial review",
    "fundamental rights",
    "directive principles",
    "monetary policy",
    "fiscal policy",
    "blue economy",
    "circular economy",
    "green hydrogen",
    "renewable energy",
    "carbon market",
    "critical minerals",
    "strategic autonomy",
    "global supply chains",
)


# ============================================================
# SOURCE WEIGHTS
# ============================================================

SOURCE_WEIGHTS = {
    "title": 4.0,
    "category": 3.0,
    "gs_paper": 1.0,
    "core_concept": 2.5,
    "current_context": 2.0,
    "why_it_matters_for_upsc": 2.0,
    "challenges": 1.5,
    "way_forward": 1.5,
    "quick_facts": 1.5,
    "recall_questions": 1.0,
    "anchors": 2.5,
}


# ============================================================
# TEXT HELPERS
# ============================================================

def _normalise_text(value: Any) -> str:
    """Return clean lowercase text."""

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
        r"[^a-z0-9\s\-']+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _normalise_token(token: str) -> str:
    """Normalise one token."""

    token = token.lower().strip()

    token = re.sub(
        r"['’]s$",
        "",
        token,
    )

    token = token.strip("-'’")

    if not token:
        return ""

    if token in TOKEN_ALIASES:
        return TOKEN_ALIASES[token]

    if len(token) > 5 and token.endswith("ies"):
        token = token[:-3] + "y"

    elif len(token) > 5 and token.endswith("sses"):
        token = token[:-2]

    elif len(token) > 4 and token.endswith("s"):
        token = token[:-1]

    return TOKEN_ALIASES.get(
        token,
        token,
    )

def _tokenise(text: str) -> list[str]:
    """Tokenise and filter one text block."""

    normalised = _normalise_text(
        text
    )

    raw_tokens = re.findall(
        r"[a-z0-9][a-z0-9\-']*",
        normalised,
    )

    tokens: list[str] = []

    for raw_token in raw_tokens:
        token = _normalise_token(
            raw_token
        )

        if not token:
            continue

        if token in STOP_WORDS:
            continue

        if len(token) < 3:
            continue

        if token.isdigit():
            continue

        tokens.append(token)

    return tokens


def _normalise_phrase(
    phrase: str,
) -> str:
    """Normalise a multi-word phrase."""

    words = _tokenise(
        phrase
    )

    return " ".join(words)


# ============================================================
# ISSUE FIELD EXTRACTION
# ============================================================

def _extract_issue_sources(
    issue: dict[str, Any],
) -> dict[str, list[str]]:
    """Extract all keyword-bearing issue fields."""

    if not isinstance(issue, dict):
        raise InvalidIssueRecordError(
            "Issue record must be a dictionary."
        )

    sources: dict[str, list[str]] = {
        "title": [],
        "category": [],
        "gs_paper": [],
        "core_concept": [],
        "current_context": [],
        "why_it_matters_for_upsc": [],
        "challenges": [],
        "way_forward": [],
        "quick_facts": [],
        "recall_questions": [],
        "anchors": [],
    }

    sources["title"].append(
        str(
            issue.get(
                "title",
                "",
            )
        )
    )

    sources["category"].append(
        str(
            issue.get(
                "category",
                "",
            )
        )
    )

    sources["gs_paper"].append(
        str(
            issue.get(
                "gs_paper",
                "",
            )
        )
    )

    pdf_content = issue.get(
        "pdf_content",
        {},
    )

    if isinstance(pdf_content, dict):
        for field_name in (
            "core_concept",
            "current_context",
            "why_it_matters_for_upsc",
            "challenges",
            "way_forward",
        ):
            sources[field_name].append(
                str(
                    pdf_content.get(
                        field_name,
                        "",
                    )
                )
            )

        quick_facts = pdf_content.get(
            "quick_facts",
            [],
        )

        if isinstance(
            quick_facts,
            (list, tuple),
        ):
            sources["quick_facts"].extend(
                str(fact)
                for fact in quick_facts
            )

    recall = issue.get(
        "recall",
        {},
    )

    if isinstance(recall, dict):
        questions = recall.get(
            "questions",
            [],
        )

        if isinstance(
            questions,
            (list, tuple),
        ):
            sources["recall_questions"].extend(
                str(question)
                for question in questions
            )

    youtube = issue.get(
        "youtube",
        {},
    )

    if isinstance(youtube, dict):
        anchors = youtube.get(
            "anchors",
            [],
        )

        if isinstance(
            anchors,
            (list, tuple),
        ):
            sources["anchors"].extend(
                str(anchor)
                for anchor in anchors
            )

    return sources


# ============================================================
# PHRASE EXTRACTION
# ============================================================

def extract_known_phrases(
    issue: dict[str, Any],
) -> list[str]:
    """Extract recognized UPSC phrases from an issue."""

    sources = _extract_issue_sources(
        issue
    )

    combined_text = " ".join(
        text
        for values in sources.values()
        for text in values
    )

    normalised_combined = _normalise_text(
        combined_text
    )

    found_phrases: list[str] = []

    for phrase in KNOWN_PHRASES:
        normalised_phrase = _normalise_text(
            phrase
        )

        if normalised_phrase in normalised_combined:
            canonical_phrase = _normalise_phrase(
                phrase
            )

            if (
                canonical_phrase
                and canonical_phrase not in found_phrases
            ):
                found_phrases.append(
                    canonical_phrase
                )

    return found_phrases


# ============================================================
# KEYWORD SCORING
# ============================================================

def _score_tokens(
    sources: dict[str, list[str]],
) -> Counter[str]:
    """Calculate weighted token scores."""

    scores: Counter[str] = Counter()

    for source_name, texts in sources.items():
        weight = SOURCE_WEIGHTS.get(
            source_name,
            1.0,
        )

        for text in texts:
            tokens = _tokenise(
                text
            )

            token_counts = Counter(
                tokens
            )

            for token, count in token_counts.items():
                scores[token] += (
                    count
                    * weight
                )

    return scores


def _score_phrases(
    phrases: Iterable[str],
) -> Counter[str]:
    """Assign strong scores to recognized phrases."""

    phrase_scores: Counter[str] = Counter()

    for phrase in phrases:
        phrase_scores[phrase] += 6.0

    return phrase_scores

def _remove_nested_phrases(
    phrases: Iterable[str],
) -> list[str]:
    """
    Remove shorter phrases already contained inside
    a more specific phrase.

    Example:
        global supply chain
        supply chain

    Keeps:
        global supply chain
    """

    ordered_phrases = sorted(
        set(phrases),
        key=lambda phrase: (
            len(phrase.split()),
            len(phrase),
        ),
        reverse=True,
    )

    selected: list[str] = []

    for phrase in ordered_phrases:
        is_nested = any(
            phrase != existing
            and phrase in existing
            for existing in selected
        )

        if not is_nested:
            selected.append(phrase)

    return selected

def _remove_phrase_component_tokens(
    token_scores: Counter[str],
    phrase_scores: Counter[str],
) -> Counter[str]:
    """
    Reduce redundant single-word tokens already represented
    inside strong multi-word phrases.
    """

    adjusted = Counter(
        token_scores
    )

    for phrase in phrase_scores:
        words = phrase.split()

        if len(words) < 2:
            continue

        for word in words:
            if word in adjusted:
                adjusted[word] *= 0.55

    return adjusted


# ============================================================
# PUBLIC EXTRACTION FUNCTIONS
# ============================================================

def extract_keywords(
    issue: dict[str, Any],
    maximum_keywords: int = 12,
    maximum_phrases: int = 6,
) -> KeywordResult:
    """
    Extract ranked keywords and phrases from one issue.

    Parameters
    ----------
    issue:
        Complete permanent issue record.

    maximum_keywords:
        Maximum number of single-word or canonical keywords.

    maximum_phrases:
        Maximum number of multi-word UPSC phrases.
    """

    if maximum_keywords < 1:
        raise KeywordExtractionError(
            "maximum_keywords must be at least 1."
        )

    if maximum_phrases < 0:
        raise KeywordExtractionError(
            "maximum_phrases cannot be negative."
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
        raise InvalidIssueRecordError(
            "Issue record does not contain issue_id."
        )

    if not title:
        raise InvalidIssueRecordError(
            "Issue record does not contain title."
        )

    sources = _extract_issue_sources(
        issue
    )

    phrases = _remove_nested_phrases(
        extract_known_phrases(issue)
    )

    token_scores = _score_tokens(
        sources
    )

    phrase_scores = _score_phrases(
        phrases
    )

    token_scores = (
        _remove_phrase_component_tokens(
            token_scores,
            phrase_scores,
        )
    )

    ranked_phrases = sorted(
        phrase_scores,
        key=lambda phrase: (
            phrase_scores[phrase],
            len(phrase.split()),
            phrase,
        ),
        reverse=True,
    )[:maximum_phrases]

    ranked_tokens = sorted(
        token_scores,
        key=lambda token: (
            token_scores[token],
            len(token),
            token,
        ),
        reverse=True,
    )

    selected_keywords: list[str] = []

    for phrase in ranked_phrases:
        if phrase not in selected_keywords:
            selected_keywords.append(
                phrase
            )

    for token in ranked_tokens:
        if len(selected_keywords) >= maximum_keywords:
            break

        if token in selected_keywords:
            continue

        selected_keywords.append(
            token
        )

    combined_scores: dict[str, float] = {}

    for keyword in selected_keywords:
        if keyword in phrase_scores:
            score = phrase_scores[keyword]
        else:
            score = token_scores[keyword]

        combined_scores[keyword] = round(
            float(score),
            2,
        )

    return KeywordResult(
        issue_id=issue_id,
        title=title,
        keywords=tuple(
            selected_keywords
        ),
        phrases=tuple(
            ranked_phrases
        ),
        scores=combined_scores,
    )


def extract_keywords_by_issue_id(
    issue_id: str,
    maximum_keywords: int = 12,
    maximum_phrases: int = 6,
) -> KeywordResult:
    """Load one repository issue and extract keywords."""

    try:
        issue = load_issue_record(
            issue_id
        )

    except RepositorySearchError as error:
        raise KeywordExtractionError(
            str(error)
        ) from error

    return extract_keywords(
        issue=issue,
        maximum_keywords=maximum_keywords,
        maximum_phrases=maximum_phrases,
    )


def keyword_set(
    issue: dict[str, Any],
    maximum_keywords: int = 12,
) -> set[str]:
    """Return a set suitable for similarity comparison."""

    result = extract_keywords(
        issue=issue,
        maximum_keywords=maximum_keywords,
    )

    return set(
        result.keywords
    )


def keyword_score_map(
    issue: dict[str, Any],
    maximum_keywords: int = 12,
) -> dict[str, float]:
    """Return keyword scores suitable for weighted comparison."""

    result = extract_keywords(
        issue=issue,
        maximum_keywords=maximum_keywords,
    )

    return dict(
        result.scores
    )


# ============================================================
# DEVELOPMENT DISPLAY
# ============================================================

def _print_keyword_result(
    result: KeywordResult,
) -> None:
    """Print one keyword result."""

    print(
        f"Issue : {result.title}"
    )

    print(
        f"ID    : {result.issue_id}"
    )

    print("-" * 68)
    print("KEYWORDS")

    for number, keyword in enumerate(
        result.keywords,
        start=1,
    ):
        score = result.scores.get(
            keyword,
            0.0,
        )

        print(
            f"{number:>2}. "
            f"{keyword:<35} "
            f"{score:>6.2f}"
        )

    print("-" * 68)
    print("PHRASES")

    if result.phrases:
        for number, phrase in enumerate(
            result.phrases,
            start=1,
        ):
            print(
                f"{number}. {phrase}"
            )
    else:
        print("No known UPSC phrases detected.")


# ============================================================
# DEVELOPMENT TEST
# ============================================================

def _development_test() -> None:
    """Test keyword extraction using the latest repository issue."""

    from src.intelligence.repository_search import (
        list_issue_summaries,
    )

    print("=" * 68)
    print("TODAY'S UPSC ISSUES")
    print("KEYWORD EXTRACTOR — VERSION 2.1")
    print("=" * 68)

    summaries = list_issue_summaries()

    if not summaries:
        print("No repository issues are available.")
        print("=" * 68)
        return

    latest_issue_id = summaries[0].issue_id

    result = extract_keywords_by_issue_id(
        latest_issue_id
    )

    _print_keyword_result(
        result
    )

    print("-" * 68)
    print("✓ Deterministic extraction enabled")
    print("✓ Stop-word filtering enabled")
    print("✓ Phrase detection enabled")
    print("✓ Weighted ranking enabled")
    print("✓ Repository issue loading enabled")
    print("=" * 68)


if __name__ == "__main__":
    _development_test()