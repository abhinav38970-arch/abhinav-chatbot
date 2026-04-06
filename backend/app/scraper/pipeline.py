from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.database.db import init_db
from backend.app.logs.logger import logger

def run_pipeline():
    # Make sure the SQLite tables are created before we start.
    init_db()
    logger.info("Starting pipeline")
    # Connect to the database.
    db = SessionLocal()

    try:
        # Step 1: Get the list of all URLs from the crawler scout.
        urls = crawl()
        
        for url in urls:
            # Check if we already have this URL in our database.
            existing = db.query(Page).filter(Page.url == url).first()
            if existing:
                logger.info("Skipping already stored page")
                continue

            content = ""
            p_type = ""

            # Step 2: Decide if we need the PDF handler or the HTML parser.
            if url.lower().endswith(".pdf"):
                data = extract_pdf_text(url)
                if data:
                    content = clean_text(data["text"])
                    p_type = "pdf"
            else:
                data = parse_page(url)
                if data:
                    content = clean_text(data["text"])
                    p_type = "html"

            # Step 3: If we found content, save it to the database.
            if content:
                page = Page(url=url, content=content, type=p_type)
                # merge() adds it if new, or updates it if it exists.
                db.merge(page)
                # Commit saves the changes to the file.
                db.commit() 
                logger.info(f"Saved {p_type}: {url}")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}")
        db.rollback()
    finally:
        # Always close the connection when finished.
        db.close()

if __name__ == "__main__":
    run_pipeline()