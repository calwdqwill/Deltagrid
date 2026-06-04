# DeltaGrid — Phase 6: Backtest Engine MVP

## 1. Контекст проекта

- **Название:** DeltaGrid
- **Тип:** backtesting-first research terminal для CEX/DEX perpetual futures
- **Локальный путь:** `C:\Users\viach\OneDrive\Desktop\Deltagrid`
- **GitHub:** https://github.com/calwdqwill/Deltagrid
- **База данных:** SQLite 52 таблицы, Alembic head `d08fc5113b42`
- **Backend:** FastAPI, SQLAlchemy 2.0, Pydantic, Alembic
- **Frontend:** Next.js 14, TypeScript (не трогать в этой задаче)

### 1.1 Данные в базе (готовы к использованию)

| Таблица | Записей | Описание |
|---------|---------|----------|
| `ohlcv_1m` | **518,400** | 1m свечи (BTC/ETH/SOL/HYPE × 90 дней × 1440 минут) |
| `funding_rates` | ~3,000+ | Funding rate history (CoinGlass, interval_hours=8 для CEX) |
| `open_interest` | ~3,000+ | OI history |
| `liquidations` | ~5,000+ | Liquidation history |
| `long_short_ratio` | ~3,000+ | Long/Short ratio history |
| `exchange_fees` | 4 | maker/taker per exchange (seed data) |
| `instruments` | 4 | BTC, ETH, SOL, HYPE |
| `instrument_aliases` | 28 | Symbol mapping per provider |

### 1.2 Существующий код (использовать, не дублировать)

**`backend/app/adapters/data/:`**
- `base_adapter.py` — `BaseDataAdapter` (ABC) с `health_check()`, `fetch()`, `normalize()`
- `data_models.py` — Pydantic модели: `OHLCVCandle(timestamp, open, high, low, close, volume)`, `FundingRate`, `OpenInterest`, `Liquidation`, `LongShortRatio`
- `data_writer.py` — `DataWriter.upsert_ohlcv()`, `upsert_funding()`, `create_sync_run()`
- `symbol_mapper.py` — `SymbolMapper` (canonical → provider alias), `seed_defaults()`
- `rate_limiter.py` — `TokenBucket`, `CircuitBreaker` (CLOSED/OPEN/HALF_OPEN), `RetryPolicy`
- `binance_adapter.py` — `BinanceAdapter` (пример рабочего адаптера)
- `coinglass_adapter.py` — `CoinGlassAdapter` (пример рабочего адаптера)

**`backend/app/domain/models.py:`**
- SQLAlchemy модели: `OHLCV1m`, `FundingRate`, `OpenInterest`, `Liquidation`, `LongShortRatio`, `ExchangeFee`, `ProviderSyncRun`, `DataQualityLog`
- Поля `OHLCV1m`: `id`, `exchange`, `symbol`, `timestamp` (ms), `open`, `high`, `low`, `close`, `volume`
- Поля `FundingRate`: `id`, `exchange`, `symbol`, `timestamp` (ms), `rate`, `interval_hours`
- Поля `ExchangeFee`: `id`, `exchange`, `maker_fee`, `taker_fee`, `funding_interval_hours`

**`backend/app/persistence/database.py:`**
- `SessionLocal` — фабрика сессий SQLAlchemy
- `get_db()` — dependency для FastAPI

---

