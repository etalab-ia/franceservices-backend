# Install

    pip install -r requirements.txt


### GPT4all quantized model (for CPUs)

To run the quantized model, the model "{model-name}.bin" needs to be imported/copied in `api/model`

Edit the parameter app_spp.py:Num_TREADS depending on your available ressources.


### vllm model (for GPUs)

You must be registered with huggingface-cli to download private models:

    huggingface-cli login --token $HF_ACCESS_TOKEN

Download a model

    python -c "from vllm import LLM; LLM(model="etalab-ia/fabrique-miaou")"


# Deploy

If GPU is available, the vllm API is ran separately with:

    python3 vllm_api.py --model etalab-ia/fabrique-miaou  --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --port 8000


Run the public API:

    gunicorn -w 2 -b 127.0.0.1:4000 app_spp:app --timeout 120


# Launching search engine services

> En se placant à la racine du projet.


    # Launch elasticsearch
    docker-compose -f docker/elasticsearch/docker-compose.yml up

    # Launch qdrant
    docker-compose -f docker/qdrant/docker-compose.yml up


# Build the indexes

> En se placant à la racine du projet.

1. Download the set of user experiences:

    wget https://opendata.plus.transformation.gouv.fr/api/explore/v2.1/catalog/datasets/export-expa-c-riences/exports/json -O "_data/export-expa-c-riences.json"

2. Download the sheets from service-public.fr

    mkdir -p _data/data.gouv
    wget https://lecomarquage.service-public.fr/vdd/3.3/part/zip/vosdroits-latest.zip -O "_data/data.gouv/vosdroits-latest.zip"
    cd _data/data.gouv
    unzip vosdroits-latest.zip -d vos-droits-et-demarche

3. Build the chunks (can be ignored if `_data/xmlfiles_as_chunks.json` already exists)

    ./gpt.py make_chunks --structured _data/data.gouv/vos-droits-et-demarche

4. Build the indexes

    # Elasticsearch indexes
    ./gpt.py index experiences --index-type bm25
    ./gpt.py index sheets --index-type bm25
    ./gpt.py index chunks --index-type bm25

    # Embeddings indexes (aka collections)
    # @WARNING: requires the file _data/embeddings_e5_experiences.npy and _data/embeddings_e5_chunks.npy which is built outside for now (in a colab notebook). 
    # see notebooks/bootstrap_embeddings.ipynb 
    ./gpt.py index experiences --index-type e5
    ./gpt.py index chunks --index-type e5


# Reverse proxy

### Nginx

```/etc/nginx/site-available/legal-assistant
server {
    listen 80;

    server_name gpt.datascience.etalab.studio;

    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;

    location / {
        proxy_pass         http://127.0.0.1:4000/;
        proxy_redirect     off;
        proxy_buffering off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;
    }
}
```
