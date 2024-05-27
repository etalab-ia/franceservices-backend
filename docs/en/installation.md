# Installation

## Models

Albert models are deployable with [VLLM](https://docs.vllm.ai/en/latest/). We provide an API to embed an Albert LLM as well as an embeddings model for the [Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation). For more information on the models, refer to the [modeles.md](./modeles.md) documentation.


### With Docker

* Build

```bash
docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./llm/Dockerfile ./llm
```

* Run

```bash
docker compose --env-file ./llm/.env.example --file ./llm/docker-compose.yml up --detach
```

> ⚠️ If you do not specify an embeddings model, the `/embeddings` endpoint of the API will return a 404 response and will be hidden in its automatic documentation (Swagger).

You can access the automatic documentation (Swagger) of the model API at [http://localhost:8000/docs](http://localhost:8000/docs).

* Without GPU: GPT4all

    If you don't have GPU, you will find in a [Dockerfile](../contrib/gpt4all/Dockerfile) to build the API image with GPT4All (instead of VLLM). This API is in the format of the previously described VLLM API but does not require the use of a GPU. However, this is maintained on a *best efforts* basis by the teams. Here are the current models available without GPU:

    - [AgentPublic/albert-tiny](https://huggingface.co/AgentPublic/albert-tiny)


### Locally

* Install
    ```bash
    pip install llm/.
    ln -s $(pwd)/pyalbert llm/pyalbert
    ```

* Run (example to deploy an Albert model with given settings)

    ```bash
    python3 llm/app.py --llm-hf-repo-id AgentPublic/albertlight-8b --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --models-dir ~/_models --host 0.0.0.0 --port 8088
    ```


## Databases 

Alert API uses three databases: a PostgreSQL database, an Elasticsearch database, and a Qdrant database. For more information on their usefulness, refer to the documentation [databases.md](./databases.md).

The Docker images for these databases are available on the official Docker registry, so no image build is necessary.


### Postgres

We recommend setting the *POSTGRES_STORAGE_DIR* environment variable to a local directory to ensure better data persistence.

* Run

    ```bash
    export PROJECT_NAME=postgres
    export POSTGRES_STORAGE_DIR=./data/postgres # configurer un dossier local

    docker compose --file ./databases/postgres/docker-compose.yml up --detach
    ```

### Vector stores (Elastic et Qdrant)

We recommend setting the *QDRANT_STORAGE_DIR* and *ELASTIC_STORAGE_DIR* environment variables to a local directory to ensure better data persistence.

> ⚠️ **Warning the folder mentioned in the ELASTIC_STORAGE_DIR variable must have rights 1000:1000.**

* Run
    ```bash
    export PROJECT_NAME=vector-store
    export QDRANT_STORAGE_DIR=./data/qdrant
    export ELASTIC_STORAGE_DIR=./data/elastic

    docker compose --file ./databases/vector_store/docker-compose.yml up --detach
    ```
