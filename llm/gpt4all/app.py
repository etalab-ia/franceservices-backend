import argparse
import json
import os
from typing import AsyncGenerator

import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from gpt4all import GPT4All

app = FastAPI()
engine = None
model_dir = None


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
    # @TODO: callback to stop ?

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


@app.get(
    "/get_prompt_config",
    status_code=200,
    summary="Get the templates files",
    description="For a given model, get the prompte templates.",
)
async def get_prompt_config(
    request: Request,
    config_file: str = "prompt_config.yml",
) -> Response:
    file_path = os.path.join(model_dir, config_file)

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
    else:
        raise HTTPException(404, detail=f"{config_file} not found.")

    for i, prompt in enumerate(config.get("prompts", [])):
        file_name = prompt["template"]
        file_path = os.path.join(model_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                config["prompts"][i]["template"] = file.read()

    return JSONResponse(config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--device", type=str, default="cpu", choices=["cpu", "amd", "intel", "nvidia"]
    )
    parser.add_argument("--model", required=True, type=str, help="Model directory")
    parser.add_argument("--model-file", type=str, help="Model file, if not specified, will use the first .bin file found in the model directory.")
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    if args.model_file is None:

        bin_files = [file for file in os.listdir(args.model) if file.endswith(".bin")]

        if len(bin_files) == 0:
            raise FileNotFoundError(
                f"No model file found in {args.model}. Please specify the model file to use with --model-file option."
            )
        elif len(bin_files) > 1:
            raise FileNotFoundError(
                f"Multiple model files found in {args.model}. Please specify the model file to use with --model-file option"
            )
        else:
            args.model_file = bin_files[0]

    engine = GPT4All(
        model_name=args.model_file,
        model_path=args.model,
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
