from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .user import User


class StreamBase(BaseModel):
    model_name: str
    # For chat/albert (+RAG) like prompt
    mode: str | None = None  # Possible value should be documented by each model/prompt
    query: str = ""
    limit: int | None = None
    # For instruct/fabrique like prompt.
    user_text: str
    context: str = ""
    institution: str = ""
    links: str = ""
    # Sampling params
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
