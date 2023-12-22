from sqlalchemy.orm import Session

from app import models, schemas


def get_feedbacks(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Feedback)
        .filter(models.Feedback.user_id == user_id)
        .order_by(models.Feedback.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_feedback(
    db: Session, feedback: schemas.FeedbackCreate, user_id: int, stream_id: int, commit=True
):
    feedback = feedback.model_dump()
    db_feedback = models.Feedback(**feedback, user_id=user_id, stream_id=stream_id)
    db.add(db_feedback)
    if commit:
        db.commit()
        db.refresh(db_feedback)
    return db_feedback


def get_feedback(db: Session, feedback_id: int):
    return db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
