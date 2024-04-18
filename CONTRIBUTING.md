## Pour contribuer

Avant de contribuer au dépôt, il est nécessaire d'initialiser les _hooks_ de _pre-commit_ :
```bash
pre-commit install
```

Si vous ne pouvez pas utiliser de pre-commit, il est nécessaire de formatter, linter et trier les imports avec [Ruff](https://docs.astral.sh/ruff/) :
```bash
ruff check --fix --select I .
```
Cette commande prendra en compte les différents `pyproject.toml` rencontrés sur le chemin.
