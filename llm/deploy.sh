#!/bin/bash
set -e

Help()
{
   # Display Help
   echo "Dynamic deploy vllm containers."
   echo
   echo "Syntax: bash build.sh [-h|r|d]"
   echo "options:"
   echo "h          display this help and exit"
   echo "r          path to routing table file"
}

while getopts "hr:" flag
do
    case "${flag}" in
        h)  Help && exit 1;;
        r)  routing_table=${OPTARG};;
    esac
done

if [[ -z $routing_table ]]; then
    echo "-r ergument is required. Help:" && Help && exit 0
elif ! [[ -r $routing_table ]]; then
    echo "file specified with -f argument does not exists. Help:" && Help && exit 0
fi

for model in $(jq -r 'keys[]' $routing_table); do
    
    env=$(jq -r '.["'$model'"] | .env' $routing_table)
    if [[ $env != "${ENV}" ]]; then
        echo "info: skipping $model container"
        continue
    fi

    echo "info: deploying $model container"
    model_dir=$(jq -r '.["'$model'"] | .hf_repo_id' $routing_table)
    model_port=$(jq -r '.["'$model'"] | .model_port' $routing_table)
    driver=$(jq -r '.["'$model'"] | .driver' $routing_table)

    # gpt4all driver
    if [[ $driver == "gpt4all" ]]; then
        model_file=$(jq -r '.["'$model'"] | .model_file' $routing_table)

        export COMPOSE_PROJECT_NAME=$model
        export GPT4ALL_PORT=$model_port
        export GPT4ALL_MODEL_DIR=/data/models/$model_dir
        export GPT4ALL_MODEL=$model_file

        docker container rm -f ${COMPOSE_PROJECT_NAME}-gpt4all || true
        docker image rm ${CI_REGISTRY_IMAGE}/gpt4all:${CI_GPT4ALL_IMAGE_TAG} || true
        docker run --restart="always" --detach --publish ${GPT4ALL_PORT}:8000 --name ${COMPOSE_PROJECT_NAME}-gpt4all -v ${GPT4ALL_MODEL_DIR}:/model ${CI_REGISTRY_IMAGE}/gpt4all:${CI_GPT4ALL_IMAGE_TAG} python3 /code/app.py --model=/model/${GPT4ALL_MODEL} --port=8000 --host=0.0.0.0 --debug
    
    # vllm driver
    elif [[ $driver == "vllm" ]]; then
        model_file=$(jq -r '.["'$model'"] | .model_file' $routing_table)
        gpu_mem_use=$(jq -r '.["'$model'"] | .gpu_mem_use' $routing_table)
        tensor_parralel_size=$(jq -r '.["'$model'"] | .tensor_parralel_size' $routing_table)

        export COMPOSE_PROJECT_NAME=$model
        export VLLM_PORT=$model_port
        export VLLM_MODEL_DIR=/data/models/$model_dir
        export VLLM_GPU_MEMORY_UTILIZATION=$gpu_mem_use
        export VLLM_TENSOR_PARALLEL_SIZE=$tensor_parralel_size

        docker container rm -f ${COMPOSE_PROJECT_NAME}-vllm || true
        docker image rm ${CI_REGISTRY_IMAGE}/vllm:${CI_VLLM_IMAGE_TAG} || true
        docker run --restart="always" --detach --gpus all --env VLLM_MODEL=/model --env VLLM_TENSOR_PARALLEL_SIZE=${VLLM_TENSOR_PARALLEL_SIZE} --env VLLM_GPU_MEMORY_UTILIZATION=${VLLM_GPU_MEMORY_UTILIZATION} --env VLLM_HOST=0.0.0.0 --publish ${VLLM_PORT}:8000 --name ${COMPOSE_PROJECT_NAME}-vllm -v ${VLLM_MODEL_DIR}:/model ${CI_REGISTRY_IMAGE}/vllm:${CI_VLLM_IMAGE_TAG}
    fi
done