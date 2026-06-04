# DeltaGrid — Полная спецификация backend (июнь 2026)

## 1. О проекте

DeltaGrid — backtesting-first research terminal для CEX/DEX perpetual futures markets.
- **Цель:** дать трейдеру возможность проверить стратегию на исторических данных перед входом в позицию.
- **Аудитория:** self-use (сам пользователь как trader/researcher), потом SaaS.
- **Рынки:** CEX perpetuals (Binance, Bybit, OKX), DEX perpetuals (Hyperliquid).
- **Токены:** BTC, ETH, SOL, HYPE (4 токена, seed data уже в БД).
- **Метрики:** funding rate, open interest, liquidations, long/short ratio, basis, OHLCV 1m.
- **Бюджет API:** $334/мес (CoinGlass Standard $299 + CoinGecko Basic $35 + биржевые API бесплатно).
- **Технологии:** FastAPI (Python), SQLAlchemy 2.0, Pydantic, Alembic, SQLite (WAL mode), Next.js 14 (frontend — НЕ трогать).
- **Локальный путь:** C:\Users\viach\OneDrive\Desktop\Deltagrid
- **GitHub:** https://github.com/calwdqwill/Deltagrid

## 2. Архитектура

```
Frontend (Next.js 14, localhost:3000) — НЕ трогать
    ↓ HTTP REST
FastAPI (localhost:8000, uvicorn app.main:app)
    ├── /api/v1/backtest/run    → BacktestEngine
    ├── /api/v1/data/health     → Data Quality (новое)
    ├── /api/v1/data/quality/*  → Data Quality (новое)
    └── /api/v1/scanner/*       → Scanner (новое, потом)
    ↓
Backend Layer
    ├── Backtest Engine (backtest/)
    │   ├── engine.py, fee_model.py, funding_model.py
    │   ├── slippage_model.py, metrics.py
    │   ├── quality_monitor.py (НОВОЕ)
    │   ├── gate.py (НОВОЕ)
    │   └── strategies/*
    ├── Data Layer (adapters/data/)
    │   ├── BaseDataAdapter, BinanceAdapter
    │   ├── CoinGlassAdapter, CoinGeckoAdapter
    │   ├── SymbolMapper, DataWriter
    │   └── RateLimiter (TokenBucket, CircuitBreaker)
    ├── Scheduler (scheduler.py) (НОВОЕ)
    └── Incremental Update (incremental_update.py) (НОВОЕ)
    ↓ SQLAlchemy ORM
SQLite (WAL mode), 52 таблицы, Alembic head: d08fc5113b42
```

## 3. Что уже реализовано (полностью, работает, в Git)

### 3.1 Data Layer (backend/app/adapters/data/)

**base_adapter.py**
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class BaseDataAdapter(ABC):
    """Абстрактный базовый класс для всех провайдеров."""
    
    def __init__(self, db_session, symbol_mapper, rate_limiter):
        self.db = db_session
        self.mapper = symbol_mapper
        self.limiter = rate_limiter
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Проверяет доступность провайдера."""
    
    @abstractmethod
    async def fetch_ohlcv_1m(self, symbol: str, start_ms: int, end_ms: int) -> List[OHLCVCandle]:
        """Возвращает 1m OHLCV свечи за указанный период."""
    
    @abstractmethod
    async def fetch_funding_rate_history(self, exchange: str, symbol: str, 
                                          start_ms: int, end_ms: int) -> List[FundingRate]:
        """Возвращает историю funding rates."""
    
    @abstractmethod
    async def fetch_open_interest_history(self, exchange: str, symbol: str,
                                           start_ms: int, end_ms: int) -> List[OpenInterest]:
        """Возвращает историю open interest."""
    
    @abstractmethod
    async def fetch_liquidation_history(self, exchange: str, symbol: str,
                                         start_ms: int, end_ms: int) -> List[Liquidation]:
        """Возвращает историю ликвидаций."""
    
    @abstractmethod
    async def fetch_long_short_ratio_history(self, exchange: str, symbol: str,
                                              start_ms: int, end_ms: int) -> List[LongShortRatio]:
        """Возвращает историю long/short ratio."""

class DataAdapterRegistry:
    """Реестр адаптеров. Позволяет получить адаптер по имени провайдера."""
    _adapters: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type):
        cls._adapters[name] = adapter_class
    
    @classmethod
    def get(cls, name: str) -> type:
        return cls._adapters.get(name)
    
    @classmethod
    def list(cls) -> List[str]:
        return list(cls._adapters.keys())

class FallbackChain:
    """Цепочка fallback: если primary не отвечает — переходим к secondary."""
    def __init__(self, adapters: List[BaseDataAdapter]):
        self.adapters = adapters
    
    async def fetch_with_fallback(self, method_name: str, *args, **kwargs):
        for adapter in self.adapters:
            try:
                method = getattr(adapter, method_name)
                return await method(*args, **kwargs)
            except Exception as e:
                continue
        raise Exception("All adapters in fallback chain failed")
```

**data_models.py** — Pydantic модели:
```python
from pydantic import BaseModel
from typing import Optional

class OHLCVCandle(BaseModel):
    exchange: str
    symbol: str          # канонический символ (BTC, ETH, SOL, HYPE)
    timestamp: int       # unix timestamp в миллисекундах
    open: float
    high: float
    low: float
    close: float
    volume: float

class FundingRate(BaseModel):
    exchange: str
    symbol: str
    timestamp: int       # unix timestamp в миллисекундах
    rate: float          # funding rate (например 0.000312 = 0.0312%)
    interval_hours: int  # 8 для CEX (Binance/Bybit/OKX), 1 для Hyperliquid

class OpenInterest(BaseModel):
    exchange: str
    symbol: str
    timestamp: int
    oi_value: float      # OI в USD

class Liquidation(BaseModel):
    exchange: str
    symbol: str
    timestamp: int
    side: str            # "long" или "short"
    qty: float
    price: float
    usd: float           # номинал ликвидации в USD

class LongShortRatio(BaseModel):
    exchange: str
    symbol: str
    timestamp: int
    long_ratio: float    # доля лонгов (0.0 - 1.0)
    short_ratio: float   # доля шортов (0.0 - 1.0)

class ProviderHealthStatus(BaseModel):
    provider: str
    healthy: bool
    latency_ms: float
    last_success: Optional[int] = None  # timestamp последнего успешного запроса
    error_count_24h: int = 0

class BackfillResult(BaseModel):
    provider: str
    symbol: str
    start_ms: int
    end_ms: int
    fetched: int
    inserted: int
    gaps: int
    elapsed_seconds: float
```

**rate_limiter.py**:
```python
import time
import asyncio
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"       # нормальная работа
    OPEN = "open"           # блокировка (too many errors)
    HALF_OPEN = "half_open" # проверка восстановления

class TokenBucket:
    """Rate limiter на основе leaky bucket algorithm."""
    def __init__(self, rate: int, per_seconds: int = 60):
        self.rate = rate           # максимум запросов
        self.per_seconds = per_seconds
        self.tokens = float(rate)
        self.last_update = time.monotonic()
    
    async def acquire(self, tokens: int = 1):
        while True:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per_seconds))
            self.last_update = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            await asyncio.sleep(0.1)

class CircuitBreaker:
    """Circuit breaker: OPEN после N ошибок, HALF_OPEN через timeout."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN

class RetryPolicy:
    """Exponential backoff + jitter."""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute(self, func, *args, **kwargs):
        import random
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                await asyncio.sleep(delay)

class GlobalRateLimiter:
    """Глобальный rate limiter, координирует все адаптеры."""
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.circuits: Dict[str, CircuitBreaker] = {}
    
    def get_bucket(self, provider: str, rate: int, per_seconds: int = 60) -> TokenBucket:
        if provider not in self.buckets:
            self.buckets[provider] = TokenBucket(rate, per_seconds)
        return self.buckets[provider]
    
    def get_circuit(self, provider: str) -> CircuitBreaker:
        if provider not in self.circuits:
            self.circuits[provider] = CircuitBreaker()
        return self.circuits[provider]
```

**symbol_mapper.py**:
```python
from sqlalchemy.orm import Session
from app.domain.models import Instrument, InstrumentAlias

