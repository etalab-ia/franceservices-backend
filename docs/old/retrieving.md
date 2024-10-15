
## Working with faiss index

```
ds = datasets.load_dataset('crime_and_punish', split='train')
ds_with_embeddings = ds.map(lambda example: {'embeddings': embed(example['line']}))
ds_with_embeddings.add_faiss_index(column='embeddings')
# query
scores, retrieved_examples = ds_with_embeddings.get_nearest_examples('embeddings', embed('my new query'), k=10)
# save index
ds_with_embeddings.save_faiss_index('embeddings', 'my_index.faiss')

ds = datasets.load_dataset('crime_and_punish', split='train')
# load index
ds.load_faiss_index('embeddings', 'my_index.faiss')
# query
scores, retrieved_examples = ds.get_nearest_examples('embeddings', embed('my new query'), k=10)
```

# Working with elasticsearch

### Docker

     docker run -d -p 9200:9200 -p 9300:9300 --name elasticsearch docker.elastic.co/elasticsearch/elasticsearch:8.9.1

     docker run -it --rm -p 7700:7700 -v $(pwd)/_data/meili_data:/meili_data getmeili/meilisearch:v1.3

### Manually 

Install

```
%%bash

wget -q https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-oss-7.9.2-linux-x86_64.tar.gz
wget -q https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-oss-7.9.2-linux-x86_64.tar.gz.sha512
tar -xzf elasticsearch-oss-7.9.2-linux-x86_64.tar.gz
sudo chown -R daemon:daemon elasticsearch-7.9.2/
shasum -a 512 -c elasticsearch-oss-7.9.2-linux-x86_64.tar.gz.sha512 
```


Run
```
%%bash --bg

sudo -H -u daemon elasticsearch-7.9.2/bin/elasticsearch
```

Test
```
%%bash

ps -ef | grep elasticsearch
curl -sX GET "localhost:9200/"
```

Example usage with huggingface dataset: https://huggingface.co/docs/datasets/v2.14.4/faiss_es#elasticsearch


# Working with Meilisearch

Install

     docker run -it --rm -p 7700:7700 -v $(pwd)/_data/meili_data:/meili_data getmeili/meilisearch:v1.3

Browser client on: http://localhost:7700/