## 2. Архитектура Backtest Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    BacktestEngine                           │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Load Data  │ →  │   Bar Loop   │ →  │   Results    │  │
│  │              │    │              │    │              │  │
│  │ ohlcv_1m     │    │ For each bar │    │ Metrics      │  │
│  │ funding_rates│    │ t in range:  │    │ PnL Decomp   │  │
│  │ exchange_fees│    │              │    │ Trade Log    │  │
│  └──────────────┘    │ 1. Generate  │    │ Equity Curve │  │
│                      │    signals   │    └──────────────┘  │
│                      │ 2. Check     │                       │
│                      │    entries   │                       │
│                      │ 3. Check     │                       │
│                      │    exits     │                       │
│                      │ 4. Funding   │                       │
│                      │    payment   │                       │
│                      │ 5. Calculate │                       │
│                      │    PnL       │                       │
│                      └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Ключевой принцип — structural look-ahead bias elimination:**
- При обработке бара `t` в памяти доступны данные **только до `t` включительно**
- Данные `t+1`, `t+2`, ... **не загружены** и **недоступны**
- Каждый бар обрабатывается строго последовательно

---

## 3. Задания

### Задание 1: Backtest Engine Core

**Файл:** `backend/app/backtest/engine.py`

```python
class BacktestEngine:
    """
    Bar-by-bar event loop for perpetual futures backtesting.
    Structural elimination of look-ahead bias.
    """
    
    def __init__(self, db_session, config: BacktestConfig):
        """
        db_session: SQLAlchemy Session
        config: BacktestConfig (see below)
        """
    
    def run(self) -> BacktestResult:
        """
        Main entry point. Executes full backtest.
        Returns: BacktestResult with all metrics
        """
    
    def _load_data(self, symbol: str, exchange: str, 
                   start_ms: int, end_ms: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Loads OHLCV + funding data from SQLite.
        Returns: (df_ohlcv, df_funding) indexed by timestamp
        """
    
    def _bar_loop(self, df_ohlcv: pd.DataFrame, df_funding: pd.DataFrame,
                  strategy: BaseStrategy) -> List[Trade]:
        """
        Core event loop. Iterates bar by bar.
        At each bar t: only data[:t+1] is available.
        """
    
    def _calculate_funding_payment(self, timestamp_ms: int, position: Position,
                                    funding_rate: float, exchange: str) -> float:
        """
        Calculates funding payment for given timestamp.
        Returns payment amount (positive = pay, negative = receive)
        """
    
    def _calculate_fees(self, trade_value_usd: float, is_maker: bool, 
                        exchange: str) -> float:
        """
        Calculates trading fees based on exchange fee schedule.
        """
    
    def _calculate_slippage(self, trade_value_usd: float, volume_1m: float,
                            token: str, exchange: str) -> float:
        """
        Calculates slippage as dollar amount.
        """
```

**Конфигурация:**

```python
@dataclass
class BacktestConfig:
    strategy_type: str           # "funding_mean_reversion" | "basis_compression" | "liquidation_cascade_fade"
    symbol: str                  # "BTC" | "ETH" | "SOL" | "HYPE"
    exchange: str                # "binance" | "bybit" | "okx" | "hyperliquid"
    start_ms: int                # unix timestamp ms
    end_ms: int                  # unix timestamp ms
    position_size_usd: float     # default 10_000
    leverage: float              # default 1.0 (spot-equivalent)
    fee_type: str                # "maker" | "taker"
    use_slippage: bool           # default True
    params: Dict[str, Any]       # strategy-specific parameters
```

**Торговля:**

```python
@dataclass 
class Position:
    side: str                    # "long" | "short" | "flat"
    entry_price: float
    size_usd: float
    entry_time_ms: int
    funding_pnl: float           # cumulative funding PnL
    fees_paid: float             # cumulative fees
    slippage_paid: float         # cumulative slippage

@dataclass
class Trade:
    entry_time_ms: int
    exit_time_ms: int
    symbol: str
    exchange: str
    side: str                    # "long" | "short"
    entry_price: float
    exit_price: float
    size_usd: float
    price_pnl: float             # (exit - entry) * size * direction
    funding_pnl: float           # sum of funding payments
    fees: float                  # entry_fee + exit_fee
    slippage: float              # entry_slippage + exit_slippage
    net_pnl: float               # price_pnl + funding_pnl - fees - slippage
    hold_duration_min: int
    exit_reason: str             # "mean_reversion" | "time_based" | "stop_loss" | "take_profit"

@dataclass
class EquityPoint:
    timestamp_ms: int
    equity: float                # running total equity
    drawdown: float              # peak-to-trough drawdown
    drawdown_pct: float          # drawdown as percentage
```

