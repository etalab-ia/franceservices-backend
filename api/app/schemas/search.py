from enum import Enum

from pydantic import BaseModel, Field

# **************
# * Embeddings *
# **************


class Embedding(BaseModel):
    text: str


# ***********
# * Indexes *
# ***********


class IndexName(str, Enum):
    experiences = "experiences"
    sheets = "sheets"
    chunks = "chunks"


class IndexSimilarity(str, Enum):
    bm25 = "bm25"
    e5 = "e5"


class IndexSource(str, Enum):
    service_public = "service-public"
    travail_emploi = "travail-emploi"


class Index(BaseModel):
    name: IndexName = Field(description="The name of the index or collection to search within.")
    query: str = Field(description="The text search query.")
    limit: int = Field(default=3, description="The maximum number of documents to return.")
    similarity: IndexSimilarity = Field(
        default=IndexSimilarity.bm25, description="The similarity algorithm to use for the search."
    )
    institution: str | None = None
    sources: list[IndexSource] | None = Field(
        default=None, description="Restrict the list of source to search within."
    )
    should_sids: list[str] | None = Field(
        default=None, description="Add document that should match."
    )
    must_not_sids: list[str] | None = Field(
        default=None, description="Filter out documents that must not match."
    )
