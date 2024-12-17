"""added fields to feeback

Revision ID: 2592138760af
Revises: 92ecafbb1549
Create Date: 2024-12-11 11:23:31.861199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2592138760af'
down_revision: Union[str, None] = '92ecafbb1549'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Créer les types ENUM s'ils n'existent pas déjà
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_type') THEN
                CREATE TYPE feedback_type AS ENUM ('chat', 'evaluations');
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbackpositives') THEN
                CREATE TYPE feedbackpositives AS ENUM ('clair', 'synthetique', 'complet', 'sources_fiables');
            END IF;
        END$$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbacknegatives') THEN
                CREATE TYPE feedbacknegatives AS ENUM ('incorrect', 'incoherent', 'manque_de_sources');
            END IF;
        END$$;
    """)

    # 2. Ajouter la colonne "type" temporairement comme nullable pour éviter les conflits
    op.add_column(
        'feedbacks',
        sa.Column('type', sa.String(), nullable=True)
    )

    # 3. Mettre à jour les données pour correspondre aux valeurs ENUM
    op.execute("""
        UPDATE feedbacks
        SET type = 'chat'
        WHERE type IS NULL OR type NOT IN ('chat', 'evaluations');
    """)

    # 4. Modifier la colonne "type" pour utiliser l'ENUM feedback_type
    op.execute("""
        ALTER TABLE feedbacks
        ALTER COLUMN type TYPE feedback_type
        USING type::text::feedback_type;
    """)

    # 5. Définir la colonne "type" comme NON NULLABLE
    op.alter_column('feedbacks', 'type', nullable=False)

    # 6. Ajouter les autres colonnes
    op.add_column(
        'feedbacks',
        sa.Column('note', sa.Integer(), nullable=True, comment='Note from 0 to 5')
    )
    op.add_column(
        'feedbacks',
        sa.Column(
            'positives',
            sa.Enum('clair', 'synthetique', 'complet', 'sources_fiables', name='feedbackpositives'),
            nullable=True
        )
    )
    op.add_column(
        'feedbacks',
        sa.Column(
            'negatives',
            sa.Enum('incorrect', 'incoherent', 'manque_de_sources', name='feedbacknegatives'),
            nullable=True
        )
    )

def downgrade() -> None:
    # Drop columns
    op.drop_column('feedbacks', 'negatives')
    op.drop_column('feedbacks', 'positives')
    op.drop_column('feedbacks', 'note')
    op.drop_column('feedbacks', 'type')

    # Drop Enum types
    op.execute("DROP TYPE IF EXISTS feedbacknegatives")
    op.execute("DROP TYPE IF EXISTS feedbackpositives")
    op.execute("DROP TYPE IF EXISTS feedbacktype")