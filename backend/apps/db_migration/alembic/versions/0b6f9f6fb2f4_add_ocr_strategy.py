"""add ocr strategy fields

Revision ID: 0b6f9f6fb2f4
Revises: a2110af1009f
Create Date: 2026-01-25 12:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0b6f9f6fb2f4'
down_revision: Union[str, None] = 'a2110af1009f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade."""
    op.add_column(
        'tracked_document_sets',
        sa.Column('ocr_strategy', sa.String(length=32), nullable=False, server_default='hi_res'),
    )
    op.add_column(
        'tracked_documents',
        sa.Column('ocr_strategy', sa.String(length=32), nullable=False, server_default='use_document_set'),
    )


def downgrade():
    """Downgrade."""
    op.drop_column('tracked_documents', 'ocr_strategy')
    op.drop_column('tracked_document_sets', 'ocr_strategy')
