from enum import Enum

from pydantic import BaseModel, Field

# **************
# * Embeddings *
# **************


class Embedding(BaseModel):
    input: str | list[str]
    # ignored for now, but keep it for openai-api compatibility
    model: str | None = None
    # Certain embedding model support asymetric queries.
    doc_type: str | None = None
    # ignored for now, but keep it for openai-api compatibility
    encoding_format: str = "float"  # only float is supported.


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
    expand_acronyms: bool = Field(
        default=True,
        description="If true, an acronym detection algorithm will try to detect and expand implicit acronyms used by the French services in the query.",
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
    stream_id: str | None = Field(
        default=None,
        description="A related stream_id use to search results information that can be used get stream/chat archive.",
    )


class QueryDocs(BaseModel):
    uids: list[str] = Field(
        description="List of documents ids. When searching in `sheets`, the uid are called sid. For `chunks` uid are called hash."
    )
