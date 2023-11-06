from app import crud, models, schemas
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/chats", response_model=list[schemas.Chat])
def read_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    chats = crud.chat.get_chats(db, current_user.id, skip=skip, limit=limit)
    return chats


@router.post("/chat", response_model=schemas.Chat)
def create_chat(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.chat.create_chat(db, current_user.id)


@router.get("/chat/{chat_id}", response_model=schemas.Chat)
def read_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_chat = crud.chat.get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if db_chat.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    return db_chat
