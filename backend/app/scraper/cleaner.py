import re
from backend.app.logs.logger import logger

def clean_text(raw_text):
    """Cleans parsed webpage text."""

    if not raw_text:
        logger.warning("Skipping empty content")
        return ""

    logger.info("Cleaning text")

    text = raw_text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    seen = set()
    cleaned_lines = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)

    logger.info("Cleaning complete")

    return cleaned_text