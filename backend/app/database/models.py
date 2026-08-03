from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from datetime import datetime
from .db import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String)  # html or pdf
    created_at = Column(DateTime, default=datetime.utcnow)
    # NEW FIELDS FOR RELEVANCE
    school_year = Column(String)  # e.g., "2026-2027"
    recency_score = Column(Float)  # 0-1, where 1 = most current
    is_current_year = Column(Integer)  # 1 = true, 0 = false
    last_updated = Column(DateTime)  # When content was last updated on source
