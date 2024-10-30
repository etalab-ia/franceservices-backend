from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.datastructures import MutableHeaders
from itsdangerous import URLSafeSerializer
import secrets
import copy

# Redis configuration
from pyalbert.config import PROCONNECT_SESSION_DURATION, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
import redis

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

class RedisSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        session_cookie: str = "session",
        max_age: int = PROCONNECT_SESSION_DURATION,
        path: str = "/",
        same_site: str = "lax",
        https_only: bool = False
    ):
        super().__init__(app)
        self.redis = redis_client
        self.serializer = URLSafeSerializer(secret_key)
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.path = path
        self.security_flags = f"HttpOnly; SameSite={same_site}"
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; Secure"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.scope["type"] not in ("http", "websocket"):
            return await call_next(request)

        session_id = self.get_session_id(request)
        request.scope["session"] = self.get_valid_session_data(session_id)

        if not request.scope["session"] or not session_id:
            session_id = secrets.token_urlsafe()
            request.scope["session"] = {}  # Initialize an empty session
            set_cookie = True
        else:
            set_cookie = False

        original_session = copy.deepcopy(request.scope["session"])
        response = await call_next(request)

        if request.scope["session"] != original_session:
            self.write_session_data(session_id, request.scope["session"])
            set_cookie = True

        if set_cookie:
            self.set_cookie(response, session_id)

        return response

    def get_session_id(self, request: Request) -> str:
        return request.cookies.get(self.session_cookie, '')

    def write_session_data(self, session_id: str, session_data: dict):
        data = self.serializer.dumps(session_data)
        self.redis.set(name=session_id, value=data, ex=self.max_age)

    def get_valid_session_data(self, session_id: str) -> dict:
        if not session_id:
            return {}

        data = self.redis.get(session_id)
        if not data:
            return {}

        try:
            session_data = self.serializer.loads(data)
        except Exception:
            self.redis.delete(session_id)
            return {}

        return session_data

    def set_cookie(self, response: Response, session_id: str):
        header_value = f"{self.session_cookie}={session_id}; Path={self.path}; Max-Age={self.max_age}; {self.security_flags}"
        response.headers.append("Set-Cookie", header_value)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)
