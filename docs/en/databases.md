# Databases

Alert API uses three databases: a PostgreSQL database, an Elasticsearch database, and a Qdrant database.

The Docker images for these databases are available on the official Docker registry, so no image build is necessary.

## Postgres

The Postgres database has two uses:
- user management
- storage of conversation logs with the models

When the API is run in development mode, an SQLite database is used instead of the PostgreSQL database.

### Creating PostgreSQL database schemas with Alembic

[Alembic](https://alembic.sqlalchemy.org/en/latest/) is a database schema migration tool for the [SQLAlchemy](https://www.sqlalchemy.org/) ORM. After deploying the Postgres container, to create or upgrade the data schemas according to the latest models in the API code, run the following command:
```bash
PYTHONPATH=. alembic upgrade head
```
When the API is run from Docker, this command is automatically executed when the API starts from the `api/start.sh` file called by the `api/Dockerfile`.

### Backing up a PostgreSQL Database

After deploying the Postgres container, you can back up the database with the following command:
```bash
PGPASSWORD=<password> pg_dump --username postgres --data-only postgres" > my_dump.dump
```
...or, if you are using Docker:
```bash
docker exec -i <postgres-container-name> /bin/bash -c "PGPASSWORD=<password> pg_dump --username postgres --data-only postgres" > my_dump.dump
```

If you want to export the database schemas (in case you also want to rebuild the database), you can omit the `--data-only` option from the `pg_dump` command:
```bash
docker exec -i <postgres-container-name> /bin/bash -c "PGPASSWORD=<password> pg_dump --username postgres postgres" > my_dump.dump
```

### Restoring a Postgres Database

After deploying the Postgres container, you can restore the database from a dump with the following command:

```bash
docker exec -i <postgres-container-name> /bin/bash -c "PGPASSWORD=<password> psql --username postgres postgres" < my_dump.dump
```

## Vector stores: Elasticsearch et Qdrant

To feed models with knowledge bases ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), two databases need to be deployed:
- an [Elasticsearch](https://www.elastic.co/) database, which stores document corpuses and chunks of these documents
- a [Qdrant](https://qdrant.tech/) database, the vector store that holds embedding vectors

To install them, follow the [installation documentation](installation.md#vector-stores-elasticsearch-and-qdrant).
