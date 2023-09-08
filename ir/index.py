

def create_index(index_type, index_name, add_doc=True):
    if index_type == "bucket":
        from .meilisearch import create_bucket_index
        return create_bucket_index(index_name, add_doc)
    elif index_type == "bm25":
        from .elasticsearch import create_bm25_index
        return create_bm25_index(index_name, add_doc)
    elif index_type == "e5":
        from .qdrant import create_vector_index
        return create_vector_index(index_name, add_doc)
    else:
        raise NotImplementedError




