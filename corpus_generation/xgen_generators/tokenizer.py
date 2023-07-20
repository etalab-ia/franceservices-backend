from typing import Callable
from transformers import AutoTokenizer


def get_tokenizer(model_name) -> AutoTokenizer:
    print(f"loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        device_map="auto",
        max_length=4000,
        padding="max_length",
    )
    tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def get_count_tokens_fn(model_name) -> Callable[[str], int]:
    tokenizer = get_tokenizer(model_name)

    def count_tokens_fn(text: str) -> int:
        return len(tokenizer.encode(text))

    return count_tokens_fn
