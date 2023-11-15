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


def make_embeddings():
    import json
    import re
    from time import time

    import numpy as np
    import torch
    import torch.nn.functional as F
    from sentence_transformers import SentenceTransformer
    from torch import Tensor
    from transformers import AutoModel, AutoTokenizer


    def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def embed(tokenizer, model, texts, batch_size=1):  # 4 on colab GPU...
        # Sentence transformers for E5 like model
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_dict = tokenizer(
                texts[i : i + batch_size],
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            if with_gpu:
                batch_dict.to("cuda")

            outputs = model(**batch_dict)

            vectors = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
            vectors = F.normalize(vectors, p=2, dim=1)
            # print(type(vectors)) -> Tensor
            # print(vectors.shape) -> (n_doc X size_embedding)
            if with_gpu:
                embeddings.append(vectors.detach().cpu().numpy())
            else:
                embeddings.append(vectors.detach().numpy())
            # torch.cuda.empty_cache()

        # return torch.cat(embeddings) # burn memory
        return np.vstack(embeddings)

    def embed_(tok, model, texts, batch_size=1):
        # Used with SentenceTransformer
        return model.encode(texts, normalize_embeddings=True, batch_size=32)

    #
    # Parameters
    #

    with_gpu = False
    device_map = None
    if torch.cuda.is_available():
        with_gpu = True
        device_map = "cuda:0"

    model_name = "intfloat/multilingual-e5-large"
    # model_name = "intfloat/multilingual-e5-base"
    # model_name = "intfloat/multilingual-e5-small"

    #
    # Load model
    #

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, device_map=device_map)  # -> SentenceTransformer
    # model = SentenceTransformer(model_name, device="cuda")

    #
    # make EXPERIENCES embeddings
    #

    with open("_data/export-expa-c-riences.json") as f:
        documents = json.load(f)

    def add_space_after_punctuation(text):
        return re.sub(r"([.,;:!?])([^\s\d])", r"\1 \2", text)

    for d in documents:
        descr = d["description"]
        d["description"] = add_space_after_punctuation(descr)

    texts = [x["description"] for x in documents]
    embeddings = embed(tokenizer, model, texts, batch_size=4)
    np.save('_data/embeddings_e5_experiences.npy', embeddings)


    #
    # Make CHUNKS embeddings
    #

    with open("_data/xmlfiles_as_chunks.json") as f:
        documents = json.load(f)

    for doc in documents:
        if "context" in doc:
            doc["context"] = " > ".join(doc["context"])

    texts = [" ".join([x["title"], x["introduction"], x["text"], x.get("context", "")]) for x in documents]
    embeddings = embed(tokenizer, model, texts, batch_size=4)
    np.save('_data/embeddings_e5_chunks.npy', embeddings)

    return
