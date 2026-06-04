"""add_rwa_alerts_enabled

Revision ID: f99eef8f0f6c
Revises: b6fa1801e11d
Create Date: 2026-05-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f99eef8f0f6c'
down_revision: Union[str, None] = 'b6fa1801e11d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('notification_preferences') as batch_op:
        batch_op.add_column(sa.Column('rwa_alerts_enabled', sa.Boolean(), server_default=sa.true()))


def downgrade() -> None:
    with op.batch_alter_table('notification_preferences') as batch_op:
        batch_op.drop_column('rwa_alerts_enabled')
