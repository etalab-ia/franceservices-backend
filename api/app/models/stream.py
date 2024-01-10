import json

from app import schemas
from app.db.base_class import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

# from app.schemas.search import IndexSource


# @obsolete ewith JSON type
class JsonEncoder(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


stream_source_association = Table(
    "stream_source",
    Base.metadata,
    Column("stream_id", Integer, ForeignKey("streams.id")),
    Column("source_id", Integer, ForeignKey("sources.id")),
)


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    is_streaming = Column(Boolean)
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

    response = Column(Text, nullable=True)
    rag_sources = Column(JSON, nullable=True)
    should_sids = Column(JSON, nullable=True)
    must_not_sids = Column(JSON, nullable=True)
    search_sids = Column(JSON, nullable=True)

    # one-to-one / use use_list=False ?
    feedback = relationship("Feedback", back_populates="stream")

    # one-to-many
    user = relationship("User", back_populates="streams")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    chat = relationship("Chat", back_populates="streams")
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NULL OR chat_id IS NULL) AND (user_id IS NOT NULL OR chat_id IS NOT NULL)",  # pylint: disable=line-too-long
            name="_streams_user_id_chat_id_cc",
        ),
    )

    # many-to-many
    sources = relationship(
        "SourceEnum", secondary=stream_source_association, back_populates="streams"
    )

    def to_dict(self):
        # For serialisation purpose

        # This raise an exception due to relationship !
        # result = schemas.Stream.from_orm(self)
        # Relationship are omitted:
        column_names = [column.name for column in self.__table__.columns]
        # Or equivalently
        # column_names = [c.key for c in sqlalchemy.inspect(self).mapper.column_attrs]

        result = schemas.Stream(**{k: getattr(self, k) for k in column_names})
        result.sources = [source.source_name for source in self.sources]
        return result


class SourceEnum(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    # How to manage safely Enum values that would be updated, or deleted in the future ?
    # source_name = Column(Enum(IndexSource), unique=True)
    source_name = Column(Text)
    streams = relationship("Stream", secondary=stream_source_association, back_populates="sources")

