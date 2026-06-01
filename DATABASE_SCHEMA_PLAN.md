# Database Schema Plan - DeltaGrid

Документ описывает план SQL-схемы для canonical market data, provider sync, data quality и backtesting. Это документационный план, а не применённая миграция. Код проекта и текущая SQLite база не менялись.

## Принципы схемы

- Совместимость: SQLite-compatible types only - `INTEGER`, `REAL`, `TEXT`, `BLOB`.
- Primary keys: `TEXT` UUID.
- Timestamp format: UTC unix milliseconds в `INTEGER`.
- Boolean fields: `INTEGER` со значениями `0` или `1`.
- JSON: `TEXT` с валидным JSON на уровне приложения.
- Decimal market values: `REAL` в SQLite-плане; для расчётов в Python-слое рекомендуется `Decimal`.
- Все market-data таблицы хранят `provider`, `ingested_at_ms`, `quality_status`, `raw_payload_json`.
- Canonical symbol хранится в `instruments.symbol`, provider symbol - в `instruments.provider_symbol`.

## Связи

```text
assets
  -> instruments.asset_id

exchanges
  -> instruments.exchange_id
  -> exchange_fees.exchange_id

instruments
  -> ohlcv_1m.instrument_id
  -> funding_rates.instrument_id
  -> open_interest.instrument_id
  -> liquidations.instrument_id
  -> long_short_ratio.instrument_id
  -> basis_premium.instrument_id
  -> backtest_trades.instrument_id

provider_sync_runs
  -> data_quality_logs.sync_run_id

backtest_configs
  -> backtest_results.config_id

backtest_results
  -> backtest_trades.result_id
  -> backtest_equity.result_id
```

## SQL DDL

Перед использованием foreign keys в SQLite:

```sql
PRAGMA foreign_keys = ON;
```

### `assets`

```sql
CREATE TABLE assets (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT,
    asset_type TEXT NOT NULL DEFAULT 'crypto',
    coingecko_id TEXT,
    metadata_json TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    CHECK (asset_type IN ('crypto', 'stablecoin', 'fiat', 'rwa', 'index', 'unknown'))
);

CREATE INDEX ix_assets_asset_type ON assets (asset_type);
CREATE INDEX ix_assets_coingecko_id ON assets (coingecko_id);
```

### `exchanges`

```sql
CREATE TABLE exchanges (
    id TEXT PRIMARY KEY,
    exchange_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    exchange_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    supports_spot INTEGER NOT NULL DEFAULT 0,
    supports_perp INTEGER NOT NULL DEFAULT 0,
    supports_ws INTEGER NOT NULL DEFAULT 0,
    supports_private_trading INTEGER NOT NULL DEFAULT 0,
    rate_limit_per_minute INTEGER,
    maker_fee_rate_default REAL,
    taker_fee_rate_default REAL,
    metadata_json TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    CHECK (exchange_type IN ('cex', 'dex', 'perp_dex', 'aggregator')),
    CHECK (status IN ('active', 'degraded', 'disabled')),
    CHECK (supports_spot IN (0, 1)),
    CHECK (supports_perp IN (0, 1)),
    CHECK (supports_ws IN (0, 1)),
    CHECK (supports_private_trading IN (0, 1))
);

CREATE INDEX ix_exchanges_type_status ON exchanges (exchange_type, status);
```

### `instruments`

```sql
CREATE TABLE instruments (
    id TEXT PRIMARY KEY,
    exchange_id TEXT NOT NULL,
    asset_id TEXT,
    symbol TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    base_asset TEXT NOT NULL,
    quote_asset TEXT NOT NULL,
    settle_asset TEXT,
    instrument_type TEXT NOT NULL,
    contract_type TEXT,
    contract_size REAL,
    tick_size REAL,
    lot_size REAL,
    min_qty REAL,
    min_notional REAL,
    price_precision INTEGER,
    quantity_precision INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    listed_at_ms INTEGER,
    expires_at_ms INTEGER,
    funding_interval_hours REAL,
    max_leverage REAL,
    metadata_json TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL,
    UNIQUE (exchange_id, symbol),
    UNIQUE (exchange_id, provider_symbol),
    CHECK (instrument_type IN ('spot', 'perp', 'future', 'option', 'index')),
    CHECK (contract_type IS NULL OR contract_type IN ('spot', 'linear', 'inverse', 'quanto')),
    CHECK (status IN ('active', 'prelaunch', 'settled', 'delisted', 'disabled')),
    CHECK (tick_size IS NULL OR tick_size > 0),
    CHECK (lot_size IS NULL OR lot_size > 0),
    CHECK (min_qty IS NULL OR min_qty >= 0),
    CHECK (min_notional IS NULL OR min_notional >= 0)
);

CREATE INDEX ix_instruments_symbol ON instruments (symbol);
CREATE INDEX ix_instruments_exchange_type_status ON instruments (exchange_id, instrument_type, status);
CREATE INDEX ix_instruments_base_quote ON instruments (base_asset, quote_asset);
```

### `ohlcv_1m`

```sql
CREATE TABLE ohlcv_1m (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    interval_start_ms INTEGER NOT NULL,
    interval_end_ms INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume_base REAL,
    volume_quote REAL,
    trade_count INTEGER,
    is_final INTEGER NOT NULL DEFAULT 1,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (instrument_id, provider, interval_start_ms),
    CHECK (interval_end_ms > interval_start_ms),
    CHECK (interval_end_ms - interval_start_ms = 60000),
    CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0),
    CHECK (high >= low),
    CHECK (high >= open AND high >= close),
    CHECK (low <= open AND low <= close),
    CHECK (volume_base IS NULL OR volume_base >= 0),
    CHECK (volume_quote IS NULL OR volume_quote >= 0),
    CHECK (trade_count IS NULL OR trade_count >= 0),
    CHECK (is_final IN (0, 1)),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_ohlcv_1m_instrument_time ON ohlcv_1m (instrument_id, interval_start_ms);
CREATE INDEX ix_ohlcv_1m_provider_time ON ohlcv_1m (provider, interval_start_ms);
```

