# Contributing

The project is open source, under the [MIT license](LICENCE). All contributions are welcome, in the form of pull requests or issue openings on [GitHub](https://github.com/etalab-ia/albert).

## Updating PostgreSQL database schemas with Alembic

If your code updates data models, it is necessary to create the corresponding PostgreSQL database migration script, and to commit this script with your modifications so that other contributors and deployment environments can update their databases automatically.

[Alembic](https://alembic.sqlalchemy.org/en/latest/) is a database schema migration tool for the [SQLAlchemy](https://www.sqlalchemy.org/) ORM, which allows you to generate this script automatically. To do this:

1. Before creating any new migration, a good practice is to check that your PostgreSQL database schema is up to date with previous migrations. Look at the revision number (`revision`) of the last migration in the `api/alembic/versions` folder, and compare it with the value of `version_num` in the `alembic_version` table of your database. If these two values are identical, your database is up to date. If they are different, you need to update your database with the following command:
```bash
PYTHONPATH=. alembic upgrade head
```

2. Create your migration script corresponding to your data model changes with the following command (run from `/api`):
```bash
PYTHONPATH=. alembic revision --autogenerate
```
A new migration script will be created in the `api/alembic/versions` folder.

3. Check the contents of the created migration script, and if necessary, modify it to suit your needs. Don't forget to commit this file to the same commit as your data model modifications.

4. Apply the migration to your database with the following command:
```bash
PYTHONPATH=. alembic upgrade head
```
This command will update your PostgreSQL database with the latest schema changes, and update the `alembic_version` table with the revision number of this latest migration to indicate that your database is up to date.

## Before any Pull Request

Before contributing to the repository, it is necessary to initialize the pre-commit hooks:
```bash
pre-commit install
```
Once this is done, code formatting and linting, as well as import sorting, will be automatically checked before each commit.

If you cannot use pre-commit, it is necessary to format, lint, and sort imports with [Ruff](https://docs.astral.sh/ruff/) before committing:
```bash
ruff check --fix --select I .
```
