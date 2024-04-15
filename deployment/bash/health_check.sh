#!/bin/bash
set -e

for model in $(jq -r 'keys[]' ./llm_routing_table.json); do

    host=$(jq -r '.["'$model'"] | .llm_host' ./llm_routing_table.json)
    if [[ $host != "${CI_DEPLOY_HOST}" ]] && [[ $host != "all" ]]; then
        echo "info: skip model $model (host: $host)"
        continue
    fi

    # Initialize counter to 0
    counter=0
    echo "info: waiting llm container..."
    # Loop to check the health status of the container
    while true; do
    health_status=$(docker inspect --format '{{.State.Health.Status}}' ${model}-app-1 2>/dev/null || true)
    if [ "$health_status" = "healthy" ]; then
        echo "info: llm container is ready."
        break
    fi

    # Increment counter by 20 seconds
    counter=$((counter+20))

    # Check if counter has reached 10 minutes (600 seconds)
    if [ $counter -ge 600 ]; then
        echo "error: llm container did not reach a healthy state after 10 minutes, check the container."
        break
        exit 1
    fi

    # Wait 20 seconds before checking health status again
    sleep 20
    done

    port=$(jq -r '.["'$model'"] | .llm_port' ./llm_routing_table.json)
    echo "info: testing $model container"
    tests=$(ls ./test_*.py)
    for test in $tests; do
        python3 $test --port=$port --debug
    done

done