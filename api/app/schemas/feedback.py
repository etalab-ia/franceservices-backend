from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .user import User


class FeedbackType(str, Enum):
    chat = "chat"
    evaluations = "evaluations"


class FeedbackPositives(str, Enum):
    clair = "clair"
    synthetique = "synthetique"
    complet = "complet"
    sources_fiables = "sources_fiables"


class FeedbackNegatives(str, Enum):
    erreurs_grammaires = "erreurs_grammaires"
    hallucinations = "hallucinations"
    imprecisions = "imprecisions"
    inconsistance = "inconsistance"
    manque_de_sources = "manque_de_sources"
    trop_long = "trop_long"


class FeedbackBase(BaseModel):
    # Pydantic configuration:
    model_config = ConfigDict(use_enum_values=True)

    type: FeedbackType = Field(..., description="Type of feedback, either 'chat' or 'evaluations'.")
    note: Optional[int] = Field(default=None, description="Note from 0 to 5.")
    positives: Optional[List[FeedbackPositives]] = Field(
        default=None, description="List of positive feedback values (enum)."
    )
    negatives: Optional[List[FeedbackNegatives]] = Field(
        default=None, description="List of negative feedback values (enum)."
    )
    is_good: Optional[bool] = Field(default=None, description="True means positive feedback, False means negative.")
    message: Optional[str] = Field(default=None, description="A free text feedback provided by a user.")

    @model_validator(mode="after")
    def validate_model(self):
        if self.type == FeedbackType.chat:
            if self.is_good is None:
                raise ValueError("For 'chat' feedback, 'is_good' is required.")
        elif self.type == FeedbackType.evaluations:
            if self.note is None:
                raise ValueError("For 'evaluations' feedback, 'note' is required.")
            # At least one feedback list should be provided
            if not self.positives and not self.negatives:
                raise ValueError("For 'evaluations' feedback, at least 'positives' or 'negatives' is required.")
        else:
            raise ValueError("Feedback type must be either 'chat' or 'evaluations'.")

        return self


class FeedbackCreate(FeedbackBase):
    pass


class Feedback(FeedbackBase):
    id: int
    user_id: int
    stream_id: int

    model_config = ConfigDict(from_attributes=True)


class FeedbackWithRelationships(Feedback):
    user: Optional[User]