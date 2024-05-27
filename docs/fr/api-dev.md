# Lancer l'API Albert en local (dev mode)

1. Installez les dépendances

```bash
cd api/
ln -s $(pwd)/../pyalbert/pyalbert
pip install . pyalbert
```

2. Assurez-vous que votre variable d'environnement `ENV` dans [pyalbert/.env](../pyalbert/.env) est égale à `dev` telle que `ENV="dev"`


3. Créez le schéma de la base de données (sqlite en mode dev) en utilisant Alembic :

```bash
PYTHONPATH=. alembic upgrade head
```

4. Lancez l'API

```bash
uvicorn app.main:app --reload
```

5. Pour tester, vous pouvez accéder à la documentation automatique (Swagger) de l'API du modèle sur [http://localhost:8000/docs](http://localhost:8000/docs).

6. Exécutez les tests unitaires :

```bash
pytest app/tests
```

Ou, pour le support des rapports :

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```
