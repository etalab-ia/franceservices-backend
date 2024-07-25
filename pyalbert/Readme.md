#!/bin/bash

#|##################################################
#|Setup Albert from scratch
#|##################################################

### Download the digested data source to build chunks

1. `pyalbert download_rag_sources --storage-dir _data` : This command will download the data in given repository
2. `pyalbert make_chunks --structured`: This command will parse the data sources to build chunks. The --structured option will use a chunking strategy that parse the service-public sheets (most important source of information for the rag to date) by respecting the semantic of the SP xml and by building **chunk context** (title/sub-title (i.e breadcrumb) to the chunk).

### Feed the search engines

3. `pyalbert index chunks --index-type bm25`: build in bm25 index in Elasticssearch.
4. `pyalbert index chunks --index-type e5`: build the embedding collection in Qdrant.

ps: install pyalbert to lastest version `pip install pyalbert -U`
pps: les commande ne peuvent fonctionner en local que si les service qdrant et elasctisearch sont correctement configuré, et que la machine à acces au endpoint embedding (voir config)


full example:

```
# Fetch and parse corpuses
pyalbert create_whitelist
pyalbert download_rag_sources
pyalbert make_chunks --structured
# Feed the search engines
pyalbert index experiences --index-type bm25
pyalbert index sheets      --index-type bm25
pyalbert index chunks      --index-type bm25
pyalbert index experiences --index-type e5
pyalbert index chunks      --index-type e5
```
