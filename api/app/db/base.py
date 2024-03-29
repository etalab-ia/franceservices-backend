import os
import tempfile

# Import all the models, so that Base has them before being imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.chat import Chat  # noqa
from app.models.login import BlacklistToken, PasswordResetToken  # noqa
from app.models.stream import Stream  # noqa
from app.models.user import User  # noqa

from pyalbert.config import ENV


def get_db_url() -> str:
    if ENV in ("unittest", "dev"):
        db_uri = "sqlite:///" + os.path.join(tempfile.gettempdir(), f"albert-{ENV}-sqlite3.db")
    else:
        db_user = "postgres"
        db_pass = os.environ["POSTGRES_PASSWORD"]
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = "postgres"
        db_uri = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return db_uri
