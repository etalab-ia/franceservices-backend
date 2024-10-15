import argparse
import json
import os
import shutil
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from gpt4all import GPT4All
from huggingface_hub import hf_hub_download, snapshot_download
from huggingface_hub.utils._errors import EntryNotFoundError
from pyalbert import Logging
from pyalbert.schemas.llm import Embeddings
from transformers import AutoModel, AutoTokenizer

from core import make_embeddings

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="localhost", help="Host name.")
parser.add_argument("--port", type=int, default=8000, help="Port number.")
parser.add_argument("--models-dir", type=str, required=True, help="Storage directory for model directories.")  # fmt: off
parser.add_argument("--embeddings-hf-repo-id", type=str, default=None, nargs='?', help="Hugging Face repository ID for embeddings model. If not provided, the embeddings endpoint is not be available.")  # fmt: off
parser.add_argument("--llm-hf-repo-id", type=str, required=True, help="Hugging Face repository ID for llm model.")  # fmt: off
parser.add_argument("--llm-model-file", type=str, default=None, help="Model file to use for LLM model (bin format is required).")  # fmt: off
parser.add_argument("--root-path", type=str, default=None, help="FastAPI root_path when app is behind a path based routing proxy.")  # fmt: off
parser.add_argument("--force-download", action="store_true", default=False, help="Force download of model files when API startups.")  # fmt: off
parser.add_argument("--debug", action="store_true", default=False, help="Print debug logs.")

args = parser.parse_args()

TIMEOUT_KEEP_ALIVE = 10  # seconds.
WITH_GPU = False
WITH_EMBEDDINGS = True if args.embeddings_hf_repo_id else False
BATCH_SIZE_MAX = 10
MODELS = {}


@asynccontextmanager
async def download_and_run_models(app: FastAPI):
    """
    Lifespan event to download the embeddings and llm models from Hugging Face repository and run them when API startup.
    For more information about FastAPI lifespan events, please visit: https://fastapi.tiangolo.com/advanced/events/#lifespan.
    """

    if WITH_EMBEDDINGS:
        # download embeddings model
        model_storage_dir = os.path.join(args.models_dir, args.embeddings_hf_repo_id)
        os.makedirs(model_storage_dir, exist_ok=True)

        params = {
            "repo_id": args.embeddings_hf_repo_id,
            "local_dir": model_storage_dir,
            "force_download": args.force_download,
            "cache_dir": model_storage_dir,
        }

        try:
            logger.info(f"downloading {args.embeddings_hf_repo_id} in {model_storage_dir}...")
            snapshot_download(**params)
        except Exception:
            shutil.rmtree(model_storage_dir)
            logger.error(traceback.print_exc())
            exit(1)

    # download llm model
    model_storage_dir = os.path.join(args.models_dir, args.llm_hf_repo_id)
    os.makedirs(model_storage_dir, exist_ok=True)

    params = {
        "repo_id": args.llm_hf_repo_id,
        "local_dir": model_storage_dir,
        "force_download": args.force_download,
        "cache_dir": model_storage_dir,
    }

    try:
        logger.info(f"downloading {args.llm_hf_repo_id}... in {model_storage_dir}")
        snapshot_download(**params)
    except Exception:
        shutil.rmtree(model_storage_dir)
        logger.error(traceback.print_exc())
        exit(1)

    if WITH_EMBEDDINGS:
        # run the embeddings model
        params = {
            "pretrained_model_name_or_path": args.embeddings_hf_repo_id,
            "force_download": args.force_download,
            "cache_dir": os.path.join(args.models_dir, args.embeddings_hf_repo_id),
        }

        tokenizer = AutoTokenizer.from_pretrained(**params)

        params["device_map"] = "cuda:0" if WITH_GPU else None
        embeddings_model = AutoModel.from_pretrained(**params)

        MODELS["tokenizer"] = tokenizer
        MODELS["embeddings_model"] = embeddings_model
    else:
        MODELS["tokenizer"] = None
        MODELS["embeddings_model"] = None

    # run the llm model
    args.model = os.path.join(args.models_dir, args.llm_hf_repo_id)

    if args.llm_model_file is None:
        bin_files = [file for file in os.listdir(args.model) if file.endswith(".bin")]
        logger.debug(f"bin_files found: {bin_files}")
        if len(bin_files) == 0:
            raise FileNotFoundError(
                f"No model file found in {args.model}. Please specify the model file to use with --model-file option."
            )
        elif len(bin_files) > 1:
            raise FileNotFoundError(
                f"Multiple model files found in {args.model}. Please specify the model file to use with --model-file option"
            )
        else:
            args.llm_model_file = bin_files[0]

    llm_model = GPT4All(
        model_name=args.llm_model_file,
        model_path=args.model,
        allow_download=False,
        device="cpu",
        verbose=args.debug,
    )

    MODELS["llm_model"] = llm_model

    yield  # release ressources when api shutdown
    logger.info("Shutting down, releasing resources...")
    MODELS.clear()


