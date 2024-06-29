import json
from typing import Generator

from pyalbert.clients import LlmClient
from pyalbert.prompt import Prompter, get_prompter
from pyalbert.schemas import RagChatCompletionRequest, SamplingParams
from pyalbert.schemas.openai import ChatCompletionResponse, ChatMessage, UsageInfo


def albert_request_intercept(request: RagChatCompletionRequest) -> tuple[Prompter, str]:
    model_name = request.model
    mode = request.mode
    limit = request.limit
    sources = request.sources
    query = request.messages[-1]["content"]
    history = request.messages


    # TODO: handle more rag strategy
    if request.rag == "last":
        # Ragify the last query and use the 3 last user queries for the embedding search
        if mode is None:
            mode = "rag"

    prompter = get_prompter(model_name, mode=mode)
    prompt = prompter.make_prompt(
        query=query,
        limit=limit,
        sources=sources,
        history=history,
    )

    return prompter, prompt


def generate_v0(request: RagChatCompletionRequest) -> Generator | ChatCompletionResponse:
    assert len(request.messages) > 0

    # Build the prompt
    # --
    prompter, prompt = albert_request_intercept(request)

    # Set the Sampling parameters
    # --
    # Use the mode sampling params by default if any
    sampling_params = prompter.sampling_params
    # Update the sampling params from user params
    sampling_params_names = SamplingParams.__fields__.keys()
    sampling_params = {f: getattr(request, f) for f in sampling_params_names if hasattr(request, f)}

    # Get the stream generator
    llm_client = LlmClient(request.model)

    generator = llm_client.generate(prompt, stream=request.stream, **sampling_params)
    if request.stream:
        generator = sse_wrapper(generator)
    else:
        generator = ChatCompletionResponse(
            **{
                "model": request.model,
                "choices": [
                    {"index": 0, "message": dict(ChatMessage(role="assistant", content=generator))}
                ],
                "usage": dict(UsageInfo()),
            }
        )

    return generator


def sse_wrapper(generator):
    try:
        acc = []
        raw_response = ""
        stream_activate = False
        for t in generator:
            # Strip stream
            if not stream_activate and t.isspace():
                continue
            else:
                stream_activate = True

            # Accumulate word
            raw_response += t
            acc.append(t)
            if t.endswith((" ", "\n")) or t.startswith((" ", "\n")):
                yield "data: " + json.dumps("".join(acc)) + "\n\n"
                acc = []

        if len(acc) > 0:
            yield "data: " + json.dumps("".join(acc)) + "\n\n"

        eos_code = json.dumps("[DONE]")
        yield f"data: {eos_code}\n\n"
    finally:
        pass
