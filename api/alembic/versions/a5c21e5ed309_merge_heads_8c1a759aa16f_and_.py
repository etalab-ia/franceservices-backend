"""Merge heads 8c1a759aa16f and 9d78427dfb52

Revision ID: a5c21e5ed309
Revises: 8c1a759aa16f, 9d78427dfb52
Create Date: 2024-09-25 16:21:13.716820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5c21e5ed309'
down_revision: Union[str, None] = ('8c1a759aa16f', '9d78427dfb52')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
