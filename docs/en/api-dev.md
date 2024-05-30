# To run the Albert API locally (dev mode)

1. Install the dependencies:

```bash
cd api/
ln -s $(pwd)/../pyalbert pyalbert
pip install . pyalbert
```

2. Ensure you are using dev environement: you should have `ENV=dev` in the file [pyalbert/.env](../pyalbert/.env)

3. Create the database schema (sqlite in dev mode) using Alembic:

```bash
PYTHONPATH=. alembic upgrade head
```

4. Start the API locally:

```bash
uvicorn app.main:app --reload
```

5. To test, you can access the automatic documenation (Swagger) of the model API at [http://localhost:8000/docs](http://localhost:8000/docs)

6. Run unit tests:

```bash
pytest app/tests
```

Or, for report options:

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```