### `funding_rates`

```sql
CREATE TABLE funding_rates (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    funding_time_ms INTEGER NOT NULL,
    interval_start_ms INTEGER,
    interval_end_ms INTEGER,
    interval_hours REAL,
    funding_rate REAL NOT NULL,
    predicted_funding_rate REAL,
    annualized_rate REAL,
    mark_price REAL,
    index_price REAL,
    premium REAL,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (instrument_id, provider, funding_time_ms),
    CHECK (interval_end_ms IS NULL OR interval_start_ms IS NULL OR interval_end_ms > interval_start_ms),
    CHECK (interval_hours IS NULL OR interval_hours > 0),
    CHECK (mark_price IS NULL OR mark_price >= 0),
    CHECK (index_price IS NULL OR index_price >= 0),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_funding_rates_instrument_time ON funding_rates (instrument_id, funding_time_ms);
CREATE INDEX ix_funding_rates_provider_time ON funding_rates (provider, funding_time_ms);
```

### `open_interest`

```sql
CREATE TABLE open_interest (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    snapshot_time_ms INTEGER NOT NULL,
    open_interest_contracts REAL,
    open_interest_base REAL,
    open_interest_quote REAL,
    open_interest_usd REAL,
    mark_price REAL,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (instrument_id, provider, snapshot_time_ms),
    CHECK (open_interest_contracts IS NULL OR open_interest_contracts >= 0),
    CHECK (open_interest_base IS NULL OR open_interest_base >= 0),
    CHECK (open_interest_quote IS NULL OR open_interest_quote >= 0),
    CHECK (open_interest_usd IS NULL OR open_interest_usd >= 0),
    CHECK (mark_price IS NULL OR mark_price >= 0),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_open_interest_instrument_time ON open_interest (instrument_id, snapshot_time_ms);
CREATE INDEX ix_open_interest_provider_time ON open_interest (provider, snapshot_time_ms);
```

### `liquidations`

```sql
CREATE TABLE liquidations (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    liquidation_id TEXT,
    is_aggregate INTEGER NOT NULL DEFAULT 0,
    event_time_ms INTEGER,
    interval_start_ms INTEGER,
    interval_end_ms INTEGER,
    side TEXT NOT NULL DEFAULT 'unknown',
    position_side TEXT,
    price REAL,
    quantity_base REAL,
    quantity_quote REAL,
    order_type TEXT,
    status TEXT,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (provider, liquidation_id),
    CHECK (is_aggregate IN (0, 1)),
    CHECK (
        (is_aggregate = 0 AND event_time_ms IS NOT NULL)
        OR
        (is_aggregate = 1 AND interval_start_ms IS NOT NULL AND interval_end_ms IS NOT NULL)
    ),
    CHECK (interval_end_ms IS NULL OR interval_start_ms IS NULL OR interval_end_ms > interval_start_ms),
    CHECK (side IN ('buy', 'sell', 'long', 'short', 'unknown')),
    CHECK (position_side IS NULL OR position_side IN ('long', 'short', 'net', 'unknown')),
    CHECK (price IS NULL OR price >= 0),
    CHECK (quantity_base IS NULL OR quantity_base >= 0),
    CHECK (quantity_quote IS NULL OR quantity_quote >= 0),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_liquidations_instrument_event ON liquidations (instrument_id, event_time_ms);
CREATE INDEX ix_liquidations_instrument_interval ON liquidations (instrument_id, interval_start_ms, interval_end_ms);
CREATE INDEX ix_liquidations_provider_event ON liquidations (provider, event_time_ms);
```

### `long_short_ratio`

```sql
CREATE TABLE long_short_ratio (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    ratio_type TEXT NOT NULL,
    interval TEXT,
    interval_start_ms INTEGER NOT NULL,
    interval_end_ms INTEGER NOT NULL,
    long_ratio REAL,
    short_ratio REAL,
    long_short_ratio REAL NOT NULL,
    long_value REAL,
    short_value REAL,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (instrument_id, provider, ratio_type, interval_start_ms),
    CHECK (ratio_type IN ('global_account', 'top_account', 'top_position', 'taker_volume', 'provider_aggregate')),
    CHECK (interval_end_ms > interval_start_ms),
    CHECK (long_ratio IS NULL OR (long_ratio >= 0 AND long_ratio <= 1)),
    CHECK (short_ratio IS NULL OR (short_ratio >= 0 AND short_ratio <= 1)),
    CHECK (long_short_ratio >= 0),
    CHECK (long_value IS NULL OR long_value >= 0),
    CHECK (short_value IS NULL OR short_value >= 0),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_long_short_ratio_instrument_time ON long_short_ratio (instrument_id, interval_start_ms);
CREATE INDEX ix_long_short_ratio_provider_type_time ON long_short_ratio (provider, ratio_type, interval_start_ms);
```

### `basis_premium`

```sql
CREATE TABLE basis_premium (
    id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    snapshot_time_ms INTEGER NOT NULL,
    mark_price REAL,
    index_price REAL,
    basis REAL,
    basis_pct REAL,
    premium REAL,
    premium_pct REAL,
    next_funding_time_ms INTEGER,
    ingested_at_ms INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'live',
    raw_payload_json TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (instrument_id, provider, snapshot_time_ms),
    CHECK (mark_price IS NULL OR mark_price >= 0),
    CHECK (index_price IS NULL OR index_price >= 0),
    CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
);

CREATE INDEX ix_basis_premium_instrument_time ON basis_premium (instrument_id, snapshot_time_ms);
CREATE INDEX ix_basis_premium_provider_time ON basis_premium (provider, snapshot_time_ms);
```

