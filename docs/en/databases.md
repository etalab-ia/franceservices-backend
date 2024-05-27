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

### Backing up a PostgreSQL Database

After deploying the Postgres container, you can back up the database with the following command:
```bash
docker exec -i postgres-postgres-1 /bin/bash -c "PGPASSWORD=<password> pg_dump --username postgres postgres" > my_dump.dump
```

### Restoring a Postgres Database

After deploying the Postgres container, you can restore the database from a dump with the following command:

```bash
docker exec -i postgres-postgres-1 /bin/bash -c "PGPASSWORD=<password> psql --username postgres postgres" < my_dump.dump
```

## Vector stores: Elastic et Qdrant

To feed models with knowledge bases ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), two databases need to be deployed:
- an Elasticsearch database, which stores document corpuses and chunks of these documents
- a Qdrant database, the vector store that holds embedding vectors

To know how to install them, refer to the documentation [installation.md](installation.md).
