FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# to export pyalbert as a python package
ENV PYTHONPATH="$PYTHONPATH:/code"

# add pyproject before the rest of the code to cache the pip install
ADD ./pyproject.toml ./pyproject.toml
COPY --from=pyalbert pyproject.toml ./pyalbert/pyproject.toml
RUN pip install --upgrade pip && pip install --no-cache-dir .
RUN pip install --no-cache-dir --default-timeout=100 .
RUN pip install --no-cache-dir ./pyalbert/.

# add the rest of the code
ADD . .
COPY --from=pyalbert . ./pyalbert

CMD ["bash", "start.sh"]
