# Installation

Ce tutoriel d'installation couvre les installations avec Docker comme en local, et est découpé en 3 parties :
1. [Déployer un modèle Albert](#déployer-un-modèle-albert)
2. [Déployer les bases de données](#déployer-les-bases-de-données)
3. [Déployer l'API](#déployer-lapi)

## Déployer un modèle Albert

Les modèles Albert sont déployables avec [VLLM](https://docs.vllm.ai/en/latest/). Nous mettons à disposition une "API LLM" (située dans `llm/`) permettant d'embarquer un LLM Albert ainsi qu'une modèle d'embeddings pour le [Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation).
Pour plus d'informations sur les modèles, référez-vous à la documentation sur les [modèles supportés](./models.md).

### Avec Docker

#### Build

* Avec [VLLM](https://docs.vllm.ai/en/latest/) :

```bash
docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./llm/Dockerfile ./llm
```

* Avec [GPT4All](https://gpt4all.io/), dans le cas sans GPU :

Si vous ne disposez pas de GPU, vous trouverez dans un [fichier Dockerfile](../../contrib/gpt4all/Dockerfile) pour build l'image de l'API avec GPT4All (à la place de VLLM). Cette API est sur le format de l'API VLLM précédement décrite mais ne nécessite pas utilisation de GPU. Toutefois, celle-ci est maintenu en *best efforts* par les équipes.
La commande pour build l'image est donc la suivante :

```bash
docker build --tag albert/llm:latest --build-context pyalbert=./pyalbert --file ./contrib/gpt4all/Dockerfile ./contrib/gpt4all
```

Les modèles disponibles sans GPU sont listés dans la [documentation sur les modèles](./models.md).

#### Run

```bash
docker compose --env-file ./llm/.env.example --file ./llm/docker-compose.yml up --detach
```

> ⚠️ Si vous ne spécifiez pas de modèle d'embeddings le endpoint de l'API `/embeddings` retournera une réponse 404 et il sera masqué dans la documentation automatique Swagger.

Vous pouvez accéder au à la documentation automatique (Swagger) de l'API du modèle sur [http://localhost:8000/docs](http://localhost:8000/docs).


### En local, sans Docker

* Install
    ```bash
    pip install llm/.
    ln -s $(pwd)/pyalbert llm/pyalbert
    ```

* Run (exemple pour mettre en service un modèle d'Albert sur des paramètrages donnés)

    ```bash
    python3 llm/app.py --llm-hf-repo-id AgentPublic/albertlight-8b --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --models-dir ~/_models --host 0.0.0.0 --port 8088
    ```


## Déployer les bases de données 

Le framework Albert nécessite trois bases de données : une base PostgreSQL, une base Elasticsearch et une base Qdrant. Pour plus d'information sur leur utilité, référez-vous à la documentation [databases.md](./databases.md).

Pour ces bases de données aucun build n'est nécessaire puisque les images Docker sont disponibles sur le registry Docker officiel.

### Postgres

Nous vous recommandons de configurer la variable d'environnement *POSTGRES_STORAGE_DIR* vers un repertoire local pour assurer une meilleure persistance des données.

* Run

    ```bash
    export PROJECT_NAME=postgres
    export POSTGRES_STORAGE_DIR=./data/postgres # configurer un dossier local

    docker compose --file ./databases/postgres/docker-compose.yml up --detach
    ```

### Vector stores (Elasticsearch et Qdrant)

Nous vous recommandons de configurer la variable d'environnement *QDRANT_STORAGE_DIR* et *ELASTIC_STORAGE_DIR* vers un repertoire local pour assurer une meilleure persistance des données.

> ⚠️ **Attention le dossier mentionné dans la variable ELASTIC_STORAGE_DIR doit avoir comme droits 1000:1000.** 

* Run
    ```bash
    export PROJECT_NAME=vector-store
    export QDRANT_STORAGE_DIR=./data/qdrant
    export ELASTIC_STORAGE_DIR=./data/elastic

    docker compose --file ./databases/vector_store/docker-compose.yml up --detach
    ```

## Déployer l'API

### Avec Docker

Assurez-vous que votre variable d'environnement `ENV` dans [pyalbert/.env](../pyalbert/.env) est égale à `dev` telle que `ENV="dev"`, puis lancez le conteneur de l'API :

```bash
docker compose --env-file ./pyalbert/.env.example --file ./api/docker-compose.yml up --detach
```

### En local, sans Docker

1. Installez les dépendances

```bash
cd api/
ln -s $(pwd)/../pyalbert pyalbert
pip install . pyalbert
```

2. Assurez-vous que votre variable d'environnement `ENV` dans [pyalbert/.env](../pyalbert/.env) est égale à `dev` telle que `ENV="dev"`


3. Créez le schéma de la base de données (sqlite en mode dev) en utilisant Alembic :

```bash
PYTHONPATH=. alembic upgrade head
```

4. Lancez l'API

```bash
uvicorn app.main:app --reload
```

5. Pour tester, vous pouvez accéder à la documentation automatique (Swagger) de l'API du modèle sur [http://localhost:8000/docs](http://localhost:8000/docs).

6. Exécutez les tests unitaires :

```bash
pytest app/tests
```

Ou, pour le support des rapports :

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```
