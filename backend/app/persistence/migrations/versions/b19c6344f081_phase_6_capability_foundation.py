"""phase_6_capability_foundation

Revision ID: b19c6344f081
Revises: f99eef8f0f6c
Create Date: 2026-05-16 15:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b19c6344f081'
down_revision: Union[str, None] = 'f99eef8f0f6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # plan_capabilities table
    op.create_table(
        'plan_capabilities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('feature_key', sa.String(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('limit_value', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'feature_key', name='uix_plan_feature')
    )
    op.create_index('ix_plan_capabilities_plan_id', 'plan_capabilities', ['plan_id'])

    # feature_flags table
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flag_key', sa.String(), nullable=False),
        sa.Column('flag_value', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'flag_key', name='uix_user_flag')
    )
    op.create_index('ix_feature_flags_user_id', 'feature_flags', ['user_id'])
    op.create_index('ix_feature_flags_expires', 'feature_flags', ['expires_at'])

    # Alter users table — use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('feature_flags_json', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('plan_started_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('plan_expires_at', sa.DateTime(), nullable=True))

    # Seed plan capabilities
    seed_plan_capabilities()


def seed_plan_capabilities() -> None:
    """Seed initial plan capability definitions."""
    bind = op.get_bind()

    capabilities = [
        # Free
        ("free", "scanner", True, None),
        ("free", "market_dashboard", True, None),
        ("free", "favorites", True, 5),
        ("free", "paper_trading", False, None),
        ("free", "execution", False, None),
        ("free", "exchange_accounts", False, None),
        ("free", "risk_rules", False, None),
        ("free", "alerts", False, None),
        ("free", "notifications", True, None),
        ("free", "rwa", True, None),
        ("free", "treasury", True, None),
        ("free", "api_access", False, None),
        ("free", "realtime_stream", True, None),
        # Pro
        ("pro", "scanner", True, None),
        ("pro", "market_dashboard", True, None),
        ("pro", "favorites", True, None),
        ("pro", "paper_trading", True, None),
        ("pro", "execution", True, None),
        ("pro", "exchange_accounts", True, 5),
        ("pro", "risk_rules", True, None),
        ("pro", "alerts", True, 10),
        ("pro", "notifications", True, None),
        ("pro", "rwa", True, None),
        ("pro", "treasury", True, None),
        ("pro", "api_access", False, None),
        ("pro", "realtime_stream", True, None),
        # Enterprise
        ("enterprise", "scanner", True, None),
        ("enterprise", "market_dashboard", True, None),
        ("enterprise", "favorites", True, None),
        ("enterprise", "paper_trading", True, None),
        ("enterprise", "execution", True, None),
        ("enterprise", "exchange_accounts", True, None),
        ("enterprise", "risk_rules", True, None),
        ("enterprise", "alerts", True, None),
        ("enterprise", "notifications", True, None),
        ("enterprise", "rwa", True, None),
        ("enterprise", "treasury", True, None),
        ("enterprise", "api_access", True, None),
        ("enterprise", "webhooks", True, None),
        ("enterprise", "white_label", True, None),
        ("enterprise", "realtime_stream", True, None),
    ]

    for plan_id, feature_key, is_enabled, limit_value in capabilities:
        bind.execute(
            sa.text("""
                INSERT INTO plan_capabilities (id, plan_id, feature_key, is_enabled, limit_value, created_at)
                VALUES (:id, :plan_id, :feature_key, :is_enabled, :limit_value, CURRENT_TIMESTAMP)
            """),
            {
                "id": str(uuid4()),
                "plan_id": plan_id,
                "feature_key": feature_key,
                "is_enabled": is_enabled,
                "limit_value": limit_value,
            }
        )


def downgrade() -> None:
    op.drop_index('ix_feature_flags_expires', table_name='feature_flags')
    op.drop_index('ix_feature_flags_user_id', table_name='feature_flags')
    op.drop_table('feature_flags')
    op.drop_index('ix_plan_capabilities_plan_id', table_name='plan_capabilities')
    op.drop_table('plan_capabilities')

    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('feature_flags_json')
        batch_op.drop_column('plan_started_at')
        batch_op.drop_column('plan_expires_at')
