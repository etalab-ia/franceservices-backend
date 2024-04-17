## Formatage et linting du code

Pour formatter, linter et trier les import Python en une commande unique :

```sh
ruff check --fix --select I .
```

Cette commande prendra en compte les différents `pyproject.toml` rencontrés sur le chemin.
