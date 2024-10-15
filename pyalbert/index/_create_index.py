from pyalbert.config import ELASTICSEARCH_IX_VER, QDRANT_IX_VER


def create_index(
    index_name, index_type, add_doc=True, recreate=False, storage_dir=None, batch_size=None
):
    if index_type == "elasticsearch":
        from .elasticsearch import create_elasticsearch_index

        print(f"Creating Elasticsearch index for '{index_name}-{ELASTICSEARCH_IX_VER}' ...")
        return create_elasticsearch_index(
            index_name, add_doc, recreate, storage_dir=storage_dir, batch_size=batch_size
        )

    elif index_type == "qdrant":
        from .qdrant import create_qdrant_index

        print(f"Creating Qdrant index for '{index_name}-{QDRANT_IX_VER}' ...")
        return create_qdrant_index(
            index_name, add_doc, recreate, storage_dir=storage_dir, batch_size=batch_size
        )

    else:
        raise NotImplementedError("index type unknown: %s" % index_type)


def list_indexes():
    from .elasticsearch import list_elasticsearch_indexes
    from .qdrant import list_qdrant_collections

    list_elasticsearch_indexes()

    list_qdrant_collections()
