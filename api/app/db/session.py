from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pyalbert.config import ENV, DATABASE_URI

engine = (
    create_engine(DATABASE_URI, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    if ENV == "unittest"
    else create_engine(DATABASE_URI)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
