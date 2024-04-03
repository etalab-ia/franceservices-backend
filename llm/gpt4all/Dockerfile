FROM python:3.10-slim

WORKDIR /code
ADD ./app.py ./pyproject.toml .
RUN pip install --no-cache-dir --upgrade /code/.
