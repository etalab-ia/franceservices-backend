#!/bin/bash
set -e

Help()
{
   # Display Help
   echo "Test deployed llm containers."
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
elif ! [[ -f $routing_table ]]; then
    echo "file specified with -r argument does not exists. Help:" && Help && exit 0
fi

for model in $(jq -r 'keys[]' $routing_table); do
    
    env=$(jq -r '.["'$model'"] | .env' $routing_table)
    if [[ $env != "${ENV}" ]]; then
        echo "info: skipping $model vllm container"
        continue
    fi

    model_dir=$(jq -r '.["'$model'"] | .hf_repo_id' $routing_table)
    model_port=$(jq -r '.["'$model'"] | .model_port' $routing_table)
    driver=$(jq -r '.["'$model'"] | .driver' $routing_table)

    echo "info: testing $model vllm container"
    python3 ./tests/test_generate_endpoint.py --port=$model_port --debug
done