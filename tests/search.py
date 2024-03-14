#!/bin/python
import sys
from pprint import pprint

sys.path.append(".")

from commons import get_albert_client


client = get_albert_client()
hits = client.search("chunks", "carte d'indentité", limit=3, similarity="bm25")
pprint(hits)
