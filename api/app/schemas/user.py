import re
from typing import TYPE_CHECKING

from pyalbert.config import PASSWORD_PATTERN
from pydantic import BaseModel, ConfigDict, EmailStr, constr, model_validator

if TYPE_CHECKING:
    from .stream import Stream

# ********
# * Misc *
# ********


class ContactForm(BaseModel):
    subject: str
    text: str
    institution: str | None = None


# ********
# * Auth *
# ********


class ConfirmUser(BaseModel):
    email: EmailStr
    is_confirmed: bool


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: constr(pattern=PASSWORD_PATTERN)

    model_config = ConfigDict(extra="forbid")


class User(UserBase):
    id: int
    is_confirmed: bool | None = None
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserWithRelationships(User):
    streams: list["Stream"] | None


class ApiTokenBase(BaseModel):
    name: str

    @model_validator(mode="after")
    def validate_model(self):
        pattern = re.compile(r"^[a-zA-Z0-9:_\-\.]{1,100}$")
        if not bool(pattern.match(self.name)):
            raise ValueError("Only alphanumeric and [:_-.] characters are supported.")

        return self


class ApiTokenCreate(ApiTokenBase):
    pass


class ApiToken(ApiTokenBase):
    pass
