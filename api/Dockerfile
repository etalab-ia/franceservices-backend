FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY ./api/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./commons /code/commons
COPY ./api/alembic.ini /code/alembic.ini
COPY ./api/alembic /code/alembic
COPY ./api/app /code/app
COPY ./api/start.sh /code/start.sh
RUN chmod +x /code/start.sh
ARG API_URL http://localhost
ENV API_URL ${API_URL}
ARG FRONT_URL http://localhost
ENV FRONT_URL ${FRONT_URL}
CMD ["bash", "start.sh"]
