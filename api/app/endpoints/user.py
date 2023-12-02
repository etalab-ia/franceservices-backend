from app import crud, models, schemas
from app.clients.mailjet_client import MailjetClient
from app.config import FIRST_ADMIN_EMAIL
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/users/pending", response_model=list[schemas.User])
def read_pending_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(403, detail="Forbidden")

    return crud.user.get_pending_users(db)


@router.post("/user/me")
def create_user_me(
    form_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    username = form_data.username
    email = form_data.email
    if crud.user.get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="Username already exists")

    if crud.user.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already exists")

    crud.user.create_user(db, form_data)
    mailjet_client = MailjetClient()
    mailjet_client.send_create_user_me_email(email)
    mailjet_client.send_create_user_me_notify_admin_email(FIRST_ADMIN_EMAIL, email)
    return {"msg": "User created. An admin must confirm the user."}


@router.get("/user/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@router.post("/user/confirm")
def confirm_user(
    form_data: schemas.ConfirmUser,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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


@router.post("/user/contact")
def contact_user(
    form: schemas.ContactForm,
    current_user: models.User = Depends(get_current_user),
):
    mailjet_client = MailjetClient()
    mailjet_client.send_contact_email(current_user, form.subject, form.text, form.institution)
    return {"msg": "Contact form email sent"}

