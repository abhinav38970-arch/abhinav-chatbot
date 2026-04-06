import httpx
from pdfminer.high_level import extract_text
from io import BytesIO
from backend.app.logs.logger import logger

# Headers including 'Referer' to prove we are coming from the school site (stops 404s).
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://fremontunified.org/washington/",
    "Accept": "application/pdf"
}

def extract_pdf_text(pdf_url):
    logger.info(f"Downloading PDF: {pdf_url}")

    try:
        # Use httpx to download the PDF file as raw 'binary' data.
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            response = client.get(pdf_url)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        return None

    try:
        # Turn the raw download into a file-like object in memory.
        pdf_file = BytesIO(response.content)
        # Use PDFMiner to scrape the actual text out of the document.
        text = extract_text(pdf_file)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None

    # If the PDF was just an image (no selectable text), it will be empty.
    if not text.strip():
        logger.warning("PDF contained no text (might be an image)")
        return None

    # Label the source so the AI knows this is a document.
    return {"url": pdf_url, "text": f"DOCUMENT SOURCE: {pdf_url}\n{text}"}