"""Update Feedback to receive positives and negatives as enums

Revision ID: f1ec44cacbfe
Revises: c2724d7a4ab4
Create Date: 2024-12-11 12:28:24.410621

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1ec44cacbfe'
down_revision = 'c2724d7a4ab4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new enum type for 'type' column
    feedback_type_enum = postgresql.ENUM('chat', 'evaluations', name='feedback_type')
    feedback_type_enum.create(op.get_bind())  # Create the new enum type in the database

    # Alter 'type' column to use the new enum with explicit casting
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN type TYPE feedback_type
        USING type::text::feedback_type
    """)

    # Modify comments for 'positives' and 'negatives'
    op.alter_column(
        'feedbacks',
        'positives',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        comment='List of positive feedback values',
        existing_comment='Array of positive feedback strings',
        existing_nullable=True
    )
    op.alter_column(
        'feedbacks',
        'negatives',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        comment='List of negative feedback values',
        existing_comment='Array of negative feedback strings',
        existing_nullable=True
    )


def downgrade() -> None:
    # Revert 'type' column to use the old enum
    old_feedback_type_enum = postgresql.ENUM('chat', 'evaluations', name='feedbacktype')
    old_feedback_type_enum.create(op.get_bind())  # Recreate the old enum type

    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN type TYPE feedbacktype
        USING type::text::feedbacktype
    """)

    # Remove the new enum type
    new_feedback_type_enum = postgresql.ENUM('chat', 'evaluations', name='feedback_type')
    new_feedback_type_enum.drop(op.get_bind())  # Drop the new enum type

    # Restore old comments
    op.alter_column(
        'feedbacks',
        'positives',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        comment='Array of positive feedback strings',
        existing_comment='List of positive feedback values',
        existing_nullable=True
    )
    op.alter_column(
        'feedbacks',
        'negatives',
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        comment='Array of negative feedback strings',
        existing_comment='List of negative feedback values',
        existing_nullable=True
    )