from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, select

from .stream import Stream

from app import schemas
from app.db.base_class import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chat_name = Column(Text, nullable=True)
    chat_type = Column(Text)
    operator = Column(Text, nullable=True)
    themes = Column(JSON, nullable=True)

    user_id = Column(String)

    streams = relationship("Stream", back_populates="chat")

    @hybrid_property
    def stream_count(self):
        return len(self.streams)

    @stream_count.expression
    def stream_count(cls):
        return (
            select([func.count(Stream.id)])
            .where(Stream.chat_id == cls.id)
            .correlate(cls)
            .label("stream_count")
        )

    def to_dict(self, with_streams=True):
        # For serialisation purpose
        # @DEBUG/HELP1: AttributeError: 'str' object has no attribute '_sa_instance_state'

        # This raise an exception due to relationship !
        # result = schemas.Stream.from_orm(self)
        # Relationship are omitted:
        column_names = [column.name for column in self.__table__.columns]
        # Or equivalently
        # column_names = [c.key for c in sqlalchemy.inspect(self).mapper.column_attrs]
        result = schemas.ChatArchive(**{k: getattr(self, k) for k in column_names})

        # Relations
        streams = [stream.to_dict() for stream in self.streams]
        result.stream_count = len(streams)
        if with_streams:
            result.streams = sorted(streams, key=lambda x: x.id)

        return result
