from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .stream import Stream
from .user import User


class ChatType(str, Enum):
    qa = "qa"
    meeting = "meeting"


class ChatBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)
    chat_type: ChatType


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    chat_name: str | None

    class Config:
        from_attributes = True


class ChatUpdate(BaseModel):
    chat_name: str | None = None
    chat_type: ChatType | None = None


class ChatArchive(Chat):
    streams: list[Stream] | None = None


class ChatWithRelationships(Chat):
    user: User | None
