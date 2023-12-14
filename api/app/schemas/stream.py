from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from .user import User

from .others import IndexSource


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
    limit: int | None = None
    # For instruct/fabrique like prompt.
    user_text: str
    context: str = ""
    institution: str = ""
    links: str = ""
    # Sampling params
    temperature: int = Field(20, ge=0, le=100)

    # Optionnal RAG sources
    sources: list[IndexSource] | None = Field(
        default=None, description="Restrict the list of source to search within in RAG mode."
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

        if not self.sources:
            self.sources = []

        return self


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
