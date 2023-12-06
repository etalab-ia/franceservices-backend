from enum import Enum

from pydantic import BaseModel

# ********
# * Misc *
# ********


class ContactForm(BaseModel):
    subject: str
    text: str
    institution: str | None = None


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


class Index(BaseModel):
    name: IndexName
    query: str
    limit: int = 3
    similarity: IndexSimilarity = IndexSimilarity.bm25
    institution: str | None = None
