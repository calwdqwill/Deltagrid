"""phase_7_data_layer

Revision ID: eacf4f46c7ce
Revises: b19c6344f081
Create Date: 2026-06-01 15:11:15.889696

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eacf4f46c7ce'
down_revision: Union[str, None] = 'b19c6344f081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- Symbol Mapping -----------------------------------------------------
    op.create_table(
        'instruments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('canonical_symbol', sa.String(), nullable=False),
        sa.Column('base_asset', sa.String(), nullable=False),
        sa.Column('quote_asset', sa.String(), nullable=False),
        sa.Column('instrument_type', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_symbol', 'exchange', 'instrument_type', name='uix_instrument')
    )
    op.create_index('ix_instruments_lookup', 'instruments', ['canonical_symbol', 'instrument_type', 'exchange'])
    op.create_index('ix_instruments_active', 'instruments', ['is_active'])

    op.create_table(
        'instrument_aliases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('instrument_id', sa.String(), sa.ForeignKey('instruments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('alias', sa.String(), nullable=False),
        sa.Column('alias_type', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.false(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'alias', name='uix_provider_alias')
    )
    op.create_index('ix_aliases_provider', 'instrument_aliases', ['provider', 'alias_type', 'is_primary'])
    op.create_index('ix_aliases_instrument', 'instrument_aliases', ['instrument_id'])

    # -- Time-Series Market Data -------------------------------------------
    op.create_table(
        'ohlcv',
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('open', sa.Float(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('close', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('quote_volume', sa.Float(), nullable=True),
        sa.Column('trades_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_ohlcv')
    )
    op.create_index('idx_ohlcv_lookup', 'ohlcv', ['symbol', 'exchange', 'interval', 'timestamp'])

    op.create_table(
        'funding_rates',
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('funding_rate', sa.Float(), nullable=True),
        sa.Column('next_funding_time', sa.BigInteger(), nullable=True),
        sa.Column('interval', sa.String(), server_default='8h', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', name='pk_funding_rates')
    )
    op.create_index('idx_funding_lookup', 'funding_rates', ['symbol', 'exchange', 'timestamp'])

    op.create_table(
        'open_interest',
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('oi_usd', sa.Float(), nullable=True),
        sa.Column('oi_coins', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_open_interest')
    )
    op.create_index('idx_oi_lookup', 'open_interest', ['symbol', 'exchange', 'interval', 'timestamp'])

    op.create_table(
        'liquidations',
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('value_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'side', name='pk_liquidations')
    )
    op.create_index('idx_liq_lookup', 'liquidations', ['symbol', 'exchange', 'timestamp'])

    op.create_table(
        'long_short_ratio',
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('interval', sa.String(), nullable=False),
        sa.Column('long_ratio', sa.Float(), nullable=True),
        sa.Column('short_ratio', sa.Float(), nullable=True),
        sa.Column('long_account_ratio', sa.Float(), nullable=True),
        sa.Column('short_account_ratio', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('timestamp', 'symbol', 'exchange', 'interval', name='pk_long_short_ratio')
    )
    op.create_index('idx_ls_lookup', 'long_short_ratio', ['symbol', 'exchange', 'interval', 'timestamp'])

    # -- Analytics & Auxiliary Tables ---------------------------------------
    op.create_table(
        'basis_premium',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('spot_price', sa.Float(), nullable=True),
        sa.Column('perp_price', sa.Float(), nullable=True),
        sa.Column('basis_pct', sa.Float(), nullable=True),
        sa.Column('premium_pct', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_basis_symbol', 'basis_premium', ['symbol'])
    op.create_index('idx_basis_exchange', 'basis_premium', ['exchange'])
    op.create_index('idx_basis_timestamp', 'basis_premium', ['timestamp'])

    op.create_table(
        'exchange_fees',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False, unique=True),
        sa.Column('maker_fee_pct', sa.Float(), nullable=True),
        sa.Column('taker_fee_pct', sa.Float(), nullable=True),
        sa.Column('withdrawal_fee_json', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'provider_sync_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('start_time', sa.BigInteger(), nullable=True),
        sa.Column('end_time', sa.BigInteger(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), server_default='0', nullable=True),
        sa.Column('records_inserted', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_runs_provider', 'provider_sync_runs', ['provider_name', 'sync_type', 'created_at'])

    op.create_table(
        'data_quality_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=True),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('check_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), server_default='warning', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # -- Backtesting Tables -------------------------------------------------
    op.create_table(
        'backtest_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('strategy', sa.String(), nullable=False),
        sa.Column('symbols_json', sa.Text(), nullable=False),
        sa.Column('exchanges_json', sa.Text(), nullable=False),
        sa.Column('start_time', sa.BigInteger(), nullable=False),
        sa.Column('end_time', sa.BigInteger(), nullable=False),
        sa.Column('interval', sa.String(), server_default='1m', nullable=True),
        sa.Column('initial_balance', sa.DECIMAL(18, 8), server_default='10000', nullable=True),
        sa.Column('fee_pct', sa.Float(), server_default='0.1', nullable=True),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_configs_user_id', 'backtest_configs', ['user_id'])

    op.create_table(
        'backtest_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('config_id', sa.String(), sa.ForeignKey('backtest_configs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=True),
        sa.Column('total_trades', sa.Integer(), server_default='0', nullable=True),
        sa.Column('win_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('loss_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_pnl', sa.DECIMAL(18, 8), server_default='0', nullable=True),
        sa.Column('total_pnl_pct', sa.DECIMAL(10, 4), server_default='0', nullable=True),
        sa.Column('max_drawdown_pct', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('sharpe_ratio', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('sortino_ratio', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('win_rate_pct', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('avg_trade_pnl', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('profit_factor', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_results_config_id', 'backtest_results', ['config_id'])

    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('result_id', sa.String(), sa.ForeignKey('backtest_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('entry_time', sa.BigInteger(), nullable=False),
        sa.Column('exit_time', sa.BigInteger(), nullable=True),
        sa.Column('entry_price', sa.DECIMAL(18, 8), nullable=False),
        sa.Column('exit_price', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('quantity', sa.DECIMAL(18, 8), nullable=False),
        sa.Column('pnl', sa.DECIMAL(18, 8), nullable=True),
        sa.Column('pnl_pct', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('fee', sa.DECIMAL(18, 8), server_default='0', nullable=True),
        sa.Column('status', sa.String(), server_default='open', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_trades_result_id', 'backtest_trades', ['result_id'])

    op.create_table(
        'backtest_equity',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('result_id', sa.String(), sa.ForeignKey('backtest_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('equity', sa.DECIMAL(18, 8), nullable=False),
        sa.Column('realized_pnl', sa.DECIMAL(18, 8), server_default='0', nullable=True),
        sa.Column('unrealized_pnl', sa.DECIMAL(18, 8), server_default='0', nullable=True),
        sa.Column('drawdown_pct', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_equity_result_ts', 'backtest_equity', ['result_id', 'timestamp'])

    # -- Seed Data ----------------------------------------------------------
    seed_instruments_and_aliases()
    seed_exchange_fees()


def seed_instruments_and_aliases() -> None:
    """Seed top perpetuals with cross-provider aliases."""
    bind = op.get_bind()

    instruments = [
        ("BTC", "BTC", "USDT", "perp", "binance"),
        ("ETH", "ETH", "USDT", "perp", "binance"),
        ("SOL", "SOL", "USDT", "perp", "binance"),
        ("HYPE", "HYPE", "USDT", "perp", "binance"),
    ]

    instr_ids = {}
    for canonical, base, quote, inst_type, exchange in instruments:
        instr_id = str(uuid4())
        instr_ids[canonical] = instr_id
        bind.execute(
            sa.text("""
                INSERT INTO instruments (id, canonical_symbol, base_asset, quote_asset, instrument_type, exchange, is_active)
                VALUES (:id, :cs, :ba, :qa, :it, :ex, :active)
            """),
            {
                "id": instr_id,
                "cs": canonical,
                "ba": base,
                "qa": quote,
                "it": inst_type,
                "ex": exchange,
                "active": True,
            }
        )

    aliases = [
        # BTC
        ("BTC", "binance", "BTCUSDT", "ticker", True),
        ("BTC", "coinglass", "BTC", "ticker", True),
        ("BTC", "coingecko", "bitcoin", "cg_id", True),
        ("BTC", "coingecko", "btc", "cg_symbol", False),
        ("BTC", "bybit", "BTCUSDT", "ticker", True),
        ("BTC", "okx", "BTC-USDT-SWAP", "ticker", True),
        ("BTC", "hyperliquid", "BTC", "ticker", True),
        # ETH
        ("ETH", "binance", "ETHUSDT", "ticker", True),
        ("ETH", "coinglass", "ETH", "ticker", True),
        ("ETH", "coingecko", "ethereum", "cg_id", True),
        ("ETH", "coingecko", "eth", "cg_symbol", False),
        ("ETH", "bybit", "ETHUSDT", "ticker", True),
        ("ETH", "okx", "ETH-USDT-SWAP", "ticker", True),
        ("ETH", "hyperliquid", "ETH", "ticker", True),
        # SOL
        ("SOL", "binance", "SOLUSDT", "ticker", True),
        ("SOL", "coinglass", "SOL", "ticker", True),
        ("SOL", "coingecko", "solana", "cg_id", True),
        ("SOL", "coingecko", "sol", "cg_symbol", False),
        ("SOL", "bybit", "SOLUSDT", "ticker", True),
        ("SOL", "okx", "SOL-USDT-SWAP", "ticker", True),
        ("SOL", "hyperliquid", "SOL", "ticker", True),
        # HYPE
        ("HYPE", "binance", "HYPEUSDT", "ticker", True),
        ("HYPE", "coinglass", "HYPE", "ticker", True),
        ("HYPE", "coingecko", "hyperliquid", "cg_id", True),
        ("HYPE", "coingecko", "hype", "cg_symbol", False),
        ("HYPE", "bybit", "HYPEUSDT", "ticker", True),
        ("HYPE", "okx", "HYPE-USDT-SWAP", "ticker", True),
        ("HYPE", "hyperliquid", "HYPE", "ticker", True),
    ]

    for canonical, provider, alias, alias_type, is_primary in aliases:
        bind.execute(
            sa.text("""
                INSERT INTO instrument_aliases (id, instrument_id, provider, alias, alias_type, is_primary)
                VALUES (:id, :iid, :pr, :al, :at, :ip)
            """),
            {
                "id": str(uuid4()),
                "iid": instr_ids[canonical],
                "pr": provider,
                "al": alias,
                "at": alias_type,
                "ip": is_primary,
            }
        )


def seed_exchange_fees() -> None:
    """Seed default exchange fee structures."""
    bind = op.get_bind()

    fees = [
        ("binance", 0.02, 0.05),
        ("bybit", 0.02, 0.055),
        ("okx", 0.02, 0.05),
        ("hyperliquid", 0.0, 0.035),
    ]

    for exchange, maker, taker in fees:
        bind.execute(
            sa.text("""
                INSERT INTO exchange_fees (id, exchange, maker_fee_pct, taker_fee_pct)
                VALUES (:id, :ex, :mk, :tk)
            """),
            {"id": str(uuid4()), "ex": exchange, "mk": maker, "tk": taker}
        )


def downgrade() -> None:
    op.drop_index('idx_equity_result_ts', table_name='backtest_equity')
    op.drop_table('backtest_equity')
    op.drop_index('ix_backtest_trades_result_id', table_name='backtest_trades')
    op.drop_table('backtest_trades')
    op.drop_index('ix_backtest_results_config_id', table_name='backtest_results')
    op.drop_table('backtest_results')
    op.drop_index('ix_backtest_configs_user_id', table_name='backtest_configs')
    op.drop_table('backtest_configs')
    op.drop_table('data_quality_logs')
    op.drop_index('idx_sync_runs_provider', table_name='provider_sync_runs')
    op.drop_table('provider_sync_runs')
    op.drop_table('exchange_fees')
    op.drop_index('idx_basis_timestamp', table_name='basis_premium')
    op.drop_index('idx_basis_exchange', table_name='basis_premium')
    op.drop_index('idx_basis_symbol', table_name='basis_premium')
    op.drop_table('basis_premium')
    op.drop_index('idx_ls_lookup', table_name='long_short_ratio')
    op.drop_table('long_short_ratio')
    op.drop_index('idx_liq_lookup', table_name='liquidations')
    op.drop_table('liquidations')
    op.drop_index('idx_oi_lookup', table_name='open_interest')
    op.drop_table('open_interest')
    op.drop_index('idx_funding_lookup', table_name='funding_rates')
    op.drop_table('funding_rates')
    op.drop_index('idx_ohlcv_lookup', table_name='ohlcv')
    op.drop_table('ohlcv')
    op.drop_index('ix_aliases_instrument', table_name='instrument_aliases')
    op.drop_index('ix_aliases_provider', table_name='instrument_aliases')
    op.drop_table('instrument_aliases')
    op.drop_index('ix_instruments_active', table_name='instruments')
    op.drop_index('ix_instruments_lookup', table_name='instruments')
    op.drop_table('instruments')
