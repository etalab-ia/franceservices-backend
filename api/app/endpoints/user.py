from fastapi import APIRouter, Depends
from app.crud.user import UserInfo
from app.deps import get_current_user

router = APIRouter()

@router.get('/userinfo', tags=["user"])
async def userinfo(current_user: UserInfo = Depends(get_current_user)):
    return current_user
