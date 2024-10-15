from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .api_v1 import ChatCompletionRequest, ChatCompletionResponse


class IndexSource(str, Enum):
    service_public = "service-public"
    travail_emploi = "travail-emploi"

class RagParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Activate the RAG with the given strategy
    strategy: str = Field(
        default="last",
        description="Activate the RAG with the given strategy. Available strategy: last.",
    )

    # The Template (aka mode) to use
    mode: str | None = Field(
        default=None,
        description="A mode is a predefined prompt engineering settings (sampling params, system prompt and user prompt template). They are defined in the huggingface repo of the model, in the pompt_config.yml file.",
    )

    # Number of reference for the RAG
    limit: int | None = Field(
        default=None,
        description="The max number of document to retrieves within the RAG. Use None to let the algorithm decides the best number.",
    )

    # Search engine sources for the RAG
    sources: list[IndexSource] | None = Field(
        default=None, description="Restrict the list of source to search within in RAG mode."
    )

class RagContext(BaseModel):
    strategy: str
    references: list[str]


class RagChatCompletionRequest(ChatCompletionRequest):
    rag: Optional[RagParams] = None

class RagChatCompletionResponse(ChatCompletionResponse):
    # Allow to return sources used with the rag
    rag_context: Optional[list[RagContext]] = None
