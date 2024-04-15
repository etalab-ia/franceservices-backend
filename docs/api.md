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

```
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


