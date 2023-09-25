FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY . /code
CMD ["python3", "app.py", "--model", "/var/lib/huggingface/fabrique-miaou", "--tensor-parallel-size", "1", "--gpu-memory-utilization", "0.4", "--host", "0.0.0.0", "--port", "8081"]
# CMD ["python3", "app.py", "--model", "/var/lib/huggingface/fabrique-reference", "--tensor-parallel-size", "1", "--gpu-memory-utilization", "0.4", "--host", "0.0.0.0", "--port", "8081"]
