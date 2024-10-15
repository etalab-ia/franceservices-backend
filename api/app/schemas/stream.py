from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .feedback import Feedback
from .search import IndexSource
from .user import User

from pyalbert.config import LLM_TABLE


class StreamBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    model_name: str
    query: str = Field(
        default="",
        description='The user query. It the query exceed a certain size wich depends on the contextual window of the model, the model will return an  HTTPException(413, detail="Prompt too large")',
    )
    mode: str | None = Field(
        default=None,
        description="A mode is a predefined prompt engineering settings (sampling params, system prompt and user prompt template). They are defined in the huggingface repo of the model, in the pompt_config.yml file.",
    )
    limit: int | None = Field(
        default=None,
        description="The max number of document to retrieves within the RAG. Use None to let the algorithm decides the best number.",
    )
    with_history: bool | None = Field(
        default=None, description="Use the conversation history to generate a new response."
    )
    # For instruct/fabrique like prompt.
    context: str = ""
    institution: str = ""
    links: str = ""
    # Sampling params
    temperature: float = Field(0.2, ge=0, le=2)

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

    postprocessing: list[str] | None = Field(
        default=None,
        description="List of postprocessing steps to apply",
    )

    # TODO: add other checks
    # --
    @model_validator(mode="after")
    def validate_model(self):
        # Do not apply this check as it break review of old stream where models
        # are not deployed anymoren, and so missing from the LLM_TABLE
        # if self.model_name not in [m["model"] for m in LLM_TABLE]:
        #     raise ValueError("Unknown model: %s" % self.model_name)

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
    prompt: bytes | None = Field(
        default=None,
        description='Raw prompt formatted, with history, if used. This data is compressed and represented has hex. To decompress use `lz4.frame.decompress(bytes.fromhex(f)).decode("utf-8")`.',
    )
    response: str | None = None
    search_sids: list[str] | None = None
    rag_sources: list[str] | None = Field(
        default=None,
        description="List of chunks used with a rag generation. The list of id can be used to retrieved a chunk on the route /get_chunk/{uid}",
    )
    feedback: Feedback | None = None

    model_config = ConfigDict(from_attributes=True, json_encoders={bytes: lambda bs: bs.hex()})


class StreamWithRelationships(Stream):
    user: User | None
