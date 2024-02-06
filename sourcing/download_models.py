
import os
from huggingface_hub import snapshot_download

try:
    from app.config import VLLM_ROUTING_TABLE
except ModuleNotFoundError:
    from api.app.config import VLLM_ROUTING_TABLE


def download_models(PATH: str | None = None):
    """Download huggingface models to the given path, or the defaut path used by HF."""

    for model in VLLM_ROUTING_TABLE:
        params = {
            "repo_id": model["model_id"]
        }

        if PATH:
            params["local_dir"] = os.path.join(PATH, model["model_id"])

        if model["do_update"]:
            # TODO: not sure if snapshot_download will automatically checkout last commit if any though.
            params["force_download"] = True

        snapshot_download(**params)

