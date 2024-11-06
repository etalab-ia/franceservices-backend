import os
import tempfile

from dotenv import load_dotenv
import requests

load_dotenv()

# @IMPROVE:
# - use a proper config file instead of defining variables in config.py -> use a albert.cfg/toml
# - load metadata from pyproject.toml using tomlib instead of this.

#######################################################################
### App metadata
#######################################################################

APP_NAME = "albert-api"
APP_DESCRIPTION = "Albert, also known as LIA: the **L**egal **I**nformation **A**ssistant, is a conversational agent that uses official French data sources to answer administrative agent questions."
APP_VERSION = os.getenv("APP_VERSION", "0.0.0")
CONTACT = {
    "name": "Etalab - Datalab",
    "url": "https://www.etalab.gouv.fr/",
    "email": "etalab@modernisation.gouv.fr",
}

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "staging", "prod"):
    raise EnvironmentError("Wrong ENV value")

VERBOSE_LEVEL = "INFO"

# CORS
# Env variable must be a string with comma separated values
# i.e.: BACKEND_CORS_ORIGINS="http://localhost:4173,http://albert-api-example.com,https://albert-api-example.com"
# WARNINF! We shouldn't use "*" as we get the error response "Credential is not supported if the CORS header ‘Access-Control-Allow-Origin’ is ‘*’"
BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS", "").split(",")

match ENV:
    case "dev":
        DATABASE_URI = os.getenv(
            "POSTGRES_URI", "postgresql+psycopg2://postgres:changeme@localhost:5432/postgres_dev"
        )
    case _:
        DATABASE_URI = os.getenv(
            "POSTGRES_URI", "postgresql+psycopg2://postgres:changeme@localhost:5432/postgres"
        )

# Email
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")

# Public URLs
# @TODO: build pyalbert with the public Albert API endpoint.
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_PREFIX = "/api"
API_ROUTE_VER = "v2"
API_PREFIX_V2 = API_PREFIX.rstrip("/") + "/" + API_ROUTE_VER if API_ROUTE_VER else ""
API_PREFIX_V1 = API_PREFIX.rstrip("/") + "/v1"

# Elasticsearch
ELASTICSEARCH_IX_VER = "v5"
ELASTIC_HOST = os.environ.get("ELASTIC_HOST", "localhost")
ELASTIC_PORT = os.environ.get("ELASTIC_PORT", "9200")
ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
ELASTIC_PASSWORD = os.environ.get("ELASTIC_PASSWORD", "")
ELASTICSEARCH_CREDS = ("elastic", ELASTIC_PASSWORD)

# Qdrant
QDRANT_IX_VER = "v4"
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_GRPC_PORT = os.environ.get("QDRANT_GRPC_PORT", "6334")
QDRANT_REST_PORT = os.environ.get("QDRANT_REST_PORT", "6333")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
QDRANT_USE_GRPC = True

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

# Base URL
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
FRONTEND_LOGGED_IN_URL = os.environ.get("FRONTEND_LOGGED_IN_URL", "http://localhost:3000")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")

# Pro-connect OIDC
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

# Pro-connect session duration in seconds
PROCONNECT_PORT = os.environ.get("PROCONNECT_PORT", "4011")
PROCONNECT_SESSION_DURATION = os.environ.get("PROCONNECT_SESSION_DURATION", 43200)  # 12 hours
PROCONNECT_OAUTH_ROOT_URL = os.environ.get("PROCONNECT_OAUTH_ROOT_URL")

# secret key for the session cookie
SECRET_KEY = os.environ.get("SECRET_KEY", "changeme")

# LLM/RAG
# --
DO_ENCODE_PROMPT = False  # if True, the Prompter class will encode the prompt according the "prompt_format" given in prompt config.
HF_TOKEN = os.getenv("HF_TOKEN")  # @deprecated
# The sources that will be parsed, chunked, indexed and embeded for the RAG.
SHEET_SOURCES = ["service-public", "travail-emploi"]
# Default embedding model
RAG_EMBEDDING_MODEL = "BAAI/bge-m3"
HYBRID_COLLECTIONS = ["spp_experiences", "chunks"]

# Build the LLM table and from the LLM API endpoints
LLM_API_VER = "v1"
ACTIVATE_SSE_WRAPPER = False
LLM_TABLE = []
ALBERT_API_URL = os.getenv("ALBERT_API_URL")
ALBERT_API_KEY = os.getenv("ALBERT_API_KEY", "changeme")
models_urls = [(ALBERT_API_URL, ALBERT_API_KEY)]
for url, key in models_urls:
    headers = {"Authorization": "Bearer " + key} if key else None
    endpoint = f"{url}/{LLM_API_VER}/models" if LLM_API_VER else f"{url}/models"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        # Response body example:
        # {"object":"list","data":[{"object":"model","id":"intfloat/multilingual-e5-large"},{"object":"model","id":"AgentPublic/llama3-instruct-8b"}]}
        models: list[dict] = response.json()["data"]
        for m in models:
            # Assume it is a text-generation model by default.
            LLM_TABLE.append(
                {"model": m["id"], "type": m.get("type", "text-generation"), "url": url, "key": key}
            )
    except Exception as err:
        # Do not block the API if an host is down. It could be one over multiple and not our responsability
        # Logging the error...
        print(f'Error while fetching model at "{endpoint}": {err}')


# JWT token
PASSWORD_PATTERN = r"^[A-Za-z\d$!%*+\-?&#_=.,:;@]{8,128}$"

if ENV == "unittest":
    DATABASE_URI = "sqlite:///" + os.path.join(tempfile.gettempdir(), "albert-unittest-sqlite3.db")
    LLM_TABLE = [
        {
            "model": "albert",
            "type": "text-generation",
            "url": "http://127.0.0.1:8899",
            "key": ALBERT_API_KEY,
        },
        {
            "model": RAG_EMBEDDING_MODEL,
            "type": "feature-extraction",
            "url": "http://127.0.0.1:8899",
            "key": ALBERT_API_KEY,
        },
    ]
    ELASTIC_HOST = "localhost"
    ELASTIC_PORT = "9211"
    QDRANT_HOST = "localhost"
    QDRANT_REST_PORT = "6344"
    QDRANT_USE_GRPC = False
    QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
    ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
    LLM_API_VER = ""
    # Pro-connect
    PROCONNECT_URL = os.getenv("PROCONNECT_TEST_URL", "http://localhost:4011")
    # @warning: prism mock does not support basepath prefix.
    # --
