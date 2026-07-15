"""
============================================================
Today's UPSC Issues
PDF Generator
Created by Sudhir
============================================================
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen.canvas import Canvas

from src.components.header import draw_header
from src.components.helpers import draw_page_border


def generate_preview_pdf(
    output_path: str | Path,
    date_text: str,
    logo_path: str | Path | None = None,
) -> Path:
    """
    Generate a one-page landscape preview PDF containing
    the page border and header.
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = landscape(A4)

    pdf = Canvas(
        str(output_file),
        pagesize=(page_width, page_height),
    )

    draw_page_border(
        canvas=pdf,
        page_width=page_width,
        page_height=page_height,
    )

    draw_header(
        canvas=pdf,
        page_width=page_width,
        page_height=page_height,
        date_text=date_text,
        logo_path=logo_path,
        page_number=1,
    )

    pdf.showPage()
    pdf.save()

    return output_file