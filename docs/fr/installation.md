# Installation

## Modèles

Les modèles Albert sont déployables avec [VLLM](https://docs.vllm.ai/en/latest/). Nous mettons à disposition une API permettant d'embarquer un LLM Albert ainsi qu'une modèle d'embeddings pour le [Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation). Pour plus d'informations sur les modèles, référez-vous à la documentation [modeles.md](./modeles.md).

### Avec Docker

* Build

    Avec [VLLM](https://docs.vllm.ai/en/latest/) :
    ```bash
    docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./llm/Dockerfile ./llm
    ```

    Avec GPT4All (dans le cas sans GPU) :
    ```bash
    docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./contrib/gpt4all/Dockerfile ./contrib/gpt4all
    ```

* Run

    ```bash
    docker compose --env-file ./llm/.env.example --file ./llm/docker-compose.yml up --detach
    ```

    > ⚠️ Si vous ne spécifiez pas de modèle d'embeddings le endpoint de l'API `/embeddings` retournera une réponse 404 et il sera masqué dans la documentation automatique Swagger.

Vous pouvez accéder au à la documentation automatique (Swagger) de l'API du modèle sur [http://localhost:8000/docs](http://localhost:8000/docs).

* Sans GPU : GPT4all

    Si vous ne disposez pas de GPU, vous trouverez dans un [fichier Dockerfile](../../contrib/gpt4all/Dockerfile) pour build l'image de l'API avec GPT4All (à la place de VLLM). Cette API est sur le format de l'API VLLM précédement décrite mais ne nécessite pas utilisation de GPU. Toutefois, celle-ci est maintenu en *best efforts* par les équipes. Voici les modèles actuels disponibles sans GPU :

    - [AgentPublic/albert-tiny](https://huggingface.co/AgentPublic/albert-tiny)


### En local

* Install
    ```bash
    pip install llm/.
    ln -s $(pwd)/pyalbert llm/pyalbert
    ```

* Run (exemple pour mettre en service un modèle d'Albert sur des paramètrages donnés)

    ```bash
    python3 llm/app.py --llm-hf-repo-id AgentPublic/albertlight-8b --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --models-dir ~/_models --host 0.0.0.0 --port 8088
    ```


## Databases 

Le framework Albert nécessite trois bases de données : une base PostgreSQL, une base ElasticSearch et une base Qdrant. Pour plus d'information sur leur utilité, référez-vous à la documentation [databases.md](./databases.md).

Pour ces bases de données aucun build n'est nécessaire puisque les images Docker sont disponibles sur le registry Docker officiel.

### Postgres

Nous vous recommandons de configurer la variable d'environnement *POSTGRES_STORAGE_DIR* vers un repertoire local pour assurer une meilleure persistance des données.

* Run

    ```bash
    export PROJECT_NAME=postgres
    export POSTGRES_STORAGE_DIR=./data/postgres # configurer un dossier local

    docker compose --file ./databases/postgres/docker-compose.yml up --detach
    ```

### Vector stores (Elastic et Qdrant)

Nous vous recommandons de configurer la variable d'environnement *QDRANT_STORAGE_DIR* et *ELASTIC_STORAGE_DIR* vers un repertoire local pour assurer une meilleure persistance des données.

> ⚠️ **Attention le dossier mentionné dans la variable ELASTIC_STORAGE_DIR doit avoir comme droits 1000:1000.** 

* Run
    ```bash
    export PROJECT_NAME=vector-store
    export QDRANT_STORAGE_DIR=./data/qdrant
    export ELASTIC_STORAGE_DIR=./data/elastic

    docker compose --file ./databases/vector_store/docker-compose.yml up --detach
    ```
