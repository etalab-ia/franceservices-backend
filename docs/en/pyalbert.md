# Pyalbert

PyAlbert is a Python module to facilitate the use of Albert models.
It can be used to:

### Download the RAG data sources
```bash
pyalbert make_chunks --structured
```

### Create the `.json` whitelist file containing phone numbers, email addresses and domain URLs extracted from local and national directories:
```bash
pyalbert create_whitelist
```

### Create document chunks for the RAG
```bash
pyalbert make_chunks --structured
```

### Create indexes in the Elasticsearch database that contains the data sources for the RAG:
```bash
pyalbert index experiences --index-type bm25
pyalbert index sheets      --index-type bm25
pyalbert index chunks      --index-type bm25
```

### Create indexes in the Qdrant database that contains the embedding vectors:
```bash
pyalbert index experiences --index-type e5
pyalbert index chunks      --index-type e5
```

### Run the Albert API locally (dev mode)
```bash
pyalbert serve
```
