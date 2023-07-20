from abc import ABC, abstractmethod
from weaviate import Client  # type: ignore

from sentence_transformers import SentenceTransformer  # type: ignore
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
from torch import Tensor


class VectorEmbeddor(ABC):
    def __init__(self, database: Client, moduleconfig="text2vec-transformers"):
        self.database = database
        self.moduleconfig = moduleconfig

    @abstractmethod
    def embed(self, context: str):
        pass

    @abstractmethod
    def launch_model(self):
        pass


class CPUEmbeddor(VectorEmbeddor):
    def __init__(self, database: Client):
        super().__init__(database)
        self.model = self.launch_model()

    def embed(self, context: str):
        return self.model.encode(context)

    def launch_model(self) -> SentenceTransformer:
        return SentenceTransformer("bert-base-nli-mean-tokens")


class MultiLingualE5Embeddor(VectorEmbeddor):
    def __init__(self, database: Client):
        super().__init__(database)
        self.model_name = "intfloat/multilingual-e5-large"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = self.launch_model()

    def launch_model(self) -> SentenceTransformer:
        return AutoModel.from_pretrained(self.model_name)

    def average_pool(
        self, last_hidden_states: Tensor, attention_mask: Tensor
    ) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(
            ~attention_mask[..., None].bool(), 0.0
        )
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def embed(self, text_to_embed: str):
        batch_dict = self.tokenizer(
            text_to_embed,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        outputs = self.model(**batch_dict)
        embedding = self.average_pool(
            outputs.last_hidden_state, batch_dict["attention_mask"]
        )
        embedding = F.normalize(embedding, p=2, dim=1)
        return embedding
