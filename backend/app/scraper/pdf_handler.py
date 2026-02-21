import httpx
from pdfminer.high_level import extract_text
from io import BytesIO
from backend.app.logs.logger import logger

# ✅ Added realistic browser headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://fremontunified.org/",
    "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
}

def extract_pdf_text(pdf_url):
    """Download PDF and extract text."""

    logger.info(f"Downloading PDF: {pdf_url}")

    try:
        # ✅ changed to client with headers + redirect support
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            response = client.get(pdf_url)

        response.raise_for_status()

    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        return None

    try:
        pdf_file = BytesIO(response.content)
        text = extract_text(pdf_file)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None

    if not text.strip():
        logger.warning("PDF contained no text")
        return None

    logger.info(f"Extracted {len(text)} characters from PDF")

    return {"url": pdf_url, "text": text}