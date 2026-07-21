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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Today's UPSC Issues Version 3.0 "
            "production workflow."
        )
    )

    parser.add_argument(
        "production_date",
        help="Production date in YYYY-MM-DD format.",
    )

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        "--prepare",
        action="store_true",
        help=(
            "Create/load the session and generate "
            "the Issue Selection Prompt."
        ),
    )

    actions.add_argument(
        "--select",
        nargs="+",
        type=int,
        metavar="NUMBER",
        help=(
            "Save selected issue numbers and generate "
            "the Final Content Prompt."
        ),
    )

    actions.add_argument(
        "--import-response",
        action="store_true",
        help=(
            "Import final_ai_response.txt as "
            "generated_content.json."
        ),
    )

    actions.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated_content.json.",
    )

    actions.add_argument(
        "--build",
        action="store_true",
        help=(
            "Validate, adapt and run the existing "
            "Version 2.1 production pipeline."
        ),
    )

    actions.add_argument(
        "--run",
        action="store_true",
        help=(
            "Import the AI response, validate it, "
            "adapt it and run complete production."
        ),
    )

    actions.add_argument(
        "--status",
        action="store_true",
        help="Display current session status.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Allow intentional replacement or rebuilding "
            "of existing session and production files."
        ),
    )

    parser.add_argument(
        "--open-pdf",
        action="store_true",
        help="Open the final PDF after production.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()

    try:
        controller = ProductionController(
            arguments.production_date
        )

        if arguments.prepare:
            controller.prepare_session(
                overwrite=arguments.overwrite
            )

        elif arguments.select:
            controller.select_issues(
                arguments.select,
                overwrite=arguments.overwrite,
            )

        elif arguments.import_response:
            controller.import_ai_response(
                overwrite=arguments.overwrite
            )

        elif arguments.validate:
            controller.validate_canonical()

        elif arguments.build:
            controller.validate_canonical()

            controller.create_v21_input(
                overwrite=arguments.overwrite
            )

            controller.run_v21_pipeline(
                overwrite=arguments.overwrite,
                open_pdf=arguments.open_pdf,
            )

        elif arguments.run:
            controller.run(
                overwrite=arguments.overwrite,
                open_pdf=arguments.open_pdf,
            )

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
        print("Production interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())