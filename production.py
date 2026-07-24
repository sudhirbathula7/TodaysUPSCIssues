"""
============================================================
TODAY'S UPSC ISSUES
VERSION 3.0 PRODUCTION ENTRY POINT
Created by Sudhir
============================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.production.controller import (  # noqa: E402
    ProductionController,
    ProductionControllerError,
)


# ==========================================================
# ARGUMENT PARSER
# ==========================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Today's UPSC Issues Version 3.0 "
            "production workflow."
        )
    )

    parser.add_argument(
        "production_date",
        help=(
            "Production date in YYYY-MM-DD format."
        ),
    )

    actions = (
        parser.add_mutually_exclusive_group()
    )

    actions.add_argument(
        "--build",
        action="store_true",
        help=(
            "Validate daily production data and "
            "run the complete production pipeline."
        ),
    )

    actions.add_argument(
        "--validate",
        action="store_true",
        help=(
            "Validate daily production data only."
        ),
    )

    actions.add_argument(
        "--status",
        action="store_true",
        help=(
            "Display production readiness."
        ),
    )

    parser.add_argument(
        "--issues",
        nargs="+",
        type=int,
        metavar="NUMBER",
        help=(
            "Issue numbers to publish. "
            "Example: --issues 1 2 3"
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Allow intentional rebuilding of "
            "existing production files."
        ),
    )

    parser.add_argument(
        "--open-pdf",
        action="store_true",
        help=(
            "Open the final PDF after production."
        ),
    )

    return parser


# ==========================================================
# MAIN
# ==========================================================

def main() -> int:
    parser = build_parser()

    arguments = parser.parse_args()

    if (
        arguments.issues
        and not arguments.build
    ):
        parser.error(
            "--issues can only be used with --build."
        )

    try:
        controller = ProductionController(
            arguments.production_date
        )

        if arguments.build:
            controller.build(
                issue_numbers=(
                    arguments.issues
                ),
                overwrite=(
                    arguments.overwrite
                ),
                open_pdf=(
                    arguments.open_pdf
                ),
            )

        elif arguments.validate:
            controller.validate_canonical()

        else:
            controller.print_status()

        return 0

    except (
        ProductionControllerError,
        FileNotFoundError,
        FileExistsError,
        ValueError,
    ) as error:
        print()
        print("=" * 72)
        print("VERSION 3.0 ERROR")
        print("=" * 72)
        print(error)
        print("=" * 72)

        return 1

    except KeyboardInterrupt:
        print()
        print(
            "Production interrupted by user."
        )

        return 130


if __name__ == "__main__":
    raise SystemExit(
        main()
    )