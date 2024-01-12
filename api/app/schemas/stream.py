from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from .user import User

from .search import IndexSource
from .feedback import Feedback


class ModelName(str, Enum):
    fabrique_miaou = "fabrique-miaou"
    fabrique_reference = "fabrique-reference"
    albert_light = "albert-light"


class StreamBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    model_name: ModelName = ModelName.fabrique_reference.value
    # For chat/albert (+RAG) like prompt
    mode: str | None = None  # Possible value should be documented by each model/prompt
    query: str = Field(
        default="",
        description='The user query. It the query exceed a certain size wich depends on the contextual window of the model, the model will return an  HTTPException(413, detail="Prompt too large")',
    )
    # @obselete: replace user_text (use by fabrique model) by query and remove this entry (db copy user_text->query)
    user_text: str = Field(
        default="",
        description='The user query. It the query exceed a certain size wich depends on the contextual window of the model, the model will return an  HTTPException(413, detail="Prompt too large")',
    )
    limit: int | None = None
    # For instruct/fabrique like prompt.
    context: str = ""
    institution: str = ""
    links: str = ""
    # Sampling params
    temperature: int = Field(20, ge=0, le=100)

    # Optionnal RAG sources
    sources: list[IndexSource] | None = Field(
        default=None, description="Restrict the list of source to search within in RAG mode."
    )
    should_sids: list[str] | None = Field(
        default=None, description="Add document that should match, in RAG mode."
    )
    must_not_sids: list[str] | None = Field(
        default=None, description="Filter out documents that must not match, in RAG mode."
    )

    # For archive reading / reload
    response: str | None = None
    rag_sources: list[str] | None = Field(
        default=None,
        description="List of chunks used with a rag generation. The list of id can be used to retrieved a chunk on the route /get_chunk/{uid}",
    )

    # TODO: add other checks
    # --
    @model_validator(mode="after")
    def validate_model(self):
        if self.model_name == ModelName.fabrique_miaou:
            if self.mode is not None:
                raise ValueError("Incompatible mode")

        elif self.model_name == ModelName.fabrique_reference:
            if self.mode not in (None, "simple", "experience", "expert"):
                raise ValueError("Incompatible mode")
            if self.mode is None:
                self.mode = "simple"  # default

        elif self.model_name == ModelName.albert_light:
            if self.mode not in (None, "simple", "rag"):
                raise ValueError("Incompatible mode")
            if self.mode is None:
                self.mode = "rag"  # default

        # For SQLAlchemy relationship compatibility
        if not self.sources:
            self.sources = []

        return self


class StreamCreate(StreamBase):
    pass


class Stream(StreamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_streaming: bool
    user_id: int | None
    chat_id: int | None
    search_sids: list[str] | None
    feedback: Feedback | None

    class Config:
        from_attributes = True


class StreamWithRelationships(Stream):
    user: Optional["User"]
