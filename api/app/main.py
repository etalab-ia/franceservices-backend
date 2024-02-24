import sys

sys.path.append("..")
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION, BACKEND_CORS_ORIGINS, CONTACT, ENV
from app.db.init_db import init_db
from app.endpoints import chat, feedback, login, misc, search, stream, user
from app.mockups import install_mockups

if ENV in ("unittest", "dev"):
    install_mockups()

init_db()


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact=CONTACT
)

if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api_router = APIRouter()
api_router.include_router(misc.router)
api_router.include_router(user.router)
api_router.include_router(login.router)
api_router.include_router(search.router)
api_router.include_router(stream.router)
api_router.include_router(chat.router)
api_router.include_router(feedback.router)
app.include_router(api_router)
