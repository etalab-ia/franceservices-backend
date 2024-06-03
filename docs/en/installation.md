# Installation

This installation tutorial covers installations with Docker as well as locally, and is divided into 3 parts:
1. [Deploy an Albert model](#deploy-an-albert-model)
2. [Deploy databases](#deploy-databases)
3. [Deploy the API](#deploy-the-api)

## Deploy an Albert model

Albert models are deployable with [VLLM](https://docs.vllm.ai/en/latest/). We provide an "LLM API" (located in `llm/`) to embed an Albert LLM as well as an embeddings model for the [Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation). For more information on the models, refer to the [documentation about supported models](./models.md).

### With Docker

#### Build

* With [VLLM](https://docs.vllm.ai/en/latest/):

```bash
docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./llm/Dockerfile ./llm
```

* With [GPT4All](https://gpt4all.io/), in the case without GPU:

If you don't have GPU, you will find in a [Dockerfile](../../contrib/gpt4all/Dockerfile) to build the API image with GPT4All (instead of VLLM). This API is in the format of the previously described VLLM API but does not require the use of a GPU. However, this is maintained on a *best efforts* basis by the teams.

```bash
docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./contrib/gpt4all/Dockerfile ./contrib/gpt4all
```

The models currently available without GPU are listed in the [models documentation](./models.md).

#### Run

```bash
docker compose --env-file ./llm/.env.example --file ./llm/docker-compose.yml up --detach
```

> ⚠️ If you do not specify an embeddings model, the `/embeddings` endpoint of the API will return a 404 response and will be hidden in its automatic documentation (Swagger).

You can access the automatic documentation (Swagger) of the model API at [http://localhost:8000/docs](http://localhost:8000/docs).


### Locally, without Docker

* Install
    ```bash
    pip install llm/.
    ln -s $(pwd)/pyalbert llm/pyalbert
    ```

* Run (example to deploy an Albert model with given settings)

    ```bash
    python3 llm/app.py --llm-hf-repo-id AgentPublic/albertlight-8b --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --models-dir ~/_models --host 0.0.0.0 --port 8088
    ```


## Deploy databases 

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

### Vector stores (Elasticsearch and Qdrant)

We recommend setting the *QDRANT_STORAGE_DIR* and *ELASTIC_STORAGE_DIR* environment variables to a local directory to ensure better data persistence.

> ⚠️ **Warning the folder mentioned in the ELASTIC_STORAGE_DIR variable must have rights 1000:1000.**

* Run
    ```bash
    export PROJECT_NAME=vector-store
    export QDRANT_STORAGE_DIR=./data/qdrant
    export ELASTIC_STORAGE_DIR=./data/elastic

    docker compose --file ./databases/vector_store/docker-compose.yml up --detach
    ```

## Deploy the API

### With Docker

Make sure your `ENV` environment variable in [pyalbert/.env](../pyalbert/.env) is set to `dev` such as `ENV="dev"`, and run:

```bash
docker compose --env-file ./pyalbert/.env.example --file ./api/docker-compose.yml up --detach
```

### Locally, without Docker

1. Install the dependencies:

```bash
cd api/
ln -s $(pwd)/../pyalbert pyalbert
pip install . pyalbert
```

2. Ensure you are using dev environement: you should have `ENV=dev` in the file [pyalbert/.env](../pyalbert/.env)

3. Create the database schema (sqlite in dev mode) using Alembic:

```bash
PYTHONPATH=. alembic upgrade head
```

4. Start the API locally:

```bash
uvicorn app.main:app --reload
```

5. To test, you can access the automatic documentation (Swagger) of the model API at [http://localhost:8000/docs](http://localhost:8000/docs)

6. Run unit tests:

```bash
pytest app/tests
```

Or, for report options:

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```