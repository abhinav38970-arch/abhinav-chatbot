from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.logs.logger import logger
from backend.app.database.db import init_db

import os
import time
import random

PDF_FOLDER = "backend/app/database/pdfs"

def pause():
    delay = random.uniform(0.8, 2.2)
    time.sleep(delay)

def run_pipeline():
    """crawl → parse → clean → pdf → store"""
    init_db()  # ✅ ensures tables exist before scraping starts

    logger.info("Starting scraping pipeline")

    db = SessionLocal()

    urls = crawl()

    logger.info(f"Total URLs discovered: {len(urls)}")
    logger.info("Beginning processing loop")

    processed_count = 0
    os.makedirs(PDF_FOLDER, exist_ok=True)

    for url in urls:

        logger.info(f"Processing URL: {url}")

        # ✅ SKIP if already stored (prevents reprocessing)
        existing = db.query(Page).filter(Page.url == url).first()
        if existing:
            logger.info("Skipping already stored page")
            continue

        # ---------- PDF HANDLING ----------
        if url.lower().endswith(".pdf"):
            logger.info("PDF detected")

            pdf_data = extract_pdf_text(url)

            if pdf_data:
                cleaned = clean_text(pdf_data["text"])

                page = Page(url=url, content=cleaned, type="pdf")
                db.merge(page)

                processed_count += 1
                logger.info(f"Saved PDF: {url}")

            pause()
            continue

        # ---------- HTML HANDLING ----------
        page_data = parse_page(url)

        if not page_data:
            logger.warning(f"Skipping page due to parse failure: {url}")
            pause()
            continue

        cleaned = clean_text(page_data["text"])

        page = Page(url=url, content=cleaned, type="html")
        db.merge(page)

        processed_count += 1
        logger.info(f"Saved HTML: {url}")

        pause()

    logger.info("Committing database changes")
    db.commit()
    db.close()

    logger.info(f"Pipeline finished. Stored {processed_count} pages.")