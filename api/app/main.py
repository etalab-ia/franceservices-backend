import sys

sys.path.append("..")
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import ENV, BACKEND_CORS_ORIGINS
from app.db.init_db import init_db
from app.endpoints import chat, login, others, stream, user
from app.mockups import install_mockups

if ENV in ("unittest", "dev"):
    install_mockups()

init_db()

app = FastAPI()

if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api_router = APIRouter()
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(others.router, tags=["others"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(user.router, tags=["user"])
app.include_router(api_router)
