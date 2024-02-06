import os
import re

import torch
from dotenv import load_dotenv


def collate_ix_name(name, version):
    if version:
        return "-".join([name, version])
    return name


def parse_vllm_routing_table(table: list[str]) -> list[dict]:
    # @TODO: add a schema validation in a test pipeline.
    structured_table = []
    columns = [
        "model_name",
        "model_id",
        "host",
        "port",
        "gpu_mem_use",
        "tensor_par_size",
        "do_update",
    ]
    for model in table:
        values = re.split("\s+", model)
        if len(values) != len(columns):
            raise ValueError(
                "VLLM_ROUTING_TABLE format error: wrong number of columns for line" % (model)
            )
        structured_table.append(dict(zip(columns, values)))

    return structured_table

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

# Environment:
load_dotenv(os.path.join(ROOT_DIR, ".env"))

ENV = os.getenv("ENV", "dev")
if ENV not in ("unittest", "dev", "prod"):
    raise EnvironmentError("Wrong ENV value")

# CORS
BACKEND_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:8080",
    "http://ia.etalab.gouv.fr",
    "http://albert.etalab.gouv.fr",
    "http://albert.staging.etalab.gouv.fr",
    "http://franceservices.etalab.gouv.fr",
    "http://franceservices.staging.etalab.gouv.fr",
    "https://ia.etalab.gouv.fr",
    "https://albert.etalab.gouv.fr",
    "https://albert.staging.etalab.gouv.fr",
    "https://franceservices.etalab.gouv.fr",
    "https://franceservices.staging.etalab.gouv.fr",
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

# Public Urls
API_URL = os.getenv("API_URL", "https://albert.etalab.gouv.fr")
FRONT_URL = os.getenv("FRONT_URL", "https://albert.etalab.gouv.fr")
API_ROUTE_VER = "/api/v2"
# For local testing, use:
# --
# API_URL = "http://localhost:8000"
# API_ROUTE_VER = "/"

# Search Engines
ELASTICSEARCH_URL = "http://127.0.0.1:9202"
ELASTICSEARCH_CREDS = ("elastic", "changeme")
QDRANT_URL = "http://127.0.0.1:6333"
ELASTICSEARCH_IX_VER = "v3"
QDRANT_IX_VER = "v3"
SHEET_SOURCES = ["service-public", "travail-emploi"]
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_BOOTSTRAP_PATH = os.path.join("_data", "embeddings", EMBEDDING_MODEL.split("/")[-1])

# Vllm Routing Table.
# Set UPDATE to "true" to force (re)download the model in the dowload-vllm-model job.
if os.path.exists("VLLM_ROUTING_TABLE"):
    with open("VLLM_ROUTING_TABLE") as f:
        VLLM_ROUTING_TABLE = [
            line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")
        ]
else:  # default
    VLLM_ROUTING_TABLE = [
        # model_name/api     model_name/ID                  HOST                PORT GPU_MEM_USE(%) TENSOR_PARALLEL_SIZE UDATE
        "albert-light        ActeurPublic/albert-light      http://127.0.0.1    8082 0.4            1                    false",
    ]

VLLM_ROUTING_TABLE = parse_vllm_routing_table(VLLM_ROUTING_TABLE)


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
