import ast
import os
from urllib.parse import urlparse

import dotenv
import requests

dotenv.load_dotenv()

# @IMPROVE:
# - use a proper config file instead of defining variables in config.py -> use a albert.cfg/toml
# - load metadata from pyproject.toml using tomlib instead of this.

#######################################################################
### App metadata
#######################################################################

APP_NAME = "albert-api"
APP_DESCRIPTION = "Albert, also known as LIA: the **L**egal **I**nformation **A**ssistant, is a conversational agent that uses official French data sources to answer administrative agent questions."
APP_VERSION = "2.0.0"
CONTACT = {
    "name": "Etalab - Datalab",
    "url": "https://www.etalab.gouv.fr/",
    "email": "etalab@modernisation.gouv.fr",
}

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "staging", "prod"):
    raise EnvironmentError("Wrong ENV value")

# CORS
# Env variable must be a string with comma separated values
# i.e.: BACKEND_CORS_ORIGINS="http://localhost:4173,http://albert-api-example.com,https://albert-api-example.com"
BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS", "").split(",")

# API / Database
FIRST_ADMIN_USERNAME = os.getenv("FIRST_ADMIN_USERNAME", "changeme")
FIRST_ADMIN_EMAIL = os.getenv("FIRST_ADMIN_EMAIL", "changeme@changeme.fr")
FIRST_ADMIN_PASSWORD = os.getenv("FIRST_ADMIN_PASSWORD", "changeme")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

# Email
MJ_API_KEY = os.getenv("MJ_API_KEY")
MJ_API_SECRET = os.getenv("MJ_API_SECRET")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")

# Public URLs
API_URL = os.getenv("API_URL", "http://localhost:8000")
FRONT_URL = os.getenv("FRONT_URL", "http://localhost:8000")
API_ROUTE_VER = "/api/v2"

# Elasticsearch
ELASTICSEARCH_IX_VER = "v3"
ELASTIC_HOST = os.environ.get("ELASTIC_HOST", "localhost")
ELASTIC_PORT = os.environ.get("ELASTIC_PORT", "9200")
ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
ELASTIC_PASSWORD = os.environ.get("ELASTIC_PASSWORD", "")
ELASTICSEARCH_CREDS = ("elastic", ELASTIC_PASSWORD)

# Qdrant
QDRANT_IX_VER = "v3"
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_GRPC_PORT = os.environ.get("QDRANT_GRPC_PORT", "6334")
QDRANT_REST_PORT = os.environ.get("QDRANT_REST_PORT", "6333")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
QDRANT_USE_GRPC = True

# RAG
# --
# The sources that will be parsed, chunked, indexed and embeded for the RAG.
SHEET_SOURCES = ["service-public", "travail-emploi"]
# Default embedding model
RAG_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# Build the LLM table and from the LLM API endpoints
OPENAI_API_VERSION = (
    ""  # @FUTURE: set it to "v1" once we move to the llm-api that support OpenAI API.
)
MODELS_URLS = ast.literal_eval(os.environ.get("MODELS_URLS", "[]"))
LLM_TABLE = []
for url in MODELS_URLS:
    endpoint = f"{url}/{OPENAI_API_VERSION}/models" if OPENAI_API_VERSION else f"{url}/models"
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        # Response body example:
        # {"object":"list","data":[{"object":"model","id":"intfloat/multilingual-e5-large"},{"object":"model","id":"AgentPublic/llama3-instruct-8b"}]}
        models: list[dict] = response.json()["data"]
        for m in models:
            LLM_TABLE.append({"model": m["id"], "url": url})
    except Exception as err:
        # Do not block the API if an host is down. It could be one over multiple and not our responsability
        # Logging the error...
        print(f'Error while fetching model at "{endpoint}": {err}')


# JWT token
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
PASSWORD_PATTERN = r"^[A-Za-z\d$!%*+\-?&#_=.,:;@]{8,128}$"
PASSWORD_RESET_TOKEN_TTL = 3600  # seconds
ACCESS_TOKEN_TTL = 3600 * 24  # seconds

if ENV == "unittest":
    API_ROUTE_VER = "/"
    LLM_TABLE = [{"model": "albert", "url": "http://127.0.0.1:8899"}]
    ELASTIC_PORT = "9211"
    QDRANT_REST_PORT = "6344"
    QDRANT_USE_GRPC = False
    QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
    ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
    PASSWORD_RESET_TOKEN_TTL = 3  # seconds
    ACCESS_TOKEN_TTL = 9  # seconds
elif ENV == "dev":
    API_ROUTE_VER = os.getenv("API_ROUTE_VER", "/")
