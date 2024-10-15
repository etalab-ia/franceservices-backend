import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, EmailStr, constr, model_validator

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
