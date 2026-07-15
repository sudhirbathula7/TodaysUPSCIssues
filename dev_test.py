"""
============================================================
Today's UPSC Issues
Development PDF Preview
Created by Sudhir
============================================================
"""

import os
from pathlib import Path

from src.config import TODAY_UPSC_LOGO
from src.pdf_generator import generate_preview_pdf


PROJECT_ROOT = Path(__file__).resolve().parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "Published"
    / "output"
    / "test_header.pdf"
)


def main() -> None:
    logo_path = TODAY_UPSC_LOGO if TODAY_UPSC_LOGO.is_file() else None

    generated_file = generate_preview_pdf(
        output_path=OUTPUT_FILE,
        date_text="15 July 2026",
        logo_path=logo_path,
    )

    print("=" * 60)
    print("TODAY'S UPSC ISSUES — DEVELOPMENT PREVIEW")
    print("=" * 60)
    print(f"PDF created: {generated_file}")
    print(f"Logo used : {logo_path}")
    print("=" * 60)

    try:
        os.startfile(generated_file)
    except OSError:
        print("PDF created successfully but could not be opened automatically.")


if __name__ == "__main__":
    main()