from pydantic import BaseModel, EmailStr, constr

from app.config import PASSWORD_PATTERN


class SignInForm(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: constr(pattern=PASSWORD_PATTERN)


class SendResetPasswordEmailForm(BaseModel):
    email: EmailStr


class ResetPasswordForm(BaseModel):
    token: str
    password: constr(pattern=PASSWORD_PATTERN)
