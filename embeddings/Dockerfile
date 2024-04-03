FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /code
ADD ./app.py ./core.py ./pyproject.toml .
COPY --from=pyalbert . ./pyalbert
RUN pip install --no-cache-dir --upgrade /code/.
