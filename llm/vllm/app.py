import argparse
import json
import os
from typing import AsyncGenerator

import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from huggingface_hub import hf_hub_download
from huggingface_hub.utils._errors import LocalEntryNotFoundError
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

# **model_taget** can be either a huggingface repod_id, or a absolute path.
# In the first case, the huggingface cache directory are used to download and access the model.
# In the other case, we assume the model is already downloaded in the given path.
model_target = None


def get_model_file(model_target: str, filename: str) -> str:
    if model_target.startswith("/"):
        model_dir = model_target
        file_path = os.path.join(model_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError
    else:
        # vllm auto-download the model if not found, but do not download extra files,
        # like prompt configuration files.
        file_path = hf_hub_download(repo_id=model_target, filename=filename)
    return file_path


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


@app.get(
    "/get_prompt_config",
    status_code=200,
    summary="Get the templates files",
    description="For a given model, get the prompte templates. If no config_file is given, we lookup for the file named 'prompt_config.ya?ml'",
)
async def get_prompt_config(
    request: Request,
    config_file: str | None = None,
) -> Response:
    if not config_file:
        config_files = ["prompt_config.yml",  "prompt_config.yaml"]
    else:
        config_files = [config_file]

    for i, conf_file in enumerate(config_files):
        try:
            file_path = get_model_file(model_target, conf_file)
        except Exception as err:
            if i < len(config_files) - 1:
                continue
            raise HTTPException(
                404, detail=f"{conf_file} not found in model {model_target}."
            ) from err

    with open(file_path, "r") as file:
        config = yaml.safe_load(file)

    for i, prompt in enumerate(config.get("prompts", [])):
        try:
            file_path = get_model_file(model_target, prompt["template"])
        except (FileNotFoundError, LocalEntryNotFoundError) as err:
            raise HTTPException(
                404, detail=f'{prompt["template"]} not found in model {model_target}.'
            ) from err

        with open(file_path, "r") as file:
            config["prompts"][i]["template"] = file.read()

    return JSONResponse(config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    model_target = args.model
    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug",
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
    )
