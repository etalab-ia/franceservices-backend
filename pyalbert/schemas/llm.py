from typing import List, Optional, Union

from pydantic import BaseModel


class Embeddings(BaseModel):
    input: str | list[str]
    # ignored for now, but keep it for openai-api compatibility
    model: str | None = None
    # Certain embedding model support asymetric queries.
    doc_type: str | None = None
    # ignored for now, but keep it for openai-api compatibility
    encoding_format: str = "float"  # only float is supported.


class SamplingParams(BaseModel):
    # sampling parameters from vllm:
    # https://github.com/vllm-project/vllm/blob/main/vllm/sampling_params.py
    n: int = 1
    best_of: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    repetition_penalty: float = 1.0
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = -1
    min_p: float = 0.0
    seed: Optional[int] = None
    use_beam_search: bool = False
    length_penalty: float = 1.0
    early_stopping: Union[bool, str] = False
    stop: Optional[Union[str, List[str]]] = None
    stop_token_ids: Optional[List[int]] = None
    include_stop_str_in_output: bool = False
    ignore_eos: bool = False
    max_tokens: Optional[int] = 16
    logprobs: Optional[int] = None
    prompt_logprobs: Optional[int] = None
    skip_special_tokens: bool = True
    spaces_between_special_tokens: bool = True
    # logits_processors: Optional[List[LogitsProcessor]] = None # ignored for now because it generate a bug with pydantic

class Generate(SamplingParams):
    # Request is needed because is_disconneted attribute is call in generate endpoint
    prompt: str
    stream: bool = False

