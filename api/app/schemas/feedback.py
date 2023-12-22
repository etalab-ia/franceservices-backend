from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, model_validator

if TYPE_CHECKING:
    from .user import User


class ReasonType(str, Enum):
    qa = "qa"
    meeting = "meeting"


class FeedbackBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    is_good: bool | None = None
    message: str | None = None
    reason: ReasonType | None = None

    @model_validator(mode="after")
    def validate_model(self):
        if all([x is None for x in [self.is_good, self.message, self.reason]]):
            raise ValueError("Empty feedback is not allowed.")
        return self


class FeedbackCreate(FeedbackBase):
    pass


class Feedback(FeedbackBase):
    id: int
    user_id: int
    stream_id: int

    class Config:
        orm_mode = True


class FeedbackWithRelationships(Feedback):
    user: Optional["User"]
