# Install

    pip install -r requirements.txt


### Gpt4all quantized model (for CPUs)

To run the quantized model, the model `"{model-name}.bin"` needs to be imported/copied in `api/app`.

### Vllm model (for GPUs)

You must be registered with `huggingface-cli` to download private models:

    huggingface-cli login --token $HF_ACCESS_TOKEN


### Download a model

#### Old version of deployment
- Fabrique model `python -c "from vllm import LLM; LLM(model='etalab-ia/fabrique-reference-2', download_dir='add_your_path')"`
- Albert model `python -c "from vllm import LLM; LLM(model='etalab-ia/albert-light', download_dir='add_your_path')"`

#### Newer version
Open python console
`python -c "from transformers import AutoTokenizer, AutoModel; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/fabrique-reference-2'); tokenizer.save_pretrained('add_your_path/fabrique-reference-2'); model=AutoModel.from_pretrained('etalab-ia/fabrique-reference-2'); model.save_pretrained('add_your_path/fabrique-reference-2') "`
`python -c "from transformers import AutoTokenizer, AutoModel; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/albert-light'); tokenizer.save_pretrained('add_your_path/albert-light'); model=AutoModel.from_pretrained('etalab-ia/albert-light'); model.save_pretrained('add_your_path/albert-light') "`


# Test

Install dev packages:

    pip install -r requirements_dev.txt


Run unit tests:

    pytest --cov=app --cov-report=html --cov-report=term-missing app/tests


Test the app locally:

    uvicorn app.main:app --reload


and in another terminal:

    python test.py


# Alembic

Create a new alembic (enpty) template version:

    PYTHONPATH=. alembic revision -m  "vXXX

Autogenerate a new alembic upgrade version script:

    PYTHONPATH=. alembic revision --autogenerate -m "vXXX"

Upgrade a database according to alemic revision:

    PYTHONPATH=. alembic upgrade head


# Production

If GPU is available, the vllm API is run separately with:

    python vllm_api.py --model etalab-ia/albert-light  --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --port 8000


Run the public API:

    uvicorn app.main:app --host 0.0.0.0 --port 8090 # --root-path /api/v2
    #gunicorn app.main:app  -w 2 -b 127.0.0.1:8090 --timeout 120



# Deploy

> En se placant à la racine du projet.

**Launch the reverse proxy**

This allows to route the incoming connections of the server. You can adapt the configuration file provided in [contrib/nginx](/contrib/nginx/).


**Launch the API database**

    # Launch postgres
    docker-compose -f contrib/postgres/docker-compose up


**Launch the search engine services**

    # Launch elasticsearch
    docker-compose -f contrib/docker/elasticsearch/docker-compose.yml up

    # Launch qdrant
    docker-compose -f contrib/docker/qdrant/docker-compose.yml up

Alternatively with docker only

    docker run --name elasticsearch -p 9202:9200 -p 9302:9300 -e discovery.type="single-node" -e xpack.security.enabled="false" -e ES_JAVA_OPTS="-Xms2g -Xmx2g" --mount source=vol-elasticsearch,target=/var/lib/elasticsearch/data -d docker.elastic.co/elasticsearch/elasticsearch:8.9.1
    docker run --name qdrant -p 6333:6333 -p 6334:6334 --mount source=vol-qdrant,target=/qdrant/storage -d qdrant/qdrant:v1.5.0


**download the corpus**

    ./pyalbert.py download_corpus
    ./pyalbert.py download_directory


**build the chunks**

    ./pyalbert.py make_chunks --structured _data/data.gouv/


**build the embeddings matrix**

    ./pyalbert.py make_embeddings


**feed the search engines / build the indexes**

    # Elasticsearch indexes
    ./pyalbert.py index experiences --index-type bm25
    ./pyalbert.py index sheets --index-type bm25
    ./pyalbert.py index chunks --index-type bm25

    # Qdrant indexes (aka collections)
    ./pyalbert.py index experiences --index-type e5
    ./pyalbert.py index chunks --index-type e5


The search API and the RAG should now be ready to be used.

**set up the mail server**

    To be completed

**possibily migrate 