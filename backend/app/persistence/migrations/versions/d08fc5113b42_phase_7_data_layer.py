"""phase_7_data_layer

Revision ID: d08fc5113b42
Revises: b19c6344f081
Create Date: 2026-06-02 02:00:01.462299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'd08fc5113b42'
down_revision: Union[str, None] = 'b19c6344f081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- Phase 7: Data Layer tables ----------------------------------------
    op.create_table('basis_premium',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('spot_price', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('perp_price', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('basis_usd', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('basis_pct', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('funding_annualized_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('basis_premium', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_basis_premium_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_basis_premium_symbol'), ['symbol'], unique=False)
        batch_op.create_index(batch_op.f('ix_basis_premium_timestamp'), ['timestamp'], unique=False)

    op.create_table('data_quality_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('interval', sa.String(), nullable=True),
        sa.Column('check_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('expected_count', sa.Integer(), nullable=True),
        sa.Column('actual_count', sa.Integer(), nullable=True),
        sa.Column('gap_start', sa.Integer(), nullable=True),
        sa.Column('gap_end', sa.Integer(), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('data_quality_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_data_quality_logs_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_quality_logs_symbol'), ['symbol'], unique=False)
        batch_op.create_index(batch_op.f('ix_data_quality_logs_table_name'), ['table_name'], unique=False)

    op.create_table('exchange_fees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('maker_pct', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('taker_pct', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('withdrawal_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('tier', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('exchange')
    )

    op.create_table('funding_rates',
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('funding_rate', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('next_funding_time', sa.Integer(), nullable=True),
        sa.Column('interval_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', name='pk_funding_rates')
    )
    with op.batch_alter_table('funding_rates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_funding_rates_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_funding_rates_symbol'), ['symbol'], unique=False)

    op.create_table('instruments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('canonical_symbol', sa.String(), nullable=False),
        sa.Column('base_asset', sa.String(), nullable=False),
        sa.Column('quote_asset', sa.String(), nullable=False),
        sa.Column('instrument_type', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_symbol', 'exchange', 'instrument_type', name='uix_instrument')
    )
    with op.batch_alter_table('instruments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_instruments_canonical_symbol'), ['canonical_symbol'], unique=False)
        batch_op.create_index(batch_op.f('ix_instruments_exchange'), ['exchange'], unique=False)

    op.create_table('liquidations',
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('quantity', sa.DECIMAL(precision=24, scale=8), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('value_usd', sa.DECIMAL(precision=24, scale=8), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'side', name='pk_liquidations')
    )
    with op.batch_alter_table('liquidations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_liquidations_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_liquidations_symbol'), ['symbol'], unique=False)

    op.create_table('long_short_ratio',
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('long_ratio', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('short_ratio', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('long_account_ratio', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('short_account_ratio', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_long_short_ratio')
    )
    with op.batch_alter_table('long_short_ratio', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_long_short_ratio_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_long_short_ratio_symbol'), ['symbol'], unique=False)

    op.create_table('ohlcv',
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('open', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('high', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('low', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('close', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('volume', sa.DECIMAL(precision=24, scale=8), nullable=False),
        sa.Column('quote_volume', sa.DECIMAL(precision=24, scale=8), nullable=True),
        sa.Column('trades_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_ohlcv')
    )
    with op.batch_alter_table('ohlcv', schema=None) as batch_op:
        batch_op.create_index('idx_ohlcv_lookup', ['symbol', 'exchange', 'interval', 'timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_ohlcv_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_ohlcv_symbol'), ['symbol'], unique=False)

    op.create_table('open_interest',
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('oi_usd', sa.DECIMAL(precision=24, scale=8), nullable=True),
        sa.Column('oi_coins', sa.DECIMAL(precision=24, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_open_interest')
    )
    with op.batch_alter_table('open_interest', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_open_interest_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_open_interest_symbol'), ['symbol'], unique=False)

    op.create_table('provider_sync_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('interval', sa.String(), nullable=True),
        sa.Column('start_time', sa.Integer(), nullable=False),
        sa.Column('end_time', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('records_fetched', sa.Integer(), nullable=True),
        sa.Column('records_inserted', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('api_requests_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('provider_sync_runs', schema=None) as batch_op:
        batch_op.create_index('idx_sync_runs_lookup', ['provider_name', 'sync_type', 'status', 'created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_provider_sync_runs_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_provider_sync_runs_provider_name'), ['provider_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_provider_sync_runs_symbol'), ['symbol'], unique=False)

    op.create_table('backtest_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('strategy', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('start_time', sa.Integer(), nullable=False),
        sa.Column('end_time', sa.Integer(), nullable=False),
        sa.Column('initial_balance', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('leverage', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('commission_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('slippage_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('backtest_configs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_backtest_configs_exchange'), ['exchange'], unique=False)
        batch_op.create_index(batch_op.f('ix_backtest_configs_symbol'), ['symbol'], unique=False)
        batch_op.create_index(batch_op.f('ix_backtest_configs_user_id'), ['user_id'], unique=False)

    op.create_table('instrument_aliases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('instrument_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('alias', sa.String(), nullable=False),
        sa.Column('alias_type', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'alias', name='uix_provider_alias')
    )
    with op.batch_alter_table('instrument_aliases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_instrument_aliases_instrument_id'), ['instrument_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_instrument_aliases_provider'), ['provider'], unique=False)

    op.create_table('backtest_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('config_id', sa.String(), nullable=False),
        sa.Column('total_return_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('sharpe_ratio', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('max_drawdown_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('win_rate_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('profit_factor', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('losing_trades', sa.Integer(), nullable=True),
        sa.Column('avg_trade_duration_ms', sa.Integer(), nullable=True),
        sa.Column('equity_curve_json', sa.Text(), nullable=True),
        sa.Column('metrics_json', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['config_id'], ['backtest_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('backtest_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_backtest_results_config_id'), ['config_id'], unique=False)

    op.create_table('backtest_equity',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('result_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=False),
        sa.Column('equity', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('drawdown_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['result_id'], ['backtest_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('result_id', 'timestamp', name='uix_backtest_equity_ts')
    )
    with op.batch_alter_table('backtest_equity', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_backtest_equity_result_id'), ['result_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_backtest_equity_timestamp'), ['timestamp'], unique=False)

    op.create_table('backtest_trades',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('result_id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('entry_price', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('exit_price', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('quantity', sa.DECIMAL(precision=18, scale=8), nullable=False),
        sa.Column('pnl', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('pnl_pct', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('fee', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('slippage', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('opened_at', sa.Integer(), nullable=False),
        sa.Column('closed_at', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['result_id'], ['backtest_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('backtest_trades', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_backtest_trades_result_id'), ['result_id'], unique=False)

    # -- Seed data ---------------------------------------------------------
    _seed_data()


def _seed_data() -> None:
    """Seed instruments, aliases, and exchange fees."""
    import uuid
    from datetime import datetime

    conn = op.get_bind()

    # Exchange fees
    fees = [
        ('binance', 0.02, 0.05, None, None, 'default'),
        ('bybit', 0.02, 0.055, None, None, 'default'),
        ('okx', 0.02, 0.05, None, None, 'default'),
        ('hyperliquid', 0.0, 0.035, None, None, 'default'),
    ]
    for exchange, maker, taker, withdrawal, symbol, tier in fees:
        conn.execute(sa.text(
            "INSERT INTO exchange_fees (id, exchange, maker_pct, taker_pct, withdrawal_pct, symbol, tier, created_at) "
            "VALUES (:id, :ex, :maker, :taker, :withdrawal, :sym, :tier, :now)"
        ), {
            'id': str(uuid.uuid4()), 'ex': exchange, 'maker': maker, 'taker': taker,
            'withdrawal': withdrawal, 'sym': symbol, 'tier': tier, 'now': datetime.utcnow()
        })

    # Instruments + aliases
    instruments = [
        {
            'canonical': 'BTC', 'base': 'BTC', 'quote': 'USDT', 'type': 'perp', 'exchange': 'binance',
            'aliases': [
                ('binance', 'BTCUSDT', 'ticker', True),
                ('coinglass', 'BTC', 'ticker', True),
                ('coingecko', 'bitcoin', 'cg_id', True),
                ('coingecko', 'btc', 'cg_symbol', False),
                ('bybit', 'BTCUSDT', 'ticker', True),
                ('okx', 'BTC-USDT-SWAP', 'ticker', True),
                ('hyperliquid', 'BTC', 'ticker', True),
            ]
        },
        {
            'canonical': 'ETH', 'base': 'ETH', 'quote': 'USDT', 'type': 'perp', 'exchange': 'binance',
            'aliases': [
                ('binance', 'ETHUSDT', 'ticker', True),
                ('coinglass', 'ETH', 'ticker', True),
                ('coingecko', 'ethereum', 'cg_id', True),
                ('coingecko', 'eth', 'cg_symbol', False),
                ('bybit', 'ETHUSDT', 'ticker', True),
                ('okx', 'ETH-USDT-SWAP', 'ticker', True),
                ('hyperliquid', 'ETH', 'ticker', True),
            ]
        },
        {
            'canonical': 'SOL', 'base': 'SOL', 'quote': 'USDT', 'type': 'perp', 'exchange': 'binance',
            'aliases': [
                ('binance', 'SOLUSDT', 'ticker', True),
                ('coinglass', 'SOL', 'ticker', True),
                ('coingecko', 'solana', 'cg_id', True),
                ('coingecko', 'sol', 'cg_symbol', False),
                ('bybit', 'SOLUSDT', 'ticker', True),
                ('okx', 'SOL-USDT-SWAP', 'ticker', True),
                ('hyperliquid', 'SOL', 'ticker', True),
            ]
        },
        {
            'canonical': 'HYPE', 'base': 'HYPE', 'quote': 'USDT', 'type': 'perp', 'exchange': 'hyperliquid',
            'aliases': [
                ('binance', 'HYPEUSDT', 'ticker', True),
                ('coinglass', 'HYPE', 'ticker', True),
                ('coingecko', 'hyperliquid', 'cg_id', True),
                ('coingecko', 'hype', 'cg_symbol', False),
                ('bybit', 'HYPEUSDT', 'ticker', True),
                ('okx', 'HYPE-USDT-SWAP', 'ticker', True),
                ('hyperliquid', 'HYPE', 'ticker', True),
            ]
        },
    ]

    for inst in instruments:
        inst_id = str(uuid.uuid4())
        conn.execute(sa.text(
            "INSERT INTO instruments (id, canonical_symbol, base_asset, quote_asset, instrument_type, exchange, is_active, created_at, updated_at) "
            "VALUES (:id, :canon, :base, :quote, :type, :ex, 1, :now, :now)"
        ), {
            'id': inst_id, 'canon': inst['canonical'], 'base': inst['base'],
            'quote': inst['quote'], 'type': inst['type'], 'ex': inst['exchange'],
            'now': datetime.utcnow()
        })
        for provider, alias, alias_type, is_primary in inst['aliases']:
            conn.execute(sa.text(
                "INSERT INTO instrument_aliases (id, instrument_id, provider, alias, alias_type, is_primary, created_at) "
                "VALUES (:id, :iid, :provider, :alias, :atype, :primary, :now)"
            ), {
                'id': str(uuid.uuid4()), 'iid': inst_id, 'provider': provider,
                'alias': alias, 'atype': alias_type,
                'primary': 1 if is_primary else 0, 'now': datetime.utcnow()
            })


def downgrade() -> None:
    op.drop_table('backtest_trades')
    with op.batch_alter_table('backtest_equity', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_backtest_equity_timestamp'))
        batch_op.drop_index(batch_op.f('ix_backtest_equity_result_id'))
    op.drop_table('backtest_equity')
    with op.batch_alter_table('backtest_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_backtest_results_config_id'))
    op.drop_table('backtest_results')
    with op.batch_alter_table('instrument_aliases', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_instrument_aliases_provider'))
        batch_op.drop_index(batch_op.f('ix_instrument_aliases_instrument_id'))
    op.drop_table('instrument_aliases')
    with op.batch_alter_table('backtest_configs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_backtest_configs_user_id'))
        batch_op.drop_index(batch_op.f('ix_backtest_configs_symbol'))
        batch_op.drop_index(batch_op.f('ix_backtest_configs_exchange'))
    op.drop_table('backtest_configs')
    with op.batch_alter_table('provider_sync_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_provider_sync_runs_symbol'))
        batch_op.drop_index(batch_op.f('ix_provider_sync_runs_provider_name'))
        batch_op.drop_index(batch_op.f('ix_provider_sync_runs_exchange'))
        batch_op.drop_index('idx_sync_runs_lookup')
    op.drop_table('provider_sync_runs')
    with op.batch_alter_table('open_interest', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_open_interest_symbol'))
        batch_op.drop_index(batch_op.f('ix_open_interest_exchange'))
    op.drop_table('open_interest')
    with op.batch_alter_table('ohlcv', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ohlcv_symbol'))
        batch_op.drop_index(batch_op.f('ix_ohlcv_exchange'))
        batch_op.drop_index('idx_ohlcv_lookup')
    op.drop_table('ohlcv')
    with op.batch_alter_table('long_short_ratio', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_long_short_ratio_symbol'))
        batch_op.drop_index(batch_op.f('ix_long_short_ratio_exchange'))
    op.drop_table('long_short_ratio')
    with op.batch_alter_table('liquidations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_liquidations_symbol'))
        batch_op.drop_index(batch_op.f('ix_liquidations_exchange'))
    op.drop_table('liquidations')
    with op.batch_alter_table('instruments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_instruments_exchange'))
        batch_op.drop_index(batch_op.f('ix_instruments_canonical_symbol'))
    op.drop_table('instruments')
    with op.batch_alter_table('funding_rates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_funding_rates_symbol'))
        batch_op.drop_index(batch_op.f('ix_funding_rates_exchange'))
    op.drop_table('funding_rates')
    op.drop_table('exchange_fees')
    with op.batch_alter_table('data_quality_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_data_quality_logs_table_name'))
        batch_op.drop_index(batch_op.f('ix_data_quality_logs_symbol'))
        batch_op.drop_index(batch_op.f('ix_data_quality_logs_exchange'))
    op.drop_table('data_quality_logs')
    with op.batch_alter_table('basis_premium', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_basis_premium_timestamp'))
        batch_op.drop_index(batch_op.f('ix_basis_premium_symbol'))
        batch_op.drop_index(batch_op.f('ix_basis_premium_exchange'))
    op.drop_table('basis_premium')
