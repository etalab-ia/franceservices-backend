from pydantic import BaseModel, EmailStr, Field
class UserInfo(BaseModel):
    id: str = Field(..., alias="sub")
    email: EmailStr
    given_name: str
    usual_name: str
    aud: str
    exp: int
    iat: int
    iss: str

    class Config:
        populate_by_name = True