"""phase_4_alerting_engine

Revision ID: 8d4a2b9ab83a
Revises: 2583b2f128b1
Create Date: 2026-05-16 05:29:25.488501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d4a2b9ab83a'
down_revision: Union[str, None] = '2583b2f128b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alert rules (user-scoped)
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('rule_type', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('threshold_value', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('comparison', sa.String(), server_default='gte'),
        sa.Column('cooldown_minutes', sa.Integer(), server_default='60'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('severity', sa.String(), server_default='info'),
        sa.Column('channels_json', sa.Text(), server_default='["email"]'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_rules_user_active', 'alert_rules', ['user_id', 'is_active'])

    # Alert events (history)
    op.create_table(
        'alert_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('rule_id', sa.String(), sa.ForeignKey('alert_rules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('dedup_hash', sa.String(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_events_user_triggered', 'alert_events', ['user_id', 'triggered_at'])

    # Alert deliveries (tracking)
    op.create_table(
        'alert_deliveries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('alert_event_id', sa.String(), sa.ForeignKey('alert_events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Notification preferences (per user)
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('email_enabled', sa.Boolean(), server_default=sa.true()),
        sa.Column('email_address', sa.String(), nullable=True),
        sa.Column('web_push_enabled', sa.Boolean(), server_default=sa.false()),
        sa.Column('web_push_subscription_json', sa.Text(), nullable=True),
        sa.Column('telegram_enabled', sa.Boolean(), server_default=sa.false()),
        sa.Column('telegram_chat_id', sa.String(), nullable=True),
        sa.Column('market_alerts_enabled', sa.Boolean(), server_default=sa.true()),
        sa.Column('execution_alerts_enabled', sa.Boolean(), server_default=sa.true()),
        sa.Column('risk_alerts_enabled', sa.Boolean(), server_default=sa.true()),
        sa.Column('min_severity', sa.String(), server_default='info'),
        sa.Column('quiet_hours_start', sa.Integer(), nullable=True),
        sa.Column('quiet_hours_end', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('alert_deliveries')
    op.drop_index('ix_alert_events_user_triggered', table_name='alert_events')
    op.drop_table('alert_events')
    op.drop_index('ix_alert_rules_user_active', table_name='alert_rules')
    op.drop_table('alert_rules')
