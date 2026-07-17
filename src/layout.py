"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir

Portrait Page Layout System
===========================================================

This module calculates page geometry only.

It does not draw text or production content.

Final test geometry:
- A4 portrait
- 9 mm side margins
- Two equal issue areas
- 2.5 mm internal box gaps
- 3 mm gap between the two issues
- Five independent boxes per issue
- Compact issue header
- Separate title and GS badge areas
===========================================================
"""

from dataclasses import dataclass

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


# ===========================================================
# PAGE SIZE
# ===========================================================

PAGE_WIDTH, PAGE_HEIGHT = A4


# ===========================================================
# PAGE MARGINS
# ===========================================================

LEFT_MARGIN = 10 * mm
RIGHT_MARGIN = 10 * mm

TOP_MARGIN = 4 * mm
BOTTOM_MARGIN = 4 * mm


# ===========================================================
# PAGE HEADER AND FOOTER
# ===========================================================

HEADER_HEIGHT = 15 * mm
FOOTER_HEIGHT = 9 * mm

HEADER_GAP = 2.5 * mm
FOOTER_GAP = 2.5 * mm


# ===========================================================
# ISSUE SPACING
# ===========================================================

ISSUE_GAP = 3 * mm

COLUMN_GAP = 2.5 * mm
LEFT_BOX_GAP = 2.5 * mm
RIGHT_BOX_GAP = 2.5 * mm


# ===========================================================
# BOX APPEARANCE
# ===========================================================

# Used by development tests and production components.
BOX_RADIUS = 3 * mm


# ===========================================================
# ISSUE WIDTH PROPORTIONS
# ===========================================================

LEFT_COLUMN_RATIO = 0.66
RIGHT_COLUMN_RATIO = 0.34


# ===========================================================
# ISSUE HEADER
# ===========================================================

ISSUE_HEADER_HEIGHT = 18 * mm

HEADER_INNER_GAP = 2 * mm
HEADER_TITLE_RATIO = 0.75
HEADER_BADGE_RATIO = 0.25


# ===========================================================
# RIGHT COLUMN HEIGHT PROPORTIONS
# ===========================================================

RECALL_RATIO = 0.25
QUICK_FACTS_RATIO = 0.45
TAKEAWAY_RATIO = 0.30


# ===========================================================
# BASIC RECTANGLE
# ===========================================================

@dataclass(frozen=True, slots=True)
class Rectangle:
    """
    One rectangular drawing area.

    ReportLab uses the bottom-left corner as the origin.
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y

    @property
    def top(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        return self.y + (self.height / 2)


# ===========================================================
# ISSUE LAYOUT
# ===========================================================

@dataclass(frozen=True, slots=True)
class IssueLayout:
    """
    Complete geometry for one issue.

    Five main boxes:
    1. Header
    2. Six-point content
    3. Recall questions
    4. Quick facts
    5. Key takeaway

    The issue header additionally contains:
    - Title area
    - GS badge area
    """

    area: Rectangle

    header: Rectangle
    header_title: Rectangle
    header_badge: Rectangle

    content: Rectangle

    recall: Rectangle
    quick_facts: Rectangle
    takeaway: Rectangle


# ===========================================================
# PAGE LAYOUT
# ===========================================================

@dataclass(frozen=True, slots=True)
class PageLayout:
    """Complete geometry for one portrait page."""

    page: Rectangle
    header: Rectangle
    footer: Rectangle

    issue1: IssueLayout
    issue2: IssueLayout

    @property
    def issues(self) -> tuple[IssueLayout, IssueLayout]:
        return self.issue1, self.issue2


# ===========================================================
# VALIDATION
# ===========================================================

def _validate_positive(name: str, value: float) -> None:
    """Ensure a calculated measurement is usable."""

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero. "
            f"Calculated value: {value:.2f}"
        )


def _validate_ratios() -> None:
    """Ensure all proportional values total 1.0."""

    column_total = LEFT_COLUMN_RATIO + RIGHT_COLUMN_RATIO

    if abs(column_total - 1.0) > 0.0001:
        raise ValueError(
            "LEFT_COLUMN_RATIO and RIGHT_COLUMN_RATIO "
            "must total 1.0."
        )

    right_total = (
        RECALL_RATIO
        + QUICK_FACTS_RATIO
        + TAKEAWAY_RATIO
    )

    if abs(right_total - 1.0) > 0.0001:
        raise ValueError(
            "Recall, Quick Facts and Takeaway ratios "
            "must total 1.0."
        )

    header_total = (
        HEADER_TITLE_RATIO
        + HEADER_BADGE_RATIO
    )

    if abs(header_total - 1.0) > 0.0001:
        raise ValueError(
            "HEADER_TITLE_RATIO and HEADER_BADGE_RATIO "
            "must total 1.0."
        )


