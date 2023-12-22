from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
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
    user_id: int
    chat_name: str | None

    class Config:
        orm_mode = True


class ChatWithRelationships(Chat):
    user: Optional["User"]
