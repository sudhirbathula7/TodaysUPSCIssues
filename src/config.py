"""
===========================================================
Today's UPSC Issues
Version : 1.0
Created By : Sudhir
Configuration File
===========================================================
"""
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
import os

# ===========================================================
# PROJECT INFORMATION
# ===========================================================

PROJECT_NAME = "Today's UPSC Issues"
VERSION = "1.0"
AUTHOR = "Sudhir"

# ===========================================================
# ROOT PATHS
# ===========================================================

# config.py is inside the src folder.
# Therefore, move one level upward to reach the project root.
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DAILY_WORK_DIR = os.path.join(ROOT_DIR, "Daily_Work")

INPUT_DIR = os.path.join(
    DAILY_WORK_DIR,
    "input",
)

GENERATED_DIR = os.path.join(
    DAILY_WORK_DIR,
    "generated",
)

OUTPUT_DIR = os.path.join(
    ROOT_DIR,
    "Published",
    "output",
)

REPOSITORY_DIR = os.path.join(
    ROOT_DIR,
    "Repository",
)

EDITORIAL_ARCHIVE_DIR = os.path.join(
    REPOSITORY_DIR,
    "Editorial_Archive",
)

ISSUE_DATASETS_DIR = os.path.join(
    REPOSITORY_DIR,
    "Issue_Datasets",
)

ISSUE_SELECTION_DIR = os.path.join(
    REPOSITORY_DIR,
    "Issue_Selection",
)

PENDING_DIR = os.path.join(
    REPOSITORY_DIR,
    "Pending",
)

PUBLISHED_REPOSITORY_DIR = os.path.join(
    REPOSITORY_DIR,
    "Published",
)

SYSTEM_DIR = os.path.join(
    ROOT_DIR,
    "System",
)

PROMPT_DIR = os.path.join(
    SYSTEM_DIR,
    "prompts",
)

TEMP_DIR = os.path.join(
    ROOT_DIR,
    "temp",
)

ASSETS_DIR = os.path.join(
    ROOT_DIR,
    "assets",
)

FONT_DIR = os.path.join(
    ASSETS_DIR,
    "fonts",
)

IMAGE_DIR = os.path.join(
    ASSETS_DIR,
    "images",
)

LOCKED_REFERENCE_IMAGE = os.path.join(
    IMAGE_DIR,
    "locked_reference.png",
)
# ===========================================================
# PDF SETTINGS
# ===========================================================

PAGE_SIZE = landscape(A4)

PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

PDF_TITLE = "Today's UPSC Issues"

# ===========================================================
# PAGE MARGINS
# ===========================================================

LEFT_MARGIN = 20
RIGHT_MARGIN = 20
TOP_MARGIN = 18
BOTTOM_MARGIN = 18

# ===========================================================
# FONTS
# ===========================================================

TITLE_FONT = "Helvetica-Bold"
HEADING_FONT = "Helvetica-Bold"
BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"

# ===========================================================
# FONT SIZES
# ===========================================================

TITLE_SIZE = 18

SECTION_TITLE_SIZE = 10
BODY_SIZE = 9

QUESTION_SIZE = 9
FACT_SIZE = 8

FOOTER_SIZE = 8
HEADER_SIZE = 9

# ===========================================================
# BRAND ASSETS
# ===========================================================

LOGOS_DIR = os.path.join(
    ASSETS_DIR,
    "logos",
)

TODAY_UPSC_LOGO = os.path.join(
    LOGOS_DIR,
    "today_upsc_logo.png",
)

# ===========================================================
# COLOURS
# ===========================================================

PRIMARY = HexColor("#0F2A5F")
SECONDARY = HexColor("#4A4A4A")

TEXT = HexColor("#202020")

LIGHT_GREY = HexColor("#F4F4F4")

BORDER = HexColor("#D8D8D8")

LINE = HexColor("#DDDDDD")

WHITE = HexColor("#FFFFFF")

# ===========================================================
# PAGE LAYOUT
# ===========================================================

HEADER_HEIGHT = 34
FOOTER_HEIGHT = 18

PAGE_GAP = 12

ISSUES_PER_PAGE = 2

TOTAL_PAGES = 2

# ===========================================================
# ISSUE BLOCK
# ===========================================================

ISSUE_SPACING = 10

SECTION_SPACING = 5

BOX_PADDING = 6

LINE_SPACING = 13

# ===========================================================
# VALIDATION
# ===========================================================

MAX_EDITORIALS = 5

MAX_EXTRACTED_ISSUES = 8

SELECTED_ISSUES = 4

MIN_ISSUE_RATING = 4.5

# ===========================================================
# OUTPUT
# ===========================================================

OUTPUT_PREFIX = "TUI"

DATE_FORMAT = "%d-%m-%Y"

# ===========================================================
# DEBUG
# ===========================================================

DEBUG = False

OPEN_PDF_AFTER_GENERATION = True