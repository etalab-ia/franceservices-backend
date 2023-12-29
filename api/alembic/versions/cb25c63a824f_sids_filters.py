"""sids_filters

Revision ID: cb25c63a824f
Revises: 324c40362d79
Create Date: 2023-12-21 01:15:48.336992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb25c63a824f'
down_revision: Union[str, None] = '324c40362d79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('streams', sa.Column('should_sids', sa.JSON(), nullable=True))
    op.add_column('streams', sa.Column('must_not_sids', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('streams', 'should_sids')
    op.drop_column('streams', 'must_not_sids')
