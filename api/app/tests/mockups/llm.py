import json
import os
from typing import Generator

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return "ok"


@app.post("/generate")
async def generate(request: Request) -> Response:
    """Return back the prompt. Support stream=True"""

    request_dict = await request.json()
    prompt = request_dict.pop("prompt")
    stream = request_dict.pop("stream", False)
    # sampling_params = SamplingParams(**request_dict)

    def chunkify(text):
        # Split the string in size of different size. Linear grow.
        start = 0
        while start < len(text):
            # Loop through chunk sizes from 1 to 10
            for chunk_size in range(1, 11):
                end = start + chunk_size
                yield text[start:end]
                start = end
                if start >= len(text):
                    break

    def stream_results() -> Generator:
        full = ""
        for chars in chunkify(prompt):
            full += chars  # Yes, it what we receive from vllm. Using the openai compatible server instead ?
            ret = {"text": [full]}
            yield (json.dumps(ret) + "\0").encode("utf-8")

    if stream:
        background_tasks = BackgroundTasks()
        return StreamingResponse(stream_results(), background=background_tasks)

    ret = {"text": [prompt]}
    return JSONResponse(ret)


@app.get("/get_prompt_config")
async def get_prompt_config(request: Request, config_file: str | None = None) -> Response:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "rag_prompt_template.jinja")) as f:
        rag_template = f.read()

    data = {
        "prompt_format": "llama-chat",
        "system_prompt": "a general system prompt...",
        "max_tokens": 2048,
        "prompts": [
            {
                "mode": "simple",
                "system_prompt": "a particular system prompt...",
                "template": rag_template,
            },
            {"mode": "rag", "template": rag_template, "default": {"limit": 4}},
        ],
    }
    return JSONResponse(data)
