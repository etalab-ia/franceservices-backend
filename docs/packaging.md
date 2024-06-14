How to build and deploy pyalbert

```sh
python -m pip install build twine
cd pyalbert/
python -m build
twine upload dist/*
```
