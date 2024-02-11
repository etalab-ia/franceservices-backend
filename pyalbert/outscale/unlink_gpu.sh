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

if [[ -z $response ]];then
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

    if [[ -z $response ]];then
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

    if [[ -z $response ]];then
        echo "error: request failed" && exit 1
    fi

    state=$(echo $response | jq -r '.Vms[0].State')
done
sleep 10 && echo "info: vm is stopped"

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

if [[ -z $response ]];then
    echo "error: request failed" && exit 1
elif [[ $(echo $response | jq -r '.FlexibleGpus | length') -eq 0 ]]; then
    echo "error: no gpu linked to the VM" && exit 1
elif [[ $(echo $response | jq -r '.FlexibleGpus | length') -gt 1 ]]; then
    echo "error: more than one gpu linked to the VM" && exit 1
fi 

gpu_id=$(echo $response | jq -r '.FlexibleGpus[0].FlexibleGpuId')

# unlink gpu
echo "info: unlink gpu"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/UnlinkFlexibleGpu \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --fail \
    --silent \
    --data '{
        "FlexibleGpuId": "'$gpu_id'"
    }')
    
if [[ -z $response ]];then
    echo "error: request failed" && exit 1
fi

# delete gpu
echo "info: delete GPU"
response=$(curl -X POST https://api.$OSC_REGION.outscale.com/api/v1/DeleteFlexibleGpu \
    --user $OSC_ACCESS_KEY:$OSC_SECRET_KEY \
    --aws-sigv4 'osc' \
    --header 'Content-Type: application/json' \
    --silent \
    --fail \
    --data '{
        "FlexibleGpuId": "'$gpu_id'"
    }')

if [[ -z $response ]];then
    echo "error: request failed" && exit 1
fi

echo "info: vm is stopped without a linked gpu"
