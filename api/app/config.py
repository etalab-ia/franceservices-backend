import os

import torch
from dotenv import load_dotenv

# Root directory:
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Environment:
load_dotenv(os.path.join(ROOT_DIR, ".env"))

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "prod"):
    raise EnvironmentError("Wrong ENV value")

# CORS
BACKEND_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:8080",
    "http://albert.etalab.gouv.fr",
    "http://franceservices.etalab.gouv.fr",
    "http://ia.etalab.gouv.fr",
    "https://albert.etalab.gouv.fr",
    "https://ia.etalab.gouv.fr",
    "https://franceservices.etalab.gouv.fr",
]

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

# Urls
# @obsolete: use HOST instead of URL, this is confusing
API_VLLM_URL = "http://127.0.0.1:8081"  # default
ELASTICSEARCH_URL = "http://127.0.0.1:9202"
ELASTICSEARCH_CREDS = ("elastic", "changeme")
QDRANT_URL = "http://127.0.0.1:6333"
API_URL = os.getenv("API_URL", "https://albert.etalab.gouv.fr")
FRONT_URL = os.getenv("FRONT_URL", "https://albert.etalab.gouv.fr")

# Search Engines
ELASTICSEARCH_IX_VER = "v3"
QDRANT_IX_VER = "v3"
API_ROUTE_VER = "/api/v2"
SHEET_SOURCES = ["service-public", "travail-emploi"]
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_BOOTSTRAP_PATH = os.path.join("_data", "embeddings", EMBEDDING_MODEL.split("/")[-1])
# For local testing, use:
# --
# API_ROUTE_VER = "/"
# API_URL = "http://localhost:8000"


def collate_ix_name(name, version):
    if version:
        return "-".join([name, version])
    return name


if ENV == "unittest":
    PASSWORD_RESET_TOKEN_TTL = 3  # seconds
    ACCESS_TOKEN_TTL = 9  # seconds
else:
    PASSWORD_RESET_TOKEN_TTL = 3600  # seconds
    ACCESS_TOKEN_TTL = 3600 * 24  # seconds

if torch.cuda.is_available():
    WITH_GPU = True
    DEVICE_MAP = "cuda:0"
else:
    WITH_GPU = False
    DEVICE_MAP = None
