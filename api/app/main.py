import sys

sys.path.append("..")
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.db.init_db import init_db
from app.endpoints import chat, feedback, login, misc, openai, search, stream, user
from app.mockups import install_mockups

from pyalbert.config import (
    API_PREFIX,
    API_PREFIX_V1,
    API_PREFIX_V2,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    BACKEND_CORS_ORIGINS,
    CONTACT,
    ENV,
)

if ENV in ("unittest", "dev"):
    install_mockups()

init_db()


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact=CONTACT,
    docs_url=API_PREFIX.rstrip("/") + "/docs",
    redoc_url=API_PREFIX.rstrip("/") + "/redoc",
    openapi_url=API_PREFIX.rstrip("/") + "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1_router = APIRouter()
api_v1_router.include_router(openai.router)

api_v2_router = APIRouter()
api_v2_router.include_router(misc.router)
api_v2_router.include_router(user.router)
api_v2_router.include_router(login.router)
api_v2_router.include_router(search.router)
api_v2_router.include_router(stream.router)
api_v2_router.include_router(chat.router)
api_v2_router.include_router(feedback.router)

app.include_router(api_v1_router, prefix=API_PREFIX_V1)
app.include_router(api_v2_router, prefix=API_PREFIX_V2)
