"""
FUSD scraping pipeline.

Flow: crawl (single fetch) -> parse -> clean -> year analysis -> smart chunk -> store.

- One row per page in `pages`, one row per chunk in `chunks` (RAG retrieval unit)
- Every page is attributed to a school_id / 'district' via the crawler
- Resume-safe: URLs already in the DB are skipped, commits happen per page
- Error-isolated: any failure on one URL is logged with a traceback and skipped
"""

import time
from datetime import datetime

from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.scraper.year_detector import SchoolYearDetector
from backend.app.scraper.domain_validator import DomainValidator
from backend.app.retrieval.chunker import smart_chunk_text
from backend.app.database.db import SessionLocal, init_db, url_hash, content_hash
from backend.app.database.models import Page, Chunk, CrawlLog, get_or_create_school
from backend.app.config import SCHOOL_CONFIG
from backend.app.logs.logger import logger

PROGRESS_LOG_EVERY = 25


def run_pipeline(max_pages_per_school=None):
    year_detector = SchoolYearDetector()
    current_year = year_detector.get_current_school_year()
    validator = DomainValidator()

    logger.info(f"📅 Current school year detected: {current_year}")
    init_db()

    db = SessionLocal()
    try:
        # Seed schools table from config (idempotent)
        for school in SCHOOL_CONFIG.schools:
            get_or_create_school(
                db,
                school["school_id"],
                school["school_name"],
                school["school_level"],
                base_url=school["base_urls"][0] if school["base_urls"] else None,
                metadata=school.get("metadata", {}),
            )
        district_cfg = getattr(SCHOOL_CONFIG, "district", {})
        get_or_create_school(
            db, "district",
            district_cfg.get("name", "Fremont Unified School District"),
            "district",
            base_url="https://fremontunified.org/",
            metadata=district_cfg.get("contact", {}),
        )
        db.commit()
        logger.info("🏫 Schools table seeded from configuration")

        stats = {"stored": 0, "skipped_existing": 0, "errors": 0, "chunks": 0}

        for result in crawl(max_pages_per_school=max_pages_per_school):
            url = result.url
            school_id = result.school_id or "district"

            try:
                existing = db.query(Page.id).filter(Page.url == url).first()
                if existing:
                    stats["skipped_existing"] += 1
                    db.add(CrawlLog(url=url, school_id=school_id, status="skipped_existing"))
                    db.commit()
                    continue

                valid, details = validator.validate_url(url)
                if not valid:
                    logger.warning(f"🚫 Domain validation failed, skipping: {url} ({details['reason']})")
                    db.add(CrawlLog(url=url, school_id=school_id, status="blocked_path",
                                    detail=details["reason"]))
                    db.commit()
                    continue

                if result.kind == "error":
                    stats["errors"] += 1
                    db.add(CrawlLog(url=url, school_id=school_id, status="failed_fetch",
                                    detail=result.error))
                    db.commit()
                    continue

                content = ""
                p_type = ""
                title = None

                if result.kind == "pdf":
                    data = extract_pdf_text(url)
                    if data:
                        title = f"PDF Document - {url.rsplit('/', 1)[-1]}"
                        content = clean_text(data["text"])
                        p_type = "pdf"
                elif result.kind == "html":
                    data = parse_page(url, html=result.html)
                    if data:
                        content = clean_text(data["text"])
                        p_type = "html"
                        raw = data["text"]
                        first_line = raw.split("\n", 1)[0]
                        if first_line.startswith("TITLE:"):
                            title = first_line.replace("TITLE:", "").strip()

                if not content:
                    stats["errors"] += 1
                    db.add(CrawlLog(url=url, school_id=school_id, status="parse_error",
                                    detail="no extractable content"))
                    db.commit()
                    continue

                years_found = year_detector.extract_years_from_text(content)
                is_current = year_detector.is_current_school_year_content(content)
                recency_score = year_detector.get_recency_score(content, url)

                content_type = "html" if p_type == "html" else "text"
                smart_chunks = smart_chunk_text(content, content_type=content_type)

                page = Page(
                    url=url,
                    url_hash=url_hash(url),
                    school_id=school_id,
                    title=title,
                    page_type=p_type,
                    content=content,
                    content_hash=content_hash(content),
                    school_year=current_year if is_current else (years_found[0] if years_found else None),
                    recency_score=recency_score,
                    is_current_year=1 if is_current else 0,
                    domain_validated=1 if valid else 0,
                    crawl_status="ok",
                    crawled_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Merge handles the rare race where an identical-content page exists
                try:
                    db.add(page)
                    db.flush()  # assigns page.id without committing
                except Exception as e:
                    db.rollback()
                    stats["errors"] += 1
                    logger.warning(f"DB insert issue for {url}: {type(e).__name__}: {e}")
                    db.add(CrawlLog(url=url, school_id=school_id, status="db_error",
                                    detail=str(e)[:500]))
                    db.commit()
                    continue

                for i, chunk_data in enumerate(smart_chunks):
                    chunk_meta = chunk_data.get("metadata", {})
                    db.add(Chunk(
                        page_id=page.id,
                        chunk_index=i,
                        content=chunk_data["content"],
                        semantic_role=chunk_meta.get("semantic_role", "unknown"),
                        content_type=chunk_meta.get("content_type", content_type),
                        token_count=len(chunk_data["content"]) // 4,
                    ))
                stats["chunks"] += len(smart_chunks)

                db.add(CrawlLog(url=url, school_id=school_id, status="stored",
                                detail=f"{len(smart_chunks)} chunks, type={p_type}, "
                                       f"recency={recency_score:.2f}"))
                db.commit()

                stats["stored"] += 1
                if stats["stored"] % PROGRESS_LOG_EVERY == 0:
                    total_pages = db.query(Page.id).count()
                    logger.info(
                        f"💾 Progress: {stats['stored']} stored this run | "
                        f"{stats['skipped_existing']} skipped | {stats['errors']} errors | "
                        f"{total_pages} total pages in DB"
                    )

            except Exception:
                db.rollback()
                stats["errors"] += 1
                logger.exception(f"Unhandled pipeline error for {url} — skipping and continuing")
                try:
                    db.add(CrawlLog(url=url, school_id=school_id, status="error",
                                    detail="unhandled exception (see traceback log)"))
                    db.commit()
                except Exception:
                    db.rollback()

        total_pages = db.query(Page.id).count()
        total_chunks = db.query(Chunk.id).count()
        logger.info(
            f"✅ Pipeline complete. Run stats: {stats} | "
            f"Database totals: {total_pages} pages, {total_chunks} chunks"
        )

    except Exception:
        db.rollback()
        logger.exception("Pipeline crashed at top level")
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
