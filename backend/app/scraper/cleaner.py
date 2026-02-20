import re


def clean_text(raw_text):
    """
    Cleans parsed webpage text for AI processing.
    """

    if not raw_text:
        print("🧹 Skipping empty content...")
        return ""

    print("🧹 Cleaning text...")

    # normalize line endings
    text = raw_text.replace("\r", "\n")

    # remove extra spaces
    text = re.sub(r"[ \t]+", " ", text)

    # remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # remove duplicate lines
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

    print("✅ Cleaning complete")

    return cleaned_text