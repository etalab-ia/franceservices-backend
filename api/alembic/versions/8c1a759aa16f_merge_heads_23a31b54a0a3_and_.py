"""Merge heads 23a31b54a0a3 and 90479cfbcf9f

Revision ID: 8c1a759aa16f
Revises: 23a31b54a0a3, 90479cfbcf9f
Create Date: 2024-07-07 16:08:36.835282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c1a759aa16f'
down_revision: Union[str, None] = ('23a31b54a0a3', '90479cfbcf9f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
