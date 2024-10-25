from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    user_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

