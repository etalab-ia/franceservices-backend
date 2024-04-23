import ast
import os

import dotenv

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
# i.e.: BACKEND_CORS_ORIGINS="http://localhost:4173,http://albert.etalab.gouv.fr,https://albert.etalab.gouv.fr"
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

# Public Urls
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

# The sources that will be parsed, chunked, indexed and embeded for the RAG.
SHEET_SOURCES = ["service-public", "travail-emploi"]

# LLM
LLM_TABLE = os.getenv("LLM_TABLE")
if LLM_TABLE:
    try:
        LLM_TABLE = ast.literal_eval(LLM_TABLE)
    except Exception as err:
        raise ValueError("LLM_TABLE is not valid") from err
else:  # default
    LLM_TABLE = [
        # model_name/api URL
        ("AgentPublic/albertlight-7b", "http://127.0.0.1:8082")
    ]

# The embedding model to target
# @FUTURE: Use same format than the LLM_TABLE to support deploying multi model ?
EMBEDDINGS_HOST = os.getenv("EMBEDDINGS_HOST", "localhost")
EMBEDDING_PORT = os.getenv("EMBEDDINGS_PORT", "8005")
EMBEDDING_URL = f"http://{EMBEDDINGS_HOST}:{EMBEDDING_PORT}"
EMBEDDING_HF_REPO_ID = os.getenv("EMBEDDING_HF_REPO_ID", "intfloat/multilingual-e5-large")
EMBEDDING_MODEL = (EMBEDDING_HF_REPO_ID, EMBEDDING_URL)

# JWT token
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
PASSWORD_PATTERN = r"^[A-Za-z\d$!%*+\-?&#_=.,:;@]{8,128}$"
PASSWORD_RESET_TOKEN_TTL = 3600  # seconds
ACCESS_TOKEN_TTL = 3600 * 24  # seconds

if ENV == "unittest":
    API_ROUTE_VER = "/"
    LLM_TABLE = [("AgentPublic/albertlight-7b", "http://127.0.0.1:8892")]
    ELASTIC_PORT = "9211"
    QDRANT_REST_PORT = "6344"
    QDRANT_USE_GRPC = False
    QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
    ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
    PASSWORD_RESET_TOKEN_TTL = 3  # seconds
    ACCESS_TOKEN_TTL = 9  # seconds
elif ENV == "dev":
    API_ROUTE_VER = os.getenv("API_ROUTE_VER", API_ROUTE_VER)
