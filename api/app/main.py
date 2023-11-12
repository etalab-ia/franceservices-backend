import sys

sys.path.append("..")
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import ENV
from app.db.init_db import init_db
from app.endpoints import login, others, stream, user
from app.mockups import install_mockups

if ENV in ("unittest", "dev"):
    install_mockups()

init_db()

app = FastAPI()

# CORS:
# TODO:
BACKEND_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:8080",
]
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(others.router, tags=["others"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(user.router, tags=["user"])
app.include_router(api_router)
