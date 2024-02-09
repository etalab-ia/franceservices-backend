import numpy as np
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoModel, AutoTokenizer

from app.config import DEVICE_MAP, EMBEDDING_MODEL, ENV, WITH_GPU

_model_name_ebd = EMBEDDING_MODEL
tokenizer_ebd = AutoTokenizer.from_pretrained(_model_name_ebd)
model_ebd = AutoModel.from_pretrained(_model_name_ebd, device_map=DEVICE_MAP)

# TODO: The following embedding/encoding function seems to give slighly
#       different results than SentenceTransformer.embed() (probably negligible)
#       AND then batching of sentenceTransformer seems faster and to consume way less memory.
#       See SentenceTransformer code:
#        - https://www.sbert.net/docs/package_reference/SentenceTransformer.html
#        - https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/SentenceTransformer.py


def _average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def _make_embeddings(texts, batch_size=1):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_dict = tokenizer_ebd(
            texts[i : i + batch_size],
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        if WITH_GPU and ENV != "dev":
            batch_dict.to("cuda")

        outputs = model_ebd(**batch_dict)

        vectors = _average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        vectors = F.normalize(vectors, p=2, dim=1)
        if WITH_GPU and ENV != "dev":
            embeddings.append(vectors.detach().cpu().numpy())
        else:
            embeddings.append(vectors.detach().numpy())

    return np.vstack(embeddings)


def make_embeddings(query):
    query = "query: " + query
    return _make_embeddings([query])[0]
