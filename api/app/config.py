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

PUBLIC_API_HOST = "142.44.40.218"
PUBLIC_API_PORT = "80"
#PUBLIC_API_HOST = "localhost"
#PUBLIC_API_PORT = "8090"
SECRET_KEY = os.environ["SECRET_KEY"]
FIRST_ADMIN_USERNAME = os.environ["FIRST_ADMIN_USERNAME"]
FIRST_ADMIN_EMAIL = os.environ["FIRST_ADMIN_EMAIL"]
FIRST_ADMIN_PASSWORD = os.environ["FIRST_ADMIN_PASSWORD"]
MJ_API_KEY = os.environ["MJ_API_KEY"]
MJ_API_SECRET = os.environ["MJ_API_SECRET"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

API_VLLM_URL = "http://127.0.0.1:8081"  # default... @obsolete ?
ELASTICSEARCH_URL = f"http://{PUBLIC_API_HOST}:9202"
ELASTICSEARCH_CREDS = ("elastic", "changeme")
QDRANT_URL = f"http://{PUBLIC_API_HOST}:6333"

PASSWORD_PATTERN = r"^[A-Za-z\d$!%*?&#_]{8,20}$"

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
