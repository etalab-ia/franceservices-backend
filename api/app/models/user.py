from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # is_confirmed:
    #  - None (default) = Account creation neither accepted nor declined
    #  - False = Account creation declined
    #  - True = Account creation accepted
    is_confirmed = Column(Boolean, nullable=True, default=None)

    is_admin = Column(Boolean, default=False)
    # pylint: disable=not-callable
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # pylint: enable=not-callable

    chats = relationship("Chat", back_populates="user")
    streams = relationship("Stream", back_populates="user")
    password_reset_token = relationship("PasswordResetToken", back_populates="user")
