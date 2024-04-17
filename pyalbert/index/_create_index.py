def create_index(index_name, index_type, add_doc=True, recreate=False, storage_dir=None):
    if index_type == "bm25":
        from .elasticsearch import create_bm25_index

        print(f"Creating Elasticsearch index for '{index_name}' ...")
        return create_bm25_index(index_name, add_doc, recreate, storage_dir=storage_dir)
    elif index_type == "e5":
        from .qdrant import create_vector_index

        print(f"Creating Qdrant index for '{index_name}' ...")
        return create_vector_index(index_name, add_doc, recreate, storage_dir=storage_dir)
    else:
        raise NotImplementedError("index type unknown: %s" % index_type)
