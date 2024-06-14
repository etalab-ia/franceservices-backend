import numpy as np
import torch
import torch.nn.functional as F

# TODO: The following embedding/encoding function seems to give slighly
#       different results than SentenceTransformer.embed() (probably negligible)
#       AND then batching of sentenceTransformer seems faster and to consume way less memory.
#       See SentenceTransformer code:
#        - https://www.sbert.net/docs/package_reference/SentenceTransformer.html
#        - https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/SentenceTransformer.py


def make_embeddings(
    tokenizer: str,
    model: str,
    texts: list[str],
    doc_type: str | None = None,
    batch_size: int = 1,
    gpu: bool = True,
) -> list:
    """
    Make embedding vectors from the given query.

    Args:
        tokenizer (str): tokenizer
        model (str): model
        texts (list): list of query
        doc_type (enum|null): type do document to embed
        batch_size (int): batch size (default: 1)
        gpu (bool): if gpu is available, set True (default: True)

    Returns:
        np.array: array of embedding vectors (row wise)
    """

    def average_pool(
        last_hidden_states: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)

        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    # Using "query" prefix instead of "passage" seems to give more stable results for our case...
    # more information at: https://huggingface.co/intfloat/multilingual-e5-large
    if not doc_type or doc_type == "query":
        texts = ["query: " + query for query in texts]
    elif doc_type == "passage":
        texts = ["passage: " + query for query in texts]
    else:
        raise ValueError("Unknow document type: %s" % doc_type)

    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_dict = tokenizer(
            texts[i : i + batch_size],
            max_length=512,  # 512 is the max length of e5-multilingual-large
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        if gpu:
            batch_dict.to("cuda")

        outputs = model(**batch_dict)
        vectors = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        vectors = F.normalize(vectors, p=2, dim=1)

        if gpu:
            embeddings.append(vectors.detach().cpu().numpy())
        else:
            embeddings.append(vectors.detach().numpy())

    embeddings = np.vstack(embeddings)

    return embeddings
