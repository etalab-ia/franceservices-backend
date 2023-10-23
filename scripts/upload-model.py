#!/bin/python

import os

from huggingface_hub import HfApi

if "HUGGINGFACE_TOKEN" in os.environ:
    hf_token = os.environ["HUGGINGFACE_TOKEN"]


def repo_exists(repo_id):
    api = HfApi()
    try:
        repo_info = api.repo_info(repo_id)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


org_name = "etalab-ia"
model_name = "albert-light"
version = "v1"
revision = "main"
repo_id = f"{org_name}/{model_name}"
folder_path = f"_data/models/{model_name}-{version}/{model_name}-{version}"


if __name__ == "__main__":
    api = HfApi()
    # Create remote space
    if not repo_exists(repo_id):
        api.create_repo(repo_id, repo_type="model", token=hf_token)

    # Upload all the content to remote space
    # Authenticate with: !huggingface-cli login --token $HUGGINGFACE_TOKEN
    api.upload_folder(
        folder_path=folder_path,
        repo_id=repo_id,
        repo_type="model",
        revision=revision,
        token=hf_token,
    )

    api.create_tag(repo_id, tag=version, revision=revision)
