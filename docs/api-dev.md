# Lancer l'API Albert en local (dev mode)

Installer les dépendances

```bash
    cd api/
    ln -s $(pwd)/../pyalbert/pyalbert
    pip install . pyalbert
```

Ensure you are using dev environement (vous devez avoir `ENV=dev` dans le fichiers pyalbert/.env)
Initialiser la base de donnée (sqlite en mode dev)

    PYTHONPATH=. alembic upgrade head


Lancer l'API

    uvicorn app.main:app --reload


