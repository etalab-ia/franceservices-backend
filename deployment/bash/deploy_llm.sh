#!/bin/bash
set -e

clear_cache=true
for model in $(jq -r 'keys[]' ./llm_routing_table.json); do

    host=$(jq -r '.["'$model'"] | .llm_host' ./llm_routing_table.json)
    if [[ $host != "${CI_DEPLOY_HOST}" ]] && [[ $host != "all" ]]; then
        echo "info: skip model $model (host: $host ; deploy host: ${CI_DEPLOY_HOST})"
        continue
    fi

    export COMPOSE_PROJECT_NAME=${model}-llm
    export LLM_HF_REPO_ID=$(jq -r '.["'$model'"] | .llm_hf_repo_id' ./llm_routing_table.json)
    export EMBEDDINGS_HF_REPO_ID=$(jq -r '.["'$model'"] | .embeddings_hf_repo_id' ./llm_routing_table.json)
    export LLM_PORT=$(jq -r '.["'$model'"] | .llm_port' ./llm_routing_table.json)
    export VLLM_GPU_MEMORY_UTILIZATION=$(jq -r '.["'$model'"] | .gpu_mem_use' ./llm_routing_table.json)
    export VLLM_TENSOR_PARALLEL_SIZE=$(jq -r '.["'$model'"] | .tensor_parralel_size' ./llm_routing_table.json)
    export API_ROOT=$(jq -r '.["'$model'"] | .api_root' ./llm_routing_table.json)

    if [[ $(jq -r '.["'$model'"] | .force_download' ./llm_routing_table.json) == "true" ]]; then
        export FORCE_DOWNLOAD=--force-download
    fi

    docker compose down

    # remove old image
    if [[ $clear_cache == true ]]; then
        echo "info: clear cache"
        docker tag ${CI_REGISTRY_IMAGE}/llm:${CI_LLM_IMAGE_TAG} ${CI_REGISTRY_IMAGE}/llm:${CI_LLM_IMAGE_TAG}-old || true
        docker image rm ${CI_REGISTRY_IMAGE}/llm:${CI_LLM_IMAGE_TAG} || true
        clear_cache=false
    fi

    docker compose up --detach
    docker image rm ${CI_REGISTRY_IMAGE}/llm:${CI_LLM_IMAGE_TAG}-old || true
    
done
