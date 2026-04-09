from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.database.db import init_db
from backend.app.logs.logger import logger

def run_pipeline():
    init_db()
    logger.info("Starting pipeline")
    db = SessionLocal()

    try:
        urls = crawl()
        for url in urls:
            existing = db.query(Page).filter(Page.url == url).first()
            if existing:
                continue

            content = ""
            p_type = ""

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

            if content:
                # NEW LOGIC: Assign Category Passport
                target_category = "washington_high" if "/washington/" in url.lower() else "district"
                
                page = Page(
                    url=url, 
                    content=content, 
                    type=p_type, 
                    category=target_category # Save the tag
                )
                db.merge(page)
                db.commit() 
                logger.info(f"Saved {p_type} [{target_category}]: {url}")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_pipeline()