---

### Задание 2: Fee Model

**Файл:** `backend/app/backtest/fee_model.py`

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class FeeConfig:
    maker: float                 # maker fee as decimal (e.g., 0.0002 = 0.02%)
    taker: float                 # taker fee as decimal
    funding_interval_hours: int  # 8 for CEX, 1 for Hyperliquid

EXCHANGE_FEES: Dict[str, FeeConfig] = {
    "binance":       FeeConfig(maker=0.0002,  taker=0.0005,  funding_interval_hours=8),
    "bybit":         FeeConfig(maker=0.0002,  taker=0.00055, funding_interval_hours=8),
    "okx":           FeeConfig(maker=0.0002,  taker=0.0005,  funding_interval_hours=8),
    "hyperliquid":   FeeConfig(maker=0.0001,  taker=0.00035, funding_interval_hours=1),
}

def get_fee_config(exchange: str) -> FeeConfig:
    """Returns fee config for given exchange."""

def calculate_trade_fee(trade_value_usd: float, is_maker: bool, exchange: str) -> float:
    """Returns fee in USD."""
```

---

### Задание 3: Funding Model

**Файл:** `backend/app/backtest/funding_model.py`

```python
from datetime import datetime, timezone

def get_funding_payment(
    timestamp_ms: int,
    position_side: str,          # "long" | "short" | "flat"
    size_usd: float,
    funding_rate: float,          # current funding rate (e.g., 0.000312 = 0.0312%)
    exchange: str,
) -> float:
    """
    Calculates funding payment for given timestamp.
    
    Logic:
    1. Check if timestamp is a funding settlement time:
       - Binance/Bybit/OKX: 00:00, 08:00, 16:00 UTC (every 8 hours)
       - Hyperliquid: every hour
    
    2. If NOT settlement time → return 0
    
    3. If settlement time:
       - Long position: pays funding_rate * size_usd  (when rate > 0)
       - Short position: receives funding_rate * size_usd (when rate > 0)
       - If funding_rate < 0: direction reverses
    
    Returns: payment amount in USD
             positive = trader pays
             negative = trader receives
    
    Example:
    position=long, size=10000, rate=0.000312, exchange=binance, time=08:00 UTC
    → pays $3.12 (returns +3.12)
    
    position=short, size=10000, rate=0.000312, exchange=binance, time=08:00 UTC  
    → receives $3.12 (returns -3.12)
    """

def is_funding_settlement_time(timestamp_ms: int, exchange: str) -> bool:
    """Returns True if timestamp matches funding settlement schedule."""

def get_funding_rate_at_time(
    timestamp_ms: int, 
    df_funding: pd.DataFrame
) -> float:
    """
    Gets applicable funding rate for given timestamp.
    Uses most recent funding rate before or at timestamp.
    NO interpolation — uses exact rate.
    """
```

**Критично:**
- Binance/Bybit/OKX funding: 00:00, 08:00, 16:00 UTC (8h intervals)
- Hyperliquid funding: every hour
- Для Binance используй поле `interval_hours=8` из таблицы `funding_rates`
- Для Hyperliquid будет `interval_hours=1`
- **Никакой интерполяции** — используй exact settlement times
- Ошибка в funding timestamp = до 5% годовых ошибка в backtest

---

### Задание 4: Slippage Model

**Файл:** `backend/app/backtest/slippage_model.py`

```python
# Token-specific slippage (in basis points, as decimal)
TOKEN_SLIPPAGE: Dict[str, Dict[str, float]] = {
    # normal: typical slippage for normal market conditions
    # stress: slippage during high volatility / low liquidity
    "BTC":  {"normal": 0.0001,  "stress": 0.0010},   # 1 bps / 10 bps
    "ETH":  {"normal": 0.0002,  "stress": 0.0015},   # 2 bps / 15 bps
    "SOL":  {"normal": 0.0005,  "stress": 0.0030},   # 5 bps / 30 bps
    "HYPE": {"normal": 0.0010,  "stress": 0.0050},   # 10 bps / 50 bps
}

