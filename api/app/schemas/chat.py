from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .stream import Stream
from .user import User


class ChatType(str, Enum):
    evaluations = "evaluations"
    meeting = "meeting"


class ChatBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)
    chat_type: ChatType
    operators: list[str] | None = None
    themes: list[str] | None = None


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    chat_name: str | None
    stream_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatUpdate(BaseModel):
    chat_name: str | None = None
    chat_type: ChatType | None = None


class ChatArchive(Chat):
    streams: list[Stream] | None = None


class ChatWithRelationships(Chat):
    user: User | None
