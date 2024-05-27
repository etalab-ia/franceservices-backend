# Bases de données

Pour une utilisation des bases de données avec Docker, aucun build d'image n'est nécessaire car les images Docker sont disponibles sur le registry Docker officiel.

## PostgreSQL

La base de données PostgreSQL a deux usages :
- la gestion des utilisateurs
- le stockage des logs des conversations avec les modèles

Lorsque l'API est exécuté en mode développement, une base de données SQLite est utilisée en lieu et place de la base de données PostgreSQL.

### Créer les schémas de la base de données PostgreSQL avec Alembic

[Alembic](https://alembic.sqlalchemy.org/en/latest/) est un outil de migration de schémas de base de données pour l'ORM [SQLAlchemy](https://www.sqlalchemy.org/).
Après avoir déployé le container Postgres, pour créer ou mettre à jour les schémas de données conformément aux derniers modèles dans le code de l'API, exécutez la commande suivante :
```bash
PYTHONPATH=. alembic upgrade head
```

### Sauvegarder une base de données PostgreSQL

Après avoir déployé le container Postgres, vous pouvez sauvegarder la base de données avec la commande suivante :
```bash
docker exec -i postgres-postgres-1 /bin/bash -c "PGPASSWORD=<password> pg_dump --username postgres postgres" > my_dump.dump
```

### Restaurer une base PostgreSQL à partir d'un dump de sauvegarde

Après avoir déployé le container Postgres, vous pouvez restaurer la base à partir d'un dump avec la commande suivante :
```bash
docker exec -i postgres-postgres-1 /bin/bash -c "PGPASSWORD=<password> psql --username postgres postgres" < my_dump.dump
```

## Vector stores: Elastic et Qdrant

Pour alimenter les modèles à des bases de connaissances ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), deux bases de données sont à déployer :
- une base Elasticsearch, qui stocke les corpus de documents et les chunks de ces documents
- une base de données Qdrant, la base vectorielle qui stocke les vecteurs d'embeddings

Pour savoir comme les installer, référez-vous à la documentation [installation.md](installation.md).