### `exchange_fees`

```sql
CREATE TABLE exchange_fees (
    id TEXT PRIMARY KEY,
    exchange_id TEXT NOT NULL,
    instrument_id TEXT,
    fee_tier TEXT NOT NULL DEFAULT 'default',
    maker_fee_rate REAL,
    taker_fee_rate REAL,
    funding_fee_rate REAL,
    withdrawal_fee_flat REAL,
    withdrawal_fee_asset TEXT,
    effective_from_ms INTEGER NOT NULL,
    effective_to_ms INTEGER,
    source TEXT NOT NULL DEFAULT 'manual',
    metadata_json TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
    UNIQUE (exchange_id, instrument_id, fee_tier, effective_from_ms),
    CHECK (maker_fee_rate IS NULL OR maker_fee_rate >= 0),
    CHECK (taker_fee_rate IS NULL OR taker_fee_rate >= 0),
    CHECK (funding_fee_rate IS NULL OR funding_fee_rate >= 0),
    CHECK (withdrawal_fee_flat IS NULL OR withdrawal_fee_flat >= 0),
    CHECK (effective_to_ms IS NULL OR effective_to_ms > effective_from_ms)
);

CREATE INDEX ix_exchange_fees_exchange_instrument ON exchange_fees (exchange_id, instrument_id);
CREATE INDEX ix_exchange_fees_effective ON exchange_fees (effective_from_ms, effective_to_ms);
```

### `provider_sync_runs`

```sql
CREATE TABLE provider_sync_runs (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    exchange_id TEXT,
    sync_type TEXT NOT NULL,
    endpoint TEXT,
    status TEXT NOT NULL,
    started_at_ms INTEGER NOT NULL,
    finished_at_ms INTEGER,
    duration_ms INTEGER,
    requested_from_ms INTEGER,
    requested_to_ms INTEGER,
    records_fetched INTEGER NOT NULL DEFAULT 0,
    records_inserted INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    records_rejected INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    request_metadata_json TEXT,
    response_metadata_json TEXT,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE SET NULL,
    CHECK (status IN ('running', 'success', 'partial', 'failed', 'cancelled')),
    CHECK (finished_at_ms IS NULL OR finished_at_ms >= started_at_ms),
    CHECK (duration_ms IS NULL OR duration_ms >= 0),
    CHECK (records_fetched >= 0),
    CHECK (records_inserted >= 0),
    CHECK (records_updated >= 0),
    CHECK (records_rejected >= 0)
);

CREATE INDEX ix_provider_sync_runs_provider_started ON provider_sync_runs (provider, started_at_ms);
CREATE INDEX ix_provider_sync_runs_type_status ON provider_sync_runs (sync_type, status);
```

### `data_quality_logs`

```sql
CREATE TABLE data_quality_logs (
    id TEXT PRIMARY KEY,
    sync_run_id TEXT,
    instrument_id TEXT,
    table_name TEXT NOT NULL,
    provider TEXT,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    message TEXT NOT NULL,
    observed_at_ms INTEGER NOT NULL,
    resolved_at_ms INTEGER,
    sample_payload_json TEXT,
    FOREIGN KEY (sync_run_id) REFERENCES provider_sync_runs(id) ON DELETE SET NULL,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE SET NULL,
    CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    CHECK (status IN ('open', 'ignored', 'resolved')),
    CHECK (resolved_at_ms IS NULL OR resolved_at_ms >= observed_at_ms)
);

CREATE INDEX ix_data_quality_logs_run ON data_quality_logs (sync_run_id);
CREATE INDEX ix_data_quality_logs_instrument_time ON data_quality_logs (instrument_id, observed_at_ms);
CREATE INDEX ix_data_quality_logs_severity_status ON data_quality_logs (severity, status);
```

### `backtest_configs`

```sql
CREATE TABLE backtest_configs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strategy_key TEXT NOT NULL,
    strategy_version TEXT,
    description TEXT,
    universe_json TEXT NOT NULL,
    params_json TEXT NOT NULL,
    timeframe TEXT NOT NULL DEFAULT '1m',
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    initial_equity REAL NOT NULL,
    quote_asset TEXT NOT NULL DEFAULT 'USDT',
    fee_model_json TEXT,
    slippage_model_json TEXT,
    risk_model_json TEXT,
    data_requirements_json TEXT,
    created_by TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    CHECK (end_ms > start_ms),
    CHECK (initial_equity > 0)
);

CREATE INDEX ix_backtest_configs_strategy ON backtest_configs (strategy_key, strategy_version);
CREATE INDEX ix_backtest_configs_timeframe_range ON backtest_configs (timeframe, start_ms, end_ms);
```

### `backtest_results`

```sql
CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    config_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at_ms INTEGER NOT NULL,
    finished_at_ms INTEGER,
    duration_ms INTEGER,
    data_start_ms INTEGER,
    data_end_ms INTEGER,
    initial_equity REAL NOT NULL,
    final_equity REAL,
    net_pnl REAL,
    total_return_pct REAL,
    annualized_return_pct REAL,
    max_drawdown_pct REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    win_rate REAL,
    profit_factor REAL,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    max_exposure REAL,
    avg_exposure REAL,
    error_message TEXT,
    metrics_json TEXT,
    FOREIGN KEY (config_id) REFERENCES backtest_configs(id) ON DELETE CASCADE,
    CHECK (status IN ('queued', 'running', 'success', 'failed', 'cancelled')),
    CHECK (finished_at_ms IS NULL OR finished_at_ms >= started_at_ms),
    CHECK (duration_ms IS NULL OR duration_ms >= 0),
    CHECK (initial_equity > 0),
    CHECK (total_trades >= 0),
    CHECK (winning_trades >= 0),
    CHECK (losing_trades >= 0),
    CHECK (win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 1))
);

CREATE INDEX ix_backtest_results_config_started ON backtest_results (config_id, started_at_ms);
CREATE INDEX ix_backtest_results_status ON backtest_results (status);
```

