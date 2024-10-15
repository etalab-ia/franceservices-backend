from .chat import Chat, ChatArchive, ChatCreate, ChatUpdate, ChatWithRelationships
from .feedback import Feedback, FeedbackCreate, FeedbackWithRelationships
from .login import ResetPasswordForm, SendResetPasswordEmailForm, SignInForm
from .search import Index, QueryDocs
from .stream import Stream, StreamCreate, StreamWithRelationships
from .user import (
    ApiToken,
    ApiTokenCreate,
    ConfirmUser,
    ContactForm,
    User,
    UserCreate,
    UserWithRelationships,
)

ChatWithRelationships.model_rebuild()
StreamWithRelationships.model_rebuild()
FeedbackWithRelationships.model_rebuild()
UserWithRelationships.model_rebuild()
