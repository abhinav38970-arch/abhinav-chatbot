#!/usr/bin/env python3
"""
Incremental refresh of time-sensitive FUSD content.

Re-crawls ONLY the pages that go stale quickly — news, calendars, events,
bulletins, board agendas — for every school plus district sections.
Pages whose content hasn't changed are left untouched; changed pages get
their chunks replaced so the vector index stays fresh after a rebuild.

Usage:
    python3 refresh.py            # refresh news/calendar/events everywhere
    python3 refresh.py --reindex  # also rebuild the FAISS index afterwards
"""

import sys
import time
from datetime import datetime

from backend.app.scraper.crawler import crawl
from backend.app.scraper.parser import parse_page
from backend.app.scraper.cleaner import clean_text
from backend.app.scraper.pdf_handler import extract_pdf_text
from backend.app.scraper.year_detector import SchoolYearDetector
from backend.app.retrieval.chunker import smart_chunk_text
from backend.app.database.db import SessionLocal, init_db, url_hash, content_hash
from backend.app.database.models import Page, Chunk, CrawlLog
from backend.app.logs.logger import logger

# URL substrings that identify time-sensitive content
FRESH_PATHS = (
    "/news", "/calendar", "/events", "/schedule", "/bulletin",
    "/announcements", "/board", "/agenda",
)

MAX_PER_SCOPE = 150   # safety cap per school for a refresh run


def is_fresh_path(url: str) -> bool:
    return any(marker in url.lower() for marker in FRESH_PATHS)


def build_refresh_entry_points() -> list:
    from backend.app.config import SCHOOL_CONFIG
    eps = []
    slugs = [s["school_id"] for s in SCHOOL_CONFIG.schools] + ["district"]
    for slug in set(slugs):
        base = "https://fremontunified.org" if slug == "district" \
            else f"https://fremontunified.org/{slug}"
        for tail in ("/news", "/schedule-news/news", "/schedule-news/calendar",
                     "/schedule-news/events"):
            eps.append(f"{base}{tail}")
    # District governance updates frequently too
    eps += ["https://fremontunified.org/about/board"]
    return eps


def upsert_page(db, url, school_id, content, p_type, title,
                year_detector, current_year):
    """Insert new page or update in place if content changed."""
    existing = db.query(Page).filter(Page.url == url).first()
    new_hash = content_hash(content)

    if existing and existing.content_hash == new_hash:
        return "unchanged"

    years_found = year_detector.extract_years_from_text(content)
    is_current = year_detector.is_current_school_year_content(content)
    recency_score = year_detector.get_recency_score(content, url)
    smart_chunks = smart_chunk_text(content, content_type="html" if p_type == "html" else "text")

    if existing is None:
        page = Page(
            url=url, url_hash=url_hash(url), school_id=school_id,
            title=title, page_type=p_type, content=content,
            content_hash=new_hash,
            school_year=current_year if is_current else (years_found[0] if years_found else None),
            recency_score=recency_score,
            is_current_year=1 if is_current else 0,
            crawled_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        )
        db.add(page)
        db.flush()
    else:
        page = existing
        page.content = content
        page.content_hash = new_hash
        page.title = title
        page.recency_score = recency_score
        page.is_current_year = 1 if is_current else 0
        page.updated_at = datetime.utcnow()
        db.query(Chunk).filter(Chunk.page_id == page.id).delete()
        db.flush()

    for i, chunk_data in enumerate(smart_chunks):
        meta = chunk_data.get("metadata", {})
        db.add(Chunk(
            page_id=page.id, chunk_index=i, content=chunk_data["content"],
            semantic_role=meta.get("semantic_role", "unknown"),
            content_type=meta.get("content_type", "text"),
            token_count=len(chunk_data["content"]) // 4,
        ))
    return "updated" if existing is not None else "new"


def main():
    reindex = "--reindex" in sys.argv
    init_db()
    year_detector = SchoolYearDetector()
    current_year = year_detector.get_current_school_year()

    stats = {"new": 0, "updated": 0, "unchanged": 0, "errors": 0}
    db = SessionLocal()

    try:
        for result in crawl(max_pages_per_school=MAX_PER_SCOPE,
                            entry_points=build_refresh_entry_points(),
                            path_scope=is_fresh_path):
            url, school_id = result.url, result.school_id or "district"
            try:
                if result.kind == "error":
                    stats["errors"] += 1
                    continue

                if result.kind == "pdf":
                    data = extract_pdf_text(url)
                    title = f"PDF Document - {url.rsplit('/', 1)[-1]}" if data else None
                    content = clean_text(data["text"]) if data else ""
                    p_type = "pdf"
                else:
                    data = parse_page(url, html=result.html)
                    content = clean_text(data["text"]) if data else ""
                    p_type = "html"
                    title = None
                    if data:
                        first = data["text"].split("\n", 1)[0]
                        title = first.replace("TITLE:", "").strip() \
                            if first.startswith("TITLE:") else None

                if not content:
                    stats["errors"] += 1
                    continue

                status = upsert_page(db, url, school_id, content, p_type,
                                     title, year_detector, current_year)
                stats[status] += 1
                db.commit()

            except Exception:
                db.rollback()
                stats["errors"] += 1
                logger.exception(f"Refresh error for {url} - skipping")

        logger.info(f"🔄 Refresh complete: {stats}")

        if reindex:
            from backend.app.retrieval.indexer import build_index
            build_index()
    finally:
        db.close()


if __name__ == "__main__":
    main()
