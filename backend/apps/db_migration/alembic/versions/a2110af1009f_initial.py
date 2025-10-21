"""rename prompt table

Revision ID: a2110af1009f
Revises: 84d90b252a78
Create Date: 2025-10-17 17:08:51.203427

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a2110af1009f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade.
    """
    schema_upgrade()
    data_upgrade()

def downgrade():
    """Downgrade.
    """
    data_downgrade()
    schema_downgrade()

def schema_upgrade():
    """Upgrade schema."""

def schema_downgrade():
    """Downgrade schema."""

def data_upgrade():
    """Migrate existing data upward.
    """

def data_downgrade():
    """Migrate existing data downward.
    """
