from sqlalchemy.orm import Session

from app import models, schemas


def get_chats(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Chat)
        .filter(models.Chat.user_id == user_id)
        .order_by(models.Chat.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_chat(db: Session, user_id: int, commit=True):
    db_chat = models.Chat(user_id=user_id)
    db.add(db_chat)
    if commit:
        db.commit()
        db.refresh(db_chat)
    return db_chat


def get_chat(db: Session, chat_id: int):
    return db.query(models.Chat).filter(models.Chat.id == chat_id).first()
