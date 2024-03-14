FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH="$PYTHONPATH:/code"

WORKDIR /code
ADD ./requirements.txt ./alembic.ini ./start.sh .
ADD ./alembic ./alembic
ADD ./app ./app
COPY --from=commons . ./commons
COPY --from=pyalbert . ./pyalbert

RUN chmod +x /code/start.sh
RUN pip install --no-cache-dir --default-timeout=100 --upgrade -r ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./pyalbert/requirements.txt

CMD ["bash", "start.sh"]
