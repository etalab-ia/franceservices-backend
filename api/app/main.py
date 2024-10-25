import sys

from helpers.redis.redis_session_middleware import RedisSessionMiddleware

sys.path.append("..")
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.db.init_db import init_db
from app.endpoints import chat, feedback, misc, openai, search, stream, login, user
from pyalbert import get_logger
from pyalbert.config import (
    API_PREFIX,
    API_PREFIX_V1,
    API_PREFIX_V2,
    API_URL,
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    BACKEND_CORS_ORIGINS,
    CONTACT,
    SECRET_KEY,
)

logger = get_logger()


init_db()


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as err:
            logger.error(f"An error occurred on **franceservice**({API_URL}): {err}", exc_info=True)
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact=CONTACT,
    docs_url=API_PREFIX.rstrip("/") + "/docs",
    redoc_url=API_PREFIX.rstrip("/") + "/redoc",
    openapi_url=API_PREFIX.rstrip("/") + "/openapi.json",
)

app.add_middleware(ErrorLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RedisSessionMiddleware, secret_key=SECRET_KEY)

api_v1_router = APIRouter()
api_v1_router.include_router(openai.router)

api_v2_router = APIRouter()
api_v2_router.include_router(misc.router)
api_v2_router.include_router(search.router)
api_v2_router.include_router(stream.router)
api_v2_router.include_router(chat.router)
api_v2_router.include_router(login.router)
api_v2_router.include_router(feedback.router)
api_v2_router.include_router(user.router)

app.include_router(api_v1_router, prefix=API_PREFIX_V1)
app.include_router(api_v2_router, prefix=API_PREFIX_V2)
