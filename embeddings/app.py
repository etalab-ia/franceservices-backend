import argparse
import os

import torch
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pyalbert import Logging
from pyalbert.models import download_models
from transformers import AutoModel, AutoTokenizer

from core import make_embeddings

app = FastAPI()

TIMEOUT_KEEP_ALIVE = 10  # seconds.
WITH_GPU = True if torch.cuda.is_available() else False
BATCH_SIZE_MAX = 10
args = None


@app.on_event("startup")
async def startup_event():
    # download model
    download_models(
        storage_dir=args.models_dir,
        hf_repo_id=args.hf_repo_id,
        force_download=args.force_download,
        debug=args.debug,
    )

    params = {
        "pretrained_model_name_or_path": args.hf_repo_id,
        "force_download": args.force_download,
        "cache_dir": args.model_dir,
    }

    tokenizer = AutoTokenizer.from_pretrained(**params)
    params["device_map"] = "cuda:0" if WITH_GPU else None

    model = AutoModel.from_pretrained(**params)

    app.state.tokenizer = tokenizer
    app.state.model = model


@app.post("/v1/embeddings")
async def embeddings(request: Request) -> dict:
    # @IMPROVE: The pydantic schema Embedding are already defined in api/app/schemas/search.py
    #           Schemas are a project level knowledge, and so should be defined at the root level
    #           of the project in order to be shared by every service. One approch could be to
    #           integrate it into pyalbert/schemas and make pyalbert a dependacy of other service
    #           (as it is already the case fo api/).
    params = await request.json()
    texts = params["input"]
    doc_type = params.get("doc_type")
    if isinstance(texts, str):
        texts = [texts]

    vectors = make_embeddings(
        tokenizer=request.app.state.tokenizer,
        model=request.app.state.model,
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
        "model": args.hf_repo_id,
        "data": [
            {"object": "embedding", "embedding": v, "index": i} for i, v in enumerate(vectors)
        ],
    }

    return JSONResponse(content=response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost", help="Host name.")
    parser.add_argument("--port", type=int, default=8000, help="Port number.")
    parser.add_argument(
        "--models-dir", type=str, required=True, help="Storage directory for model directories."
    )
    parser.add_argument("--hf-repo-id", type=str, required=True, help="Hugging Face repository ID.")
    parser.add_argument(
        "--force-download",
        action="store_true",
        default=False,
        help="Force download of model files when API startups.",
    )
    parser.add_argument("--debug", action="store_true", default=False, help="Print debug logs.")

    args = parser.parse_args()
    args.model_dir = os.path.join(args.models_dir, args.hf_repo_id)

    logging = Logging(level="DEBUG" if args.debug else "INFO")
    logger = logging.get_logger()

    # run API server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
        timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
    )
