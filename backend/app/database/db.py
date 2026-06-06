from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///backend/app/database/school_data.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

from backend.app.database import models  

def init_db():
    """
    Creates database tables if they do not exist.
    Safe to run multiple times.
    """
    Base.metadata.create_all(bind=engine)
