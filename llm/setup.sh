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

    hf_repo_id=$(jq -r '.["'$model'"] | .hf_repo_id' $routing_table)
    force_download=$(jq -r '.["'$model'"] | .force_download' $routing_table)
    if [[ $force_download == true ]]; then
        force_download="--force-download"
    else
        force_download=""
    fi

    echo "info: testing $model vllm container"
    python3 ./pyalbert/albert.py download_models --storage-dir=/data/models --hf-repo-id=$hf_repo_id $force_download
done