def calculate_slippage(
    trade_value_usd: float,
    volume_1m: float,            # 1-minute volume in USD
    token: str,
    exchange: str,
    mode: str = "normal",        # "normal" | "stress" | "conservative"
) -> float:
    """
    Two-component slippage model:
    1. Fixed component: token-specific base slippage
    2. Volume component: increases when trade_size / volume_ratio is high
    
    volume_ratio = trade_value_usd / volume_1m
    if volume_ratio > 0.01 (trade > 1% of 1m volume): apply stress slippage
    if volume_ratio > 0.05 (trade > 5% of 1m volume): apply 2x stress slippage
    
    Conservative mode: uses 2x normal + stress slippage
    
    Returns: slippage in USD
    """
```

---

### Задание 5: Стратегия S01 — Funding Mean Reversion

**Файл:** `backend/app/backtest/strategies/funding_mean_reversion.py`

```python
class FundingMeanReversionStrategy(BaseStrategy):
    """
    S01: Funding Rate Extreme Mean Reversion
    
    Идея: funding rate — это плата за позицию. Когда funding экстремально высокий 
    (лонгеры переплачивают), открываем шорт. Когда экстремально низкий — лонг.
    Edge основан на mean reversion: funding возвращается к среднему.
    
    Entry rules:
      - Long:  funding_rate < percentile_10 (extremely negative)
      - Short: funding_rate > percentile_90 (extremely positive)
    
    Exit rules:
      - Mean reversion: funding returns to neutral zone (percentile_40-60)
      - Time-based: max_hold_hours (default 24)
      - Stop-loss: 2% от entry price
    
    Position sizing: fixed USD amount
    """
    
    DEFAULT_PARAMS = {
        "funding_long_threshold": -0.0001,    # -0.01% (10th percentile typical)
        "funding_short_threshold": 0.0003,     # +0.03% (90th percentile typical)
        "neutral_low": -0.00005,               # -0.005% (40th percentile)
        "neutral_high": 0.00005,               # +0.005% (60th percentile)
        "max_hold_hours": 24,
        "stop_loss_pct": 0.02,                 # 2%
        "position_size_usd": 10_000,
    }
    
    def generate_signals(self, data_up_to_t: pd.DataFrame) -> Optional[str]:
        """
        Returns: "long" | "short" | None
        Uses only data[:t+1] (no look-ahead)
        """
    
    def check_exit(self, position: Position, data_up_to_t: pd.DataFrame) -> Tuple[bool, str]:
        """
        Returns: (should_exit, exit_reason)
        exit_reason: "mean_reversion" | "time_based" | "stop_loss"
        """
```

**Expected edge (per research):** Sharpe 1.0-1.8, 8-15% APR (2022-2024 data)

---

### Задание 6: Стратегия S02 — Basis Compression

**Файл:** `backend/app/backtest/strategies/basis_compression.py`

```python
class BasisCompressionStrategy(BaseStrategy):
    """
    S02: Spot/Perp Basis Compression
    
    Идея: perpetual futures торгуются с premium/discount к споту (basis).
    Basis = (perp_price - spot_price) / spot_price
    Когда basis экстремально широкий — открываем позицию против basis.
    
    Entry rules:
      - Long perp + short spot proxy: basis < -0.1%
      - Short perp + long spot proxy: basis > +0.2%
    
    Note: мы не торгуем реальный спот. В backtest:
      - "Long perp" = long perpetual position
      - "Short spot proxy" = modeled as offset (simplified for MVP)
    
    Exit rules:
      - Basis returns to 0 (crosses zero line)
      - Time-based: max_hold_hours (default 48)
    
    Expected edge: 1.8-11% APR net
    """
    
    DEFAULT_PARAMS = {
        "basis_long_threshold": -0.001,     # -0.1%
        "basis_short_threshold": 0.002,      # +0.2%
        "max_hold_hours": 48,
        "position_size_usd": 10_000,
    }
    
    # Spot price получаем из ohlcv_1m.close (перп) и CoinGecko (спот)
    # Для MVP: basis = (perp_close - perp_close_lagged) / perp_close_lagged
    # Упрощённая версия: используем только perp цены, спот как reference