# ===========================================================
# CREATE ISSUE LAYOUT
# ===========================================================

def create_issue_layout(
    x: float,
    y: float,
    width: float,
    height: float,
) -> IssueLayout:
    """
    Divide one issue area into its component boxes.
    """

    _validate_positive("Issue width", width)
    _validate_positive("Issue height", height)

    # -------------------------------------------------------
    # LEFT AND RIGHT COLUMNS
    # -------------------------------------------------------

    usable_column_width = width - COLUMN_GAP

    _validate_positive(
        "Usable column width",
        usable_column_width,
    )

    left_width = (
        usable_column_width
        * LEFT_COLUMN_RATIO
    )

    right_width = (
        usable_column_width
        * RIGHT_COLUMN_RATIO
    )

    left_x = x
    right_x = x + left_width + COLUMN_GAP

    # -------------------------------------------------------
    # LEFT COLUMN: HEADER + CONTENT
    # -------------------------------------------------------

    content_height = (
        height
        - ISSUE_HEADER_HEIGHT
        - LEFT_BOX_GAP
    )

    _validate_positive(
        "Six-point content height",
        content_height,
    )

    content_box = Rectangle(
        x=left_x,
        y=y,
        width=left_width,
        height=content_height,
    )

    header_box = Rectangle(
        x=left_x,
        y=content_box.top + LEFT_BOX_GAP,
        width=left_width,
        height=ISSUE_HEADER_HEIGHT,
    )

    # -------------------------------------------------------
    # ISSUE HEADER INTERNAL DIVISION
    # -------------------------------------------------------

    usable_header_width = (
        header_box.width
        - HEADER_INNER_GAP
    )

    title_width = (
        usable_header_width
        * HEADER_TITLE_RATIO
    )

    badge_width = (
        usable_header_width
        * HEADER_BADGE_RATIO
    )

    header_title_box = Rectangle(
        x=header_box.x,
        y=header_box.y,
        width=title_width,
        height=header_box.height,
    )

    header_badge_box = Rectangle(
        x=header_title_box.right + HEADER_INNER_GAP,
        y=header_box.y,
        width=badge_width,
        height=header_box.height,
    )

    # -------------------------------------------------------
    # RIGHT COLUMN
    # -------------------------------------------------------

    right_usable_height = (
        height
        - (2 * RIGHT_BOX_GAP)
    )

    _validate_positive(
        "Usable right-column height",
        right_usable_height,
    )

    recall_height = (
        right_usable_height
        * RECALL_RATIO
    )

    quick_facts_height = (
        right_usable_height
        * QUICK_FACTS_RATIO
    )

    takeaway_height = (
        right_usable_height
        * TAKEAWAY_RATIO
    )

    takeaway_box = Rectangle(
        x=right_x,
        y=y,
        width=right_width,
        height=takeaway_height,
    )

    quick_facts_box = Rectangle(
        x=right_x,
        y=takeaway_box.top + RIGHT_BOX_GAP,
        width=right_width,
        height=quick_facts_height,
    )

    recall_box = Rectangle(
        x=right_x,
        y=quick_facts_box.top + RIGHT_BOX_GAP,
        width=right_width,
        height=recall_height,
    )

    issue_area = Rectangle(
        x=x,
        y=y,
        width=width,
        height=height,
    )

    return IssueLayout(
        area=issue_area,

        header=header_box,
        header_title=header_title_box,
        header_badge=header_badge_box,

        content=content_box,

        recall=recall_box,
        quick_facts=quick_facts_box,
        takeaway=takeaway_box,
    )


# ===========================================================
# CREATE COMPLETE PAGE LAYOUT
# ===========================================================

