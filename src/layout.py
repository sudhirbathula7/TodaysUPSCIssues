"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir

Portrait Page Layout System
===========================================================

This module calculates page geometry only.

It does not:
- draw boxes
- draw text
- set colours
- set fonts

Every PDF component receives a Rectangle from this module.
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

LEFT_MARGIN = 4 * mm
RIGHT_MARGIN = 4 * mm

TOP_MARGIN = 4 * mm
BOTTOM_MARGIN = 4 * mm


# ===========================================================
# PAGE-LEVEL HEIGHTS
# ===========================================================

HEADER_HEIGHT = 15 * mm
FOOTER_HEIGHT = 9 * mm


# ===========================================================
# PAGE-LEVEL GAPS
# ===========================================================

HEADER_GAP = 4 * mm
ISSUE_GAP = 4 * mm
FOOTER_GAP = 4 * mm


# ===========================================================
# ISSUE INTERNAL GAPS
# ===========================================================

COLUMN_GAP = 4 * mm
LEFT_BOX_GAP = 2 * mm
RIGHT_BOX_GAP = 4 * mm


# ===========================================================
# ISSUE COLUMN RATIOS
# ===========================================================

LEFT_COLUMN_RATIO = 0.68
RIGHT_COLUMN_RATIO = 0.32


# ===========================================================
# ISSUE INTERNAL HEIGHTS
# ===========================================================

ISSUE_HEADER_HEIGHT = 20 * mm

RECALL_RATIO = 0.25
QUICK_FACTS_RATIO = 0.50
TAKEAWAY_RATIO = 0.25


# ===========================================================
# BASIC RECTANGLE
# ===========================================================

@dataclass(frozen=True, slots=True)
class Rectangle:
    """
    Represents one rectangular drawing area.

    Coordinates follow ReportLab convention:

    x, y
        Bottom-left corner of the rectangle.

    width, height
        Rectangle dimensions in points.
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
    Stores the five independent boxes of one issue.

    Left side:
    - header
    - content

    Right side:
    - recall
    - quick_facts
    - takeaway
    """

    area: Rectangle

    header: Rectangle
    content: Rectangle

    recall: Rectangle
    quick_facts: Rectangle
    takeaway: Rectangle


# ===========================================================
# COMPLETE PAGE LAYOUT
# ===========================================================

@dataclass(frozen=True, slots=True)
class PageLayout:
    """
    Stores the full page geometry.
    """

    page: Rectangle

    header: Rectangle
    footer: Rectangle

    issue1: IssueLayout
    issue2: IssueLayout

    @property
    def issues(self) -> tuple[IssueLayout, IssueLayout]:
        return self.issue1, self.issue2


# ===========================================================
# VALIDATION HELPERS
# ===========================================================

def _validate_positive(name: str, value: float) -> None:
    """
    Raise an error when a calculated dimension is zero or negative.
    """

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero. "
            f"Calculated value: {value:.2f}"
        )


def _validate_ratio_total() -> None:
    """
    Ensure column and right-box ratios add up correctly.
    """

    column_total = LEFT_COLUMN_RATIO + RIGHT_COLUMN_RATIO

    if abs(column_total - 1.0) > 0.0001:
        raise ValueError(
            "LEFT_COLUMN_RATIO and RIGHT_COLUMN_RATIO "
            "must total 1.0."
        )

    right_height_total = (
        RECALL_RATIO
        + QUICK_FACTS_RATIO
        + TAKEAWAY_RATIO
    )

    if abs(right_height_total - 1.0) > 0.0001:
        raise ValueError(
            "Recall, Quick Facts and Takeaway ratios "
            "must total 1.0."
        )


# ===========================================================
# CREATE ONE ISSUE LAYOUT
# ===========================================================

