"""phase_4_realtime_streams

Revision ID: 2583b2f128b1
Revises: 69bd5d1e4711
Create Date: 2026-05-16 05:21:23.098484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2583b2f128b1'
down_revision: Union[str, None] = '69bd5d1e4711'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Realtime feed sessions
    op.create_table(
        'realtime_feed_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('feed_type', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('channel', sa.String(), nullable=True),
        sa.Column('symbols', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Normalized stream events
    op.create_table(
        'stream_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), sa.ForeignKey('realtime_feed_sessions.id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stream_events_session_symbol', 'stream_events', ['session_id', 'symbol'])


def downgrade() -> None:
    op.drop_index('ix_stream_events_session_symbol', table_name='stream_events')
    op.drop_table('stream_events')
    op.drop_table('realtime_feed_sessions')
