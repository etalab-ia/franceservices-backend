"""v4

Revision ID: 2f54c357b7fe
Revises: 8079b4c73914
Create Date: 2024-01-10 15:06:16.480129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f54c357b7fe'
down_revision: Union[str, None] = '8079b4c73914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('streams', sa.Column('search_sids', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('streams', 'search_sids')
    # ### end Alembic commands ###