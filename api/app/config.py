import ast
import os

import torch


def collate_ix_name(name, version):
    if version:
        return "-".join([name, version])
    return name


# App metadata
# TODO load metadata from pyproject.toml using tomlib instead of this
APP_NAME = "albert-api"
APP_DESCRIPTION = "Albert, also known as LIA: the **L**egal **I**nformation **A**ssistant, is a conversational agent that uses official French data sources to answer administrative agent questions."
APP_VERSION = "2.0.0"
CONTACT = {
    "name": "Etalab - Datalab",
    "url": "https://www.etalab.gouv.fr/",
    "email": "etalab@mail.numerique.gouv.fr",
}

# Root directory:
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "staging", "prod"):
    raise EnvironmentError("Wrong ENV value")

# CORS
# Env variable must be a string with comma separated values
# i.e.: BACKEND_CORS_ORIGINS="http://localhost:4173,http://albert.etalab.gouv.fr,https://albert.etalab.gouv.fr"
BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS", "").split(",")

# JWT token
SECRET_KEY = os.environ["SECRET_KEY"]
PASSWORD_PATTERN = r"^[A-Za-z\d$!%*+\-?&#_=.,:;@]{8,128}$"

# Database
FIRST_ADMIN_USERNAME = os.environ["FIRST_ADMIN_USERNAME"]
FIRST_ADMIN_EMAIL = os.environ["FIRST_ADMIN_EMAIL"]
FIRST_ADMIN_PASSWORD = os.environ["FIRST_ADMIN_PASSWORD"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

# Email
MJ_API_KEY = os.getenv("MJ_API_KEY")
MJ_API_SECRET = os.getenv("MJ_API_SECRET")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")

# Public Urls
API_URL = os.getenv("API_URL", "http://localhost:8000")
FRONT_URL = os.getenv("FRONT_URL", "http://localhost:8000")
if ENV == "dev":
    API_ROUTE_VER = "/"
else:
    API_ROUTE_VER = "/api/v2"

# Elasticsearch
ELASTIC_HOST = os.environ.get("ELASTIC_HOST", "localhost")
ELASTIC_PORT = os.environ.get("ELASTIC_PORT", "9200")
ELASTICSEARCH_URL = f"http://{ELASTIC_HOST}:{ELASTIC_PORT}"
ELASTIC_PASSWORD = os.environ.get("ELASTIC_PASSWORD", None)
ELASTICSEARCH_CREDS = ("elastic", ELASTIC_PASSWORD)
ELASTICSEARCH_IX_VER = "v3"

# Qdrant
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_GRPC_PORT = os.environ.get("QDRANT_GRPC_PORT", "6334")
QDRANT_REST_PORT = os.environ.get("QDRANT_REST_PORT", "6333")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_REST_PORT}"
QDRANT_IX_VER = "v3"

# Embedding
SHEET_SOURCES = ["service-public", "travail-emploi"]
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_BOOTSTRAP_PATH = os.path.join(
    "_data", "embeddings", EMBEDDING_MODEL.split("/")[-1]
)

# LLM
LLM_TABLE = os.getenv("LLM_TABLE")
if LLM_TABLE:
    try:
        LLM_TABLE = ast.literal_eval(LLM_TABLE)
    except Exception as e:
        raise ValueError("LLM_TABLE is not valid: %s" % e)
else:  # default
    LLM_TABLE = [
        # model_name/api URL
        ("AgentPuclic/albert-light", "http://127.0.0.1:8082")
    ]


PASSWORD_RESET_TOKEN_TTL = 3600  # seconds
ACCESS_TOKEN_TTL = 3600 * 24  # seconds
if ENV == "unittest":
    PASSWORD_RESET_TOKEN_TTL = 3  # seconds
    ACCESS_TOKEN_TTL = 9  # seconds

# If local, download the model Tiny Albert from HuggingFace
# @DEBUG: Do not do that here, it pop that string for every intereaction with pyalbert, from test scripts to lib imports.
#         And why giving a warning for just that model, and not others. Each model has its potential quantized version
#         Also, it is not very clear yet where, when by whom the model should be downloaded. . For example, it could be
#         - by calling `pyalbert download_models
#         - by lettin the llm-api download model on the fly
#         - or by a ci/cd pipeline
#         - or again, in dev, we could use a dummy api that stream hardcoded string just efor the purpose of testing the main api.
#
#if ENV == "dev":
#    TINY_ALBERT_LOCAL_PATH = Path("../../../pyalbert/models/tiny_albert/ggml-model-expert-q4_K.bin").resolve()
#    if not TINY_ALBERT_LOCAL_PATH.exists():
#        print("Le modèle Tiny Albert n'est pas présent localement. Téléchargez-le depuis HuggingFace à l'aide du script pyalbert/albert.py en utilisant la configuration vllm_routing_table.json, puis relancez l'API.")

if torch.cuda.is_available() and os.getenv("DISABLE_CUDA", "").lower() not in ["y", "yes", "1", "true"]:
    WITH_GPU = True
    DEVICE_MAP = "cuda:0"
else:
    WITH_GPU = False
    DEVICE_MAP = None
