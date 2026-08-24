from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, JSON,
    Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from .db import Base


class School(Base):
    """One row per school/site in the district. Populated from schools.json."""
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True)
    school_id = Column(String, unique=True, nullable=False, index=True)   # e.g. "washington"
    school_name = Column(String, nullable=False)                          # e.g. "Washington High School"
    school_level = Column(String, nullable=False, index=True)             # elementary/middle/high/preschool/adult/alternative/district
    base_url = Column(String)
    principal = Column(String)
    phone = Column(String)
    address = Column(String)
    extra_metadata = Column(JSON)                                         # grades, query patterns, hints
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship("Page", back_populates="school", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<School {self.school_id}>"


class Page(Base):
    """
    One row per crawled URL. Holds the full cleaned document text so we can
    re-chunk later without re-crawling. Retrieval itself works on Chunk rows.
    """
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    url_hash = Column(String(64), unique=True, nullable=False, index=True)  # fast dedupe lookup

    # School attribution (which site this page belongs to)
    school_id = Column(String, ForeignKey("schools.school_id"), nullable=False, index=True)

    title = Column(String)
    page_type = Column(String, nullable=False)          # "html" or "pdf"
    content = Column(Text, nullable=False)              # full cleaned text of the page
    content_hash = Column(String(64), unique=True, nullable=False)  # dedupes identical pages across sites

    # Temporal metadata for recency-aware retrieval
    school_year = Column(String)                        # e.g. "2026-2027"
    recency_score = Column(Float)                       # 0-1
    is_current_year = Column(Integer, default=0, index=True)

    # Provenance / quality
    domain_validated = Column(Integer, default=1)
    crawl_status = Column(String, default="ok")         # ok / partial / error
    page_metadata = Column(JSON)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School", back_populates="pages")
    chunks = relationship("Chunk", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pages_school_recency", "school_id", "recency_score"),
        Index("idx_pages_school_year", "school_id", "is_current_year"),
    )

    def __repr__(self):
        return f"<Page {self.url}>"


class Chunk(Base):
    """
    One row per retrievable chunk. This is the unit the vector index maps to,
    so every chunk carries enough context for the LLM to never be confused:
    school name/id + page title + section role are embedded alongside content.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)
    semantic_role = Column(String)                      # schedule_info / policy_info / contact_info / ...
    content_type = Column(String)                       # text / html_table / pdf
    token_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    page = relationship("Page", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("page_id", "chunk_index", name="uq_chunk_page_index"),
        Index("idx_chunks_role", "semantic_role"),
    )


class CrawlLog(Base):
    """Per-URL observability so you can audit exactly what was crawled/blocked and why."""
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, index=True)
    school_id = Column(String, index=True)
    status = Column(String, nullable=False)             # fetched / stored / skipped_existing / blocked_path / failed_fetch / parse_error / db_error
    detail = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


def get_or_create_school(db_session, school_id: str, school_name: str, school_level: str,
                         base_url: str = None, metadata: dict = None) -> School:
    existing = db_session.query(School).filter(School.school_id == school_id).first()
    if existing:
        return existing
    meta = metadata or {}
    school = School(
        school_id=school_id,
        school_name=school_name,
        school_level=school_level,
        base_url=base_url,
        principal=meta.get("principal"),
        phone=meta.get("phone"),
        address=meta.get("address"),
        extra_metadata=meta,
    )
    db_session.add(school)
    return school
