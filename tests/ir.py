#!/bin/python

import json
import os
from time import time

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

# Do not print up warnings on a CPU machine only
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Utils
# --

# Load stop words
stopwords = []
with open("_data/stopwords/fr.txt", "r") as file:
    for line in file:
        stopwords.append(line.strip())


#
# Testing tfidf similarity approached
# for document search.
#

score = "e5"
n_best = 3
question = "qu'est ce que le JOAFE ?"

# Tfidf feature extractions
# --
# Get documents from chunks
with open("_data/xmlfiles_as_chunks.json") as f:
    documents = [x["text"] for x in json.load(f)]

now = time()

if score == "bm25":
    # Initialize the TF-IDF vectorizer (do not match number)
    # vectorizer = TfidfVectorizer(norm=None, smooth_idf=False, stop_words=stopwords, min_df=0.05, max_df=0.9, token_pattern=r"\b[A-Za-z_][A-Za-z_]+\b")
    vectorizer = TfidfVectorizer(norm=None, smooth_idf=False, stop_words=stopwords, token_pattern=r"\b[A-Za-z_][A-Za-z_]+\b")

    # Compute the TF-IDF matrix
    X = vectorizer.fit_transform(documents)
    print("Num doc x Size voc: ", X.shape)
    loading_time = time() - now
    print("Loading time: %.3f" % loading_time)

    # INFERENCE
    # convert to csc for better column slicing
    b = 0.75
    k1 = 1.6
    len_X = X.sum(1).A1
    avdl = X.sum(1).mean()

    (q,) = vectorizer.transform([question])
    assert sparse.isspmatrix_csr(q)

    X = X.tocsc()[:, q.indices]
    denom = X + (k1 * (1 - b + b * len_X / avdl))[:, None]
    # idf(t) = log [ n / df(t) ] + 1 in sklearn, so it need to be coneverted
    # to idf(t) = log [ n / df(t) ] with minus 1
    idf = vectorizer._tfidf.idf_[None, q.indices] - 1.0
    numer = X.multiply(np.broadcast_to(idf, X.shape)) * (k1 + 1)
    scores = (numer / denom).sum(1).A1
elif score == "cosine":
    # Initialize the TF-IDF vectorizer (do not match number)
    # vectorizer = TfidfVectorizer(norm=None, smooth_idf=False, stop_words=stopwords, min_df=0.05, max_df=0.9, token_pattern=r"\b[A-Za-z_][A-Za-z_]+\b")
    vectorizer = TfidfVectorizer(norm=None, smooth_idf=False, stop_words=stopwords, token_pattern=r"\b[A-Za-z_][A-Za-z_]+\b")

    # Compute the TF-IDF matrix
    X = vectorizer.fit_transform(documents)
    print("Num doc x Size voc: ", X.shape)
    loading_time = time() - now
    print("Loading time: %.3f" % loading_time)

    # INFERENCE
    # tfidf similarity
    # faster thant cosine_similarity
    (scores,) = linear_kernel(q, X)
elif score == "e5":
    import torch.nn.functional as F
    from sentence_transformers import SentenceTransformer
    from torch import Tensor
    from transformers import AutoModel, AutoTokenizer

    def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def embed(tokenizer, model, texts, batch_size=10):
        # Sentence transformers for E5
        batch_dict = tokenizer(
            texts,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        outputs = model(**batch_dict)

        embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        # print(type(embeddings)) -> Tensor
        # print(embeddings.shape) -> (n_doc X size_embedding)
        return embeddings

    # sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="e5-multilingual", device = "cuda")
    # model_name = "intfloat/multilingual-e5-large"
    model_name = "intfloat/multilingual-e5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)  # -> SentenceTransformer

    loading_time = time() - now
    print("Loading time: %.3f" % loading_time)

    q_embed = embed(tokenizer, model, [question])
    docs_embed = embed(tokenizer, model, documents)

    scores = q_embed @ docs_embed.T
    print(scores.shape)

else:
    raise NotImplementedError("similarity unknown")


print(f"Inference time: {time() - loading_time :.5f}")

for i in np.argsort(scores)[-n_best:][::-1]:
    print(f"doc {i}\n---")