### `backtest_trades`

```sql
CREATE TABLE backtest_trades (
    id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL,
    exchange_id TEXT,
    trade_group_id TEXT,
    side TEXT NOT NULL,
    order_type TEXT,
    entry_time_ms INTEGER NOT NULL,
    exit_time_ms INTEGER,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity_base REAL NOT NULL,
    quantity_quote REAL,
    fee_paid REAL NOT NULL DEFAULT 0,
    fee_asset TEXT,
    slippage_paid REAL NOT NULL DEFAULT 0,
    gross_pnl REAL,
    net_pnl REAL,
    pnl_pct REAL,
    exit_reason TEXT,
    metadata_json TEXT,
    FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE,
    FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE RESTRICT,
    FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE SET NULL,
    CHECK (side IN ('long', 'short', 'buy', 'sell')),
    CHECK (exit_time_ms IS NULL OR exit_time_ms >= entry_time_ms),
    CHECK (entry_price >= 0),
    CHECK (exit_price IS NULL OR exit_price >= 0),
    CHECK (quantity_base > 0),
    CHECK (quantity_quote IS NULL OR quantity_quote >= 0),
    CHECK (fee_paid >= 0),
    CHECK (slippage_paid >= 0)
);

CREATE INDEX ix_backtest_trades_result_entry ON backtest_trades (result_id, entry_time_ms);
CREATE INDEX ix_backtest_trades_instrument_entry ON backtest_trades (instrument_id, entry_time_ms);
CREATE INDEX ix_backtest_trades_group ON backtest_trades (trade_group_id);
```

### `backtest_equity`

```sql
CREATE TABLE backtest_equity (
    id TEXT PRIMARY KEY,
    result_id TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,
    equity REAL NOT NULL,
    cash REAL,
    position_value REAL,
    unrealized_pnl REAL,
    realized_pnl REAL,
    drawdown_pct REAL,
    exposure REAL,
    metadata_json TEXT,
    FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE,
    UNIQUE (result_id, timestamp_ms),
    CHECK (equity >= 0),
    CHECK (drawdown_pct IS NULL OR drawdown_pct <= 0),
    CHECK (exposure IS NULL OR exposure >= 0)
);

CREATE INDEX ix_backtest_equity_result_time ON backtest_equity (result_id, timestamp_ms);
```

## Alembic migration script

Рекомендуемый revision ID:

```text
c2f8e9a7410d
```

Предполагаемый `down_revision` для текущего проекта:

```text
b19c6344f081
```

Скрипт ниже намеренно использует raw SQL, чтобы явно сохранить SQLite-compatible types (`INTEGER`, `REAL`, `TEXT`, `BLOB`) и избежать случайного появления dialect-specific типов.

