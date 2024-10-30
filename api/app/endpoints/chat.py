from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.deps import get_current_user, get_db
from app.crud.user import UserInfo

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/chat/{chat_id}", response_model=schemas.Chat, tags=["chat"])
def read_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> models.Chat:
    db_chat = crud.chat.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if not (db_chat.user_id == current_user.id):
        raise HTTPException(403, detail="Forbidden")

    return db_chat


@router.get("/chats", response_model=list[schemas.Chat], tags=["chat"])
def read_chats(
    skip: int = 0,
    limit: int = 100,
    desc: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> list[models.Chat]:
    chats = crud.chat.get_chats(db, user_id=current_user.id, skip=skip, limit=limit, desc=desc)
    return chats


@router.post("/chat", response_model=schemas.Chat, tags=["chat"])
def create_chat(
    chat: schemas.ChatCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> models.Chat:
    return crud.chat.create_chat(db, chat, user_id=current_user.id)


@router.post("/chat/{chat_id}", response_model=schemas.Chat, tags=["chat"])
def update_chat(
    chat_id: int,
    chat_updates: schemas.ChatUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> models.Chat:
    db_chat = crud.chat.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if db_chat.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    crud.chat.update_chat(db, db_chat, chat_updates)
    return db_chat


@router.get("/chat/archive/{chat_id}", response_model=schemas.ChatArchive, tags=["chat"])
def read_chat_archive(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> schemas.ChatArchive:
    db_chat = crud.chat.get_chat_archive(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if not (db_chat.user_id == current_user.id):
        raise HTTPException(403, detail="Forbidden")

    return db_chat.to_dict()


@router.delete("/chat/delete/{chat_id}", response_model=schemas.Chat, tags=["chat"])
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
) -> models.Chat:
    db_chat = crud.chat.get_chat(db, chat_id=chat_id)
    if db_chat is None:
        raise HTTPException(404, detail="Chat not found")

    if db_chat.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    # Prevent a DetachedInstanceError error if the hybrid attribute stream_count is accessed after the object is deleted.
    c = db_chat.to_dict(with_streams=False)

    crud.chat.delete_chat(db, chat_id)

    return c
