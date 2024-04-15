from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app import schemas
from app.db.base_class import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chat_name = Column(Text, nullable=True)
    chat_type = Column(Text)

    user = relationship("User", back_populates="chats")
    user_id = Column(Integer, ForeignKey("users.id"))

    streams = relationship("Stream", back_populates="chat")

    def to_dict(self):
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
        result.streams = [stream.to_dict() for stream in self.streams]

        return result
