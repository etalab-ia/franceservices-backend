#!/bin/sh
set -e

Help()
{
    # Display Help
    echo "Download a HuggingFace repository and launch a local api for the model."
    echo
    echo "Syntax: bash launch_local_llm.sh [-h|m|p|d|g|t]"
    echo "options:"
    echo "h          display this help and exit"
    echo "s          storage directory to download model, default /data/models"
    echo "r          HuggingFace repository id"
    echo "m          model file (only for gpt4all driver)"
    echo "p          port, default: 8000"
    echo "d          driver (gpt4all or vllm)"
    echo "g          gpu memory utilization (only for vllm driver), default: 0.5"
    echo "t          tensor parallel size (only for vllm driver), default 1"
}

while getopts "hs:fr:m:p:d:g:t:" flag
do
    case "${flag}" in
        h)  Help && exit 1;;
        s)  storage_dir=${OPTARG};;
        f)  force_download=${OPTARG:-"disable"};;
        r)  hf_repo_id=${OPTARG};;
        m)  model_file=${OPTARG};;
        p)  port=${OPTARG:-8000};;
        d)  driver=${OPTARG};;
        g)  gpu_mem_use=${OPTARG};;
        t)  tensor_parralel_size=${OPTARG};;
    esac
done

base_path=$(dirname $(realpath $0))
 
# check if model path is provided
if [[ -z $hf_repo_id ]]; then
    echo "-r argument is required. Help:" && Help && exit 0
fi

# check if driver is provided
if [[ -z $driver ]]; then
    echo "-d argument is required. Help:" && Help && exit 0
fi

# check if model file is provided if gpt4all is selected

# check if storage directory is provided
if [[ -z $storage_dir ]]; then
    storage_dir="/data/models"
fi
# check if gpu memory utilization is provided
if [[ -z $gpu_mem_use ]]; then
    gpu_mem_use=0.5
fi

# check if tensor parallel size is provided
if [[ -z $tensor_parralel_size ]]; then
    tensor_parralel_size=1
fi
# if force_download is not disable, it should be true
if [[ -z $force_download ]]; then
    force_download=""
else
    force_download="--force-download"
fi

# model if gpt4all
if [[ $driver == "gpt4all" ]]; then
    if [[ -z $model_file ]]; then
        echo "-m argument is required for gpt4all driver. Help:" && Help && exit 0
    fi
fi

echo "Arguments:"
echo "storage_dir: $storage_dir"
echo "force_download: $force_download"
echo "hf_repo_id: $hf_repo_id"
echo "port: $port"
echo "driver: $driver"
echo "model_file: $model_file"
echo "gpu_mem_use: $gpu_mem_use"
echo "tensor_parralel_size: $tensor_parralel_size"

python3 $base_path/../pyalbert/albert.py download_models --storage-dir=$storage_dir --hf-repo-id=$hf_repo_id $force_download --debug

# lauch gpt4all
if [[ $driver == "gpt4all" ]]; then
    python3 $base_path/../llm/gpt4all/app.py --host=0.0.0.0 --port=$port --model=$storage_dir/$hf_repo_id/$model_file

# check if driver is vllm
elif [[ $driver == "vllm" ]]; then
    python3 $base_path/../llm/vllm/app.py --host=0.0.0.0 --port=$port --model=$storage_dir/$hf_repo_id --tensor-parallel-size=$tensor_parralel_size --gpu-memory-utilization=$gpu_mem_use
fi