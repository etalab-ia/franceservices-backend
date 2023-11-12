"""Second revision

Revision ID: 324c40362d79
Revises: 8eb351ec0fd8
Create Date: 2023-10-23 11:40:46.787985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '324c40362d79'
down_revision: Union[str, None] = '8eb351ec0fd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('streams', sa.Column('model_name', sa.Text(), nullable=True))
    op.add_column('streams', sa.Column('mode', sa.Text(), nullable=True))
    op.add_column('streams', sa.Column('query', sa.Text(), nullable=True))
    op.add_column('streams', sa.Column('limit', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('streams', 'limit')
    op.drop_column('streams', 'query')
    op.drop_column('streams', 'mode')
    op.drop_column('streams', 'model_name')
    # ### end Alembic commands ###