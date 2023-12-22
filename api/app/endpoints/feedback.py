from app import crud, models, schemas
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/feedbacks", response_model=list[schemas.Feedback])
def read_feedbacks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    feedbacks = crud.feedback.get_feedbacks(db, user_id=current_user.id, skip=skip, limit=limit)
    return feedbacks


@router.post("/feedback/add/{stream_id}", response_model=schemas.Feedback)
def create_feedback(
    stream_id: int,
    feedback: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_stream = crud.stream.get_stream(db, stream_id)
    if db_stream is None:
        raise HTTPException(404, detail="Stream not found")

    return crud.feedback.create_feedback(db, feedback, user_id=current_user.id, stream_id=stream_id)


@router.get("/feedback/{feedback_id}", response_model=schemas.Feedback)
def read_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_feedback = crud.feedback.get_feedback(db, feedback_id=feedback_id)
    if db_feedback is None:
        raise HTTPException(404, detail="Feedback not found")

    if db_feedback.user_id != current_user.id:
        raise HTTPException(403, detail="Forbidden")

    return db_feedback
