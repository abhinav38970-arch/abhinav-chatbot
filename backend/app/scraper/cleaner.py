import re

from backend.app.logs.logger import logger

def clean_text(raw_text):
    # Check if the text actually exists; if not, stop here.
    if not raw_text:
        logger.warning("Skipping empty content")
        return ""

    logger.info("Cleaning text")

    # Replace old-style Windows carriage returns (\r) with standard newlines (\n).
    text = raw_text.replace("\r", "\n")
    # Find any group of tabs or extra spaces and turn them into one single space.
    text = re.sub(r"[ \t]+", " ", text)
    # Find any places where there are 3+ newlines in a row and turn them into just 2.
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Use a 'set' to keep track of lines we have already seen.
    seen = set()
    cleaned_lines = []

    # Split the big block of text into individual lines to check them one by one.
    for line in text.split("\n"):
        # Remove whitespace from the start and end of the line.
        line = line.strip()
        # If the line is empty after stripping, skip it.
        if not line:
            continue
        # If we haven't seen this exact line before, save it and mark it as 'seen'.
        # This is what stops the repetitive menu items from filling your DB.
        if line not in seen:
            seen.add(line)
            cleaned_lines.append(line)

    # Join all the unique lines back together into one big string.
    cleaned_text = "\n".join(cleaned_lines)

    logger.info("Cleaning complete")
    return cleaned_text