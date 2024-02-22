# Albert API

## Execution locale (Draft)

- Installez les requirements:

    ```bash
    cd api
    pip install -r requirements.txt
    ```
    ...ou en utilisant `pyproject.toml` via un Python manager moderne comme [pip-tools](https://github.com/jazzband/pip-tools), [PDM](https://pdm.fming.dev/), [Poetry](https://python-poetry.org/docs/cli/#export) ou [hatch](https://hatch.pypa.io/)

    Assurez-vous dans un premier temps que votre variable d'environnement `ENV` présent dans [api/app/.env](../api/app/.env) est égale à `dev` telle que: `ENV="dev"`.

### Modèle quantisé

- 1: Lancez l'API du modèle:

    - Via GPT4All: Lancer l'API du modèle quantisé sur CPU

        Cas d'utilisation: Si vous n'avez pas de carte graphique ou que votre carte graphique n'est pas compatible avec CUDA.

    - Via VLLM: Lancer l'API du modèle quantisé sur GPU

        Cas d'utilisation: Si vous avez une carte graphique NVIDIA compatible avec CUDA

Pour déployer l'API du modèle via le module de votre choix, allez voir la section 'LLM' du README du [deploiement](../docs/deploiement/README.md)

- 2: Lancez ensuite l'API en local:

    ```bash
    cd api
    source start.sh
    ```


- 3: Testez le modèle:

    Le fichier [test.py](../api/test.py) permet de tester l'endpoint `stream` de l'api du modèle. 
    Vous pouvez alors utliser le modèle et generér un output en fonction des paramètres en entrée.
    Les paramètres en entrée sont configurables dans la variable `data` au début du code.
    La variable `data` est un dictionnaire où chaque clé correspond à un paramètre.

    - Description non exhaustive des paramètres : (cf [stream.py](../api/app/schemas/stream.py) pour la liste complète)

        - `model_name` : Par defaut: 'fabrique-reference'. (cf: [models.md](../docs/models.md) pour la liste complète)
        - `user_text` (si `model_name`==`fabrique-reference`): Requête de l'utilisateur. L'input que vous donnez au modèle. 
        - `query` (si `model_name`==`albert-light`): Requête de l'utilisateur. L'input que vous donnez au modèle. 
        - `sources` : Restreint la liste des sources à rechercher (en mode RAG). ex: ["travail-emploi"]
        - `should_sids` : Ajouter le document qui doit correspondre (en mode RAG). ex: ["F35789"]
        - `must_not_sids` (optionnel): Filtre les documents qui ne doivent pas correspondre (en mode RAG). ex: ["F35789"]
        - `postprocessing` (optionnel): Liste des étapes de post processing à appliquer au texte generé. ex :  ["check_url", "check_mail", "check_number"].
            Pour utiliser cette feature, n'oubliez pas de télécharger la whitelist via le module `pyalbert` (cf [albert.py](../pyalbert/albert.py)) et d'entrer le path du fichier de whitelist téléchargé dans la variable d'environnement `API_WHITELIST_FILE` dans le fichier [api/app/.env](../api/app/.env).

    Executez enfin dans une nouvelle console:

    ```bash
    python test.py
    ```

### Download a model

#### Old version of deployment

- Fabrique model
```bash
python -c "from vllm import LLM; LLM(model='etalab-ia/fabrique-reference-2', download_dir='add_your_path')"
```
- Albert model
```bash
python -c "from vllm import LLM; LLM(model='etalab-ia/albert-light', download_dir='add_your_path')"
```

#### Newer version

Open python console
```bash
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/fabrique-reference-2'); tokenizer.save_pretrained('add_your_path/fabrique-reference-2'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/fabrique-reference-2'); model.save_pretrained('add_your_path/fabrique-reference-2') "
```

```bash
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/albert-light'); tokenizer.save_pretrained('add_your_path/albert-light'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/albert-light'); model.save_pretrained('add_your_path/albert-light') "
```

## Tests unitaires de l'API

Lancer les test unitaires :
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```

Lancer l'API localement...
```bash
uvicorn app.main:app --reload
```

...puis les tests unitaires en parallèle dans un autre terminal :
```bash
python test.py
```

## Alembic

Create a new alembic (empty) template version:

    PYTHONPATH=. alembic revision -m  "vXXX"

Autogenerate a new alembic upgrade version script:

    PYTHONPATH=. alembic revision --autogenerate -m "vXXX"

Upgrade a database according to alemic revision:

    PYTHONPATH=. alembic upgrade head

## Deploy

**set up the mail server**

    To be completed

**possibily migrate 


## Export pinned dependencies from pyproject.toml to requirements.txt

Using [PDM](https://pdm.fming.dev/)
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


################# OLD documentation
# API

> @obsolete since commit 6342af5
> See the openapi generated by fastapi instead.

### Fabrique LLM Routes

> **POST /api/fabrique**

Register configuration for "fabrique" text generation.

Headers:
```
Content-type: application/x-www-form-urlencoded  
```

Params:  
```
user_text(required): string : the user/civil experience to be answered
context: string : prompt information (need better doc @pclanglais ?)
institution: string : should be automatically added...
links: string : should be automatically added...
temperature: number between 0 and 1 : the orignalality of the answer (0: deterministic, 1: more creative)
```

Note: the answer result can then be obtained with `fabrique_stream`


> **GET /api/fabrique_stream**

Fabrique text answer generation.  
Server-sent stream like content.  
https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events


> **GET /api/fabrique_stop**

Stop a Fabrique text stream generation.

### Search Engines Routes

> **POST /api/search/{index}**

Search most relevant from a given {index}.

{index} can be:
- experiences: search the most relevant user experiences.
- sheets: search the most relevant sheets from service-public.fr.
- chunks: search the msot relevant chunks.

Headers:
```
Content-type: application/json
```

Params:  
```
q(required): string: search query
n(default=3): integer: max document to return
similarity(default=bm25) : string : similarity algorithm. Possible values : bm25, bucket, e5.
institution: string : Filter the search with the given institution (correspond to the field `intitule_typologie_1`) 
```

Returns: A Json list of result object ->  

For index=experiences:
```json
{
    "title" : "Title of the experience",
    "description" : "The user experience",
    "intitule_typologie_1" : "where it comes from"
    "reponse_structure_1" : "see https://opendata.plus.transformation.gouv.fr/explore/dataset/export-expa-c-riences/information"
}
```

For index=sheets
```json
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
}
```

For index=chunks
```json
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
    "text" : "The text part of the sheet (the chunk)"
    "context" : "The context of the chunk (successive chapter/sub-chapter/situation titles if any)"
}
```

### Misc

> **GET /api/institutions*

Get a list of known institutions.

Returns: A Json list of string.