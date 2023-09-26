from typing import Optional

from pydantic import BaseSettings, PostgresDsn

from app.config import SECRET_KEY


class Settings(BaseSettings):
    SECRET_KEY: str = SECRET_KEY
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    class Config:
        case_sensitive = True


settings = Settings()
