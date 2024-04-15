#!/bin/bash
set -e

Help()
{
   # Display Help
   echo "Dynamic deploy llm containers."
   echo
   echo "Syntax: bash build.sh [-h|r|d|e]"
   echo "options:"
   echo "h          display this help and exit"
   echo "r          path to routing table file"
   echo "e          CI environment name. Only services in routing table with this CI environment will be deployed. If not specified, all services will be deployed"
}

while getopts "hr:e:" flag
do
    case "${flag}" in
        h)  Help && exit 1;;
        r)  routing_table=${OPTARG};;
        e)  ci_environment_name=${OPTARG};;
    esac
done

# check if required env variables are set
if [[ -z $CI_REGISTRY_IMAGE ]] || [[ -z $CI_VLLM_IMAGE_TAG ]] || [[ -z $CI_GPT4ALL_IMAGE_TAG ]]; then
    echo "error: CI_REGISTRY_IMAGE, CI_VLLM_IMAGE_TAG, CI_GPT4ALL_IMAGE_TAG env variables are required" && exit 1
fi

if [[ -z $routing_table ]]; then
    echo "-r argument is required. Help:" && Help && exit 0
elif ! [[ -f $routing_table ]]; then
    echo "file specified with -r argument does not exists. Help:" && Help && exit 0
fi

for model in $(jq -r 'keys[]' $routing_table); do

    if ! [[ -z $ci_environment_name ]]; then
        routing_table_ci_environment_name=$(jq -r '.["'$model'"] | .ci_environment_name' $routing_table)
        if [[ $routing_table_ci_environment_name != "${ci_environment_name}" ]]; then
            echo "info: skipping $model because of ci_environment_name mismatch ($routing_table_ci_environment_name != $ci_environment_name)"
            continue
        fi
    fi

    echo "info: deploying $model container"
    model_repo_id=$(jq -r '.["'$model'"] | .hf_repo_id' $routing_table)
    model_port=$(jq -r '.["'$model'"] | .model_port' $routing_table)
    driver=$(jq -r '.["'$model'"] | .driver' $routing_table)

    # gpt4all driver
    if [[ $driver == "gpt4all" ]]; then
        model_file=$(jq -r '.["'$model'"] | .model_file' $routing_table)

        export COMPOSE_PROJECT_NAME=$model
        export GPT4ALL_PORT=$model_port
        export GPT4ALL_MODEL_DIR=/data/models/$model_repo_id
        export GPT4ALL_MODEL=$model_file
        export MODEL_REPO_ID=$model_repo_id

        docker container rm --force ${COMPOSE_PROJECT_NAME}-gpt4all || true
        docker image rm ${CI_REGISTRY_IMAGE}/gpt4all:${CI_GPT4ALL_IMAGE_TAG} || true

        docker run --restart always --detach  --publish ${GPT4ALL_PORT}:8000 --name ${COMPOSE_PROJECT_NAME}-gpt4all \
        --env MODEL_REPO_ID=${MODEL_REPO_ID} \
        --volume ${GPT4ALL_MODEL_DIR}:/model \
        ${CI_REGISTRY_IMAGE}/gpt4all:${CI_GPT4ALL_IMAGE_TAG} \
        python3 /code/app.py --model=/model --port=8000 --host=0.0.0.0 --debug

    # vllm driver
    elif [[ $driver == "vllm" ]]; then
        model_file=$(jq -r '.["'$model'"] | .model_file' $routing_table)
        gpu_mem_use=$(jq -r '.["'$model'"] | .gpu_mem_use' $routing_table)
        tensor_parralel_size=$(jq -r '.["'$model'"] | .tensor_parralel_size' $routing_table)

        export COMPOSE_PROJECT_NAME=$model
        export VLLM_PORT=$model_port
        export VLLM_MODEL_DIR=/data/models/$model_repo_id
        export VLLM_GPU_MEMORY_UTILIZATION=$gpu_mem_use
        export VLLM_TENSOR_PARALLEL_SIZE=$tensor_parralel_size
        export MODEL_REPO_ID=$model_repo_id

        docker container rm --force ${COMPOSE_PROJECT_NAME}-vllm || true
        docker image rm ${CI_REGISTRY_IMAGE}/vllm:${CI_VLLM_IMAGE_TAG} || true

        docker run --restart always --detach --publish ${VLLM_PORT}:8000 --gpus all --name ${COMPOSE_PROJECT_NAME}-vllm \
        --env MODEL_REPO_ID=${MODEL_REPO_ID} \
        --env VLLM_MODEL=/model \
        --env VLLM_TENSOR_PARALLEL_SIZE=${VLLM_TENSOR_PARALLEL_SIZE} \
        --env VLLM_GPU_MEMORY_UTILIZATION=${VLLM_GPU_MEMORY_UTILIZATION} \
        --env VLLM_HOST=0.0.0.0 \
        --volume ${VLLM_MODEL_DIR}:/model \
        ${CI_REGISTRY_IMAGE}/vllm:${CI_VLLM_IMAGE_TAG}
    fi
done
