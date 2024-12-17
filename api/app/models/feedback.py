from enum import Enum
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import schemas
from app.db.base_class import Base


class FeedbackType(str, Enum):
    chat = "chat"
    evaluations = "evaluations"


class FeedbackPositives(str, Enum):
    clair = "clair"
    synthetique = "synthetique"
    complet = "complet"
    sources_fiables = "sources_fiables"


class FeedbackNegatives(str, Enum):
    incorrect = "incorrect"
    incoherent = "incoherent"
    manque_de_sources = "manque_de_sources"


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    type = Column(SQLAlchemyEnum(FeedbackType, name="feedback_type"), nullable=False, default=FeedbackType.chat)
    note = Column(Integer, nullable=True, default=0, comment="Note from 0 to 5")
    positives = Column(JSON, nullable=True, comment="List of positive feedback values")
    negatives = Column(JSON, nullable=True, comment="List of negative feedback values")
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