class SymbolMapper:
    """Маппинг канонических символов ↔ провайдер-специфичные."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_alias(self, symbol: str, provider: str) -> str:
        """BTC + binance → BTCUSDT. BTC + okx → BTC-USDT-SWAP."""
        alias = self.db.query(InstrumentAlias).join(Instrument).filter(
            Instrument.symbol == symbol,
            InstrumentAlias.provider == provider
        ).first()
        return alias.provider_symbol if alias else symbol
    
    def get_canonical(self, provider_symbol: str, provider: str) -> str:
        """BTCUSDT + binance → BTC."""
        alias = self.db.query(InstrumentAlias).filter(
            InstrumentAlias.provider_symbol == provider_symbol,
            InstrumentAlias.provider == provider
        ).first()
        return alias.instrument.symbol if alias and alias.instrument else provider_symbol
    
    def seed_defaults(self):
        """Создаёт seed: 4 токена + 7 aliases каждый."""
        instruments = [
            {"symbol": "BTC", "name": "Bitcoin", "category": "crypto"},
            {"symbol": "ETH", "name": "Ethereum", "category": "crypto"},
            {"symbol": "SOL", "name": "Solana", "category": "crypto"},
            {"symbol": "HYPE", "name": "Hyperliquid", "category": "crypto"},
        ]
        aliases = [
            # BTC
            {"symbol": "BTC", "provider": "binance", "provider_symbol": "BTCUSDT"},
            {"symbol": "BTC", "provider": "bybit", "provider_symbol": "BTCUSDT"},
            {"symbol": "BTC", "provider": "okx", "provider_symbol": "BTC-USDT-SWAP"},
            {"symbol": "BTC", "provider": "hyperliquid", "provider_symbol": "BTC"},
            {"symbol": "BTC", "provider": "coinglass", "provider_symbol": "BTC"},
            {"symbol": "BTC", "provider": "coingecko", "provider_symbol": "bitcoin"},
            # ETH
            {"symbol": "ETH", "provider": "binance", "provider_symbol": "ETHUSDT"},
            {"symbol": "ETH", "provider": "bybit", "provider_symbol": "ETHUSDT"},
            {"symbol": "ETH", "provider": "okx", "provider_symbol": "ETH-USDT-SWAP"},
            {"symbol": "ETH", "provider": "hyperliquid", "provider_symbol": "ETH"},
            {"symbol": "ETH", "provider": "coinglass", "provider_symbol": "ETH"},
            {"symbol": "ETH", "provider": "coingecko", "provider_symbol": "ethereum"},
            # SOL
            {"symbol": "SOL", "provider": "binance", "provider_symbol": "SOLUSDT"},
            {"symbol": "SOL", "provider": "bybit", "provider_symbol": "SOLUSDT"},
            {"symbol": "SOL", "provider": "okx", "provider_symbol": "SOL-USDT-SWAP"},
            {"symbol": "SOL", "provider": "hyperliquid", "provider_symbol": "SOL"},
            {"symbol": "SOL", "provider": "coinglass", "provider_symbol": "SOL"},
            {"symbol": "SOL", "provider": "coingecko", "provider_symbol": "solana"},
            # HYPE
            {"symbol": "HYPE", "provider": "binance", "provider_symbol": "HYPEUSDT"},
            {"symbol": "HYPE", "provider": "bybit", "provider_symbol": "HYPEUSDT"},
            {"symbol": "HYPE", "provider": "okx", "provider_symbol": "HYPE-USDT-SWAP"},
            {"symbol": "HYPE", "provider": "hyperliquid", "provider_symbol": "HYPE"},
            {"symbol": "HYPE", "provider": "coinglass", "provider_symbol": "HYPE"},
            {"symbol": "HYPE", "provider": "coingecko", "provider_symbol": "hyperliquid"},
        ]
        # ... (seed logic, проверка на существование перед insert)
```

**data_writer.py**:
```python
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from typing import List
from app.domain.models import OHLCV1m, FundingRate as FundingRateModel, ProviderSyncRun, DataQualityLog

class DataWriter:
    """Записывает нормализованные данные в SQLite."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def upsert_ohlcv(self, candles: List[OHLCVCandle]):
        """Batch UPSERT. Вставляет новые, обновляет существующие."""
        if not candles:
            return 0
        data = [c.model_dump() for c in candles]
        stmt = sqlite_insert(OHLCV1m).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['exchange', 'symbol', 'timestamp'],
            set_={
                'open': stmt.excluded.open,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'close': stmt.excluded.close,
                'volume': stmt.excluded.volume,
            }
        )
        self.db.execute(stmt)
        self.db.commit()
        return len(candles)
    
    def upsert_funding_rates(self, rates: List[FundingRate]):
        """Аналогично upsert_ohlcv для funding_rates таблицы."""
        # ...
    
    def create_sync_run(self, provider: str, symbol: str, start_ms: int, end_ms: int,
                       fetched: int, inserted: int, status: str, error: str = None):
        """Логирует результат sync в provider_sync_runs."""
        run = ProviderSyncRun(
            provider=provider,
            symbol=symbol,
            start_time=start_ms,
            end_time=end_ms,
            records_fetched=fetched,
            records_inserted=inserted,
            status=status,
            error_message=error,
        )
        self.db.add(run)
        self.db.commit()
```

**backfill_orchestrator.py**:
```python
class ChunkedBackfill:
    """Оркестрирует chunked backfill с gap detection."""
    
    def __init__(self, adapter: BaseDataAdapter, writer: DataWriter, chunk_size: int = 1500):
        self.adapter = adapter
        self.writer = writer
        self.chunk_size = chunk_size
    
    async def backfill_symbol(self, symbol: str, exchange: str, start_ms: int, end_ms: int):
        """Backfill одного символа за период."""
        total_fetched = 0
        total_inserted = 0
        gaps = 0
        current_start = start_ms
        
        while current_start < end_ms:
            candles = await self.adapter.fetch_ohlcv_1m(symbol, current_start, end_ms)
            if not candles:
                break
            inserted = self.writer.upsert_ohlcv(candles)
            total_fetched += len(candles)
            total_inserted += inserted
            
            # Gap detection
            if len(candles) < self.chunk_size:
                break  # последний чанк
            
            last_ts = candles[-1].timestamp
            expected_next = last_ts + 60000  # +1 минута
            if candles[0].timestamp > current_start + 300000:  # gap > 5 минут
                gaps += 1
            
            current_start = expected_next
        
        return BackfillResult(
            provider=self.adapter.__class__.__name__,
            symbol=symbol,
            start_ms=start_ms,
            end_ms=end_ms,
            fetched=total_fetched,
            inserted=total_inserted,
            gaps=gaps,
            elapsed_seconds=0,  # измеряется выше
        )
```

**binance_adapter.py**:
```python
import httpx
from app.adapters.data.base_adapter import BaseDataAdapter
from app.adapters.data.data_models import OHLCVCandle

