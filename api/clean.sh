find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
rm -f .coverage
rm -rf .pytest_cache
rm -rf htmlcov
