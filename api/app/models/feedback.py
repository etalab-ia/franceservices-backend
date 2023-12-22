from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    # pylint: disable=not-callable
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    # pylint: enable=not-callable

    is_good = Column(Boolean, nullable=True)
    message = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    user = relationship("User", back_populates="feedbacks")
    user_id = Column(Integer, ForeignKey("users.id"))

    stream = relationship("Stream", back_populates="feedback")
    stream_id = Column(Integer, ForeignKey("streams.id"))
