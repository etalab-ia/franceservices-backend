from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    is_streaming = Column(Boolean)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_name = Column(Text)
    mode = Column(Text)
    query = Column(Text)
    limit = Column(Integer)
    user_text = Column(Text)
    context = Column(Text)
    institution = Column(Text)
    links = Column(Text)
    temperature = Column(Integer, nullable=False, default=20)
    # pylint: disable=not-callable
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # pylint: enable=not-callable

    user = relationship("User", back_populates="streams")
