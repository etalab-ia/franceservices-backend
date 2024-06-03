# Contribuer au projet

Le projet est en open source, sous [licence MIT](LICENCE). Toutes les contributions sont bienvenues, sous forme de pull requests ou d'ouvertures d'issues sur le repo officiel [GitHub](https://github.com/etalab-ia/albert).

## Mise à jour des chémas de base de données PostgreSQL avec Alembic

Si votre code modifie les modèles de données, il est nécessaire de créer le script de migration correspondant à la mise à jour la base de données PostgreSQL, et de commiter ce script avec vos modifications afin que les autres contributeurs et environnements de déploiement puissent mettre à jour leur base de données automatiquement.

[Alembic](https://alembic.sqlalchemy.org/en/latest/) est un outil de migration de schéma de base de données pour l'ORM [SQLAlchemy](https://www.sqlalchemy.org/), qui permet de générer ce script automatiquement. Pour ce faire :

1. Avant de créer toute nouvelle migration, une bonne pratique est de bien vérifier que le schéma de votre base de données PostgreSQL est à jour avec les migrations précedentes. Regardez le numéro de de révision (`revision`) de la dernière migration dans le dossier `api/alembic/versions`, et comparez avec la valeur de `version_num` dans la table `alembic_version` de votre base de données. Si ces deux valeurs sont identiques, votre base de données est à jour. Si elles sont différentes, vous devez mettre à jour votre base de données avec la commande suivante :
```bash
PYTHONPATH=. alembic upgrade head
```

2. Créez votre script de migration correspondant à vos changements de modèles de données avec la commande suivante (à lancer depuis `/api`) :
```bash
PYTHONPATH=. alembic revision --autogenerate
```
Un nouveau script de migration sera créé dans le dossier `api/alembic/versions`.

3. Vérifiez le contenu du script de migration créé, et si nécessaire, modifiez-le pour qu'il corresponde à vos besoins. N'oubliez pas de commiter ce fichier sur le même commit que vos modifications de modèles de données.

4. Appliquez la migration à votre base de données avec la commande suivante :
```bash
PYTHONPATH=. alembic upgrade head
```
Cette commande mettra à jour votre base de données PostgreSQL avec les derniers changements de schéma, et mettra à jour la table `alembic_version` avec le numéro de révision de cette dernière migration pour indiquer que votre base de données est à jour.

## Avant toute Pull Request

Avant de contribuer au dépôt, il est nécessaire d'initialiser les _hooks_ de _pre-commit_ :
```bash
pre-commit install
```
Une fois ceci fait, le formattage et le linting du code, ainsi que le tri des imports, seront automatiquement vérifiés avant chaque commit.

Si vous ne pouvez pas utiliser de pre-commit, il est nécessaire de formatter, linter et trier les imports avec [Ruff](https://docs.astral.sh/ruff/) avant chaque commit :
```bash
ruff check --fix --select I .
```