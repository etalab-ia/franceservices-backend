from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, EmailStr, Extra, constr

from app.config import PASSWORD_PATTERN

if TYPE_CHECKING:
    from .stream import Stream


class ConfirmUser(BaseModel):
    email: EmailStr
    is_confirmed: bool


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: constr(pattern=PASSWORD_PATTERN)

    class Config:
        extra = Extra.forbid


class User(UserBase):
    id: int
    is_confirmed: Optional[bool] = None
    is_admin: bool

    class Config:
        orm_mode = True


class UserWithRelationships(User):
    streams: list["Stream"] | None