app = FastAPI(
    title="Albert model API with GPT4All engine",
    description="GPT4All engine enables Albert models to be launched without a GPU.",
    version="0.0.1",
    lifespan=download_and_run_models,
)


@app.get("/health")
async def health() -> Response:
    """Health check."""

    return Response(status_code=200)


@app.get("/models")
async def show_available_models() -> Response:
    if WITH_EMBEDDINGS:
        models = [args.embeddings_hf_repo_id, args.llm_hf_repo_id]
    else:
        models = [args.llm_hf_repo_id]

    response = {
        "object": "list",
        "data": [{"object": "model", "id": model} for model in models],
    }
    return JSONResponse(content=response)


@app.post("/embeddings", include_in_schema=WITH_EMBEDDINGS)
async def embeddings(request: Embeddings) -> Response:
    """
    Generate embeddings for the input text(s).

    Args:
        request (Embeddings): input request.

    Returns:
        Response: JSONResponse
    """

    if not WITH_EMBEDDINGS:
        raise HTTPException(status_code=404, detail="Embeddings endpoint is not available.")

    texts = request.input
    doc_type = request.doc_type
    if isinstance(texts, str):
        texts = [texts]

    vectors = make_embeddings(
        tokenizer=MODELS["tokenizer"],
        model=MODELS["embeddings_model"],
        texts=texts,
        doc_type=doc_type,
        batch_size=BATCH_SIZE_MAX,
        gpu=WITH_GPU,
    )
    # convert np.array to list for JSON response
    vectors = [v.tolist() for v in vectors]

    response = {
        "id": None,
        "object": "list",
        "model": args.embeddings_hf_repo_id,
        "data": [
            {"object": "embedding", "embedding": v, "index": i} for i, v in enumerate(vectors)
        ],
    }

    return JSONResponse(content=response)


@app.post("/generate")
async def generate(request: Request) -> Response:
    params = request.dict()
    prompt = params.pop("prompt")
    stream = params.pop("stream", False)
    sampling_params = {
        "max_tokens": params.pop("max_tokens", 100),
        "temp": params.pop("temperature", 0),
        "streaming": stream,
    }
    # @TODO: callback to stop ?

    tokens = app.state.llm_model.generate(prompt=prompt, **sampling_params)

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


@app.get("/get_prompt_config")
async def get_prompt_config(
    request: Request, config_file: Optional[str] = None, allow_download: bool = True
) -> Response:
    """
    Get the templates files for the model.

    Args:
        config_file (Optional[str], optional): path to the config file containing the routing table. Defaults to None.
        allow_download (bool, optional): allow download from remote model repository. Defaults to True.

    Returns:
        Response: JSONResponse
    """

    def _get_model_files(file, allow_download: bool):
        if allow_download:
            try:
                file_path = hf_hub_download(
                    repo_id=args.llm_hf_repo_id,
                    filename=file,
                    local_dir=args.model,
                    cache_dir=args.model,
                )
            except EntryNotFoundError:
                logger.debug(f"{file} not found in remote model repository.")
                file_path = None
        else:
            file_path = (
                os.path.join(args.model, file)
                if os.path.exists(os.path.join(args.model, file))
                else None
            )
            if file_path is None:
                logger.debug(f"{file} not found in local model directory.")

        return file_path

    # if no config_file is given, we lookup for the files named 'prompt_config.yaml' or 'prompt_config.yml'
    config_files = ["prompt_config.yml", "prompt_config.yaml"] if not config_file else [config_file]

    local_files = list()
    for file in config_files:
        file_path = _get_model_files(file, allow_download=allow_download)
        if file_path:
            local_files.append(file_path)

    if len(local_files) == 0:
        raise HTTPException(404, detail=f"{config_file} not found in model directory.")

    if len(local_files) > 1:
        raise HTTPException(
            404,
            detail=f"Multiple files found in model directory: {config_files}, please specify the file to use.",
        )

    # open the file
    file_path = local_files[0]
    with open(file_path, "r") as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError:
            raise HTTPException(404, detail=f"Error reading YAML file: {file_path}.")

    # open the prompt templates
    for i, prompt in enumerate(config.get("prompts", [])):
        try:
            file = prompt["template"]
        except KeyError:
            raise HTTPException(
                404, detail=f"Error parsing YAML file (template key not found): {file_path}"
            )

        file_path = _get_model_files(file, allow_download=allow_download)

        if file_path is None:
            if allow_download:
                raise HTTPException(404, detail=f"{file} not found in remote model repository.")
            else:
                raise HTTPException(404, detail=f"{file} not found in model directory.")

        with open(file_path, "r") as file:
            try:
                config["prompts"][i]["template"] = file.read()
            except Exception:
                raise HTTPException(404, detail=f"Error reading template file: {file_path}.")

    return JSONResponse(config)


if __name__ == "__main__":
    logging = Logging(level="DEBUG" if args.debug else "INFO")
    logger = logging.get_logger()
    logger.debug(f"arguments: {args}")

    app.root_path = args.root_path
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
    )
