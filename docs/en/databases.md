# Databases

Alert API uses three databases: a PostgreSQL database, an Elasticsearch database, and a Qdrant database.

The Docker images for these databases are available on the official Docker registry, so no image build is necessary.

## Postgres

The Postgres database has two uses:
- user management
- storage of conversation logs with the models

When the API is run in development mode, an SQLite database is used instead of the PostgreSQL database.


### Database name

In order to partition the databases in test, dev or production mode, the name of the database is not the same depending on the `ENV` environment variable in the API's `.env` file.

When `ENV` is set to `unittest`, we are using the SQLite database. (no name to set)

When `ENV` is set to `dev`, the name of the PostgreSQL database is `postgres_dev`.

Otherwise, the name of the PostgreSQL database is `postgres`.

### Creating PostgreSQL database schemas with Alembic

[Alembic](https://alembic.sqlalchemy.org/en/latest/) is a database schema migration tool for the [SQLAlchemy](https://www.sqlalchemy.org/) ORM. After deploying the Postgres container, to create or upgrade the data schemas according to the latest models in the API code, run the following command:
```bash
PYTHONPATH=. alembic upgrade head
```
When the API is run from Docker, this command is automatically executed when the API starts from the `api/start.sh` file called by the `api/Dockerfile`.

### Backing up a PostgreSQL Database

You can back up the database with the following command:
```bash
PGPASSWORD=<password> pg_dump postgres -Fc --data-only --on-conflict-do-nothing --inserts --username postgres" > my_dump.dump
```
...or, if you are using Docker:
```bash
docker exec -i <postgres-container-name> pg_dump postgres -Fc --data-only --on-conflict-do-nothing --inserts --username postgres > my_dump.dump
```

### Restoring a Postgres Database

You can restore the database from a dump with the following command:
```bash
PGPASSWORD=<password> pg_restore --username postgres --dbname postgres --single-transaction --data-only my_dump.dump
```
...or, if you are using Docker:
```bash
docker exec -i <postgres-container-name> pg_restore -v --single-transaction --data-only --username postgres --dbname postgres < my_dump.dump
```

In case of an error like `sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "streams_pkey")` after a database restoration process, you can reset the sequences for each table that has an auto-incrementing primary key with the following command:
```bash
PGPASSWORD=<password> psql --username postgres --dbname postgres -c "
SELECT setval('api_tokens_id_seq', COALESCE((SELECT MAX(id)+1 FROM api_tokens), 1), false);
SELECT setval('chats_id_seq', COALESCE((SELECT MAX(id)+1 FROM chats), 1), false);
SELECT setval('feedbacks_id_seq', COALESCE((SELECT MAX(id)+1 FROM feedbacks), 1), false);
SELECT setval('password_reset_tokens_id_seq', COALESCE((SELECT MAX(id)+1 FROM password_reset_tokens), 1), false);
SELECT setval('sources_id_seq', COALESCE((SELECT MAX(id)+1 FROM sources), 1), false);
SELECT setval('streams_id_seq', COALESCE((SELECT MAX(id)+1 FROM streams), 1), false);
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id)+1 FROM users), 1), false);"
```

## Vector stores: Elasticsearch et Qdrant

To feed models with knowledge bases ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), two databases need to be deployed:
- an [Elasticsearch](https://www.elastic.co/) database, which stores document corpuses and chunks of these documents
- a [Qdrant](https://qdrant.tech/) database, the vector store that holds embedding vectors

To install them, follow the [installation documentation](installation.md#vector-stores-elasticsearch-and-qdrant).
