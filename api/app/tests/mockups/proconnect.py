import time
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from itsdangerous import URLSafeSerializer
import secrets
from faker import Faker

from app.crud.user import UserInfo
from app.deps import get_current_user
from pyalbert.config import  PROCONNECT_SESSION_DURATION
from helpers.redis.redis_session_middleware import redis_client
from pyalbert.config import SECRET_KEY

serializer = URLSafeSerializer(SECRET_KEY)

app = FastAPI()

    
def create_fake_user() -> UserInfo:
    fake = Faker()
    current_time = int(time.time())
    return UserInfo(
        sub=fake.uuid4(),
        email=fake.email(),
        given_name=fake.first_name(),
        usual_name=fake.last_name(),
        aud="france-services",
        exp=current_time + 3600,  # 1 hour from now
        iat=current_time,
        iss="https://mock.franceconnect.gouv.fr"
    )

@app.get('/userinfo')
async def userinfo(current_user: UserInfo = Depends(get_current_user)):
    return current_user

@app.get('/mocked-login')
async def mocked_login():
    user = create_fake_user()
    session_id = secrets.token_urlsafe()
    session_data = serializer.dumps(user.dict())
    redis_client.setex(session_id, PROCONNECT_SESSION_DURATION, session_data)
    
    response = JSONResponse({"message": "Logged in successfully"})
    response.set_cookie(key="session", value=session_id, httponly=True, max_age=PROCONNECT_SESSION_DURATION)
    return response

@app.get('/mocked-logout')
async def mocked_logout(request: Request):
    session_id = request.cookies.get("session")
    if session_id:
        redis_client.delete(session_id)
    
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("session")
    return response

@app.get('/healthcheck')
async def healthcheck():
    print("healthcheck called 🤖")
    return {"status": "ok"}
