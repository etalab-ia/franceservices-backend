# Install

```
pip install -r requirements.txt
```

### GPT4all quantized model (for CPUs)

To run the quantized model, the model `"{model-name}.bin"` needs to be imported/copied in `api/app`.

### vllm model (for GPUs)

You must be registered with `huggingface-cli` to download private models:
```
huggingface-cli login --token $HF_ACCESS_TOKEN
```

Download a model:
- Fabrique model `python -c "from vllm import LLM; LLM(model='etalab-ia/fabrique-reference-2')"`
- Albert model python -c `"from vllm import LLM; LLM(model='etalab-ia/albert-light')"`


# Test

Install dev packages:
```
pip install -r requirements_dev.txt
```

Run unit tests:
```
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```

Test the app locally:
```
uvicorn app.main:app --reload
```
In another terminal:
```
python test.py
```


# Deploy

If GPU is available, the vllm API is run separately with:
```
python vllm_api.py --model etalab-ia/albert-light  --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --port 8000
```

Run the public API:
```
gunicorn -w 2 -b 127.0.0.1:4000 app_spp:app --timeout 120
```


# Launching search engine services

> En se placant à la racine du projet.

```
# Launch elasticsearch:
docker-compose -f docker/elasticsearch/docker-compose.yml up

# Launch qdrant:
docker-compose -f docker/qdrant/docker-compose.yml up
```

Alternatively with docker only

    docker run --name elasticsearch -p 9202:9200 -p 9302:9300 -e discovery.type="single-node" -e xpack.security.enabled="false" -e ES_JAVA_OPTS="-Xms2g -Xmx2g" --mount source=vol-elasticsearch,target=/var/lib/elasticsearch/data -d docker.elastic.co/elasticsearch/elasticsearch:8.9.1

    docker run --name qdrant -p 6333:6333 -p 6334:6334 --mount source=vol-qdrant,target=/qdrant/storage -d qdrant/qdrant:v1.5.0

# Build the indexes

> En se placant à la racine du projet.

1. Download the set of user experiences:

```
wget https://opendata.plus.transformation.gouv.fr/api/explore/v2.1/catalog/datasets/export-expa-c-riences/exports/json -O _data/export-expa-c-riences.json
```

2. Download the sheets from `service-public.fr`:
```
mkdir -p _data/data.gouv
wget https://lecomarquage.service-public.fr/vdd/3.3/part/zip/vosdroits-latest.zip -O _data/data.gouv/vosdroits-latest.zip
cd _data/data.gouv
unzip vosdroits-latest.zip -d vos-droits-et-demarche
wget https://github.com/SocialGouv/fiches-travail-data/raw/master/data/fiches-travail.json -O _data/fiches-travail.json
```

3. Build the chunks (can be ignored if `_data/sheets_as_chunks.json` already exists):
```
./gpt.py make_chunks --structured _data/data.gouv/vos-droits-et-demarche
```

4. Build the indexes:
```
# Elasticsearch indexes
./gpt.py index experiences --index-type bm25
./gpt.py index sheets --index-type bm25
./gpt.py index chunks --index-type bm25

# Embeddings indexes (aka collections)
# @WARNING: requires data to be generated in _data/embeddings/ which is built outside for now as its convenient to run it in a GPU (in a colab notebook).
# see notebooks/bootstrap_embeddings.ipynb or run: ./gpt.py make_embeddings
./gpt.py index experiences --index-type e5
./gpt.py index chunks --index-type e5
```