def create_issue_layout(
    x: float,
    y: float,
    width: float,
    height: float,
) -> IssueLayout:
    """
    Divide one issue area into five independent boxes.

    Structure:

    Left column
        Compact issue header
        Small gap
        Six-point content box

    Right column
        Recall questions
        Gap
        Quick facts
        Gap
        Key takeaway
    """

    _validate_positive("Issue width", width)
    _validate_positive("Issue height", height)

    # -------------------------------------------------------
    # Horizontal division
    # -------------------------------------------------------

    usable_column_width = width - COLUMN_GAP

    _validate_positive(
        "Usable issue column width",
        usable_column_width,
    )

    left_width = usable_column_width * LEFT_COLUMN_RATIO
    right_width = usable_column_width * RIGHT_COLUMN_RATIO

    _validate_positive("Left column width", left_width)
    _validate_positive("Right column width", right_width)

    left_x = x
    right_x = x + left_width + COLUMN_GAP

    # -------------------------------------------------------
    # Left column
    # -------------------------------------------------------

    header_height = ISSUE_HEADER_HEIGHT

    content_height = (
        height
        - header_height
        - LEFT_BOX_GAP
    )

    _validate_positive(
        "Issue header height",
        header_height,
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
        height=header_height,
    )

    # -------------------------------------------------------
    # Right column
    # -------------------------------------------------------

    right_usable_height = (
        height
        - (2 * RIGHT_BOX_GAP)
    )

    _validate_positive(
        "Usable right-column height",
        right_usable_height,
    )

    recall_height = right_usable_height * RECALL_RATIO
    quick_facts_height = (
        right_usable_height
        * QUICK_FACTS_RATIO
    )
    takeaway_height = (
        right_usable_height
        * TAKEAWAY_RATIO
    )

    _validate_positive(
        "Recall questions height",
        recall_height,
    )
    _validate_positive(
        "Quick facts height",
        quick_facts_height,
    )
    _validate_positive(
        "Key takeaway height",
        takeaway_height,
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

    # -------------------------------------------------------
    # Complete issue area
    # -------------------------------------------------------

    issue_area = Rectangle(
        x=x,
        y=y,
        width=width,
        height=height,
    )

    return IssueLayout(
        area=issue_area,
        header=header_box,
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
    Create the complete portrait page layout.

    Vertical structure:

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

    _validate_ratio_total()

    usable_width = (
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    _validate_positive(
        "Usable page width",
        usable_width,
    )

    available_issue_height = (
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
        "Available issue height",
        available_issue_height,
    )

    issue_height = available_issue_height / 2

    _validate_positive(
        "Individual issue height",
        issue_height,
    )

    # -------------------------------------------------------
    # Footer
    # -------------------------------------------------------

    footer_box = Rectangle(
        x=LEFT_MARGIN,
        y=BOTTOM_MARGIN,
        width=usable_width,
        height=FOOTER_HEIGHT,
    )

    # -------------------------------------------------------
    # Issue 2
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
    # Issue 1
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
    # Header
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

    # -------------------------------------------------------
    # Page
    # -------------------------------------------------------

    page_box = Rectangle(
        x=0,
        y=0,
        width=PAGE_WIDTH,
        height=PAGE_HEIGHT,
    )

    # -------------------------------------------------------
    # Safety validation
    # -------------------------------------------------------

    expected_header_top = PAGE_HEIGHT - TOP_MARGIN

    if abs(header_box.top - expected_header_top) > 0.01:
        raise ValueError(
            "Page layout height calculation failed. "
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
    """
    Convert ReportLab points to millimetres.
    """

    return value / mm


def _print_rectangle(
    name: str,
    rectangle: Rectangle,
) -> None:
    """
    Print one rectangle in millimetres.
    """

    print(
        f"{name:<24}"
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

    print("=" * 90)
    print("TODAY'S UPSC ISSUES — PORTRAIT PAGE LAYOUT")
    print("=" * 90)

    _print_rectangle("Page", layout.page)
    _print_rectangle("Page Header", layout.header)

    print("-" * 90)
    print("ISSUE 1")
    _print_rectangle("Issue 1 Area", layout.issue1.area)
    _print_rectangle("Issue 1 Header", layout.issue1.header)
    _print_rectangle("Issue 1 Content", layout.issue1.content)
    _print_rectangle("Issue 1 Recall", layout.issue1.recall)
    _print_rectangle(
        "Issue 1 Quick Facts",
        layout.issue1.quick_facts,
    )
    _print_rectangle(
        "Issue 1 Takeaway",
        layout.issue1.takeaway,
    )

    print("-" * 90)
    print("ISSUE 2")
    _print_rectangle("Issue 2 Area", layout.issue2.area)
    _print_rectangle("Issue 2 Header", layout.issue2.header)
    _print_rectangle("Issue 2 Content", layout.issue2.content)
    _print_rectangle("Issue 2 Recall", layout.issue2.recall)
    _print_rectangle(
        "Issue 2 Quick Facts",
        layout.issue2.quick_facts,
    )
    _print_rectangle(
        "Issue 2 Takeaway",
        layout.issue2.takeaway,
    )

    print("-" * 90)
    _print_rectangle("Page Footer", layout.footer)

    print("=" * 90)
    print("✓ Portrait page geometry calculated successfully")
    print("=" * 90)