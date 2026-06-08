from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base

_DB_PATH = Path(__file__).parent.parent.parent / "ticketing.db"
_engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def create_tables():
    Base.metadata.create_all(bind=_engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
