FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . /code
ARG VLLM_MODEL
ENV VLLM_MODEL ${VLLM_MODEL}
ARG VLLM_TENSOR_PARALLEL_SIZE=1
ENV VLLM_TENSOR_PARALLEL_SIZE ${VLLM_TENSOR_PARALLEL_SIZE}
ARG VLLM_GPU_MEMORY_UTILIZATION=0.4
ENV VLLM_GPU_MEMORY_UTILIZATION ${VLLM_GPU_MEMORY_UTILIZATION}
ARG VLLM_HOST=0.0.0.0
ENV VLLM_HOST ${VLLM_HOST}
ARG VLLM_PORT
ENV VLLM_PORT ${VLLM_PORT}
CMD ["sh", "-c", "python3 app.py --model ${VLLM_MODEL} --tensor-parallel-size ${VLLM_TENSOR_PARALLEL_SIZE} --gpu-memory-utilization ${VLLM_GPU_MEMORY_UTILIZATION} --host ${VLLM_HOST} --port ${VLLM_PORT}"]
