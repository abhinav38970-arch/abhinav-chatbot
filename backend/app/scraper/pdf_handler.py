import httpx
import pdfplumber
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
        
        # TASK 2: Use pdfplumber for better text and table extraction
        text_parts = []
        table_parts = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                # Extract regular text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"PAGE {i+1}: {page_text}")
                
                # Extract tables from the page
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:  # Only process non-empty tables
                        # Convert table to markdown format
                        markdown_table = []
                        headers = table[0] if len(table) > 1 else [f"Column {j+1}" for j in range(len(table[0]))]
                        markdown_table.append('| ' + ' | '.join(str(cell) for cell in headers) + ' |')
                        markdown_table.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
                        
                        for row in table[1:] if len(table) > 1 else table:
                            markdown_table.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
                        
                        table_parts.append(f"TABLE {table_idx+1} (Page {i+1}):\n" + '\n'.join(markdown_table))
        
        full_text = '\n\n'.join(text_parts)
        full_tables = '\n\n'.join(table_parts)
        
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None

    # If the PDF was just an image (no selectable text), it will be empty.
    if not full_text.strip() and not full_tables.strip():
        logger.warning("PDF contained no text (might be an image)")
        return None

    # Label the source so the AI knows this is a document.
    content = f"DOCUMENT SOURCE: {pdf_url}\n"
    if full_tables:
        content += "PDF TABLES:\n\n" + full_tables + "\n\n"
    if full_text:
        content += "PDF CONTENT:\n" + full_text
    
    return {"url": pdf_url, "text": content}