from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from .user import User


class ChatBase(BaseModel):
    pass


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class ChatWithRelationships(Chat):
    user: Optional["User"]
