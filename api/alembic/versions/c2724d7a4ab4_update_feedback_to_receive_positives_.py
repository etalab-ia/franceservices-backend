"""Update Feedback to receive positives and negatives as arrays

Revision ID: c2724d7a4ab4
Revises: 2592138760af
Create Date: 2024-12-11 12:14:22.982087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2724d7a4ab4'
down_revision: Union[str, None] = '2592138760af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert 'positives' to JSON with explicit casting
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN positives TYPE JSON USING positives::TEXT::JSON
    """)
    # Add comment to 'positives'
    op.alter_column('feedbacks', 'positives',
               comment='Array of positive feedback strings',
               existing_nullable=True)

    # Convert 'negatives' to JSON with explicit casting
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN negatives TYPE JSON USING negatives::TEXT::JSON
    """)
    # Add comment to 'negatives'
    op.alter_column('feedbacks', 'negatives',
               comment='Array of negative feedback strings',
               existing_nullable=True)


def downgrade() -> None:
    # Convert 'negatives' back to ENUM with explicit casting
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN negatives TYPE VARCHAR USING negatives::TEXT
    """)
    op.alter_column('feedbacks', 'negatives',
               type_=postgresql.ENUM('incorrect', 'incoherent', 'manque_de_sources', name='feedbacknegatives'),
               existing_comment='Array of negative feedback strings',
               comment=None,
               existing_nullable=True)

    # Convert 'positives' back to ENUM with explicit casting
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN positives TYPE VARCHAR USING positives::TEXT
    """)
    op.alter_column('feedbacks', 'positives',
               type_=postgresql.ENUM('clair', 'synthetique', 'complet', 'sources_fiables', name='feedbackpositives'),
               existing_comment='Array of positive feedback strings',
               comment=None,
               existing_nullable=True)