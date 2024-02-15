from app import crud, models, schemas
from app.clients.mailjet_client import MailjetClient
from app.config import FIRST_ADMIN_EMAIL, CONTACT_EMAIL
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/users/pending", response_model=list[schemas.User], tags=["user"])
def read_pending_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.User]:
    if not current_user.is_admin:
        raise HTTPException(403, detail="Forbidden")

    return crud.user.get_pending_users(db)


@router.post("/user/me", tags=["user"])
def create_user_me(
    form_data: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    username = form_data.username
    email = form_data.email
    if crud.user.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already exists")

    if crud.user.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    crud.user.create_user(db, form_data)
    mailjet_client = MailjetClient()
    mailjet_client.send_create_user_me_email(email)
    mailjet_client.send_create_user_me_notify_admin_email(CONTACT_EMAIL, email)
    return {"msg": "User created. An admin must confirm the user."}


@router.get("/user/me", response_model=schemas.User, tags=["user"])
def read_user_me(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    return current_user


@router.post("/user/confirm", tags=["user"])
def confirm_user(
    form_data: schemas.ConfirmUser,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> dict[str, str]:
    if not current_user.is_admin:
        raise HTTPException(403, detail="Forbidden")

    email = form_data.email
    is_confirmed = form_data.is_confirmed

    db_user = crud.user.get_user_by_email(db, email)
    if not db_user:
        raise HTTPException(404, detail="User not found")

    if db_user.is_confirmed is not None:
        raise HTTPException(400, detail="Account creation already accepted or declined")

    crud.user.confirm_user(db, db_user, is_confirmed)
    if is_confirmed:
        mailjet_client = MailjetClient()
        mailjet_client.send_confirm_user_email(email)
    return {"msg": "Success"}


@router.post("/user/contact", tags=["user"])
def contact_user(
    form_data: schemas.ContactForm,
    current_user: models.User = Depends(get_current_user),
) -> dict[str, str]:
    mailjet_client = MailjetClient()
    mailjet_client.send_contact_email(current_user, form_data.subject, form_data.text, form_data.institution)
    return {"msg": "Contact form email sent"}