def create_layout() -> PageLayout:
    """
    Create the complete A4 portrait layout.

    Vertical order:

    Top margin
    Header
    Header gap
    Issue 1
    Issue gap
    Issue 2
    Footer gap
    Footer
    Bottom margin
    """

    _validate_ratios()

    usable_width = (
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    _validate_positive(
        "Usable page width",
        usable_width,
    )

    total_issue_height = (
        PAGE_HEIGHT
        - TOP_MARGIN
        - BOTTOM_MARGIN
        - HEADER_HEIGHT
        - FOOTER_HEIGHT
        - HEADER_GAP
        - ISSUE_GAP
        - FOOTER_GAP
    )

    _validate_positive(
        "Total issue height",
        total_issue_height,
    )

    issue_height = total_issue_height / 2

    # -------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------

    footer_box = Rectangle(
        x=LEFT_MARGIN,
        y=BOTTOM_MARGIN,
        width=usable_width,
        height=FOOTER_HEIGHT,
    )

    # -------------------------------------------------------
    # ISSUE 2
    # -------------------------------------------------------

    issue2_y = (
        footer_box.top
        + FOOTER_GAP
    )

    issue2 = create_issue_layout(
        x=LEFT_MARGIN,
        y=issue2_y,
        width=usable_width,
        height=issue_height,
    )

    # -------------------------------------------------------
    # ISSUE 1
    # -------------------------------------------------------

    issue1_y = (
        issue2.area.top
        + ISSUE_GAP
    )

    issue1 = create_issue_layout(
        x=LEFT_MARGIN,
        y=issue1_y,
        width=usable_width,
        height=issue_height,
    )

    # -------------------------------------------------------
    # PAGE HEADER
    # -------------------------------------------------------

    header_y = (
        issue1.area.top
        + HEADER_GAP
    )

    header_box = Rectangle(
        x=LEFT_MARGIN,
        y=header_y,
        width=usable_width,
        height=HEADER_HEIGHT,
    )

    page_box = Rectangle(
        x=0,
        y=0,
        width=PAGE_WIDTH,
        height=PAGE_HEIGHT,
    )

    # Ensure the layout ends exactly at the top margin.
    expected_header_top = (
        PAGE_HEIGHT
        - TOP_MARGIN
    )

    if abs(header_box.top - expected_header_top) > 0.01:
        raise ValueError(
            "Vertical page calculation failed. "
            f"Header top: {header_box.top:.2f}; "
            f"expected: {expected_header_top:.2f}"
        )

    return PageLayout(
        page=page_box,
        header=header_box,
        footer=footer_box,
        issue1=issue1,
        issue2=issue2,
    )


# ===========================================================
# DEVELOPMENT DISPLAY
# ===========================================================

def _to_mm(value: float) -> float:
    """Convert ReportLab points to millimetres."""

    return value / mm


def _print_rectangle(
    name: str,
    rectangle: Rectangle,
) -> None:
    """Print one rectangle in millimetres."""

    print(
        f"{name:<25}"
        f"x={_to_mm(rectangle.x):>7.2f} mm  "
        f"y={_to_mm(rectangle.y):>7.2f} mm  "
        f"w={_to_mm(rectangle.width):>7.2f} mm  "
        f"h={_to_mm(rectangle.height):>7.2f} mm"
    )


# ===========================================================
# DEVELOPMENT TEST
# ===========================================================

if __name__ == "__main__":

    layout = create_layout()

    print("=" * 92)
    print("TODAY'S UPSC ISSUES — PORTRAIT PAGE GEOMETRY")
    print("=" * 92)

    _print_rectangle("Page", layout.page)
    _print_rectangle("Page Header", layout.header)

    for number, issue in enumerate(
        layout.issues,
        start=1,
    ):
        print("-" * 92)
        print(f"ISSUE {number}")

        _print_rectangle(
            f"Issue {number} Area",
            issue.area,
        )

        _print_rectangle(
            f"Issue {number} Header",
            issue.header,
        )

        _print_rectangle(
            f"Issue {number} Title Area",
            issue.header_title,
        )

        _print_rectangle(
            f"Issue {number} Badge Area",
            issue.header_badge,
        )

        _print_rectangle(
            f"Issue {number} Content",
            issue.content,
        )

        _print_rectangle(
            f"Issue {number} Recall",
            issue.recall,
        )

        _print_rectangle(
            f"Issue {number} Quick Facts",
            issue.quick_facts,
        )

        _print_rectangle(
            f"Issue {number} Takeaway",
            issue.takeaway,
        )

    print("-" * 92)
    _print_rectangle("Page Footer", layout.footer)

    print("=" * 92)
    print("✓ Portrait geometry calculated successfully")
    print("=" * 92)