```

**Упрощение для MVP:**
- У нас нет реального спот потока. Используй proxy:
  - `basis = (close - vwap_24h) / vwap_24h` где `vwap_24h` — volume-weighted average price за 24 часа
  - Или `basis = (close - sma_24h) / sma_24h`
- В комментариях укажи: "FIXME: replace with real spot price when spot adapter added"

---

### Задание 7: Стратегия S04 — Liquidation Cascade Fade

**Файл:** `backend/app/backtest/strategies/liquidation_cascade_fade.py`

```python
class LiquidationCascadeFadeStrategy(BaseStrategy):
    """
    S04: Liquidation Cascade Fade
    
    Идея: liquidation cascades создают экстремальное движение цены.
    После cascade цена часто отскакивает (fade). 
    Торгуем против направления cascade.
    
    Entry rules:
      - Long:  liq_spike_1h > 95th percentile AND price_change_1h < -3%
      - Short: liq_spike_1h > 95th percentile AND price_change_1h > +3%
    
    Exit rules:
      - Time-based: hold_hours (default 6) — лучший результат по исследованиям
      - Price recovery: 50% of initial move
    
    Expected edge: PF 2.0-3.2, WR 55-68% (walk-forward validated)
    """
    
    DEFAULT_PARAMS = {
        "liq_percentile_threshold": 95.0,    # 95th percentile
        "price_move_threshold": 0.03,         # 3% move in 1 hour
        "hold_hours": 6,
        "recovery_pct": 0.5,                  # exit at 50% recovery
        "position_size_usd": 10_000,
    }
    
    def detect_liquidation_spike(self, data_up_to_t: pd.DataFrame) -> Tuple[bool, float]:
        """
        Checks if last 1h liquidation volume is above 95th percentile
        of historical distribution.
        Uses only data[:t+1] to calculate percentile (rolling window).
        """
    
    def detect_price_move(self, data_up_to_t: pd.DataFrame) -> Tuple[bool, str, float]:
        """
        Checks if price moved > threshold in last 1 hour.
        Returns: (triggered, direction "up"/"down", move_pct)
        """