```python
"""market_data_contracts_and_backtesting

Revision ID: c2f8e9a7410d
Revises: b19c6344f081
Create Date: 2026-06-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c2f8e9a7410d"
down_revision: Union[str, None] = "b19c6344f081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys = ON")

    op.execute("""
    CREATE TABLE assets (
        id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL UNIQUE,
        name TEXT,
        asset_type TEXT NOT NULL DEFAULT 'crypto',
        coingecko_id TEXT,
        metadata_json TEXT,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        CHECK (asset_type IN ('crypto', 'stablecoin', 'fiat', 'rwa', 'index', 'unknown'))
    )
    """)
    op.execute("CREATE INDEX ix_assets_asset_type ON assets (asset_type)")
    op.execute("CREATE INDEX ix_assets_coingecko_id ON assets (coingecko_id)")

    op.execute("""
    CREATE TABLE exchanges (
        id TEXT PRIMARY KEY,
        exchange_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        exchange_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        supports_spot INTEGER NOT NULL DEFAULT 0,
        supports_perp INTEGER NOT NULL DEFAULT 0,
        supports_ws INTEGER NOT NULL DEFAULT 0,
        supports_private_trading INTEGER NOT NULL DEFAULT 0,
        rate_limit_per_minute INTEGER,
        maker_fee_rate_default REAL,
        taker_fee_rate_default REAL,
        metadata_json TEXT,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        CHECK (exchange_type IN ('cex', 'dex', 'perp_dex', 'aggregator')),
        CHECK (status IN ('active', 'degraded', 'disabled')),
        CHECK (supports_spot IN (0, 1)),
        CHECK (supports_perp IN (0, 1)),
        CHECK (supports_ws IN (0, 1)),
        CHECK (supports_private_trading IN (0, 1))
    )
    """)
    op.execute("CREATE INDEX ix_exchanges_type_status ON exchanges (exchange_type, status)")

    op.execute("""
    CREATE TABLE instruments (
        id TEXT PRIMARY KEY,
        exchange_id TEXT NOT NULL,
        asset_id TEXT,
        symbol TEXT NOT NULL,
        provider_symbol TEXT NOT NULL,
        base_asset TEXT NOT NULL,
        quote_asset TEXT NOT NULL,
        settle_asset TEXT,
        instrument_type TEXT NOT NULL,
        contract_type TEXT,
        contract_size REAL,
        tick_size REAL,
        lot_size REAL,
        min_qty REAL,
        min_notional REAL,
        price_precision INTEGER,
        quantity_precision INTEGER,
        status TEXT NOT NULL DEFAULT 'active',
        listed_at_ms INTEGER,
        expires_at_ms INTEGER,
        funding_interval_hours REAL,
        max_leverage REAL,
        metadata_json TEXT,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL,
        UNIQUE (exchange_id, symbol),
        UNIQUE (exchange_id, provider_symbol),
        CHECK (instrument_type IN ('spot', 'perp', 'future', 'option', 'index')),
        CHECK (contract_type IS NULL OR contract_type IN ('spot', 'linear', 'inverse', 'quanto')),
        CHECK (status IN ('active', 'prelaunch', 'settled', 'delisted', 'disabled')),
        CHECK (tick_size IS NULL OR tick_size > 0),
        CHECK (lot_size IS NULL OR lot_size > 0),
        CHECK (min_qty IS NULL OR min_qty >= 0),
        CHECK (min_notional IS NULL OR min_notional >= 0)
    )
    """)
    op.execute("CREATE INDEX ix_instruments_symbol ON instruments (symbol)")
    op.execute("CREATE INDEX ix_instruments_exchange_type_status ON instruments (exchange_id, instrument_type, status)")
    op.execute("CREATE INDEX ix_instruments_base_quote ON instruments (base_asset, quote_asset)")

    op.execute("""
    CREATE TABLE ohlcv_1m (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        interval_start_ms INTEGER NOT NULL,
        interval_end_ms INTEGER NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume_base REAL,
        volume_quote REAL,
        trade_count INTEGER,
        is_final INTEGER NOT NULL DEFAULT 1,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (instrument_id, provider, interval_start_ms),
        CHECK (interval_end_ms > interval_start_ms),
        CHECK (interval_end_ms - interval_start_ms = 60000),
        CHECK (open >= 0 AND high >= 0 AND low >= 0 AND close >= 0),
        CHECK (high >= low),
        CHECK (high >= open AND high >= close),
        CHECK (low <= open AND low <= close),
        CHECK (volume_base IS NULL OR volume_base >= 0),
        CHECK (volume_quote IS NULL OR volume_quote >= 0),
        CHECK (trade_count IS NULL OR trade_count >= 0),
        CHECK (is_final IN (0, 1)),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_ohlcv_1m_instrument_time ON ohlcv_1m (instrument_id, interval_start_ms)")
    op.execute("CREATE INDEX ix_ohlcv_1m_provider_time ON ohlcv_1m (provider, interval_start_ms)")

    op.execute("""
    CREATE TABLE funding_rates (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        funding_time_ms INTEGER NOT NULL,
        interval_start_ms INTEGER,
        interval_end_ms INTEGER,
        interval_hours REAL,
        funding_rate REAL NOT NULL,
        predicted_funding_rate REAL,
        annualized_rate REAL,
        mark_price REAL,
        index_price REAL,
        premium REAL,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (instrument_id, provider, funding_time_ms),
        CHECK (interval_end_ms IS NULL OR interval_start_ms IS NULL OR interval_end_ms > interval_start_ms),
        CHECK (interval_hours IS NULL OR interval_hours > 0),
        CHECK (mark_price IS NULL OR mark_price >= 0),
        CHECK (index_price IS NULL OR index_price >= 0),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_funding_rates_instrument_time ON funding_rates (instrument_id, funding_time_ms)")
    op.execute("CREATE INDEX ix_funding_rates_provider_time ON funding_rates (provider, funding_time_ms)")

    op.execute("""
    CREATE TABLE open_interest (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        snapshot_time_ms INTEGER NOT NULL,
        open_interest_contracts REAL,
        open_interest_base REAL,
        open_interest_quote REAL,
        open_interest_usd REAL,
        mark_price REAL,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (instrument_id, provider, snapshot_time_ms),
        CHECK (open_interest_contracts IS NULL OR open_interest_contracts >= 0),
        CHECK (open_interest_base IS NULL OR open_interest_base >= 0),
        CHECK (open_interest_quote IS NULL OR open_interest_quote >= 0),
        CHECK (open_interest_usd IS NULL OR open_interest_usd >= 0),
        CHECK (mark_price IS NULL OR mark_price >= 0),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_open_interest_instrument_time ON open_interest (instrument_id, snapshot_time_ms)")
    op.execute("CREATE INDEX ix_open_interest_provider_time ON open_interest (provider, snapshot_time_ms)")

    op.execute("""
    CREATE TABLE liquidations (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        liquidation_id TEXT,
        is_aggregate INTEGER NOT NULL DEFAULT 0,
        event_time_ms INTEGER,
        interval_start_ms INTEGER,
        interval_end_ms INTEGER,
        side TEXT NOT NULL DEFAULT 'unknown',
        position_side TEXT,
        price REAL,
        quantity_base REAL,
        quantity_quote REAL,
        order_type TEXT,
        status TEXT,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (provider, liquidation_id),
        CHECK (is_aggregate IN (0, 1)),
        CHECK (
            (is_aggregate = 0 AND event_time_ms IS NOT NULL)
            OR
            (is_aggregate = 1 AND interval_start_ms IS NOT NULL AND interval_end_ms IS NOT NULL)
        ),
        CHECK (interval_end_ms IS NULL OR interval_start_ms IS NULL OR interval_end_ms > interval_start_ms),
        CHECK (side IN ('buy', 'sell', 'long', 'short', 'unknown')),
        CHECK (position_side IS NULL OR position_side IN ('long', 'short', 'net', 'unknown')),
        CHECK (price IS NULL OR price >= 0),
        CHECK (quantity_base IS NULL OR quantity_base >= 0),
        CHECK (quantity_quote IS NULL OR quantity_quote >= 0),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_liquidations_instrument_event ON liquidations (instrument_id, event_time_ms)")
    op.execute("CREATE INDEX ix_liquidations_instrument_interval ON liquidations (instrument_id, interval_start_ms, interval_end_ms)")
    op.execute("CREATE INDEX ix_liquidations_provider_event ON liquidations (provider, event_time_ms)")

    op.execute("""
    CREATE TABLE long_short_ratio (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        ratio_type TEXT NOT NULL,
        interval TEXT,
        interval_start_ms INTEGER NOT NULL,
        interval_end_ms INTEGER NOT NULL,
        long_ratio REAL,
        short_ratio REAL,
        long_short_ratio REAL NOT NULL,
        long_value REAL,
        short_value REAL,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (instrument_id, provider, ratio_type, interval_start_ms),
        CHECK (ratio_type IN ('global_account', 'top_account', 'top_position', 'taker_volume', 'provider_aggregate')),
        CHECK (interval_end_ms > interval_start_ms),
        CHECK (long_ratio IS NULL OR (long_ratio >= 0 AND long_ratio <= 1)),
        CHECK (short_ratio IS NULL OR (short_ratio >= 0 AND short_ratio <= 1)),
        CHECK (long_short_ratio >= 0),
        CHECK (long_value IS NULL OR long_value >= 0),
        CHECK (short_value IS NULL OR short_value >= 0),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_long_short_ratio_instrument_time ON long_short_ratio (instrument_id, interval_start_ms)")
    op.execute("CREATE INDEX ix_long_short_ratio_provider_type_time ON long_short_ratio (provider, ratio_type, interval_start_ms)")

    op.execute("""
    CREATE TABLE basis_premium (
        id TEXT PRIMARY KEY,
        instrument_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        snapshot_time_ms INTEGER NOT NULL,
        mark_price REAL,
        index_price REAL,
        basis REAL,
        basis_pct REAL,
        premium REAL,
        premium_pct REAL,
        next_funding_time_ms INTEGER,
        ingested_at_ms INTEGER NOT NULL,
        quality_status TEXT NOT NULL DEFAULT 'live',
        raw_payload_json TEXT,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (instrument_id, provider, snapshot_time_ms),
        CHECK (mark_price IS NULL OR mark_price >= 0),
        CHECK (index_price IS NULL OR index_price >= 0),
        CHECK (quality_status IN ('live', 'cached', 'stale', 'partial', 'fallback', 'unavailable'))
    )
    """)
    op.execute("CREATE INDEX ix_basis_premium_instrument_time ON basis_premium (instrument_id, snapshot_time_ms)")
    op.execute("CREATE INDEX ix_basis_premium_provider_time ON basis_premium (provider, snapshot_time_ms)")

    op.execute("""
    CREATE TABLE exchange_fees (
        id TEXT PRIMARY KEY,
        exchange_id TEXT NOT NULL,
        instrument_id TEXT,
        fee_tier TEXT NOT NULL DEFAULT 'default',
        maker_fee_rate REAL,
        taker_fee_rate REAL,
        funding_fee_rate REAL,
        withdrawal_fee_flat REAL,
        withdrawal_fee_asset TEXT,
        effective_from_ms INTEGER NOT NULL,
        effective_to_ms INTEGER,
        source TEXT NOT NULL DEFAULT 'manual',
        metadata_json TEXT,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE CASCADE,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE,
        UNIQUE (exchange_id, instrument_id, fee_tier, effective_from_ms),
        CHECK (maker_fee_rate IS NULL OR maker_fee_rate >= 0),
        CHECK (taker_fee_rate IS NULL OR taker_fee_rate >= 0),
        CHECK (funding_fee_rate IS NULL OR funding_fee_rate >= 0),
        CHECK (withdrawal_fee_flat IS NULL OR withdrawal_fee_flat >= 0),
        CHECK (effective_to_ms IS NULL OR effective_to_ms > effective_from_ms)
    )
    """)
    op.execute("CREATE INDEX ix_exchange_fees_exchange_instrument ON exchange_fees (exchange_id, instrument_id)")
    op.execute("CREATE INDEX ix_exchange_fees_effective ON exchange_fees (effective_from_ms, effective_to_ms)")

    op.execute("""
    CREATE TABLE provider_sync_runs (
        id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        exchange_id TEXT,
        sync_type TEXT NOT NULL,
        endpoint TEXT,
        status TEXT NOT NULL,
        started_at_ms INTEGER NOT NULL,
        finished_at_ms INTEGER,
        duration_ms INTEGER,
        requested_from_ms INTEGER,
        requested_to_ms INTEGER,
        records_fetched INTEGER NOT NULL DEFAULT 0,
        records_inserted INTEGER NOT NULL DEFAULT 0,
        records_updated INTEGER NOT NULL DEFAULT 0,
        records_rejected INTEGER NOT NULL DEFAULT 0,
        error_code TEXT,
        error_message TEXT,
        request_metadata_json TEXT,
        response_metadata_json TEXT,
        FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE SET NULL,
        CHECK (status IN ('running', 'success', 'partial', 'failed', 'cancelled')),
        CHECK (finished_at_ms IS NULL OR finished_at_ms >= started_at_ms),
        CHECK (duration_ms IS NULL OR duration_ms >= 0),
        CHECK (records_fetched >= 0),
        CHECK (records_inserted >= 0),
        CHECK (records_updated >= 0),
        CHECK (records_rejected >= 0)
    )
    """)
    op.execute("CREATE INDEX ix_provider_sync_runs_provider_started ON provider_sync_runs (provider, started_at_ms)")
    op.execute("CREATE INDEX ix_provider_sync_runs_type_status ON provider_sync_runs (sync_type, status)")

    op.execute("""
    CREATE TABLE data_quality_logs (
        id TEXT PRIMARY KEY,
        sync_run_id TEXT,
        instrument_id TEXT,
        table_name TEXT NOT NULL,
        provider TEXT,
        issue_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open',
        message TEXT NOT NULL,
        observed_at_ms INTEGER NOT NULL,
        resolved_at_ms INTEGER,
        sample_payload_json TEXT,
        FOREIGN KEY (sync_run_id) REFERENCES provider_sync_runs(id) ON DELETE SET NULL,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE SET NULL,
        CHECK (severity IN ('info', 'warning', 'error', 'critical')),
        CHECK (status IN ('open', 'ignored', 'resolved')),
        CHECK (resolved_at_ms IS NULL OR resolved_at_ms >= observed_at_ms)
    )
    """)
    op.execute("CREATE INDEX ix_data_quality_logs_run ON data_quality_logs (sync_run_id)")
    op.execute("CREATE INDEX ix_data_quality_logs_instrument_time ON data_quality_logs (instrument_id, observed_at_ms)")
    op.execute("CREATE INDEX ix_data_quality_logs_severity_status ON data_quality_logs (severity, status)")

    op.execute("""
    CREATE TABLE backtest_configs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        strategy_key TEXT NOT NULL,
        strategy_version TEXT,
        description TEXT,
        universe_json TEXT NOT NULL,
        params_json TEXT NOT NULL,
        timeframe TEXT NOT NULL DEFAULT '1m',
        start_ms INTEGER NOT NULL,
        end_ms INTEGER NOT NULL,
        initial_equity REAL NOT NULL,
        quote_asset TEXT NOT NULL DEFAULT 'USDT',
        fee_model_json TEXT,
        slippage_model_json TEXT,
        risk_model_json TEXT,
        data_requirements_json TEXT,
        created_by TEXT,
        created_at_ms INTEGER NOT NULL,
        updated_at_ms INTEGER NOT NULL,
        CHECK (end_ms > start_ms),
        CHECK (initial_equity > 0)
    )
    """)
    op.execute("CREATE INDEX ix_backtest_configs_strategy ON backtest_configs (strategy_key, strategy_version)")
    op.execute("CREATE INDEX ix_backtest_configs_timeframe_range ON backtest_configs (timeframe, start_ms, end_ms)")

    op.execute("""
    CREATE TABLE backtest_results (
        id TEXT PRIMARY KEY,
        config_id TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at_ms INTEGER NOT NULL,
        finished_at_ms INTEGER,
        duration_ms INTEGER,
        data_start_ms INTEGER,
        data_end_ms INTEGER,
        initial_equity REAL NOT NULL,
        final_equity REAL,
        net_pnl REAL,
        total_return_pct REAL,
        annualized_return_pct REAL,
        max_drawdown_pct REAL,
        sharpe_ratio REAL,
        sortino_ratio REAL,
        win_rate REAL,
        profit_factor REAL,
        total_trades INTEGER NOT NULL DEFAULT 0,
        winning_trades INTEGER NOT NULL DEFAULT 0,
        losing_trades INTEGER NOT NULL DEFAULT 0,
        max_exposure REAL,
        avg_exposure REAL,
        error_message TEXT,
        metrics_json TEXT,
        FOREIGN KEY (config_id) REFERENCES backtest_configs(id) ON DELETE CASCADE,
        CHECK (status IN ('queued', 'running', 'success', 'failed', 'cancelled')),
        CHECK (finished_at_ms IS NULL OR finished_at_ms >= started_at_ms),
        CHECK (duration_ms IS NULL OR duration_ms >= 0),
        CHECK (initial_equity > 0),
        CHECK (total_trades >= 0),
        CHECK (winning_trades >= 0),
        CHECK (losing_trades >= 0),
        CHECK (win_rate IS NULL OR (win_rate >= 0 AND win_rate <= 1))
    )
    """)
    op.execute("CREATE INDEX ix_backtest_results_config_started ON backtest_results (config_id, started_at_ms)")
    op.execute("CREATE INDEX ix_backtest_results_status ON backtest_results (status)")

    op.execute("""
    CREATE TABLE backtest_trades (
        id TEXT PRIMARY KEY,
        result_id TEXT NOT NULL,
        instrument_id TEXT NOT NULL,
        exchange_id TEXT,
        trade_group_id TEXT,
        side TEXT NOT NULL,
        order_type TEXT,
        entry_time_ms INTEGER NOT NULL,
        exit_time_ms INTEGER,
        entry_price REAL NOT NULL,
        exit_price REAL,
        quantity_base REAL NOT NULL,
        quantity_quote REAL,
        fee_paid REAL NOT NULL DEFAULT 0,
        fee_asset TEXT,
        slippage_paid REAL NOT NULL DEFAULT 0,
        gross_pnl REAL,
        net_pnl REAL,
        pnl_pct REAL,
        exit_reason TEXT,
        metadata_json TEXT,
        FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE,
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE RESTRICT,
        FOREIGN KEY (exchange_id) REFERENCES exchanges(id) ON DELETE SET NULL,
        CHECK (side IN ('long', 'short', 'buy', 'sell')),
        CHECK (exit_time_ms IS NULL OR exit_time_ms >= entry_time_ms),
        CHECK (entry_price >= 0),
        CHECK (exit_price IS NULL OR exit_price >= 0),
        CHECK (quantity_base > 0),
        CHECK (quantity_quote IS NULL OR quantity_quote >= 0),
        CHECK (fee_paid >= 0),
        CHECK (slippage_paid >= 0)
    )
    """)
    op.execute("CREATE INDEX ix_backtest_trades_result_entry ON backtest_trades (result_id, entry_time_ms)")
    op.execute("CREATE INDEX ix_backtest_trades_instrument_entry ON backtest_trades (instrument_id, entry_time_ms)")
    op.execute("CREATE INDEX ix_backtest_trades_group ON backtest_trades (trade_group_id)")

    op.execute("""
    CREATE TABLE backtest_equity (
        id TEXT PRIMARY KEY,
        result_id TEXT NOT NULL,
        timestamp_ms INTEGER NOT NULL,
        equity REAL NOT NULL,
        cash REAL,
        position_value REAL,
        unrealized_pnl REAL,
        realized_pnl REAL,
        drawdown_pct REAL,
        exposure REAL,
        metadata_json TEXT,
        FOREIGN KEY (result_id) REFERENCES backtest_results(id) ON DELETE CASCADE,
        UNIQUE (result_id, timestamp_ms),
        CHECK (equity >= 0),
        CHECK (drawdown_pct IS NULL OR drawdown_pct <= 0),
        CHECK (exposure IS NULL OR exposure >= 0)
    )
    """)
    op.execute("CREATE INDEX ix_backtest_equity_result_time ON backtest_equity (result_id, timestamp_ms)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_backtest_equity_result_time")
    op.execute("DROP INDEX IF EXISTS ix_backtest_trades_group")
    op.execute("DROP INDEX IF EXISTS ix_backtest_trades_instrument_entry")
    op.execute("DROP INDEX IF EXISTS ix_backtest_trades_result_entry")
    op.execute("DROP INDEX IF EXISTS ix_backtest_results_status")
    op.execute("DROP INDEX IF EXISTS ix_backtest_results_config_started")
    op.execute("DROP INDEX IF EXISTS ix_backtest_configs_timeframe_range")
    op.execute("DROP INDEX IF EXISTS ix_backtest_configs_strategy")
    op.execute("DROP INDEX IF EXISTS ix_data_quality_logs_severity_status")
    op.execute("DROP INDEX IF EXISTS ix_data_quality_logs_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_data_quality_logs_run")
    op.execute("DROP INDEX IF EXISTS ix_provider_sync_runs_type_status")
    op.execute("DROP INDEX IF EXISTS ix_provider_sync_runs_provider_started")
    op.execute("DROP INDEX IF EXISTS ix_exchange_fees_effective")
    op.execute("DROP INDEX IF EXISTS ix_exchange_fees_exchange_instrument")
    op.execute("DROP INDEX IF EXISTS ix_basis_premium_provider_time")
    op.execute("DROP INDEX IF EXISTS ix_basis_premium_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_long_short_ratio_provider_type_time")
    op.execute("DROP INDEX IF EXISTS ix_long_short_ratio_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_liquidations_provider_event")
    op.execute("DROP INDEX IF EXISTS ix_liquidations_instrument_interval")
    op.execute("DROP INDEX IF EXISTS ix_liquidations_instrument_event")
    op.execute("DROP INDEX IF EXISTS ix_open_interest_provider_time")
    op.execute("DROP INDEX IF EXISTS ix_open_interest_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_funding_rates_provider_time")
    op.execute("DROP INDEX IF EXISTS ix_funding_rates_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_ohlcv_1m_provider_time")
    op.execute("DROP INDEX IF EXISTS ix_ohlcv_1m_instrument_time")
    op.execute("DROP INDEX IF EXISTS ix_instruments_base_quote")
    op.execute("DROP INDEX IF EXISTS ix_instruments_exchange_type_status")
    op.execute("DROP INDEX IF EXISTS ix_instruments_symbol")
    op.execute("DROP INDEX IF EXISTS ix_exchanges_type_status")
    op.execute("DROP INDEX IF EXISTS ix_assets_coingecko_id")
    op.execute("DROP INDEX IF EXISTS ix_assets_asset_type")

    for table_name in [
        "backtest_equity",
        "backtest_trades",
        "backtest_results",
        "backtest_configs",
        "data_quality_logs",
        "provider_sync_runs",
        "exchange_fees",
        "basis_premium",
        "long_short_ratio",
        "liquidations",
        "open_interest",
        "funding_rates",
        "ohlcv_1m",
        "instruments",
        "exchanges",
        "assets",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table_name}")
```

