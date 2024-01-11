from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .user import User

from .stream import Stream


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
    streams: list[Stream]


class ChatWithRelationships(Chat):
    user: Optional["User"]