```

---

### Задание 8: PnL Decomposition + Metrics

**Файл:** `backend/app/backtest/metrics.py`

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np
import pandas as pd

@dataclass
class BacktestResult:
    # Meta
    strategy_type: str
    symbol: str
    exchange: str
    start_ms: int
    end_ms: int
    total_bars: int
    data_coverage: float           # % of bars with complete data
    
    # Returns
    total_return_pct: float         # total return in %
    cagr_pct: float                 # compound annual growth rate
    
    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float             # CAGR / max drawdown
    
    # Drawdown
    max_drawdown_pct: float
    max_drawdown_duration_ms: int   # longest drawdown in ms
    
    # Trade stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float                 # %
    profit_factor: float            # gross profit / gross loss
    avg_trade_pnl: float            # USD
    median_trade_pnl: float         # USD
    avg_win: float                  # USD
    avg_loss: float                 # USD
    best_trade: float               # USD
    worst_trade: float              # USD
    
    # Time
    exposure_time_pct: float        # % of time in market
    avg_hold_time_min: float
    median_hold_time_min: float
    
    # PnL Decomposition (all in % of initial equity)
    price_pnl_pct: float            # from price movement
    funding_pnl_pct: float          # from funding payments
    fees_drag_pct: float            # negative (cost)
    slippage_drag_pct: float        # negative (cost)
    net_pnl_pct: float              # total after all costs
    
    # Detailed data
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[EquityPoint] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes to dict for JSON response."""
    
    def summary(self) -> str:
        """Returns human-readable summary string."""


def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Annualized Sharpe ratio.
    returns: daily returns series
    """

def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Annualized Sortino ratio (downside deviation only).
    """

def calculate_drawdown(equity_series: pd.Series) -> Tuple[float, int]:
    """
    Returns: (max_drawdown_pct, max_drawdown_duration_ms)
    """

def decompose_pnl(trades: List[Trade], initial_equity: float) -> Dict[str, float]:
    """
    Decomposes total PnL into components:
    - price_pnl
    - funding_pnl  
    - fees
    - slippage
    Returns each as % of initial_equity.
    """
```

---

### Задание 9: Backtest CLI

**Файл:** `backend/scripts/run_backtest.py`

```bash
# Usage examples:
cd backend

# S01 — Funding Mean Reversion, BTC, 30 days
python scripts/run_backtest.py \
  --strategy funding_mean_reversion \
  --symbol BTC \
  --exchange binance \
  --days 30 \
  --output results_s01_btc.json

# S02 — Basis Compression, ETH, 60 days
python scripts/run_backtest.py \
  --strategy basis_compression \
  --symbol ETH \
  --exchange binance \
  --days 60

# S04 — Liquidation Cascade, BTC, 30 days
python scripts/run_backtest.py \
  --strategy liquidation_cascade_fade \
  --symbol BTC \
  --exchange binance \
  --days 30
```

CLI должен:
1. Парсить аргументы (`--strategy`, `--symbol`, `--exchange`, `--days`, `--output`)
2. Создавать `BacktestConfig`
3. Создавать соответствующую стратегию
4. Запускать `BacktestEngine.run()`
5. Выводить `result.summary()` в консоль
6. Сохранять JSON если `--output` указан

---

### Задание 10: API Endpoint

**Файл:** `backend/app/api/v1/backtest.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.persistence.database import get_db
from app.backtest.engine import BacktestEngine
from app.backtest.strategies import STRATEGY_REGISTRY

router = APIRouter(prefix="/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    strategy: str                    # "funding_mean_reversion" | "basis_compression" | "liquidation_cascade_fade"
    symbol: str                      # "BTC" | "ETH" | "SOL" | "HYPE"
    exchange: str = "binance"
    start_date: Optional[str] = None # "2026-04-01" (YYYY-MM-DD)
    end_date: Optional[str] = None   # "2026-06-01" (YYYY-MM-DD)
    days: int = 30                   # if start_date not provided: backtest last N days
    position_size_usd: float = 10_000
    leverage: float = 1.0
    fee_type: str = "taker"
    use_slippage: bool = True
    params: Dict[str, Any] = {}      # strategy-specific parameter overrides

class BacktestResponse(BaseModel):
    success: bool
    result: Optional[BacktestResult] = None
    error: Optional[str] = None
    elapsed_ms: int

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    POST /api/v1/backtest/run
    
    Executes backtest with specified strategy and parameters.
    Returns full BacktestResult with metrics, trades, and equity curve.
    """
```

**Подключи router в** `backend/app/main.py`.

---

## 4. Проверки

После реализации запусти все 3 стратегии и покажи результат:

```bash
cd C:\Users\viach\OneDrive\Desktop\Deltagrid\backend

# S01 — Funding Mean Reversion
.\venv\Scripts\python.exe scripts\run_backtest.py --strategy funding_mean_reversion --symbol BTC --days 30

# S02 — Basis Compression  
.\venv\Scripts\python.exe scripts\run_backtest.py --strategy basis_compression --symbol ETH --days 60

# S04 — Liquidation Cascade Fade
.\venv\Scripts\python.exe scripts\run_backtest.py --strategy liquidation_cascade_fade --symbol BTC --days 30
```

