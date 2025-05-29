"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


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
    """Upgrade schema.
    """
    ${upgrades if upgrades else ""}

def schema_downgrade():
    """Downgrade schema.
    """
    ${downgrades if downgrades else ""}

def data_upgrade():
    """Migrate existing data upward.
    """

def data_downgrade():
    """Migrate existing data downward.
    """
