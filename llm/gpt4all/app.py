import argparse
from typing import AsyncGenerator
import json

from gpt4all import GPT4All
import uvicorn
from huggingface_hub import hf_hub_download

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

app = FastAPI()


@app.post("/generate", status_code=200)
async def generate(request: Request) -> Response:
    request = await request.json()
    prompt = request.pop("prompt")
    stream = request.pop("stream", False)
    sampling_params = {
        "max_tokens": request.pop("max_tokens", 100),
        "temp": request.pop("temperature", 0),
        "streaming": stream,
    }

    tokens = engine.generate(prompt=prompt, **sampling_params)

    # Streaming case
    if stream:

        async def stream_results(tokens) -> AsyncGenerator[bytes, None]:
            output = ""
            for token in tokens:
                output += token
                yield (json.dumps({"text": output}) + "\0").encode("utf-8")

        background_tasks = BackgroundTasks()
        return StreamingResponse(stream_results(tokens), background=background_tasks)

    # Non-streaming case
    response = JSONResponse({"text": tokens})

    return response


@app.post("/get_templates_files")
async def get_templates_files() -> Response:
    prompt_config_file = hf_hub_download(repo_id=model["hf_repo_id"], filename="prompt_config.yml")
    config_files = {}
    with open(prompt_config_file) as f:
        config = yaml.safe_load(f)
        config_files["prompt_config.yml"] = f.read()

    for prompt in config.get("prompts", []):
        filename = prompt["template"]
        file_path = hf_hub_download(repo_id=model["hf_repo_id"], filename=filename)
        with open(file_path) as f:
            config_files[filename] = f.read()

    return JSONResponse(config_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--device", type=str, default="cpu", choices=["cpu", "amd", "intel", "nvidia"]
    )
    parser.add_argument("--model", required=True, type=str)
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    model_name = args.model.split("/")[-1]
    model_path = args.model.replace(model_name, "")
    engine = GPT4All(
        model_name=model_name,
        model_path=model_path,
        allow_download=False,
        device=args.device,
        verbose=args.debug,
    )

    # run API server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
        timeout_keep_alive=5,
    )
