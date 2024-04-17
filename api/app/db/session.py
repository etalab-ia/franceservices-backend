from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import get_db_url

from pyalbert.config import ENV

db_url: str = get_db_url()

if ENV in ("unittest", "dev"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
