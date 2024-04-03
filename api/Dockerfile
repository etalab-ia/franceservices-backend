FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH="$PYTHONPATH:/code"

WORKDIR /code
ADD ./pyproject.toml ./alembic.ini ./start.sh .
ADD ./alembic ./alembic
ADD ./app ./app
COPY --from=pyalbert . ./pyalbert

RUN chmod +x /code/start.sh
RUN pip install --no-cache-dir --default-timeout=100 --upgrade .
RUN pip install --no-cache-dir --upgrade ./pyalbert/.

CMD ["bash", "start.sh"]
