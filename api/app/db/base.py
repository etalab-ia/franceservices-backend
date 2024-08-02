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

from pyalbert.config import DATABASE_URI

def create_database_if_not_exists(database_url: str = DATABASE_URI):
    """Create empty database if it does not exist yet."""
    engine = create_engine(database_url)
    if not database_exists(engine.url):
        create_database(engine.url)
    # Does not work :(
    # conn = engine.connect()
    # conn.execute("commit")
    # conn.execute("CREATE DATABASE IF NOT EXISTS mydatabase")
    # conn.close()
