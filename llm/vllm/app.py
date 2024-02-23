import argparse
import json
import os
from typing import AsyncGenerator

import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from huggingface_hub import hf_hub_download
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
from vllm.utils import random_uuid

"""
Modified version from https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/api_server.py
"""

TIMEOUT_KEEP_ALIVE = 5  # seconds.
TIMEOUT_TO_PREVENT_DEADLOCK = 1  # seconds.
app = FastAPI()
engine = None
MODEL_REPO_ID = os.environ.get("MODEL_REPO_ID")
LOCAL_DIR = None


@app.post("/generate")
async def generate(request: Request) -> Response:
    """Generate completion for the request.

    The request should be a JSON object with the following fields:
    - prompt: the prompt to use for the generation.
    - stream: whether to stream the results or not.
    - other fields: the sampling parameters (See `SamplingParams` for details).
    """
    request_dict = await request.json()
    prompt = request_dict.pop("prompt")
    stream = request_dict.pop("stream", False)
    sampling_params = SamplingParams(**request_dict)
    request_id = random_uuid()

    results_generator = engine.generate(prompt, sampling_params, request_id)

    # Streaming case
    async def stream_results() -> AsyncGenerator[bytes, None]:
        async for request_output in results_generator:
            # prompt = request_output.prompt
            text_outputs = [output.text for output in request_output.outputs]
            ret = {"text": text_outputs}
            yield (json.dumps(ret) + "\0").encode("utf-8")

    async def abort_request() -> None:
        await engine.abort(request_id)

    if stream:
        background_tasks = BackgroundTasks()
        # Abort the request if the client disconnects.
        background_tasks.add_task(abort_request)
        return StreamingResponse(stream_results(), background=background_tasks)

    # Non-streaming case
    final_output = None
    async for request_output in results_generator:
        if await request.is_disconnected():
            # Abort the request if the client disconnects.
            await engine.abort(request_id)
            return Response(status_code=499)
        final_output = request_output

    assert final_output is not None
    # prompt = final_output.prompt
    text_outputs = [output.text for output in final_output.outputs]
    ret = {"text": text_outputs}
    return JSONResponse(ret)


@app.get("/get_templates_files")
async def get_templates_files() -> Response:
    config_files = {}
    prompt_config_file = hf_hub_download(repo_id=MODEL_REPO_ID, filename="prompt_config.yml", local_files_only=True, local_dir=LOCAL_DIR)
    with open(prompt_config_file) as f:
        config_files["prompt_config.yml"] = f.read()

    config = yaml.safe_load(config_files["prompt_config.yml"])

    for prompt in config.get("prompts", []):
        filename = prompt["template"]
        file_path = hf_hub_download(repo_id=MODEL_REPO_ID, filename=filename, local_files_only=True, local_dir=LOCAL_DIR)
        with open(file_path) as f:
            config_files[filename] = f.read()

    return JSONResponse(config_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()
    if args.model.startswith((".", "/")):
        LOCAL_DIR = args.model

    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug",
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
    )
