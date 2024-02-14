FROM python:3.10-slim

WORKDIR /code
ADD ./app.py ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
