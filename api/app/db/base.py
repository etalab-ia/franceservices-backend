import os
import tempfile

from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists

# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.chat import Chat  # noqa
from app.models.login import BlacklistToken, PasswordResetToken  # noqa
from app.models.stream import Stream  # noqa
from app.models.user import User  # noqa

from pyalbert.config import (
    ENV,
    FIRST_ADMIN_USERNAME,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
)


def get_db_url() -> str:
    if ENV == "unittest":
        return "sqlite:///" + os.path.join(tempfile.gettempdir(), f"albert-{ENV}-sqlite3.db")
    else:
        if ENV == "dev":
            db_name = "postgres_dev"
        else:
            db_name = "postgres"
        db_user = "postgres"
        db_host = POSTGRES_HOST
        db_port = POSTGRES_PORT
        db_pass = POSTGRES_PASSWORD
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


def create_database_if_not_exists(database_url):
    """Create empty database if it does not exist yet."""
    engine = create_engine(database_url)
    if not database_exists(engine.url):
        create_database(engine.url)
    # Does not work :(
    # conn = engine.connect()
    # conn.execute("commit")
    # conn.execute("CREATE DATABASE IF NOT EXISTS mydatabase")
    # conn.close()
