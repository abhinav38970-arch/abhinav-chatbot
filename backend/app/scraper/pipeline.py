from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text

from backend.app.database.db import SessionLocal
from backend.app.database.models import Page

from urllib.parse import urlparse
import os

# folder to temporarily store pdf files
PDF_FOLDER = "backend/app/database/pdfs"


def run_pipeline():
    """
    Runs the full scraping pipeline:
    crawl -> parse -> clean -> pdf extract -> save to database
    """

    print("\nStarting scraping pipeline...\n")

    # create database session
    db = SessionLocal()

    # Step 1: Crawl the site
    urls = crawl()

    print(f"\nTotal URLs discovered: {len(urls)}\n")

    processed_count = 0

    # make sure pdf folder exists
    os.makedirs(PDF_FOLDER, exist_ok=True)

    for url in urls:

        # Step 2: Handle PDFs separately
        if url.lower().endswith(".pdf"):

            pdf_data = extract_pdf_text(url)

            if pdf_data:
                cleaned = clean_text(pdf_data["text"])

                page = Page(
                    url=url,
                    content=cleaned,
                    type="pdf"
                )

                db.merge(page)   # prevents duplicates
                processed_count += 1

            continue

        # Step 3: Parse HTML pages
        page_data = parse_page(url)

        if not page_data:
            continue

        # Step 4: Clean text
        cleaned = clean_text(page_data["text"])

        page = Page(
            url=url,
            content=cleaned,
            type="html"
        )

        db.merge(page)   # prevents duplicates
        processed_count += 1

    # commit all changes
    db.commit()
    db.close()

    print(f"\nPipeline finished. Stored {processed_count} pages.\n")
