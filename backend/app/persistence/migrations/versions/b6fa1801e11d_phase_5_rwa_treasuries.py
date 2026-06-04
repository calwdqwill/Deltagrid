"""phase_5_rwa_treasuries

Revision ID: b6fa1801e11d
Revises: bd43594cd747
Create Date: 2026-05-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6fa1801e11d'
down_revision: Union[str, None] = 'bd43594cd747'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # RWA asset master data
    op.create_table(
        'rwa_assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('asset_class', sa.String(), server_default='rwa', nullable=False),
        sa.Column('issuer', sa.String(), nullable=True),
        sa.Column('blockchain', sa.String(), nullable=True),
        sa.Column('contract_address', sa.String(), nullable=True),
        sa.Column('decimals', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('is_executable', sa.Boolean(), server_default=sa.false()),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', name='uix_rwa_symbol')
    )

    # RWA asset snapshots (time-series)
    op.create_table(
        'rwa_asset_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('asset_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_quality', sa.String(), server_default='verified', nullable=False),
        sa.Column('price_usd', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('nav_usd', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('market_cap_usd', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('total_supply', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('volume_24h_usd', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('yield_apr', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('premium_discount_pct', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('raw_payload_json', sa.Text(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('next_expected_update_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['asset_id'], ['rwa_assets.id'], ondelete='CASCADE')
    )
    op.create_index('ix_rwa_snap_asset_fetched', 'rwa_asset_snapshots', ['asset_id', sa.text('fetched_at DESC')])

    # Treasury entities (companies, platforms, issuers)
    op.create_table(
        'treasury_entities',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=True),
        sa.Column('sector', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uix_treasury_name')
    )

    # Treasury snapshots (holdings, exposure)
    op.create_table(
        'treasury_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_quality', sa.String(), server_default='verified', nullable=False),
        sa.Column('btc_holdings', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('btc_value_usd', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('total_treasury_usd', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('shares_outstanding', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('btc_per_share', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('raw_payload_json', sa.Text(), nullable=True),
        sa.Column('report_date', sa.Date(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('next_expected_update_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entity_id'], ['treasury_entities.id'], ondelete='CASCADE')
    )
    op.create_index('ix_treasury_snap_entity_date', 'treasury_snapshots', ['entity_id', sa.text('report_date DESC')])

    # Tokenization platforms
    op.create_table(
        'tokenization_platforms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(), nullable=True),
        sa.Column('tvl_usd', sa.DECIMAL(24, 8), nullable=True),
        sa.Column('active_pools', sa.Integer(), nullable=True),
        sa.Column('blockchain', sa.String(), nullable=True),
        sa.Column('governance_token', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uix_platform_name')
    )


def downgrade() -> None:
    op.drop_table('tokenization_platforms')
    op.drop_index('ix_treasury_snap_entity_date', table_name='treasury_snapshots')
    op.drop_table('treasury_snapshots')
    op.drop_table('treasury_entities')
    op.drop_index('ix_rwa_snap_asset_fetched', table_name='rwa_asset_snapshots')
    op.drop_table('rwa_asset_snapshots')
    op.drop_table('rwa_assets')
