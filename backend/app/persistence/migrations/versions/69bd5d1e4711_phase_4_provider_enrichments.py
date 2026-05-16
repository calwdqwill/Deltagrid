"""phase_4_provider_enrichments

Revision ID: 69bd5d1e4711
Revises: 9cc9da229c47
Create Date: 2026-05-15 21:08:31.898851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69bd5d1e4711'
down_revision: Union[str, None] = '9cc9da229c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Provider health tracking
    op.create_table(
        'provider_health',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('avg_response_ms', sa.Integer(), nullable=True),
        sa.Column('failure_count_24h', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name')
    )

    # Market enrichments (CoinGlass, GeckoTerminal data)
    op.create_table(
        'market_enrichments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('enrichment_type', sa.String(), nullable=False),
        sa.Column('value_decimal', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('value_json', sa.Text(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), server_default='300'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_enrichments_symbol_type_ts', 'market_enrichments', ['symbol', 'enrichment_type', 'timestamp'])

    # Provider sync logs
    op.create_table(
        'provider_sync_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('records_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_sync_logs_name_created', 'provider_sync_logs', ['provider_name', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_provider_sync_logs_name_created', table_name='provider_sync_logs')
    op.drop_table('provider_sync_logs')
    op.drop_index('ix_market_enrichments_symbol_type_ts', table_name='market_enrichments')
    op.drop_table('market_enrichments')
    op.drop_table('provider_health')
