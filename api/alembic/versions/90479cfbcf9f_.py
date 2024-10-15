"""empty message

Revision ID: 90479cfbcf9f
Revises: 40fcf98bde4c
Create Date: 2024-06-26 10:51:06.002191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90479cfbcf9f'
down_revision: Union[str, None] = '40fcf98bde4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chats', sa.Column('operator', sa.Text(), nullable=True))
    op.add_column('chats', sa.Column('themes', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chats', 'themes')
    op.drop_column('chats', 'operator')
    # ### end Alembic commands ###