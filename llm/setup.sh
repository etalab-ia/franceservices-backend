#!/bin/bash
set -e

Help()
{
   # Display Help
   echo "Download model files."
   echo
   echo "Syntax: bash build.sh [-h|r|d|e]"
   echo "options:"
   echo "h          display this help and exit"
   echo "r          path to routing table file"
   echo "e          CI environment name. Only services in routing table with this environment will be deployed. If not specified, all services will be deployed"
}

while getopts "hr:e:" flag
do
    case "${flag}" in
        h)  Help && exit 1;;
        r)  routing_table=${OPTARG};;
        e)  ci_environment_name=${OPTARG};;
    esac
done

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

    hf_repo_id=$(jq -r '.["'$model'"] | .hf_repo_id' $routing_table)
    force_download=$(jq -r '.["'$model'"] | .force_download' $routing_table)
    if [[ $force_download == true ]]; then
        force_download="--force-download"
    else
        force_download=""
    fi

    echo "info: download $hf_repo_id files."
    python3 ./pyalbert/albert.py download_models --storage-dir=/data/models --hf-repo-id=$hf_repo_id $force_download
done