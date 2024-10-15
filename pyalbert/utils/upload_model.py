#!/usr/bin/env python

import os

from huggingface_hub import HfApi

hf_token = None
if "HUGGINGFACE_TOKEN" in os.environ:
    hf_token = os.environ["HUGGINGFACE_TOKEN"]


def repo_exists(repo_id):
    api = HfApi()
    try:
        _ = api.repo_info(repo_id)
        return True
    except Exception as e:
        print(f"Warning repo exists: {e}")
        return False


org_name = "AgentPublic"
model_name = "albert-light"
version = "v1"
revision = "main"
repo_id = f"{org_name}/{model_name}"
folder_path = f"_data/models/{model_name}-{version}/{model_name}-{version}"
is_private = False


if __name__ == "__main__":
    api = HfApi()
    # Create remote space
    if not repo_exists(repo_id):
        api.create_repo(repo_id, repo_type="model", token=hf_token, private=is_private)

    # Upload all the content to remote space
    # Authenticate with: !huggingface-cli login --token $HUGGINGFACE_TOKEN
    api.upload_folder(
        folder_path=folder_path,
        repo_id=repo_id,
        repo_type="model",
        revision=revision,
        token=hf_token,
    )

    if version:
        api.create_tag(repo_id, tag=version, revision=revision)
