# Albert

## Préambule

Ce projet contient le code source d'Albert, l'agent conversationnel de l'administration française, développé par les équipes du Datalab de la Direction Interministérielle du Numérique (DINUM). Albert a été créé pour citer ses sources et est spécialisé pour répondre à des questions administratives en français.

Albert est encore en développement et en amélioration continue. Il est conçu pour être utilisé sous la responsabilité d'un agent public.

## Installation

Variables d'environnement. Créez un fichier .ENV.
>>> TODO

Environnement python (pensez à modifier le .gitignore si vous utilisez un nom différent de `venv` pour votre environnement) :
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
``

Il est nécessaire de lancer les commandes `pyalbert` afin d'importer et structurer les sources de données et les modèles utilisés par Albert. La documentation est accessible via la commande `./pyablert.py --help` :

1. [x] importer le corpus -- `pyalbert download`.



--- ENGLISH ---
# LIA - Legal Information Assistant

This project contains the source code for LIA (***L**egal **I**nformation **A**ssistant*), also known as *Albert*.
*Albert* is a conversational agent, using LLM models fine-tuned mainly on official French data sources.


## Pre-requisite: run PyAlbert

Use the CLI tool `pyalbert` to build necessary datasets and models. The documentation can be viewed by running `./pyalbert.py --help`:

1. [x] fetching the French data corpus -- `pyalbert download`.
2. [x] pre-processing and formatting the data corpus -- `pyalbert make_chunks`.
3. [x] feed the <index/vector> search engines -- `pyalbert index`
3. [ ] fine-tuning the LLMs. Independents script located in the folder `finetuning/`.
4. [x] evaluating the models -- `pyalbert evaluate`.

**NOTE**: Step 3 hides a step which consists of building the embeddings from pieces of text (chunks). This step is highly GPU intensive and can be achieves with the command `pyalbert make_embeddings`. This command will create the data required for vector indexes build with the option `pyalbert index --index-type e5`. You can see the [deploy section](/api/README.md#deploy) of the API Readme to see all the step involved in the build process.

### Install 

```bash
pip install -r requirements.txt
```
...or using `pyproject.toml` via a modern Python manager like [pip-tools](https://github.com/jazzband/pip-tools), [PDM](https://pdm.fming.dev/), [Poetry](https://python-poetry.org/docs/cli/#export) or [hatch](https://hatch.pypa.io/)


### Export pinned dependencies from pyproject.toml to requirements.txt

Using [PDM](https://pdm.fming.dev/
```bash
pdm export --output requirements.txt --production --without-hashes
```

Using [Poetry](https://python-poetry.org/docs/cli/#export)
```bash
poetry export --without-hashes -f requirements.txt -o requirements.txt
```

Using [pip-tools](https://github.com/jazzband/pip-tools)
```bash
pip-compile --output-file requirements.txt requirements.in
```

## Albert APIs

The API is built upon multiple services :

* The LLM API (GPU intensive): This API is managed by vllm, and the executable is located in `api_vllm/`.
* A vector database (for semantic search), based on Qdrant.
* A search-engine (for full-text search), based on ElasticSearch.
* The main/exposed API: the app executable and configurations are located in the folder `api/`.

See the dedicated [Readme](/api/README.md) for more information about the API configuration, testing, and  **deployment**.


## Folder structure

- \_data/: contains volatile and large data downloaded by pyalbert.
- api/: the code of the main API.
- api_vllm/: the code of the vllm API.
- commons/: code shared by different modules, such as the Albert API client, and prompt encoder.
- sourcing/: code behind `pyalbert download ...` and `pyalbert make_chunks`.
- ir/: code behind `pyalbert index ...`
- evaluation/: code behind `pyalbert evaluate ...`
- scripts/: Various tests scripts, not integrated to pyalbert (yet).
- tests/: Various util scripts, not integrated to pyalbert (yet).
- contrib/: configuration files to deploy Albert.
- docs/: documentation resources.
- wiki/: wiki resources.


## Docker debug commands cheat sheet

List containers in a friendly manner:
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

Display error logs for a specific container:
```bash
docker logs [CONTAINER_NAME]
```

Access shell in an already running container:
```bash
docker exec -e API_URL=[API_URL] -e FRONT_URL=[API_URL] --gpus all --network="host" -it --rm -p 8090:8090 --name miaou-api-v2 registry.gitlab.com/etalab-datalab/llm/albert-backend/api-v2:latest /bin/sh
```

Force stopping and removing a running container:
```bash
docker rm -f [CONTAINER_NAME]
```

Start a container in interactive mode for debug, while automatically removing it after exiting:
```bash
docker run -e API_URL=[API_URL] -e FRONT_URL=[API_URL] --rm --gpus all --network="host" -it -p 8090:8090 --name miaou-api-v2 registry.gitlab.com/etalab-datalab/llm/albert-backend/api-v2:latest /bin/sh
```


## Contributing

TODO


## License

TODO


## Acknowledgements

TODO