class BinanceAdapter(BaseDataAdapter):
    """Binance USD-M Futures adapter."""
    BASE_URL = "https://fapi.binance.com"
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.BASE_URL}/fapi/v1/ping", timeout=5)
                return r.status_code == 200
            except:
                return False
    
    async def fetch_ohlcv_1m(self, symbol: str, start_ms: int, end_ms: int) -> List[OHLCVCandle]:
        """Fetch 1m klines с pagination. 1500 candles max per request."""
        await self.limiter.acquire(1)
        binance_symbol = self.mapper.get_alias(symbol, "binance")
        
        all_candles = []
        current_start = start_ms
        
        async with httpx.AsyncClient() as client:
            while current_start < end_ms:
                params = {
                    "symbol": binance_symbol,
                    "interval": "1m",
                    "startTime": current_start,
                    "endTime": end_ms,
                    "limit": 1500,
                }
                r = await client.get(f"{self.BASE_URL}/fapi/v1/klines", params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
                
                if not data:
                    break
                
                for row in data:
                    all_candles.append(OHLCVCandle(
                        exchange="binance",
                        symbol=symbol,  # канонический символ
                        timestamp=row[0],  # open_time
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                    ))
                
                # next chunk
                last_ts = data[-1][0]
                current_start = last_ts + 60000  # +1 min
                
                if len(data) < 1500:
                    break
        
        return all_candles
```

**coinglass_adapter.py**:
```python
import httpx
import os

class CoinGlassAdapter(BaseDataAdapter):
    """CoinGlass API V4 adapter."""
    BASE_URL = "https://open-api-v4.coinglass.com"
    API_KEY = os.environ.get("COINGLASS_API_KEY", "")
    
    async def health_check(self) -> bool:
        headers = {"CG-API-KEY": self.API_KEY}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(f"{self.BASE_URL}/api/futures/fundingRate/ohlc-history",
                                     headers=headers, params={"limit": 1}, timeout=5)
                return r.status_code == 200
            except:
                return False
    
    async def fetch_funding_rate_history(self, exchange: str, symbol: str,
                                          start_ms: int, end_ms: int) -> List[FundingRate]:
        """Fetch funding rate OHLC history."""
        headers = {"CG-API-KEY": self.API_KEY}
        cg_symbol = self.mapper.get_alias(symbol, "coinglass")
        
        params = {
            "exchange": exchange,
            "symbol": cg_symbol,
            "interval": "1m",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }
        
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.BASE_URL}/api/futures/fundingRate/ohlc-history",
                                 headers=headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            rates = []
            for row in data.get("data", []):
                rates.append(FundingRate(
                    exchange=exchange,
                    symbol=symbol,
                    timestamp=row["t"],  # timestamp from CoinGlass
                    rate=float(row["c"]),  # close funding rate
                    interval_hours=8 if exchange != "hyperliquid" else 1,
                ))
            return rates
    
    # ... fetch_open_interest_history, fetch_liquidation_history, fetch_long_short_ratio_history
    # аналогичная структура, разные endpoints
```

### 3.2 Backtest Engine (backend/app/backtest/)

**engine.py**:
```python
import pandas as pd
from typing import List, Tuple, Optional, Dict
from app.backtest.config import BacktestConfig, Position, Trade, EquityPoint
from app.backtest.fee_model import EXCHANGE_FEES, calculate_trade_fee
from app.backtest.funding_model import get_funding_payment
from app.backtest.slippage_model import calculate_slippage
from app.backtest.metrics import BacktestResult, calculate_sharpe, calculate_sortino, calculate_drawdown, decompose_pnl
from app.domain.models import OHLCV1m, FundingRate as FundingRateModel

