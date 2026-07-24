from pathlib import Path

PROMPT_FILE = Path(r"project\prompt\Master_Prompt_v5.0.md")

text = PROMPT_FILE.read_text(encoding="utf-8")

marker = """============================================================
PDF OBJECT
============================================================
"""

description_section = """============================================================
DESCRIPTION
============================================================

Generate ONE concise description for every issue.

The description must summarise the issue in one sentence.

It will be used for:

• Repository preview
• Search results
• Website cards
• Future AI retrieval

Maximum 25 words.

============================================================
PDF OBJECT
============================================================
"""

if "DESCRIPTION\n============================================================" in text:
    print("DESCRIPTION section already exists.")
elif marker not in text:
    raise RuntimeError("PDF OBJECT section not found.")
else:
    text = text.replace(marker, description_section, 1)
    PROMPT_FILE.write_text(text, encoding="utf-8")
    print("✅ DESCRIPTION section added successfully.")