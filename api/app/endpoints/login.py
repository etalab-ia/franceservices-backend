from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from helpers.redis.redis_session_middleware import redis_client
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client
import urllib.parse
import secrets
import jwt
import httpx

from pyalbert.config import BASE_URL, CLIENT_ID, CLIENT_SECRET, FRONTEND_BASE_URL, FRONTEND_LOGGED_IN_URL, PROCONNECT_OAUTH_ROOT_URL

oauth = OAuth()
oauth.register(
    name="fca",
    server_metadata_url=f"{PROCONNECT_OAUTH_ROOT_URL}/.well-known/openid-configuration",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email given_name usual_name",
    },
)
router = APIRouter()


@router.get("/login", tags=["login"])
async def login(request: Request):
    redirect_uri = f"{BASE_URL}/api/v2/callback"
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    request.session["state"] = state
    request.session["nonce"] = nonce
    return await oauth.fca.authorize_redirect(request, redirect_uri, state=state, nonce=nonce)


@router.get("/callback", tags=["login"])
async def auth(request: Request):
    try:
        stored_state = request.session.get("state")
        stored_nonce = request.session.get("nonce")
        client_state = request.query_params.get("state")
        client_code = request.query_params.get("code")

        if not client_state or client_state != stored_state:
            raise HTTPException(status_code=400, detail="Invalid state")

        async with AsyncOAuth2Client(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET, token_endpoint=oauth.fca.server_metadata["token_endpoint"]
        ) as client:
            token_response = await client.fetch_token(
                oauth.fca.server_metadata["token_endpoint"], grant_type="authorization_code", code=client_code, redirect_uri=f"{BASE_URL}/api/v2/callback"
            )

        id_token = token_response.get("id_token")
        if id_token:
            id_token_claims = await oauth.fca.parse_id_token(token_response, nonce=stored_nonce)
            if id_token_claims.get("nonce") != stored_nonce:
                raise HTTPException(status_code=400, detail="Invalid nonce")
            request.session["id_token"] = id_token

        userinfo_endpoint = oauth.fca.server_metadata["userinfo_endpoint"]
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(userinfo_endpoint, headers={"Authorization": f"Bearer {token_response['access_token']}"})
            userinfo_response.raise_for_status()
            if not userinfo_response.text:
                raise ValueError("Empty response from userinfo endpoint")

            user = jwt.decode(userinfo_response.text, options={"verify_signature": False})
        if user:
            request.session["user"] = user
        else:
            raise ValueError("No user info received")

        return RedirectResponse(url=FRONTEND_LOGGED_IN_URL)
    except (OAuthError, httpx.HTTPError, ValueError) as error:
        return {"error": str(error)}


@router.get("/prepare-logout", tags=["login"])
async def prepare_logout(request: Request):
    logout_state = secrets.token_urlsafe(32)
    request.session["logout_state"] = logout_state

    id_token = request.session.get("id_token")
    if not id_token:
        return JSONResponse({"error": "No active session"}, status_code=400)

    post_logout_redirect_uri = f"{BASE_URL}/api/v2/logout"
    logout_params = {"id_token_hint": id_token, "state": logout_state, "post_logout_redirect_uri": post_logout_redirect_uri}

    session_id = request.cookies.get("session")
    if session_id:
        redis_client.set(name=f"logout_state:{session_id}", value=logout_state, ex=3600)

    logout_url = f"{PROCONNECT_OAUTH_ROOT_URL}/session/end?{urllib.parse.urlencode(logout_params)}"
    return RedirectResponse(url=logout_url)


@router.get("/logout", tags=["login"])
async def logout(request: Request, state: str = None):
    session_id = request.cookies.get("session")
    stored_state = redis_client.get(f"logout_state:{session_id}") if session_id else None

    if not state or state != stored_state:
        return JSONResponse({"error": "Invalid state"}, status_code=400)

    if session_id:
        redis_client.delete(session_id)
        redis_client.delete(f"logout_state:{session_id}")

    request.session.clear()
    response = RedirectResponse(url=FRONTEND_BASE_URL)
    response.delete_cookie("session")
    return response
