# Albert API

## Execution locale (Draft)

- Installez les requirements :

    ```bash
    cd api
    pip install .
    ```

    Assurez-vous dans un premier temps que votre variable d'environnement `ENV` présent dans [api/app/.env](../api/app/.env) est égale à `dev` telle que: `ENV="dev"`.

### Modèle quantisé

- 1: Lancez l'API du modèle :

    - Via GPT4All: Lancer l'API du modèle quantisé sur CPU

        Cas d'utilisation: Si vous n'avez pas de carte graphique ou que votre carte graphique n'est pas compatible avec CUDA.

    - Via VLLM: Lancer l'API du modèle quantisé sur GPU

        Cas d'utilisation: Si vous avez une carte graphique NVIDIA compatible avec CUDA

Pour déployer l'API du modèle via le module de votre choix, allez voir la section 'LLM' du README du [deploiement](../docs/deploiement/README.md)

- 2: Lancez ensuite l'API en local :

    ```bash
    cd api
    source start.sh
    ```


- 3: Testez le modèle :

```
```

### Télécharegment d'un modèle

#### Téléchargement d'un modèle selon la version dépréciée

- Par exemple, pour le modèle Fabrique Reference 2 :
```bash
python3 -c "from vllm import LLM; LLM(model='etalab-ia/fabrique-reference-2', download_dir='add_your_path')"
```
- Par exemple, pour le modèle Albert Light :
```bash
python3 -c "from vllm import LLM; LLM(model='etalab-ia/albert-light', download_dir='add_your_path')"
```

#### Téléchargement d'un modèle selon la version actuelle

- Par exemple, pour le modèle Fabrique Reference 2 :
```bash
python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/fabrique-reference-2'); tokenizer.save_pretrained('add_your_path/fabrique-reference-2'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/fabrique-reference-2'); model.save_pretrained('add_your_path/fabrique-reference-2') "
```

- Par exemple, pour le modèle Albert Light :
```bash
python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/albert-light'); tokenizer.save_pretrained('add_your_path/albert-light'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/albert-light'); model.save_pretrained('add_your_path/albert-light') "
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

Create a new Alembic (empty) template version:

    PYTHONPATH=. alembic revision -m  "vXXX"

Autogenerate a new alembic upgrade version script:

    PYTHONPATH=. alembic revision --autogenerate -m "vXXX"

Upgrade a database according to alemic revision:

    PYTHONPATH=. alembic upgrade head

## Deploy

**set up the mail server**

    To be completed

**possibily migrate 
