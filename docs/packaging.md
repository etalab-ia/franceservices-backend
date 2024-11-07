# Comment build et publier une nouvelle version de PyAAlbert

Le module `pyalbert` est publié dabs les dépôts PyPi. Il faut incrémenter manuellement toute nouvelle version de `pyalbert`.
Pour cela, modifier:
- la variable `__version__` dans `pyalbert/_version.py`
- la variable `version` dans le `pyproject.toml` racine

Puis lancer: 
```sh
python -m pip install build twine
python -m build
twine upload dist/*
```


# Mise à jour du module dans l'API
Pour que l'API utilise la nouvelle version du module, modifier la valeur du module `pyalbert==0.x.y` (section `dependencies`) dans le `pyproject.toml` du dossier api.

