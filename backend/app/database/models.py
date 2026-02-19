from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .db import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String)  # html or pdf
    created_at = Column(DateTime, default=datetime.utcnow)
