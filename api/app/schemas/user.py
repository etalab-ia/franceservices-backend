import re
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, constr, model_validator, validator

from pyalbert.config import PASSWORD_PATTERN
from pyalbert.lexicon.mfs_organizations import MFS_ORGANIZATIONS

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
    # login
    username: str
    email: EmailStr

    # Org/Role
    organization_id: str | None = None  # For MFS, Matricule
    organization_name: str | None = None

    # RGPD
    accept_cookie: bool = False
    accept_retrain: bool = False


class User(BaseModel):
    id: str
    username: str
    email: str

    is_confirmed: Optional[bool] = False
    is_admin: Optional[bool] = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    accept_cookie: Optional[bool] = False
    accept_retrain: Optional[bool] = False
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None

    @validator("is_confirmed", "is_admin", "accept_cookie", "accept_retrain", pre=True)
    def parse_bool(cls, v):
        if isinstance(v, list) and len(v) == 1:
            v = v[0]
        if isinstance(v, str):
            return v.lower() == "true"
        return v

    @validator("organization_id", "organization_name", "created_at", "updated_at", pre=True)
    def unwrap_single_element_list(cls, v):
        if isinstance(v, list) and len(v) == 1:
            return v[0]
        return v

    class Config:
        orm_mode = True

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: constr(pattern=PASSWORD_PATTERN)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_model(self):
        organisation_data_required = [self.organization_id, self.organization_name]
        organisation_data_required = [
            "_empty_not_allowed_" if s == "" else s for s in organisation_data_required
        ]
        if any(organisation_data_required) and not all(organisation_data_required):
            raise ValueError("organization_id and organization_name must be jointly given.")

        if any(organisation_data_required):
            found = 0
            for x in MFS_ORGANIZATIONS:
                if x["id"] == self.organization_id:
                    found += 1
                    if x["name"] == self.organization_name:
                        found += 1
                if found == 2:
                    break
            if found == 0:
                raise ValueError("unknown organization_id")
            elif found == 1:
                raise ValueError("unknown organization_name")

        return self


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
