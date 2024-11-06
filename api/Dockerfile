FROM python:3.10-slim

WORKDIR /code

# to export pyalbert as a python package
ENV PYTHONPATH="$PYTHONPATH:/code"

# add pyproject before the rest of the code to cache the pip install
ADD ./pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip && pip install --no-cache-dir .
RUN pip install --no-cache-dir --default-timeout=100 .

# add the rest of the code
ADD . .

RUN ln -s ../pyalbert pyalbert && pip install . pyalbert


CMD ["bash", "start.sh"]
