import httpx
from pdfminer.high_level import extract_text
from io import BytesIO


def extract_pdf_text(pdf_url):
    """
    Downloads a PDF and extracts its text.
    """

    print(f"Downloading PDF: {pdf_url}")

    try:
        response = httpx.get(pdf_url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    try:
        pdf_file = BytesIO(response.content)
        text = extract_text(pdf_file)
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        return None

    if not text.strip():
        return None

    return {
        "url": pdf_url,
        "text": text
    }
