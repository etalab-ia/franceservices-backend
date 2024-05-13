# Databases

## Postgres

La base de données Postgres à 2 usages : la gestion des utilisateurs et le stockage des logs du modèle.

### Restaurer une base postgres

Après avoir déployer le container postgres, vous pouvez restaurer la base à partir d'un dump avec la commande suivante :

```bash
docker exec -i postgres-postgres-1 /bin/bash -c "PGPASSWORD=<password> psql --username postgres postgres" < my_dump.dump
```

## Vector stores

Pour alimenter les modèles à des bases de connaissances ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), deux bases de données sont à déployer : une base Elasticsearch et une base de données Qdrant. Pour savoir comme les installer, référez-vous à la documentation [installation.md](installation.md).

La base ElasticSearch stocke les corpus de documents et les chunks de ces documents. La base Qdrant est une base vectorielle qui stocke les vecteurs d'embeddings.
