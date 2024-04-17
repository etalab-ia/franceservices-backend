import os
import sys

from ._logging import Logging


def collate_ix_name(name: str, version: str):
    # Forge the collection name alias.
    if version:
        return "-".join([name, version])
    return name
