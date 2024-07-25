from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic.
revision: str = 'ca390c84606d'
down_revision: Union[str, None] = '40fcf98bde4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop foreign key constraints first
    op.drop_constraint('chats_user_id_fkey', 'chats', type_='foreignkey')
    op.drop_constraint('password_reset_tokens_user_id_fkey', 'password_reset_tokens', type_='foreignkey')
    op.drop_constraint('streams_user_id_fkey', 'streams', type_='foreignkey')
    op.drop_constraint('feedbacks_user_id_fkey', 'feedbacks', type_='foreignkey')
    op.drop_constraint('api_tokens_user_id_fkey', 'api_tokens', type_='foreignkey')

    # Drop the users table
    op.drop_table('users')

    # Drop the api_tokens table
    op.drop_table('api_tokens')

    # Update the feedbacks table user_id column type
    op.alter_column(
        'feedbacks', 
        'user_id',
        existing_type=sa.INTEGER(),
        type_=sa.String(),
        existing_nullable=True
    )

def downgrade() -> None:
    # Recreate the users table
    op.create_table(
        'users',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('is_confirmed', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('is_admin', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
        sa.Column('accept_cookie', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('accept_retrain', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('organization_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('organization_name', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='users_pkey')
    )

    # Recreate indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_organization_id', 'users', ['organization_id'], unique=False)
    op.create_index('ix_users_organization_name', 'users', ['organization_name'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=False)

    # Recreate foreign key constraints
    op.create_foreign_key('chats_user_id_fkey', 'chats', 'users', ['user_id'], ['id'])
    op.create_foreign_key('password_reset_tokens_user_id_fkey', 'password_reset_tokens', 'users', ['user_id'], ['id'])
    op.create_foreign_key('streams_user_id_fkey', 'streams', 'users', ['user_id'], ['id'])
    op.create_foreign_key('feedbacks_user_id_fkey', 'feedbacks', 'users', ['user_id'], ['id'])
    op.create_foreign_key('api_tokens_user_id_fkey', 'api_tokens', 'users', ['user_id'], ['id'])

    # Recreate the api_tokens table
    op.create_table(
        'api_tokens',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.Column('hash', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='api_tokens_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='api_tokens_pkey')
    )

    # Recreate indexes
    op.create_index('ix_api_tokens_hash', 'api_tokens', ['hash'], unique=False)
    op.create_index('ix_api_tokens_id', 'api_tokens', ['id'], unique=False)

    # Revert feedbacks table user_id column type
    op.alter_column(
        'feedbacks', 
        'user_id',
        existing_type=sa.String(),
        type_=sa.INTEGER(),
        existing_nullable=True
    )
