FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# to export pyalbert as a python package
ENV PYTHONPATH="$PYTHONPATH:/code"

# add pyproject before the rest of the code to cache the pip install
ADD ./pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip && pip install --no-cache-dir .

# add the rest of the code
ADD . .
COPY --from=pyalbert . ./pyalbert
