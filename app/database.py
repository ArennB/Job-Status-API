from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from .config import get_database_url

Base = declarative_base()

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """Give each request its own session, including cleanup on errors."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
