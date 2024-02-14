FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
ADD ./app.py ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["sh", "-c", "python3 app.py --model ${VLLM_MODEL} --tensor-parallel-size ${VLLM_TENSOR_PARALLEL_SIZE} --gpu-memory-utilization ${VLLM_GPU_MEMORY_UTILIZATION} --host ${VLLM_HOST} --port 8000"]
