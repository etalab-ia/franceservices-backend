from app import schemas
from app.db.base_class import Base
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, Table,
                        Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# from app.schemas.other import IndexSource

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

    # one-to-many
    user = relationship("User", back_populates="streams")
    user_id = Column(Integer, ForeignKey("users.id"))

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
