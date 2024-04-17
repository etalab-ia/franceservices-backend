from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import schemas
from app.db.base_class import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    is_good = Column(Boolean, nullable=True)
    message = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    user = relationship("User", back_populates="feedbacks")
    user_id = Column(Integer, ForeignKey("users.id"))

    stream = relationship("Stream", back_populates="feedback")
    stream_id = Column(Integer, ForeignKey("streams.id"))

    def to_dict(self):
        # For serialisation purpose
        # @DEBUG/HELP1: AttributeError: 'str' object has no attribute '_sa_instance_state'

        # This raise an exception due to relationship !
        # result = schemas.Stream.from_orm(self)
        # Relationship are omitted:
        column_names = [column.name for column in self.__table__.columns]
        # Or equivalently
        # column_names = [c.key for c in sqlalchemy.inspect(self).mapper.column_attrs]
        result = schemas.Feedback(**{k: getattr(self, k) for k in column_names})

        return result
