from fastapi import HTTPException
from itsdangerous import URLSafeSerializer
from starlette.requests import Request

from app.db.session import SessionLocal
from helpers.redis.redis_session_middleware import redis_client
from pyalbert.config import SECRET_KEY
from app.crud.user import UserInfo

serializer = URLSafeSerializer(SECRET_KEY)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
def get_current_user(request: Request) -> UserInfo:
    session_id = request.cookies.get("session")
    
    if not session_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    session_data = redis_client.get(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        user_data = serializer.loads(session_data)
        if "user" in user_data:
            user = UserInfo(**user_data["user"])
        else:
            user = UserInfo(**user_data)
        return user
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=401, detail="Invalid session data")
