from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .protocol import ChatCompletionRequest


class IndexSource(str, Enum):
    service_public = "service-public"
    travail_emploi = "travail-emploi"


class RagChatCompletionRequest(ChatCompletionRequest):
    # Activate the RAG with the given strategy
    rag: str | None = Field(
        default=None,
        description="Activate the RAG with the given strategy. Available strategy: last.",
    )

    # Optionnal mode
    mode: str | None = Field(
        default=None,
        description="A mode is a predefined prompt engineering settings (sampling params, system prompt and user prompt template). They are defined in the huggingface repo of the model, in the pompt_config.yml file.",
    )

    # Optionnal limit
    limit: int | None = Field(
        default=None,
        description="The max number of document to retrieves within the RAG. Use None to let the algorithm decides the best number.",
    )

    # Optionnal RAG sources
    sources: list[IndexSource] | None = Field(
        default=None, description="Restrict the list of source to search within in RAG mode."
    )

    @model_validator(mode="after")
    def check_rag(self):
        if self.rag and self.rag not in ["last"]:
            raise ValueError("Unknown rag strategy: %s" % self.rag)
        elif self.mode and self.mode.startswith("rag") and not self.rag:
            raise ValueError("The rag option must be activated to use this mode.")
        return self
