import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import ENV, POSTGRES_PASSWORD, ROOT_DIR

if ENV in ("unittest", "dev"):
    # sqlite3:
    DB_URL = "sqlite:///" + os.path.join(ROOT_DIR, "sqlite3.db")
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    # PostgreSQL:
    db_user = "postgres"
    db_pass = os.environ["POSTGRES_PASSWORD"]
    db_host = os.environ.get("POSTGRES_HOST", "localhost")
    db_port = os.environ.get("POSTGRES_PORT", "5432")
    db_name = "postgres"
    DB_URL = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
