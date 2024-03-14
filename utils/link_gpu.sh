#!/bin/sh

# retrieve vm state
echo "info: retrieve vm state"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/ReadVms \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
        "Filters": {
            "VmIds": ["'$OSC_VM_ID'"]
        }
    }')

if [[ -z $response ]]; then
    echo "error: request failed" && exit 1
elif [[ $(echo $response | jq -r '.Vms | length') -eq 0 ]]; then
    echo "error: no vm with this id" && exit 1
fi

state=$(echo $response | jq -r '.Vms[0].State')

# check if vm state is running or stop
if [[ $state != "running" && $state != "stopped" ]]; then
    echo "error: the vm state is $state" && exit 1
fi

# stop vm if running
if [[ $state = "running" ]]; then

    echo "info: stop vm"
    response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/StopVms \
        --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
        --aws-sigv4 'osc' \
        --header 'Content-Type: application/json' \
        --silent \
        --fail \
        --data '{
            "VmIds": ["'$OSC_VM_ID'"]
        }')

    if [[ -z $response ]]; then
        echo "error: request failed" && exit 1
    fi    
fi

# wait for vm to be stopped
start_time=$(date +%s)
while [[ $state != "stopped" ]]; do
    
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if [[ $elapsed_time -gt 300 ]]; then
        echo "error: timeout - vm did not stop within 5 minutes" && exit 1
    fi

    echo "info: wait for vm to be stopped..."
    sleep 10

    response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/ReadVms \
        --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
        --aws-sigv4 'osc' \
        --header 'Content-Type: application/json' \
        --silent \
        --fail \
        --data '{
            "Filters": {
                "VmIds": ["'$OSC_VM_ID'"]
            }
        }')

    if [[ -z $response ]]; then
        echo "error: request failed" && exit 1
    fi

    state=$(echo $response | jq -r '.Vms[0].State')
done

sleep 10 && echo "info: vm is stopped"

# allocate gpu
echo "info: allocate GPU"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/CreateFlexibleGpu \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
    "SubregionName": "'$OSC_SUBREGION'",
    "ModelName": "'$OSC_GPU_MODEL_NAME'",
    "Generation": "'$OSC_CPU_GENERATION'",
    "DeleteOnVmDeletion": true
    }')

if [[ -z $response ]]; then
    echo "error: request failed - unvailable gpu ressource" && exit 1
fi

gpu_id=$(echo $response | jq -r '.FlexibleGpu.FlexibleGpuId')

# link gpu
echo "info: link gpu"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/LinkFlexibleGpu \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
        "FlexibleGpuId": "'$gpu_id'",
        "VmId": "'$OSC_VM_ID'"
    }')

if [[ -z $response ]]; then
    echo "error: request failed" && exit 1
fi

# check if gpu state is attached
echo "info: check if gpu state is attached"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/ReadFlexibleGpus \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
    "Filters": {
        "VmIds": ["'$OSC_VM_ID'"]
        }
    }')

if [[ -z $response ]]; then
    echo "error: request failed" && exit 1
elif [[ $(echo $response | jq -r '.FlexibleGpus | length') -eq 0 && $(echo $response | jq -r '.FlexibleGpus[0].FlexibleGpuId') != $gpu_id ]]; then
    echo "error: the gpu is not correctly linked to the VM"

    echo "info: release gpu"
    response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/DeleteFlexibleGpu \
        --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
        --aws-sigv4 'osc' \
        --header 'Content-Type: application/json' \
        --silent \
        --fail \
        --data '{
            "FlexibleGpuIds": ["'$gpu_id'"]
        }')
    
    if [[ -z $response ]]; then
        echo "error: request failed" && exit 1
    fi
    echo "info: gpu released" && exit 1
fi

# restart vm
echo "info: restart vm"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/StartVms \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
        "VmIds": ["'$OSC_VM_ID'"]
    }')

if [[ -z $response ]]; then
    echo "error: request failed" && exit 1
fi

# wait for vm to be running
start_time=$(date +%s)
while [[ $state != "running" ]]; do
    
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    if [[ $elapsed_time -gt 300 ]]; then
        echo "error: timeout - vm did not start within 5 minutes" && exit 1
    fi

    echo "info: wait for vm to be running..."
    sleep 10

    response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/ReadVms \
        --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
        --aws-sigv4 'osc' \
        --header 'Content-Type: application/json' \
        --silent \
        --fail \
        --data '{
            "Filters": {
                "VmIds": ["'$OSC_VM_ID'"]
            }
        }')

    if [[ -z $response ]]; then
        echo "error: request failed" && exit 1
    fi

    state=$(echo $response | jq -r '.Vms[0].State')
done

sleep 60 && echo "info: vm is running with a linked gpu" 
