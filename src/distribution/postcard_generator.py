from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont


CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350
NAVY = "#102A5C"
WHITE = "#FFFFFF"
INK = "#16243C"
MUTED = "#64748B"
BORDER = "#DCE3ED"
PALE_BLUE = "#F6F8FC"


class PostcardGeneratorError(RuntimeError):
    """Raised when the daily postcard cannot be generated."""


@dataclass(frozen=True)
class PostcardIssue:
    number: int
    question: str
    anchors: tuple[str, ...]


@dataclass(frozen=True)
class PostcardData:
    production_date: datetime
    issues: tuple[PostcardIssue, ...]


def _font_candidates(bold: bool = False) -> list[Path]:
    if sys.platform.startswith("win"):
        win = Path("C:/Windows/Fonts")
        names = ["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]
        return [win / name for name in names]

    names = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    )
    return [Path(name) for name in names]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _font_candidates(bold=bold):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def parse_date(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise PostcardGeneratorError(
        "production.production_date must use YYYY-MM-DD, DD-MM-YYYY, or DD-MM-YY. "
        f"Received: {value!r}"
    )


def load_postcard_data(input_file: Path) -> PostcardData:
    if not input_file.exists():
        raise PostcardGeneratorError(f"Input JSON not found: {input_file}")

    try:
        raw = json.loads(input_file.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PostcardGeneratorError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    production = raw.get("production")
    issues = raw.get("issues")
    if not isinstance(production, dict):
        raise PostcardGeneratorError("Missing valid 'production' object.")
    if not isinstance(issues, list):
        raise PostcardGeneratorError("Missing valid 'issues' list.")
    if len(issues) not in (3, 4):
        raise PostcardGeneratorError("Postcard currently supports exactly 3 or 4 issues.")

    date_value = str(production.get("production_date", "")).strip()
    if not date_value:
        raise PostcardGeneratorError("Missing production.production_date.")

    declared = production.get("total_issues")
    if declared is not None and declared != len(issues):
        raise PostcardGeneratorError(
            f"production.total_issues is {declared}, but {len(issues)} issues were found."
        )

    parsed_issues: list[PostcardIssue] = []
    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            raise PostcardGeneratorError(f"Issue {index} must be an object.")

        metadata = issue.get("metadata") or {}
        recall = issue.get("recall")
        if not isinstance(recall, dict):
            raise PostcardGeneratorError(f"Issue {index} is missing a valid recall object.")

        questions = recall.get("recall_questions")
        anchors = recall.get("revision_anchors")
        if not isinstance(questions, list) or not questions:
            raise PostcardGeneratorError(f"Issue {index} needs at least one recall question.")
        if not isinstance(anchors, list) or len(anchors) != 5:
            raise PostcardGeneratorError(f"Issue {index} must contain exactly five revision anchors.")

        question = str(questions[0]).strip()
        cleaned_anchors = tuple(str(anchor).strip() for anchor in anchors)
        if not question or any(not anchor for anchor in cleaned_anchors):
            raise PostcardGeneratorError(f"Issue {index} contains an empty question or anchor.")

        number = metadata.get("issue_number", index)
        if not isinstance(number, int):
            number = index

        parsed_issues.append(
            PostcardIssue(number=number, question=question, anchors=cleaned_anchors)
        )

    return PostcardData(
        production_date=parse_date(date_value),
        issues=tuple(parsed_issues),
    )


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int | None = None,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        final = lines[-1]
        while final and text_width(draw, final + "…", font) > max_width:
            final = final[:-1].rstrip()
        lines[-1] = final + "…"

    return lines


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: str,
) -> None:
    width = text_width(draw, text, font)
    draw.text((center_x - width / 2, y), text, font=font, fill=fill)


def draw_logo(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    logo_file: Path | None,
    x: int,
    y: int,
    size: int,
) -> None:
    if logo_file and logo_file.exists():
        try:
            logo = Image.open(logo_file).convert("RGBA")
            logo.thumbnail((size, size), Image.Resampling.LANCZOS)
            px = x + (size - logo.width) // 2
            py = y + (size - logo.height) // 2
            canvas.alpha_composite(logo, (px, py))
            return
        except OSError:
            pass

    draw.rounded_rectangle((x, y, x + size, y + size), radius=16, fill=NAVY)
    font = load_font(27, bold=True)
    draw_centered_text(draw, "TUI", x + size // 2, y + 22, font, WHITE)


def draw_paper_plane(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int = 22) -> None:
    draw.polygon(
        [(x, y + scale // 2), (x + scale, y), (x + scale * 3 // 5, y + scale)],
        fill=NAVY,
    )
    draw.line(
        [(x + scale // 3, y + scale // 2), (x + scale * 3 // 5, y + scale)],
        fill=WHITE,
        width=2,
    )


def generate_postcard(
    input_file: Path,
    output_file: Path,
    logo_file: Path | None = None,
    overwrite: bool = True,
) -> Path:
    if output_file.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output_file}")

    data = load_postcard_data(input_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    title_font = load_font(43, bold=True)
    hero_font = load_font(36, bold=True)
    progress_font = load_font(20, bold=True)
    date_font = load_font(19, bold=True)
    number_font = load_font(21, bold=True)
    question_font = load_font(27, bold=False)
    anchor_font = load_font(23, bold=True)
    cta_font = load_font(21, bold=True)
    value_font = load_font(17, bold=False)
    footer_font = load_font(18, bold=True)

    # Header
    margin_x = 64
    draw_logo(canvas, draw, logo_file, margin_x, 40, 102)
    draw_centered_text(draw, "TODAY'S UPSC ISSUES", CANVAS_WIDTH // 2, 58, title_font, NAVY)

    # Hero banner
    hero_box = (64, 151, 1016, 228)
    draw.rounded_rectangle(hero_box, radius=20, fill=NAVY)
    draw_centered_text(draw, f"{len(data.issues)} TOPICS TO COVER TODAY", CANVAS_WIDTH // 2, 169, hero_font, WHITE)

    # Progress/date line
    progress_y = 260
    draw.text((68, progress_y), "Small Daily Progress. Big UPSC Success.", font=progress_font, fill=INK)
    date_text = data.production_date.strftime("%d %B %Y").upper()
    date_w = text_width(draw, date_text, date_font)
    calendar_x = 1012 - date_w - 34
    draw.rounded_rectangle((calendar_x, progress_y + 1, calendar_x + 22, progress_y + 23), radius=4, outline=NAVY, width=2)
    draw.line((calendar_x + 4, progress_y + 7, calendar_x + 18, progress_y + 7), fill=NAVY, width=2)
    draw.text((calendar_x + 31, progress_y), date_text, font=date_font, fill=NAVY)

    # Main card
    card_left, card_top, card_right, card_bottom = 64, 313, 1016, 1035
    draw.rounded_rectangle(
        (card_left, card_top, card_right, card_bottom),
        radius=32,
        fill=WHITE,
        outline=BORDER,
        width=3,
    )

    inner_left = card_left + 36
    inner_right = card_right - 36
    issue_height = (card_bottom - card_top - 18) / len(data.issues)

    for idx, issue in enumerate(data.issues):
        section_top = int(card_top + 10 + idx * issue_height)
        section_bottom = int(card_top + 10 + (idx + 1) * issue_height)

        # Number badge
        badge_x, badge_y = inner_left, section_top + 22
        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + 48, badge_y + 38),
            radius=10,
            fill=NAVY,
        )
        label = f"{idx + 1:02d}"
        label_w = text_width(draw, label, number_font)
        draw.text((badge_x + 24 - label_w / 2, badge_y + 6), label, font=number_font, fill=WHITE)

        # Question
        question_x = badge_x + 67
        question_width = inner_right - question_x
        q_lines = wrap_text(draw, issue.question, question_font, question_width, max_lines=2)
        q_y = section_top + 16
        for line in q_lines:
            draw.text((question_x, q_y), line, font=question_font, fill=INK)
            q_y += 37

        # Anchors
        anchor_text = "  •  ".join(issue.anchors)
        anchor_lines = wrap_text(draw, anchor_text, anchor_font, question_width, max_lines=2)
        anchor_y = max(section_top + 94, q_y + 8)
        for line in anchor_lines:
            draw.text((question_x, anchor_y), line, font=anchor_font, fill="#4B5563")
            anchor_y += 31

        # Divider between issues only
        if idx < len(data.issues) - 1:
            divider_y = section_bottom
            draw.line((inner_left, divider_y, inner_right, divider_y), fill=BORDER, width=2)

    # PDF value strip
    cta_top, cta_bottom = 1068, 1204
    draw.rounded_rectangle((64, cta_top, 1016, cta_bottom), radius=22, fill=PALE_BLUE, outline=BORDER, width=2)
    draw.rounded_rectangle((82, cta_top + 18, 382, cta_top + 61), radius=13, fill=NAVY)
    draw.text((101, cta_top + 27), "CONTINUE WITH TODAY'S PDF  →", font=cta_font, fill=WHITE)

    value_text = (
        "Current Context  •  Why It Matters  •  Core Concept  •  Challenges  •  "
        "Way Forward  •  Quick Facts  •  UPSC Practice Question"
    )
    value_lines = wrap_text(draw, value_text, value_font, 892, max_lines=2)
    value_y = cta_top + 77
    for line in value_lines:
        draw.text((94, value_y), line, font=value_font, fill=INK)
        value_y += 24

    # Footer
    footer_y = 1270
    draw.line((64, footer_y - 20, 1016, footer_y - 20), fill=BORDER, width=2)
    draw.text((68, footer_y), "UPSC Issues by Kumar", font=footer_font, fill=NAVY)
    telegram_text = "@upscissues"
    telegram_w = text_width(draw, telegram_text, footer_font)
    icon_x = 1012 - telegram_w - 34
    draw_paper_plane(draw, icon_x, footer_y + 1, scale=22)
    draw.text((icon_x + 31, footer_y), telegram_text, font=footer_font, fill=NAVY)

    canvas.convert("RGB").save(output_file, quality=95)

    # Automatically open the postcard after generation on Windows.
    try:
        os.startfile(output_file)
    except (AttributeError, OSError):
        pass

    return output_file


def default_logo_path(project_root: Path) -> Path | None:
    candidates = [
        project_root / "src" / "distribution" / "assets" / "logo.png",
        project_root / "src" / "distribution" / "assets" / "logo.jpg",
        project_root / "assets" / "logo.png",
    ]
    return next((path for path in candidates if path.exists()), None)


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    input_file = project_root / "input" / "DAILY_INPUT.json"
    output_dir = project_root / "output" / "postcard_preview"

    try:
        data = load_postcard_data(input_file)
        date_slug = data.production_date.strftime("%d-%m-%y")
        output_file = output_dir / f"Todays_UPSC_Issues_Postcard_{date_slug}.png"
        created = generate_postcard(
            input_file=input_file,
            output_file=output_file,
            logo_file=default_logo_path(project_root),
            overwrite=True,
        )
        print("=" * 72)
        print("TODAY'S UPSC ISSUES — POSTCARD GENERATED")
        print("=" * 72)
        print(created)
        return 0
    except (PostcardGeneratorError, FileNotFoundError, FileExistsError, OSError) as exc:
        print("=" * 72)
        print("POSTCARD GENERATION FAILED")
        print("=" * 72)
        print(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())