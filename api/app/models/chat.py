from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # pylint: disable=not-callable
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # pylint: enable=not-callable

    chat_name = Column(Text, nullable=True)
    chat_type = Column(Text)

    user = relationship("User", back_populates="chats")
    streams = relationship("Stream", back_populates="chat")
