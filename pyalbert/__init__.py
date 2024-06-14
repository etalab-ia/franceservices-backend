from ._logging import Logging
from .config import LLM_TABLE


def collate_ix_name(name: str, version: str):
    # Forge the collection name alias.
    if version:
        return "-".join([name, version])
    return name


def set_llm_table(llm_table: list[dict]):
    # Used by external script to declare custom LLM_TABLE
    LLM_TABLE.clear()
    LLM_TABLE.extend(llm_table)
