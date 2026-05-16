"""phase_4_auth_extensions

Revision ID: bd43594cd747
Revises: 8d4a2b9ab83a
Create Date: 2026-05-16 06:00:14.028035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd43594cd747'
down_revision: Union[str, None] = '8d4a2b9ab83a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('session_version', sa.Integer(), server_default='1'))


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('session_version')
