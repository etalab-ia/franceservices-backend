from sqlalchemy.orm import Session

from app import models, schemas


def get_feedbacks(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> list[models.Feedback]:
    return (
        db.query(models.Feedback)
        .filter(models.Feedback.user_id == user_id)
        .order_by(models.Feedback.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_feedback(db: Session, feedback_id: int) -> models.Feedback:
    return db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()


def create_feedback(
    db: Session, feedback: schemas.FeedbackCreate, user_id: int, stream_id: int, commit=True
) -> models.Feedback:
    feedback = feedback.model_dump()
    db_feedback = models.Feedback(**feedback, user_id=user_id, stream_id=stream_id)
    db.add(db_feedback)
    if commit:
        db.commit()
        db.refresh(db_feedback)
    return db_feedback


def delete_feedback(db: Session, feedback_id: int, commit=True):
    result = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).delete()
    if commit:
        db.commit()
    return result
