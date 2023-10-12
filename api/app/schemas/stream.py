from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .user import User


class StreamBase(BaseModel):
    model_name: str
    mode: str = ""  # None instead ?
    user_text: str
    context: str = ""
    institution: str = ""
    links: str = ""
    temperature: int = Field(20, ge=0, le=100)


class StreamCreate(StreamBase):
    pass


class Stream(StreamBase):
    id: int
    is_streaming: bool
    user_id: int

    class Config:
        orm_mode = True


class StreamWithRelationships(Stream):
    user: Optional["User"]
