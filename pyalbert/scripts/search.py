#!/usr/bin/env python
import sys

sys.path.append(".")

from pprint import pprint

from pyalbert.clients import SearchEngineClient

client = SearchEngineClient()
hits = client.search("chunks", "carte d'indentité", limit=5)
pprint(hits)

