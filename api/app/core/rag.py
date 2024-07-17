from typing import Generator

from pyalbert.prompt import Prompter, get_prompter
from pyalbert.schemas import RagChatCompletionRequest


def albert_request_intercept(
    request: RagChatCompletionRequest,
) -> tuple[RagChatCompletionRequest, Prompter]:
    """Overwrite the request with prompt augmentation"""
    if not request.rag:
        return request, None

    model_name = request.model
    messages = request.messages

    if request.rag.strategy == "last":
        # Ragify the last query and use the 3 last user queries for the embedding search
        # This is the current approach
        # TODO: handle more rag strategy
        pass
    else:
        raise NotImplementedError("Unknown RAG strategy")

    # Prompt augmentation
    # --
    prompter = get_prompter(model_name, mode=request.rag.mode)
    messages = prompter.make_prompt(history=messages, **request.rag.model_dump())
    request.messages = messages

    # Update the Sampling parameters from model upstream values
    for k, v in prompter.get_upstream_sampling_params().items():
        if k not in request.__fields_set__:
            setattr(request, k, v)

    return request, prompter
