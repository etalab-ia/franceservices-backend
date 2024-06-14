# Bases de données

Pour une utilisation des bases de données avec Docker, aucun build d'image n'est nécessaire car les images Docker sont disponibles sur le registry Docker officiel.

## PostgreSQL

La base de données PostgreSQL a deux usages :
- la gestion des utilisateurs
- le stockage des logs des conversations avec les modèles

Lorsque l'API est exécuté en mode développement, une base de données SQLite est utilisée en lieu et place de la base de données PostgreSQL.


### Nom de la base de données

Pour cloisonner les bases de données en mode test, dev ou production, le nom de la base de données n'est pas le même en focntion de la variable d'environnement `ENV` dans le fichier `.env` de l'API.

Lorsque `ENV` est défini à `unittest`, nous utilisons la base de données SQLite. (pas de nom à définir)

Lorsque `ENV` est défini à `dev`, le nom de la base de données PostgreSQL est `postgres_dev`.

Autrement, le nom de la base de données PostgreSQL est `postgres`.

### Créer les schémas de la base de données PostgreSQL avec Alembic

[Alembic](https://alembic.sqlalchemy.org/en/latest/) est un outil de migration de schémas de base de données pour l'ORM [SQLAlchemy](https://www.sqlalchemy.org/).
Après avoir déployé le container Postgres, pour créer ou mettre à jour les schémas de données conformément aux derniers modèles dans le code de l'API, exécutez la commande suivante :
```bash
PYTHONPATH=. alembic upgrade head
```
Lorsque l'API est lancée depuis Docker, cette commande est automatiquement exécutée lors du démarrage de l'API depuis le fichier `api/start.sh` appelé par le fichier `api/Dockerfile`.

### Sauvegarder une base de données PostgreSQL

Vous pouvez sauvegarder les données de la base de données avec la commande suivante :
```bash
PGPASSWORD=<password> pg_dump postgres -Fc --data-only --on-conflict-do-nothing --inserts --username postgres" > my_dump.dump
```
...ou, si vous utilisez Docker :
```bash
docker exec -i <postgres-container-name> pg_dump postgres -Fc --data-only --on-conflict-do-nothing --inserts --username postgres > my_dump.dump
```

### Restaurer une base PostgreSQL à partir d'un dump de sauvegarde

Vous pouvez restaurer la base à partir d'un dump avec la commande suivante :
```bash
PGPASSWORD=<password> pg_restore --username postgres --dbname postgres --single-transaction --data-only my_dump.dump
```
...ou, si vous utilisez Docker :
```bash
docker exec -i <postgres-container-name> pg_restore -v --single-transaction --data-only --username postgres --dbname postgres < my_dump.dump
```

En cas d'erreur du type `sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "streams_pkey")` après un processus de restauration de base, vous pouvez réinitialiser les séquences pour chaque table qui possède une clef primaire à incrémentation automatique avec la commande suivante :
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

## Vector stores : Elasticsearch et Qdrant

Pour alimenter les modèles à des bases de connaissances ([Retrieval Augmented Generation, RAG](https://en.wikipedia.org/wiki/Prompt_engineering#Retrieval-augmented_generation)), deux bases de données sont à déployer :
- une base [Elasticsearch](https://www.elastic.co/), qui stocke les corpus de documents et les chunks de ces documents
- une base de données [Qdrant](https://qdrant.tech/) , la base vectorielle qui stocke les vecteurs d'embeddings

Pour savoir comment les installer, référez-vous à la [documentation sur l'installation](installation.md#vector-stores-elasticsearch-et-qdrant).
