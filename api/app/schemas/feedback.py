from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator, Field

from .user import User


class ReasonType(str, Enum):
    # Good
    reliable_sources = "reliable_sources"
    consistent = "consistent"
    concise = "concise"
    clear = "clear"
    # Bad
    lack_of_sources = "lack_of_sources"
    hallucinations = "hallucinations"
    inconsistent = "inconsistent"
    too_long = "too_long"
    grammar_errors = "grammar_errors"


class FeedbackBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    is_good: bool | None = Field(
        default=None,
        description="True means a +1 or positive feedback, while False means a -1 or negative feedback.",
    )
    message: str | None = Field(
        default=None, description="A free text feedback provided by an user."
    )
    reason: ReasonType | None = Field(
        default=None,
        description="A reason for positive or negative feedback in a given set possible values (enum).",
    )

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
        from_attributes = True


class FeedbackWithRelationships(Feedback):
    user: User | None
