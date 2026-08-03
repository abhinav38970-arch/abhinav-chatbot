from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.scraper.year_detector import SchoolYearDetector
from backend.app.retrieval.chunker import smart_chunk_text
from backend.app.database.db import SessionLocal
from backend.app.database.models import Page
from backend.app.database.db import init_db
from backend.app.logs.logger import logger
from datetime import datetime

def run_pipeline():
    # Initialize school year detector
    year_detector = SchoolYearDetector()
    current_year = year_detector.get_current_school_year()
    logger.info(f"📅 Current school year detected: {current_year}")
    
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

            # Step 3: Analyze content for school year relevance
            if content:
                # Extract school year information
                years_found = year_detector.extract_years_from_text(content)
                is_current = year_detector.is_current_school_year_content(content)
                recency_score = year_detector.get_recency_score(content, url)
                
                logger.info(f"🔍 Analyzed {url}: years={years_found}, current={is_current}, score={recency_score:.2f}")

                # Step 4: Apply smart chunking based on content type
                content_type = "html" if p_type == "html" else "text"
                smart_chunks = smart_chunk_text(content, content_type=content_type)
                
                # Step 5: Save each chunk with enhanced metadata
                for chunk_data in smart_chunks:
                    chunk_content = chunk_data["content"]
                    chunk_metadata = chunk_data.get("metadata", {})
                    
                    # Step 5: Save each chunk with enhanced metadata
                    chunk_content = chunk_data["content"]
                    chunk_metadata = chunk_data.get("metadata", {})
                    
                    # Add metadata to content for storage
                    metadata_str = ""
                    if chunk_metadata:
                        metadata_str = f"\n\n---\nMETADATA: {chunk_metadata.get('semantic_role', 'unknown')}"
                        if chunk_metadata.get('content_type') == 'html_table':
                            metadata_str += " | TABLE_DATA"
                    
                    final_content = chunk_content + metadata_str
                    
                    page = Page(
                        url=url, 
                        content=final_content, 
                        type=p_type,
                        school_year=current_year if is_current else (years_found[0] if years_found else None),
                        recency_score=recency_score,
                        is_current_year=1 if is_current else 0,
                        last_updated=datetime.utcnow()
                    )
                    
                    # merge() adds it if new, or updates it if it exists.
                    db.merge(page)
                    # Commit saves the changes to the file.
                    db.commit() 
                    logger.info(f"💾 Saved {p_type} chunk: {url} (recency: {recency_score:.2f}, role: {chunk_metadata.get('semantic_role', 'unknown')})")

    except Exception as e:
        logger.error(f"Pipeline crashed: {e}")
        db.rollback()
    finally:
        # Always close the connection when finished.
        db.close()

if __name__ == "__main__":
    run_pipeline()