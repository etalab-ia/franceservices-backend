from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, constr

from app.config import PASSWORD_PATTERN


class App(str, Enum):
    spp = "spp"
    albert = "albert"


class SignInForm(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: constr(pattern=PASSWORD_PATTERN)


class SendResetPasswordEmailForm(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr
    app: App = App.albert.value


class ResetPasswordForm(BaseModel):
    token: str
    password: constr(pattern=PASSWORD_PATTERN)
