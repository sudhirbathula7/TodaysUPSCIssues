"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 → VERSION 2.1 ADAPTER TEST
Created by Sudhir
============================================================
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.production.paths import (  # noqa: E402
    PRODUCTION_TEMPLATES_DIR,
)
from src.production.v21_adapter import (  # noqa: E402
    AdapterOutputError,
    V21Adapter,
    convert_canonical_data_to_v21,
)
from src.repository_generator import (  # noqa: E402
    normalise_issue,
)


TEST_DATE = "2026-07-21"

SAMPLE_FILE = (
    PRODUCTION_TEMPLATES_DIR
    / "generated_content_sample.json"
)

TEST_DIR = (
    PROJECT_ROOT
    / "production"
    / "adapter_test"
)

TEST_OUTPUT_FILE = (
    TEST_DIR
    / "selected_issues.json"
)


def main() -> None:
    print("=" * 72)
    print(
        "TODAY'S UPSC ISSUES — VERSION 2.1 ADAPTER TEST"
    )
    print("=" * 72)

    # ------------------------------------------------------
    # CLEAN TEST DIRECTORY
    # ------------------------------------------------------

    if TEST_DIR.exists():
        shutil.rmtree(
            TEST_DIR
        )

    TEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("✓ Adapter test directory prepared")

    # ------------------------------------------------------
    # SAMPLE FILE
    # ------------------------------------------------------

    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(
            f"Canonical sample not found: {SAMPLE_FILE}"
        )

    print("✓ Canonical sample found")

    # ------------------------------------------------------
    # LOAD CANONICAL DATA
    # ------------------------------------------------------

    canonical_data = json.loads(
        SAMPLE_FILE.read_text(
            encoding="utf-8"
        )
    )

    converted_data = (
        convert_canonical_data_to_v21(
            canonical_data,
            source_files=[],
        )
    )

    if converted_data[
        "publication_date"
    ] != TEST_DATE:
        raise AssertionError(
            "Publication date was not converted correctly."
        )

    if len(
        converted_data["selected_issues"]
    ) != 2:
        raise AssertionError(
            "Expected two converted issues."
        )

    print("✓ Canonical dataset translated in memory")

    # ------------------------------------------------------
    # FIELD MAPPING TEST
    # ------------------------------------------------------

    first_issue = (
        converted_data["selected_issues"][0]
    )

    required_fields = {
        "title",
        "gs_paper",
        "category",
        "rating",
        "current_context",
        "why_it_matters_for_upsc",
        "core_concept",
        "challenges",
        "way_forward",
        "quick_facts",
        "what_upsc_asks",
        "key_takeaway",
        "recall_questions",
        "youtube_short_script",
        "anchors",
        "telegram_caption",
        "website_heading",
    }

    missing_fields = (
        required_fields
        - set(first_issue.keys())
    )

    if missing_fields:
        raise AssertionError(
            "Converted issue is missing fields: "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    if first_issue["rating"] != "4.8/5":
        raise AssertionError(
            "Rating was not converted correctly."
        )

    if (
        first_issue["why_it_matters_for_upsc"]
        != canonical_data["issues"][0][
            "content"
        ]["why_it_matters"]
    ):
        raise AssertionError(
            "why_it_matters was not mapped correctly."
        )

    if (
        first_issue["recall_questions"]
        != canonical_data["issues"][0][
            "recall"
        ]["questions"]
    ):
        raise AssertionError(
            "Recall questions were not mapped correctly."
        )

    print("✓ Version 2.1 field mapping verified")

    # ------------------------------------------------------
    # EXISTING VERSION 2.1 COMPATIBILITY
    # ------------------------------------------------------

    normalised_issue = normalise_issue(
        issue=first_issue,
        publication_date=date.fromisoformat(
            TEST_DATE
        ),
        sequence_number=1,
    )

    required_normalised_fields = {
        "issue_id",
        "slug",
        "publication_date",
        "title",
        "gs_paper",
        "category",
        "rating",
        "pdf_content",
        "recall",
        "youtube",
        "telegram",
        "website",
        "usage",
    }

    missing_normalised_fields = (
        required_normalised_fields
        - set(normalised_issue.keys())
    )

    if missing_normalised_fields:
        raise AssertionError(
            "Version 2.1 normalisation output is "
            "missing fields: "
            + ", ".join(
                sorted(
                    missing_normalised_fields
                )
            )
        )

    if (
        normalised_issue["title"]
        != first_issue["title"]
    ):
        raise AssertionError(
            "Version 2.1 changed the issue title "
            "unexpectedly."
        )

    if (
        normalised_issue["recall"]["questions"]
        != first_issue["recall_questions"]
    ):
        raise AssertionError(
            "Version 2.1 did not accept recall questions."
        )

    print(
        "✓ Existing Version 2.1 normalise_issue() accepted "
        "the converted issue"
    )

    # ------------------------------------------------------
    # WRITE TEST OUTPUT
    # ------------------------------------------------------

    adapter = V21Adapter(
        expected_production_date=TEST_DATE
    )

    result = adapter.convert_file(
        canonical_file=SAMPLE_FILE,
        output_file=TEST_OUTPUT_FILE,
        source_files=[],
        overwrite=False,
    )

    if not TEST_OUTPUT_FILE.exists():
        raise AssertionError(
            "Adapter output file was not created."
        )

    if result.issue_count != 2:
        raise AssertionError(
            "Adapter result issue count is incorrect."
        )

    print("✓ Test selected_issues.json created")

    # ------------------------------------------------------
    # OUTPUT JSON TEST
    # ------------------------------------------------------

    output_data = json.loads(
        TEST_OUTPUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    if output_data != converted_data:
        raise AssertionError(
            "Written adapter output differs from "
            "the in-memory conversion."
        )

    print("✓ Written Version 2.1 JSON verified")

    # ------------------------------------------------------
    # IDENTICAL RE-RUN TEST
    # ------------------------------------------------------

    identical_result = adapter.convert_file(
        canonical_file=SAMPLE_FILE,
        output_file=TEST_OUTPUT_FILE,
        source_files=[],
        overwrite=False,
    )

    if identical_result.issue_count != 2:
        raise AssertionError(
            "Identical rerun result is incorrect."
        )

    print(
        "✓ Identical adapter rerun completed safely"
    )

    # ------------------------------------------------------
    # OVERWRITE PROTECTION TEST
    # ------------------------------------------------------

    changed_data = json.loads(
        TEST_OUTPUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    changed_data["selected_issues"][0][
        "title"
    ] = "Changed Test Title"

    TEST_OUTPUT_FILE.write_text(
        json.dumps(
            changed_data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        adapter.convert_file(
            canonical_file=SAMPLE_FILE,
            output_file=TEST_OUTPUT_FILE,
            source_files=[],
            overwrite=False,
        )
    except AdapterOutputError:
        print(
            "✓ Different existing output protected"
        )
    else:
        raise AssertionError(
            "Adapter did not protect different "
            "existing output."
        )

    # ------------------------------------------------------
    # OVERWRITE AND BACKUP TEST
    # ------------------------------------------------------

    overwrite_result = adapter.convert_file(
        canonical_file=SAMPLE_FILE,
        output_file=TEST_OUTPUT_FILE,
        source_files=[],
        overwrite=True,
        create_backup=True,
    )

    if overwrite_result.backup_file is None:
        raise AssertionError(
            "Expected an adapter backup file."
        )

    if not overwrite_result.backup_file.exists():
        raise AssertionError(
            "Adapter backup file was not created."
        )

    print("✓ Explicit overwrite created backup")

    # ------------------------------------------------------
    # FINAL VERSION 2.1 NORMALISATION TEST
    # ------------------------------------------------------

    final_data = json.loads(
        TEST_OUTPUT_FILE.read_text(
            encoding="utf-8"
        )
    )

    for sequence_number, issue in enumerate(
        final_data["selected_issues"],
        start=1,
    ):
        normalised = normalise_issue(
            issue=issue,
            publication_date=date.fromisoformat(
                final_data[
                    "publication_date"
                ]
            ),
            sequence_number=sequence_number,
        )

        if not normalised.get("issue_id"):
            raise AssertionError(
                "Version 2.1 did not generate issue_id."
            )

        if not normalised.get("slug"):
            raise AssertionError(
                "Version 2.1 did not generate slug."
            )

    print(
        "✓ All converted issues accepted by "
        "Version 2.1"
    )

    print("-" * 72)
    result.display()
    print("-" * 72)
    print("VERSION 2.1 ADAPTER TEST PASSED")
    print("-" * 72)
    print("Test output:")
    print(f"  {TEST_OUTPUT_FILE}")
    print()
    print("Real daily input was not modified.")
    print()
    print("Next locked step:")
    print("  Build the Version 3.0 Prompt Builder")
    print("=" * 72)


if __name__ == "__main__":
    main()