## Важные замечания к миграции

- В текущем проекте уже существует `provider_sync_logs`. Новая таблица `provider_sync_runs` не заменяет её автоматически: это отдельный run-level план для будущего ingest/backfill слоя.
- В текущем проекте уже есть execution/paper trading таблицы. Таблицы `backtest_*` отделены от `paper_*`, чтобы не смешивать симуляции стратегий с demo trading lifecycle.
- `ohlcv_1m` намеренно закрепляет только 1-minute candles. Higher timeframe лучше строить материализацией/aggregation job, а не хранить как первичный источник до появления явной продуктовой причины.
- `liquidations` поддерживает event-level и aggregate-level записи через `is_aggregate`, потому что CoinGlass и биржи могут отдавать разные гранулярности данных.

## Факт / допущение / рекомендация

### Факт

- Текущая архитектура DeltaGrid использует SQLite с Alembic и уже имеет provider health/sync logging, exchange connectors, alerting и paper trading.
- В проекте уже есть таблицы execution и market enrichment, но нет нормализованных таблиц `ohlcv_1m`, `open_interest`, `liquidations`, `long_short_ratio`, `basis_premium` и backtest result/equity слоя в каноническом формате.
- Все timestamp-поля в этом плане заданы как UTC unix milliseconds в `INTEGER`.

### Допущение

- `b19c6344f081` принят как текущий Alembic head на момент подготовки документа.
- SQLite `REAL` достаточно для первичного хранения и аналитических запросов, но точные расчёты PnL/risk/funding должны выполняться через `Decimal` в application layer.
- `assets` описывает базовый asset, а не конкретный tradable instrument; конкретика биржи и контракта находится в `instruments`.

### Рекомендация

- Реализовывать схему отдельной миграцией только после adapter contract tests на raw fixtures от каждого provider.
- Перед production backfill добавить idempotent upsert policy по unique constraints каждой market-data таблицы.
- Для больших объёмов 1m candles заранее заложить PostgreSQL migration path и partitioning strategy, потому что SQLite быстро станет узким местом на multi-symbol history.
