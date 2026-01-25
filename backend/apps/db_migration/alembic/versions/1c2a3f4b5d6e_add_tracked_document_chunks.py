"""
Revision ID: 1c2a3f4b5d6e
Revises: 0b6f9f6fb2f4
Create Date: 2026-01-25 13:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1c2a3f4b5d6e'
down_revision: Union[str, None] = '0b6f9f6fb2f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade."""
    op.create_table(
        'tracked_document_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tracked_document_id', sa.Uuid(), nullable=False),
        sa.Column('vector_id', sa.String(length=200), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['tracked_document_id'],
            ['tracked_documents.id'],
            name='fk_tracked_document_chunks_document',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute(
        """
        INSERT INTO tracked_document_chunks (id, tracked_document_id, vector_id)
        SELECT gen_random_uuid(), id, unnest(vector_ids)
        FROM tracked_documents
        WHERE vector_ids IS NOT NULL
        """
    )

    op.drop_column('tracked_documents', 'vector_ids')


def downgrade():
    """Downgrade."""
    op.add_column(
        'tracked_documents',
        sa.Column('vector_ids', postgresql.ARRAY(sa.String()), nullable=True),
    )

    op.execute(
        """
        UPDATE tracked_documents
        SET vector_ids = chunk_data.vector_ids
        FROM (
            SELECT tracked_document_id, array_agg(vector_id) AS vector_ids
            FROM tracked_document_chunks
            GROUP BY tracked_document_id
        ) AS chunk_data
        WHERE tracked_documents.id = chunk_data.tracked_document_id
        """
    )

    op.drop_table('tracked_document_chunks')