class BacktestEngine:
    """
    Bar-by-bar event loop для perpetual futures backtesting.
    Ключевой принцип: structural look-ahead bias elimination.
    При обработке бара t данные t+1, t+2... НЕ доступны.
    """
    
    def __init__(self, db_session, config: BacktestConfig):
        self.db = db_session
        self.config = config
        self.position = Position(side="flat", entry_price=0, size_usd=0,
                                  entry_time_ms=0, funding_pnl=0, fees_paid=0, slippage_paid=0)
        self.trades: List[Trade] = []
        self.equity_curve: List[EquityPoint] = []
        self.current_equity = config.position_size_usd
        self.peak_equity = self.current_equity
    
    def run(self) -> BacktestResult:
        """Main entry point. Загружает данные, запускает bar loop, возвращает результат."""
        df_ohlcv, df_funding = self._load_data(
            self.config.symbol, self.config.exchange,
            self.config.start_ms, self.config.end_ms
        )
        
        strategy_class = STRATEGY_REGISTRY.get(self.config.strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {self.config.strategy_type}")
        
        strategy = strategy_class(self.config.params)
        
        trades = self._bar_loop(df_ohlcv, df_funding, strategy)
        
        result = self._compute_metrics(trades, df_ohlcv)
        return result
    
    def _load_data(self, symbol: str, exchange: str, start_ms: int, end_ms: int
                    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Загружает OHLCV и funding из SQLite."""
        ohlcv_rows = self.db.query(OHLCV1m).filter(
            OHLCV1m.symbol == symbol,
            OHLCV1m.exchange == exchange,
            OHLCV1m.timestamp >= start_ms,
            OHLCV1m.timestamp <= end_ms,
        ).order_by(OHLCV1m.timestamp).all()
        
        funding_rows = self.db.query(FundingRateModel).filter(
            FundingRateModel.symbol == symbol,
            FundingRateModel.exchange == exchange,
            FundingRateModel.timestamp >= start_ms,
            FundingRateModel.timestamp <= end_ms,
        ).order_by(FundingRateModel.timestamp).all()
        
        df_ohlcv = pd.DataFrame([{
            "timestamp": r.timestamp, "open": r.open, "high": r.high,
            "low": r.low, "close": r.close, "volume": r.volume,
        } for r in ohlcv_rows]).set_index("timestamp")
        
        df_funding = pd.DataFrame([{
            "timestamp": r.timestamp, "rate": r.rate, "interval_hours": r.interval_hours,
        } for r in funding_rows]).set_index("timestamp")
        
        return df_ohlcv, df_funding
    
    def _bar_loop(self, df_ohlcv: pd.DataFrame, df_funding: pd.DataFrame,
                   strategy) -> List[Trade]:
        """
        Core event loop. Итерирует бар за баром.
        На каждом шаге t: стратегия видит только data.iloc[:t+1].
        """
        for t in range(len(df_ohlcv)):
            current_bar = df_ohlcv.iloc[t]
            current_ts = df_ohlcv.index[t]
            
            # Данные только до t включительно — никакого look-ahead
            data_up_to_t = df_ohlcv.iloc[:t+1]
            funding_up_to_t = df_funding[df_funding.index <= current_ts]
            
            # Funding payment если наступил settlement time
            if self.position.side != "flat":
                applicable_funding = funding_up_to_t.iloc[-1] if len(funding_up_to_t) > 0 else None
                if applicable_funding is not None:
                    funding_payment = get_funding_payment(
                        current_ts, self.position.side, self.position.size_usd,
                        applicable_funding["rate"], self.config.exchange
                    )
                    self.position.funding_pnl -= funding_payment
            
            # Генерация сигналов (стратегия видит только data_up_to_t)
            if self.position.side == "flat":
                signal = strategy.generate_signals(data_up_to_t, funding_up_to_t)
                if signal in ["long", "short"]:
                    self._open_position(signal, current_ts, current_bar["close"],
                                        current_bar["volume"])
            else:
                should_exit, exit_reason = strategy.check_exit(
                    self.position, data_up_to_t, funding_up_to_t
                )
                if should_exit:
                    self._close_position(current_ts, current_bar["close"],
                                         current_bar["volume"], exit_reason)
            
            # Обновление equity curve
            self._update_equity(current_ts)
        
        # Закрыть открытую позицию в конце
        if self.position.side != "flat":
            last_ts = df_ohlcv.index[-1]
            last_close = df_ohlcv.iloc[-1]["close"]
            self._close_position(last_ts, last_close, df_ohlcv.iloc[-1]["volume"], "end_of_data")
        
        return self.trades
    
    def _open_position(self, side: str, timestamp: int, price: float, volume: float):
        """Открывает позицию."""
        fee = calculate_trade_fee(self.config.position_size_usd,
                                   self.config.fee_type == "maker", self.config.exchange)
        slippage = calculate_slippage(self.config.position_size_usd, volume,
                                       self.config.symbol, self.config.exchange)
        
        self.position = Position(
            side=side, entry_price=price, size_usd=self.config.position_size_usd,
            entry_time_ms=timestamp, funding_pnl=0, fees_paid=fee, slippage_paid=slippage
        )
        self.current_equity -= (fee + slippage)
    
    def _close_position(self, timestamp: int, price: float, volume: float, reason: str):
        """Закрывает позицию и записывает trade."""
        fee = calculate_trade_fee(self.config.position_size_usd,
                                   self.config.fee_type == "maker", self.config.exchange)
        slippage = calculate_slippage(self.config.position_size_usd, volume,
                                       self.config.symbol, self.config.exchange)
        
        direction = 1 if self.position.side == "long" else -1
        price_pnl = (price - self.position.entry_price) * direction * self.position.size_usd / self.position.entry_price
        
        trade = Trade(
            entry_time_ms=self.position.entry_time_ms,
            exit_time_ms=timestamp,
            symbol=self.config.symbol,
            exchange=self.config.exchange,
            side=self.position.side,
            entry_price=self.position.entry_price,
            exit_price=price,
            size_usd=self.position.size_usd,
            price_pnl=price_pnl,
            funding_pnl=self.position.funding_pnl,
            fees=self.position.fees_paid + fee,
            slippage=self.position.slippage_paid + slippage,
            net_pnl=price_pnl + self.position.funding_pnl - self.position.fees_paid - fee - self.position.slippage_paid - slippage,
            hold_duration_min=(timestamp - self.position.entry_time_ms) // 60000,
            exit_reason=reason,
        )
        self.trades.append(trade)
        self.current_equity += trade.net_pnl
        self.position = Position(side="flat", entry_price=0, size_usd=0,
                                  entry_time_ms=0, funding_pnl=0, fees_paid=0, slippage_paid=0)
    
    def _update_equity(self, timestamp: int):
        """Обновляет equity curve."""
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
        drawdown = self.peak_equity - self.current_equity
        drawdown_pct = drawdown / self.peak_equity if self.peak_equity > 0 else 0
        self.equity_curve.append(EquityPoint(
            timestamp_ms=timestamp, equity=self.current_equity,
            drawdown=drawdown, drawdown_pct=drawdown_pct
        ))
    
    def _compute_metrics(self, trades: List[Trade], df_ohlcv: pd.DataFrame) -> BacktestResult:
        """Вычисляет все метрики."""
        # ... (detailed metric calculation using metrics.py functions)
        pass
```

**funding_model.py**:
```python
from datetime import datetime, timezone

def get_funding_payment(timestamp_ms: int, position_side: str, size_usd: float,
                         funding_rate: float, exchange: str) -> float:
    """
    Рассчитывает funding payment для данного timestamp.
    
    Логика:
    1. Проверяем, является ли timestamp временем settlement:
       - CEX (binance/bybit/okx): 00:00, 08:00, 16:00 UTC → каждые 8 часов
       - Hyperliquid: каждый час (XX:00)
    
    2. Если НЕ settlement time → return 0
    
    3. Если settlement time:
       - Long + rate > 0 → платит rate * size (return положительное)
       - Long + rate < 0 → получает |rate| * size (return отрицательное)
       - Short → наоборот
    
    ВАЖНО: никакой интерполяции. Только exact settlement times.
    Ошибка в 1 час funding settlement = до 5% годовых ошибка в backtest.
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    hour = dt.hour
    minute = dt.minute
    
    # Проверка settlement time
    is_settlement = False
    if exchange == "hyperliquid":
        is_settlement = (minute == 0)
    else:
        is_settlement = (minute == 0 and hour in [0, 8, 16])
    
    if not is_settlement:
        return 0.0
    
    if position_side == "flat" or size_usd <= 0:
        return 0.0
    
    payment = funding_rate * size_usd
    
    if position_side == "long":
        return payment  # long платит когда rate > 0, получает когда rate < 0
    else:  # short
        return -payment  # short получает когда rate > 0, платит когда rate < 0

def is_funding_settlement_time(timestamp_ms: int, exchange: str) -> bool:
    """True если timestamp — время funding settlement."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    if exchange == "hyperliquid":
        return dt.minute == 0
    return dt.minute == 0 and dt.hour in [0, 8, 16]

def get_funding_rate_at_time(timestamp_ms: int, df_funding: pd.DataFrame) -> float:
    """
    Получает applicable funding rate для timestamp.
    Использует most recent funding rate <= timestamp.
    БЕЗ интерполяции.
    """
    applicable = df_funding[df_funding.index <= timestamp_ms]
    if len(applicable) == 0:
        return 0.0
    return applicable.iloc[-1]["rate"]
```

**metrics.py**:
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
    data_coverage: float
    
    # Returns
    total_return_pct: float
    cagr_pct: float
    
    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Drawdown
    max_drawdown_pct: float
    max_drawdown_duration_ms: int
    
    # Trade stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_trade_pnl: float
    median_trade_pnl: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    
    # Time
    exposure_time_pct: float
    avg_hold_time_min: float
    median_hold_time_min: float
    
    # PnL Decomposition
    price_pnl_pct: float
    funding_pnl_pct: float
    fees_drag_pct: float
    slippage_drag_pct: float
    net_pnl_pct: float
    
    # Detailed
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализует в dict для JSON response. Конвертирует numpy → Python types."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, (np.integer, np.int64)):
                result[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                result[key] = float(value)
            elif isinstance(value, list):
                result[key] = [
                    {k: float(v) if isinstance(v, (np.floating, np.float64)) else 
                     int(v) if isinstance(v, (np.integer, np.int64)) else v
                     for k, v in item.items()} if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def summary(self) -> str:
        """Human-readable summary."""
        return f"""
Backtest Result: {self.strategy_type} | {self.symbol} | {self.exchange}
─────────────────────────────────────────────────
Total Return:     {self.total_return_pct:+.2f}%
Sharpe Ratio:     {self.sharpe_ratio:.2f}
Max Drawdown:     {self.max_drawdown_pct:.2f}%
Win Rate:         {self.win_rate:.1f}%
Total Trades:     {self.total_trades}
Profit Factor:    {self.profit_factor:.2f}
Avg Trade PnL:    ${self.avg_trade_pnl:+.2f}
Exposure Time:    {self.exposure_time_pct:.1f}%
─────────────────────────────────────────────────
PnL Decomposition:
  Price PnL:      {self.price_pnl_pct:+.2f}%
  Funding:        {self.funding_pnl_pct:+.2f}%
  Fees (drag):    {self.fees_drag_pct:.2f}%
  Slippage (drag):{self.slippage_drag_pct:.2f}%
  ─────────────────
  Net PnL:        {self.net_pnl_pct:+.2f}%
─────────────────────────────────────────────────
Data Coverage:    {self.data_coverage:.1f}%
"""

def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio. returns — daily returns series."""
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 365
    excess_returns = returns - daily_rf
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(365)

def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sortino ratio (только downside deviation)."""
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / 365
    excess_returns = returns - daily_rf
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return float('inf') if excess_returns.mean() > 0 else 0.0
    return (excess_returns.mean() / downside_returns.std()) * np.sqrt(365)

def calculate_drawdown(equity_series: pd.Series) -> tuple:
    """Returns: (max_drawdown_pct, max_drawdown_duration_ms)"""
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd_idx = drawdown.idxmin()
    max_dd = drawdown.min()
    
    # Duration: от peak до recovery (или конца)
    peak_before = rolling_max.loc[:max_dd_idx].idxmax()
    recovery_after = drawdown.loc[max_dd_idx:]
    recovery_points = recovery_after[recovery_after >= 0]
    if len(recovery_points) > 0:
        recovery_idx = recovery_points.index[0]
        duration_ms = recovery_idx - peak_before
    else:
        duration_ms = equity_series.index[-1] - peak_before
    
    return max_dd, duration_ms

def decompose_pnl(trades: List, initial_equity: float) -> Dict[str, float]:
    """Разлагает PnL на компоненты. Возвращает % от initial_equity."""
    total_price_pnl = sum(t.price_pnl for t in trades)
    total_funding_pnl = sum(t.funding_pnl for t in trades)
    total_fees = sum(t.fees for t in trades)
    total_slippage = sum(t.slippage for t in trades)
    
    return {
        "price_pnl_pct": (total_price_pnl / initial_equity) * 100,
        "funding_pnl_pct": (total_funding_pnl / initial_equity) * 100,
        "fees_drag_pct": -(total_fees / initial_equity) * 100,
        "slippage_drag_pct": -(total_slippage / initial_equity) * 100,
    }
```

**strategies/__init__.py**:
```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
import pandas as pd

STRATEGY_REGISTRY: Dict[str, type] = {}

def register_strategy(name: str):
    """Декоратор для регистрации стратегии."""
    def decorator(cls):
        STRATEGY_REGISTRY[name] = cls
        return cls
    return decorator

class BaseStrategy(ABC):
    """Базовый класс для всех стратегий."""
    
    DEFAULT_PARAMS: Dict[str, Any] = {}
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
    
    @abstractmethod
    def generate_signals(self, ohlcv_up_to_t: pd.DataFrame,
                         funding_up_to_t: pd.DataFrame) -> Optional[str]:
        """Возвращает 'long', 'short', или None. Видит только data[:t+1]."""
    
    @abstractmethod
    def check_exit(self, position, ohlcv_up_to_t: pd.DataFrame,
                   funding_up_to_t: pd.DataFrame) -> Tuple[bool, str]:
        """Возвращает (should_exit, exit_reason)."""
```

### 3.3 SQLAlchemy модели (backend/app/domain/models.py)

```python
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, Text, UniqueConstraint, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.persistence.database import Base
from datetime import datetime

class Instrument(Base):
    __tablename__ = 'instruments'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)      # "BTC"
    name = Column(String)                                      # "Bitcoin"
    category = Column(String, default='crypto')               # "crypto"
    created_at = Column(DateTime, default=datetime.utcnow)
    aliases = relationship("InstrumentAlias", back_populates="instrument")

class InstrumentAlias(Base):
    __tablename__ = 'instrument_aliases'
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('instruments.id'), nullable=False)
    provider = Column(String, nullable=False)                 # "binance"
    provider_symbol = Column(String, nullable=False)          # "BTCUSDT"
    is_primary = Column(Boolean, default=True)
    instrument = relationship("Instrument", back_populates="aliases")

class OHLCV1m(Base):
    __tablename__ = 'ohlcv_1m'
    __table_args__ = (UniqueConstraint('exchange', 'symbol', 'timestamp', name='uix_ohlcv'),)
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)                 # "binance"
    symbol = Column(String, nullable=False)                   # "BTC"
    timestamp = Column(BigInteger, nullable=False)            # unix ms
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

class FundingRate(Base):
    __tablename__ = 'funding_rates'
    __table_args__ = (UniqueConstraint('exchange', 'symbol', 'timestamp', name='uix_funding'),)
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    rate = Column(Float, nullable=False)                      # 0.000312
    interval_hours = Column(Integer, default=8)              # 8 CEX, 1 HL

class OpenInterest(Base):
    __tablename__ = 'open_interest'
    __table_args__ = (UniqueConstraint('exchange', 'symbol', 'timestamp', name='uix_oi'),)
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    oi_value = Column(Float, nullable=False)                  # OI в USD

class Liquidation(Base):
    __tablename__ = 'liquidations'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    side = Column(String, nullable=False)                     # "long" или "short"
    qty = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    usd = Column(Float, nullable=False)                       # номинал в USD

class LongShortRatio(Base):
    __tablename__ = 'long_short_ratio'
    __table_args__ = (UniqueConstraint('exchange', 'symbol', 'timestamp', name='uix_ls'),)
    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    long_ratio = Column(Float, nullable=False)               # 0.0 - 1.0
    short_ratio = Column(Float, nullable=False)              # 0.0 - 1.0

class ExchangeFee(Base):
    __tablename__ = 'exchange_fees'
    id = Column(Integer, primary_key=True)
    exchange = Column(String, unique=True, nullable=False)
    maker_fee = Column(Float, nullable=False)                # 0.0002 = 0.02%
    taker_fee = Column(Float, nullable=False)                # 0.0005 = 0.05%
    funding_interval_hours = Column(Integer, default=8)

class ProviderSyncRun(Base):
    __tablename__ = 'provider_sync_runs'
    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)                # "binance", "coinglass"
    endpoint = Column(String)                                 # "fapi/v1/klines"
    symbol = Column(String)
    start_time = Column(BigInteger)                          # unix ms
    end_time = Column(BigInteger)
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    status = Column(String, default='success')              # "success" | "error" | "partial"
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataQualityLog(Base):
    __tablename__ = 'data_quality_logs'
    id = Column(Integer, primary_key=True)
    check_type = Column(String, nullable=False)              # "gap", "stale", "coverage"
    symbol = Column(String)
    exchange = Column(String)
    metric = Column(String)                                   # "ohlcv", "funding"
    value = Column(Float)                                     # фактическое значение
    threshold = Column(Float)                                 # порог
    status = Column(String, nullable=False)                   # "ok" | "warning" | "critical"
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3.4 API Endpoints (backend/app/api/v1/backtest.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.persistence.database import get_db
from app.backtest.engine import BacktestEngine
from app.backtest.config import BacktestConfig
from app.backtest.metrics import BacktestResult

router = APIRouter(prefix="/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    strategy: str                    # "funding_mean_reversion" | "basis_compression" | "liquidation_cascade_fade"
    symbol: str                      # "BTC" | "ETH" | "SOL" | "HYPE"
    exchange: str = "binance"
    start_date: Optional[str] = None # "2026-04-01" (YYYY-MM-DD)
    end_date: Optional[str] = None   # "2026-06-01"
    days: int = 30                   # если start_date не указан — backtest последние N дней
    position_size_usd: float = 10_000
    leverage: float = 1.0
    fee_type: str = "taker"          # "maker" | "taker"
    use_slippage: bool = True
    params: Dict[str, Any] = {}      # strategy-specific overrides

class BacktestResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_ms: int

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    POST /api/v1/backtest/run
    
    Запускает backtest с указанной стратегией и параметрами.
    Возвращает полный BacktestResult с метриками, сделками, equity curve.
    """
    import time
    start_time = time.monotonic()
    
    try:
        # Конвертация дат в timestamps
        if request.start_date and request.end_date:
            from datetime import datetime, timezone
            start_ms = int(datetime.strptime(request.start_date, "%Y-%m-%d")
                           .replace(tzinfo=timezone.utc).timestamp() * 1000)
            end_ms = int(datetime.strptime(request.end_date, "%Y-%m-%d")
                         .replace(tzinfo=timezone.utc).timestamp() * 1000)
        else:
            import datetime as dt
            end_ms = int(dt.datetime.utcnow().timestamp() * 1000)
            start_ms = end_ms - (request.days * 24 * 60 * 60 * 1000)
        
        config = BacktestConfig(
            strategy_type=request.strategy,
            symbol=request.symbol,
            exchange=request.exchange,
            start_ms=start_ms,
            end_ms=end_ms,
            position_size_usd=request.position_size_usd,
            leverage=request.leverage,
            fee_type=request.fee_type,
            use_slippage=request.use_slippage,
            params=request.params,
        )
        
        engine = BacktestEngine(db, config)
        result = engine.run()
        
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        
        return BacktestResponse(
            success=True,
            result=result.to_dict(),
            elapsed_ms=elapsed_ms,
        )
    
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return BacktestResponse(
            success=False,
            error=str(e),
            elapsed_ms=elapsed_ms,
        )
```

### 3.5 Результаты бэктестов (подтверждено, работает)

**S01 — Funding Mean Reversion (BTC, 30 дней):**
- total_return_pct: +30.37%
- sharpe_ratio: 8.76
- max_drawdown_pct: -7.77%
- win_rate: 59.5%
- total_trades: 37
- profit_factor: 2.93
- avg_trade_pnl: +$82.24
- exposure_time_pct: 98.4%
- fees_drag_pct: -3.70%
- funding_pnl_pct: +35.10%
- slippage_drag_pct: -1.19%
- data_coverage: 100.0%

**S02 — Basis Compression (ETH, 60 дней):**
- total_return_pct: -22.89%
- sharpe_ratio: -3.71
- max_drawdown_pct: -29.89%
- win_rate: 60.0%
- total_trades: 200
- profit_factor: 0.59
- avg_trade_pnl: -$11.44
- fees_drag_pct: -20.00%
- Примечание: использует proxy basis (close - SMA_24h) / SMA_24h вместо реального spot/perp basis. FIXME: replace with real spot price when spot adapter added.

**S04 — Liquidation Cascade Fade (BTC, 30 дней):**
- total_return_pct: +4.17%
- sharpe_ratio: 6.75
- max_drawdown_pct: -0.96%
- win_rate: 71.4%
- total_trades: 7
- profit_factor: 7.62
- avg_trade_pnl: +$59.62
- exposure_time_pct: 2.7%
- fees_drag_pct: -0.70%
- funding_pnl_pct: +0.37%
- slippage_drag_pct: -0.14%
- data_coverage: 100.0%

## 4. Что НУЖНО реализовать (эта задача)

### Задание 1: Incremental Update Service

**Файл:** `backend/scripts/incremental_update.py`

**Назначение:** Автоматическое обновление данных каждые N минут. Забирает только новые данные с момента последнего обновления.

**Что делает:**

```python
#!/usr/bin/env python3
"""
Incremental Update Service для DeltaGrid.
Запускать по cron каждые 5-15 минут или вручную.

Usage:
    cd backend
    python scripts/incremental_update.py

Логика работы:
    1. Для каждого токена (BTC, ETH, SOL, HYPE):
       a. Находит MAX(timestamp) в ohlcv_1m WHERE exchange='binance'
       b. Если MAX < now - 5 минут:
          - BinanceAdapter.fetch_ohlcv_1m(MAX, now)
          - DataWriter.upsert_ohlcv()
       c. Логирует в provider_sync_runs
    
    2. Для CoinGlass (funding_rates, open_interest, liquidations, long_short_ratio):
       a. Для каждой таблицы: MAX(timestamp) WHERE exchange='binance'
       b. Fetch оттуда до now через CoinGlassAdapter
       c. UPSERT через DataWriter
       d. Логирует в provider_sync_runs
    
    3. Summary: что обновлено, сколько добавлено, elapsed time.
"""

import asyncio
import time
from datetime import datetime, timezone
from app.persistence.database import SessionLocal
from app.adapters.data import BinanceAdapter, CoinGlassAdapter, SymbolMapper
from app.adapters.data.rate_limiter import GlobalRateLimiter
from app.adapters.data.data_writer import DataWriter
from app.domain.models import OHLCV1m, FundingRate, OpenInterest, Liquidation, LongShortRatio

async def incremental_update_ohlcv():
    """Обновляет OHLCV 1m данные с Binance."""
    db = SessionLocal()
    try:
        limiter = GlobalRateLimiter()
        bucket = limiter.get_bucket("binance", rate=1200, per_seconds=60)
        circuit = limiter.get_circuit("binance")
        
        mapper = SymbolMapper(db)
        writer = DataWriter(db)
        adapter = BinanceAdapter(db, mapper, limiter)
        
        symbols = ["BTC", "ETH", "SOL", "HYPE"]
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        
        for symbol in symbols:
            # Находим последний timestamp
            last_row = db.query(OHLCV1m).filter(
                OHLCV1m.symbol == symbol,
                OHLCV1m.exchange == "binance"
            ).order_by(OHLCV1m.timestamp.desc()).first()
            
            if not last_row:
                print(f"  {symbol}: no existing data, skipping (run backfill first)")
                continue
            
            start_ms = last_row.timestamp + 60000  # +1 минута
            
            if start_ms >= now_ms - 300000:  # данные свежие (< 5 мин)
                print(f"  {symbol}: up to date (last: {last_row.timestamp})")
                continue
            
            # Fetch новые данные
            candles = await adapter.fetch_ohlcv_1m(symbol, start_ms, now_ms)
            if candles:
                inserted = writer.upsert_ohlcv(candles)
                writer.create_sync_run("binance", symbol, start_ms, now_ms,
                                       len(candles), inserted, "success")
                print(f"  {symbol}: +{inserted} candles ({len(candles)} fetched)")
            else:
                print(f"  {symbol}: no new data")
    
    finally:
        db.close()

async def incremental_update_coinglass():
    """Обновляет данные CoinGlass (funding, OI, liq, L/S)."""
    db = SessionLocal()
    try:
        limiter = GlobalRateLimiter()
        mapper = SymbolMapper(db)
        writer = DataWriter(db)
        adapter = CoinGlassAdapter(db, mapper, limiter)
        
        symbols = ["BTC", "ETH", "SOL", "HYPE"]
        exchange = "binance"
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        
        # Funding rates
        for symbol in symbols:
            last_row = db.query(FundingRate).filter(
                FundingRate.symbol == symbol,
                FundingRate.exchange == exchange
            ).order_by(FundingRate.timestamp.desc()).first()
            
            start_ms = last_row.timestamp + 1 if last_row else now_ms - (24 * 3600 * 1000)
            
            if start_ms >= now_ms - 3600000:  # < 1 час
                continue
            
            rates = await adapter.fetch_funding_rate_history(exchange, symbol, start_ms, now_ms)
            if rates:
                inserted = writer.upsert_funding_rates(rates)
                writer.create_sync_run("coinglass_funding", symbol, start_ms, now_ms,
                                       len(rates), inserted, "success")
                print(f"  {symbol} funding: +{inserted}")
        
        # Аналогично для open_interest, liquidations, long_short_ratio
        # ... (реализовать по аналогии с funding)
    
    finally:
        db.close()

async def main():
    print(f"Incremental Update started at {datetime.utcnow().isoformat()}")
    start = time.monotonic()
    
    await incremental_update_ohlcv()
    await incremental_update_coinglass()
    
    elapsed = time.monotonic() - start
    print(f"Completed in {elapsed:.1f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

**Приёмочный тест:**
1. Запусти `python scripts/incremental_update.py`
2. Должно показать: "BTC: up to date" (так как backfill только что сделан)
3. Подожди 6 минут, запусти снова
4. Должно показать: "BTC: +N candles"
5. Проверка SQL: `SELECT MAX(timestamp) FROM ohlcv_1m WHERE symbol='BTC'` — должен быть свежий timestamp

---

### Задание 2: Data Quality Monitor

**Файл:** `backend/app/backtest/quality_monitor.py`

**Назначение:** Проверка качества данных. Определяет, можно ли запускать backtest на этих данных.

```python
"""
Data Quality Monitor для DeltaGrid.
Проверяет данные перед backtest: gaps, stale data, coverage.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from app.domain.models import (
    OHLCV1m, FundingRate, OpenInterest, Liquidation, LongShortRatio,
    DataQualityLog, ProviderSyncRun
)

@dataclass
class Gap:
    """Описание разрыва в данных."""
    symbol: str
    exchange: str
    start_ms: int           # начало gap
    end_ms: int             # конец gap
    expected_candles: int   # сколько должно было быть
    actual_candles: int     # сколько реально
    duration_min: int       # длительность gap в минутах

@dataclass
class QualityReport:
    """Полный отчёт о качестве данных."""
    symbol: str
    exchange: str
    ohlcv_score: int        # 0-100
    funding_score: int      # 0-100
    overall_score: int      # 0-100 (weighted average)
    gaps: List[Gap] = field(default_factory=list)
    stale_metrics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def is_backtest_ready(self) -> bool:
        """True если данные достаточно хороши для backtest."""
        return self.overall_score >= 80


class DataQualityMonitor:
    """Монитор качества данных."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_ohlcv_gaps(self, symbol: str, exchange: str, 
                          max_gap_min: int = 5) -> List[Gap]:
        """
        Находит разрывы в OHLCV данных.
        
        Алгоритм:
        1. Загружает все timestamps для symbol+exchange, сортирует
        2. Вычисляет diff между соседними timestamps
        3. Если diff > max_gap_min * 60000 ms → это gap
        4. Возвращает список Gap объектов
        """
        rows = self.db.query(OHLCV1m.timestamp).filter(
            OHLCV1m.symbol == symbol,
            OHLCV1m.exchange == exchange
        ).order_by(OHLCV1m.timestamp).all()
        
        if len(rows) < 2:
            return []
        
        timestamps = [r[0] for r in rows]
        gaps = []
        
        for i in range(1, len(timestamps)):
            diff_ms = timestamps[i] - timestamps[i-1]
            expected_diff = 60000  # 1 минута
            
            if diff_ms > max_gap_min * expected_diff:
                gap_min = (diff_ms - expected_diff) // 60000
                gaps.append(Gap(
                    symbol=symbol,
                    exchange=exchange,
                    start_ms=timestamps[i-1] + 60000,
                    end_ms=timestamps[i],
                    expected_candles=diff_ms // 60000,
                    actual_candles=1,  # только start и end
                    duration_min=gap_min,
                ))
        
        return gaps
    
    def check_stale_data(self, table_model, symbol: str, exchange: str,
                          max_age_min: int = 15) -> bool:
        """
        Проверяет что данные не устарели.
        
        Args:
            table_model: SQLAlchemy model (OHLCV1m, FundingRate, etc.)
            max_age_min: максимальный допустимый возраст в минутах
        
        Returns:
            True если данные stale (устарели)
        """
        last_row = self.db.query(table_model).filter(
            table_model.symbol == symbol,
            table_model.exchange == exchange
        ).order_by(table_model.timestamp.desc()).first()
        
        if not last_row:
            return True  # нет данных = stale
        
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        age_min = (now_ms - last_row.timestamp) // 60000
        
        return age_min > max_age_min
    
    def check_coverage(self, symbol: str, exchange: str,
                        start_ms: int, end_ms: int) -> float:
        """
        Вычисляет процент покрытия данных за период.
        
        Returns:
            float 0.0-1.0 — доля минут, для которых есть данные
        """
        total_minutes = (end_ms - start_ms) // 60000
        if total_minutes <= 0:
            return 0.0
        
        count = self.db.query(func.count(OHLCV1m.id)).filter(
            OHLCV1m.symbol == symbol,
            OHLCV1m.exchange == exchange,
            OHLCV1m.timestamp >= start_ms,
            OHLCV1m.timestamp <= end_ms
        ).scalar()
        
        return min(count / total_minutes, 1.0)
    
    def get_quality_score(self, symbol: str, exchange: str) -> int:
        """
        Вычисляет агрегированный quality score (0-100).
        
        Алгоритм:
        - Начинаем с 100
        - -20 за каждый gap > 60 минут
        - -30 если данные stale (> 1 час)
        - -10 если coverage < 95%
        - -5 за каждый gap 5-60 минут
        """
        score = 100
        
        # Gaps
        gaps = self.check_ohlcv_gaps(symbol, exchange, max_gap_min=5)
        for gap in gaps:
            if gap.duration_min > 60:
                score -= 20
            else:
                score -= 5
        
        # Stale
        if self.check_stale_data(OHLCV1m, symbol, exchange, max_age_min=60):
            score -= 30
        
        # Coverage (последние 7 дней)
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        week_ms = now_ms - (7 * 24 * 3600 * 1000)
        coverage = self.check_coverage(symbol, exchange, week_ms, now_ms)
        if coverage < 0.95:
            score -= 10
        
        return max(score, 0)
    
    def run_all_checks(self) -> List[QualityReport]:
        """
        Запускает все проверки для всех токенов.
        Пишет результаты в data_quality_logs.
        Возвращает список QualityReport (по одному на токен).
        """
        symbols = ["BTC", "ETH", "SOL", "HYPE"]
        exchange = "binance"
        reports = []
        
        for symbol in symbols:
            report = QualityReport(symbol=symbol, exchange=exchange)
            
            # OHLCV checks
            report.gaps = self.check_ohlcv_gaps(symbol, exchange)
            ohlcv_score = self.get_quality_score(symbol, exchange)
            report.ohlcv_score = ohlcv_score
            
            # Funding checks
            funding_stale = self.check_stale_data(
                FundingRate, symbol, exchange, max_age_min=60
            )
            report.funding_score = 70 if funding_stale else 95
            
            # Overall
            report.overall_score = int(ohlcv_score * 0.7 + report.funding_score * 0.3)
            
            # Warnings
            if report.gaps:
                report.warnings.append(f"Found {len(report.gaps)} OHLCV gaps")
            if funding_stale:
                report.warnings.append("Funding data is stale")
            if report.overall_score < 80:
                report.warnings.append("Data quality below threshold for backtest")
            
            # Log to database
            self._log_quality_check(report)
            
            reports.append(report)
        
        return reports
    
    def _log_quality_check(self, report: QualityReport):
        """Пишет результаты проверки в data_quality_logs."""
        log = DataQualityLog(
            check_type="aggregate",
            symbol=report.symbol,
            exchange=report.exchange,
            metric="overall_score",
            value=float(report.overall_score),
            threshold=80.0,
            status="ok" if report.overall_score >= 80 else "warning",
            details="; ".join(report.warnings) if report.warnings else "All checks passed",
        )
        self.db.add(log)
        self.db.commit()
```

---

### Задание 3: Pre-backtest Quality Gate

**Файл:** `backend/app/backtest/gate.py`

**Назначение:** Проверяет данные ПЕРЕД запуском бэктеста. Если данные плохие — бэктест не запускаем.

```python
"""
Pre-backtest Quality Gate.
Проверяет данные перед запуском backtest.
"""

from typing import Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.backtest.quality_monitor import DataQualityMonitor
from app.backtest.config import BacktestConfig
from app.domain.models import OHLCV1m, FundingRate


def pre_backtest_gate(db: Session, config: BacktestConfig) -> Tuple[bool, List[str]]:
    """
    Проверяет качество данных перед запуском backtest.
    
    Args:
        db: SQLAlchemy session
        config: BacktestConfig с параметрами backtest
    
    Returns:
        (can_run, warnings)
        - can_run=True: можно запускать (возможно с warnings)
        - can_run=False: данные непригодны
        - warnings: список предупреждений для пользователя
    
    Проверки:
        1. OHLCV coverage > 95% за запрошенный период
        2. Funding data coverage > 90%
        3. Нет gaps > 60 минут
        4. Данные не stale (MAX(timestamp) < 1 час назад)
        5. Достаточно данных (> 1000 баров)
    """
    monitor = DataQualityMonitor(db)
    warnings = []
    can_run = True
    
    # 1. OHLCV coverage
    ohlcv_coverage = monitor.check_coverage(
        config.symbol, config.exchange, config.start_ms, config.end_ms
    )
    if ohlcv_coverage < 0.95:
        warnings.append(f"OHLCV coverage is {ohlcv_coverage*100:.1f}% (minimum 95%)")
        can_run = False
    elif ohlcv_coverage < 0.98:
        warnings.append(f"OHLCV coverage is {ohlcv_coverage*100:.1f}% (optimal > 98%)")
    
    # 2. Funding coverage
    funding_coverage = _check_funding_coverage(db, config)
    if funding_coverage < 0.90:
        warnings.append(f"Funding data coverage is {funding_coverage*100:.1f}% (minimum 90%)")
        can_run = False
    
    # 3. Gaps
    gaps = monitor.check_ohlcv_gaps(config.symbol, config.exchange, max_gap_min=60)
    if gaps:
        total_gap_min = sum(g.duration_min for g in gaps)
        warnings.append(f"Found {len(gaps)} gaps > 60 min (total: {total_gap_min} min)")
        if total_gap_min > 120:
            can_run = False
    
    # 4. Stale data
    if monitor.check_stale_data(OHLCV1m, config.symbol, config.exchange, max_age_min=60):
        warnings.append("OHLCV data is stale (> 1 hour old)")
        can_run = False
    
    # 5. Minimum bars
    total_minutes = (config.end_ms - config.start_ms) // 60000
    if total_minutes < 1000:
        warnings.append(f"Backtest period too short: {total_minutes} minutes (minimum 1000)")
        can_run = False
    
    # Quality score
    score = monitor.get_quality_score(config.symbol, config.exchange)
    if score < 50:
        warnings.append(f"Data quality score is {score}/100 (critical)")
        can_run = False
    elif score < 80:
        warnings.append(f"Data quality score is {score}/100 (below optimal)")
    
    return can_run, warnings


def _check_funding_coverage(db: Session, config: BacktestConfig) -> float:
    """Вспомогательная: coverage funding data."""
    from sqlalchemy import func
    
    total_hours = (config.end_ms - config.start_ms) // 3600000
    if total_hours <= 0:
        return 0.0
    
    count = db.query(func.count(FundingRate.id)).filter(
        FundingRate.symbol == config.symbol,
        FundingRate.exchange == config.exchange,
        FundingRate.timestamp >= config.start_ms,
        FundingRate.timestamp <= config.end_ms
    ).scalar()
    
    # Ожидаем 3 funding events per day для CEX
    expected = total_hours / 8  # 8h intervals
    return min(count / expected, 1.0) if expected > 0 else 0.0
```

**Интеграция с BacktestEngine:**

В `engine.py`, метод `run()` добавить:

```python
def run(self) -> BacktestResult:
    # Quality gate
    from app.backtest.gate import pre_backtest_gate
    can_run, warnings = pre_backtest_gate(self.db, self.config)
    
    if not can_run:
        raise ValueError(f"Data quality check failed: {'; '.join(warnings)}")
    
    if warnings:
        print(f"WARNINGS: {'; '.join(warnings)}")
    
    # ... остальной код run()
```

---

### Задание 4: API Endpoints для Data Quality

**Файл:** `backend/app/api/v1/data.py` (новый файл)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime

from app.persistence.database import get_db
from app.backtest.quality_monitor import DataQualityMonitor

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/health")
async def data_health(db: Session = Depends(get_db)):
    """
    GET /api/v1/data/health
    
    Возвращает полный отчёт о качестве данных для всех токенов.
    """
    monitor = DataQualityMonitor(db)
    reports = monitor.run_all_checks()
    
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "overall_status": "healthy" if all(r.overall_score >= 80 for r in reports) else "degraded",
        "reports": [
            {
                "symbol": r.symbol,
                "exchange": r.exchange,
                "overall_score": r.overall_score,
                "ohlcv_score": r.ohlcv_score,
                "funding_score": r.funding_score,
                "gaps_count": len(r.gaps),
                "warnings": r.warnings,
                "backtest_ready": r.is_backtest_ready(),
            }
            for r in reports
        ]
    }

@router.get("/quality/{symbol}")
async def data_quality_symbol(symbol: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/data/quality/{symbol}
    
    Возвращает quality score для конкретного токена.
    """
    monitor = DataQualityMonitor(db)
    score = monitor.get_quality_score(symbol, "binance")
    gaps = monitor.check_ohlcv_gaps(symbol, "binance")
    is_stale = monitor.check_stale_data(
        OHLCV1m, symbol, "binance", max_age_min=15
    )
    
    return {
        "symbol": symbol,
        "score": score,
        "gaps_found": len(gaps),
        "is_stale": is_stale,
        "backtest_ready": score >= 80,
    }
```

**Подключение router в main.py:**

```python
from app.api.v1 import data as data_router

app.include_router(data_router.router, prefix="/api/v1")
```

---

### Задание 5: CLI для проверки качества

**Файл:** `backend/scripts/check_quality.py`

```python
#!/usr/bin/env python3
"""
CLI для проверки качества данных.

Usage:
    cd backend
    python scripts/check_quality.py
    python scripts/check_quality.py --symbol BTC
"""

import argparse
from app.persistence.database import SessionLocal
from app.backtest.quality_monitor import DataQualityMonitor

def main():
    parser = argparse.ArgumentParser(description="Check data quality")
    parser.add_argument("--symbol", help="Check specific symbol (BTC/ETH/SOL/HYPE)")
    args = parser.parse_args()
    
    db = SessionLocal()
    monitor = DataQualityMonitor(db)
    
    if args.symbol:
        score = monitor.get_quality_score(args.symbol, "binance")
        gaps = monitor.check_ohlcv_gaps(args.symbol, "binance")
        print(f"Quality Report for {args.symbol}")
        print(f"  Score: {score}/100")
        print(f"  Gaps: {len(gaps)}")
        for g in gaps[:5]:
            print(f"    - {g.duration_min} min gap at {g.start_ms}")
    else:
        reports = monitor.run_all_checks()
        print("Quality Report for all symbols:")
        print("-" * 50)
        for r in reports:
            status = "OK" if r.is_backtest_ready() else "FAIL"
            print(f"  {r.symbol:6} | Score: {r.overall_score:3}/100 | {status}")
            if r.warnings:
                for w in r.warnings:
                    print(f"    WARNING: {w}")

if __name__ == "__main__":
    main()
```

---

### Задание 6: APScheduler

**Файл:** `backend/app/scheduler.py`

```python
"""
APScheduler для фоновых задач DeltaGrid.
Запускается при старте FastAPI.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def job_incremental_ohlcv():
    """Обновление OHLCV каждые 5 минут."""
    try:
        from scripts.incremental_update import incremental_update_ohlcv
        await incremental_update_ohlcv()
        logger.info("Incremental OHLCV update completed")
    except Exception as e:
        logger.error(f"Incremental OHLCV failed: {e}")

async def job_incremental_coinglass():
    """Обновление CoinGlass данных каждые 5 минут."""
    try:
        from scripts.incremental_update import incremental_update_coinglass
        await incremental_update_coinglass()
        logger.info("Incremental CoinGlass update completed")
    except Exception as e:
        logger.error(f"Incremental CoinGlass failed: {e}")

async def job_quality_check():
    """Проверка качества данных каждые 15 минут."""
    try:
        from app.persistence.database import SessionLocal
        from app.backtest.quality_monitor import DataQualityMonitor
        db = SessionLocal()
        monitor = DataQualityMonitor(db)
        reports = monitor.run_all_checks()
        for r in reports:
            logger.info(f"Quality {r.symbol}: {r.overall_score}/100")
    except Exception as e:
        logger.error(f"Quality check failed: {e}")

def start_scheduler():
    """Запускает все scheduled jobs."""
    scheduler.add_job(
        job_incremental_ohlcv,
        IntervalTrigger(minutes=5),
        id="ohlcv_update",
        name="OHLCV Incremental Update",
        replace_existing=True,
    )
    scheduler.add_job(
        job_incremental_coinglass,
        IntervalTrigger(minutes=5),
        id="coinglass_update",
        name="CoinGlass Incremental Update",
        replace_existing=True,
    )
    scheduler.add_job(
        job_quality_check,
        IntervalTrigger(minutes=15),
        id="quality_check",
        name="Data Quality Check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with 3 jobs")

def shutdown_scheduler():
    """Останавливает scheduler."""
    scheduler.shutdown()
```

**Интеграция в main.py:**

```python
from app.scheduler import start_scheduler, shutdown_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()
```

**requirements.txt добавить:**
```
apscheduler>=3.10.0
```

---

## 5. Правила реализации

- **Не ломай существующие модули.** `uvicorn app.main:app` должен стартовать без ошибок.
- **Используй существующие компоненты:** SQLAlchemy модели из `domain/models.py`, DataWriter, SymbolMapper, RateLimiter.
- **Git commit после каждого задания:**
  - "feat: add incremental update service"
  - "feat: add data quality monitor"
  - "feat: add pre-backtest quality gate"
  - "feat: add data quality API endpoints"
  - "feat: add APScheduler for background tasks"
- **.md комментарии на русском, код на английском.**
- **Не подключаем Redis, не меняем БД на PostgreSQL.** SQLite WAL mode достаточно для MVP.
- **APScheduler используем в async режиме** (AsyncIOScheduler) чтобы не блокировать event loop FastAPI.

## 6. Ожидаемый результат (чеклист)

- [ ] `backend/scripts/incremental_update.py` — работает (тест: запусти, проверь что данные добавились)
- [ ] `backend/app/backtest/quality_monitor.py` — все методы: check_ohlcv_gaps, check_stale_data, check_coverage, get_quality_score, run_all_checks
- [ ] `backend/app/backtest/gate.py` — pre_backtest_gate, интегрирован в BacktestEngine.run()
- [ ] `backend/app/api/v1/data.py` — GET /api/v1/data/health, GET /api/v1/data/quality/{symbol}
- [ ] `backend/scripts/check_quality.py` — CLI отчёт
- [ ] `backend/app/scheduler.py` — APScheduler с 3 jobs (ohlcv каждые 5 мин, coinglass каждые 5 мин, quality каждые 15 мин)
- [ ] `uvicorn app.main:app` стартует без ошибок, scheduler запускается
- [ ] Тест: `curl http://localhost:8000/api/v1/data/health` → returns JSON с quality scores
- [ ] Тест: `python scripts/check_quality.py` → shows scores for all 4 symbols
