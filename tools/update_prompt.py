from pathlib import Path

PROMPT_FILE = Path(r"project\prompt\Master_Prompt_v5.0.md")   # Change if needed

text = PROMPT_FILE.read_text(encoding="utf-8")

replacements = [
    ("learning", "pdf"),
    ("Learning Object", "PDF Object"),
    ("LEARNING OBJECT", "PDF OBJECT"),
    ("media", "outputs"),
    ("Media Object", "Outputs Object"),
    ("MEDIA OBJECT", "OUTPUTS OBJECT"),
    ("gs_paper", "gs_papers"),
    ("youtube_shorts", "youtube_short"),
    ("YouTube_shorts", "YouTube_short"),
]

for old, new in replacements:
    text = text.replace(old, new)

PROMPT_FILE.write_text(text, encoding="utf-8")

print("✅ Prompt updated successfully.")