Для каждой стратегии покажи:

| Metric | Example |
|--------|---------|
| `total_return_pct` | +12.5% |
| `sharpe_ratio` | 1.45 |
| `max_drawdown_pct` | -8.3% |
| `win_rate` | 62% |
| `total_trades` | 34 |
| `profit_factor` | 1.8 |
| `avg_trade_pnl` | $127 |
| `exposure_time_pct` | 45% |
| `fees_drag_pct` | -2.1% |
| `funding_pnl_pct` | +3.4% |
| `slippage_drag_pct` | -0.8% |
| `data_coverage` | 98.5% |
| `elapsed_ms` | 2,450 |

**Sanity checks:**
- `net_pnl_pct ≈ price_pnl_pct + funding_pnl_pct - fees_drag_pct - slippage_drag_pct`
- `win_rate` между 30% и 80% (вне этого диапазона — проверить логику)
- `sharpe_ratio` положительный для положительных стратегий
- `fees_drag_pct` отрицательный (всегда)
- `data_coverage > 95%` (ниже — проверить данные)

---

## 5. Файловая структура (что создать)

```
backend/
├── app/
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py                    # [Задание 1] BacktestEngine
│   │   ├── config.py                    # BacktestConfig, Position, Trade, EquityPoint
│   │   ├── fee_model.py                 # [Задание 2]
│   │   ├── funding_model.py             # [Задание 3]
│   │   ├── slippage_model.py            # [Задание 4]
│   │   ├── metrics.py                   # [Задание 8] BacktestResult + расчёты
│   │   └── strategies/
│   │       ├── __init__.py              # STRATEGY_REGISTRY, BaseStrategy
│   │       ├── funding_mean_reversion.py # [Задание 5] S01
│   │       ├── basis_compression.py     # [Задание 6] S02
│   │       └── liquidation_cascade_fade.py # [Задание 7] S04
│   └── api/
│       └── v1/
│           └── backtest.py              # [Задание 10] API endpoint
├── scripts/
│   └── run_backtest.py                  # [Задание 9] CLI
```

---

## 6. Правила

- **Не ломай существующие модули** — `uvicorn app.main:app` должен стартовать
- **Используй существующие SQLAlchemy модели** из `domain/models.py`
- **Используй существующие Pydantic модели** из `data_models.py` (OHLCVCandle)
- **Git commit после каждого задания** (или после каждой стратегии)
- **.md комментарии на русском, код на английском**
- **Look-ahead bias: данные t+1 НЕ доступны при обработке бара t** — это главное правило
- **Funding settlement: exact times, NO interpolation** — 00:00/08:00/16:00 UTC для CEX
- **Если тест не проходит sanity check — не игнорируй, разберись почему**

---

## 7. Ожидаемый результат (чеклист)

- [ ] `engine.py` — bar-by-bar event loop с look-ahead protection
- [ ] `fee_model.py` — maker/taker fees per exchange
- [ ] `funding_model.py` — exact settlement times (8h CEX, 1h HL)
- [ ] `slippage_model.py` — token-specific two-component slippage
- [ ] `strategies/funding_mean_reversion.py` — S01
- [ ] `strategies/basis_compression.py` — S02  
- [ ] `strategies/liquidation_cascade_fade.py` — S04
- [ ] `metrics.py` — 20+ metrics, PnL decomposition
- [ ] `scripts/run_backtest.py` — CLI
- [ ] `api/v1/backtest.py` — POST /api/v1/backtest/run
- [ ] Результаты 3 стратегий (таблица metrics)
- [ ] `uvicorn app.main:app` стартует без ошибок
