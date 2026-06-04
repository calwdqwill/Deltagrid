# DeltaGrid — Полное код-ревью backend

## Контекст
- Проект: DeltaGrid
- Путь: C:\Users\viach\OneDrive\Desktop\Deltagrid
- GitHub: https://github.com/calwdqwill/Deltagrid
- Ревью №2 (первое было ранее, проверяем что поменялось с тех пор)

## Что реализовано с момента первого ревью

### Слой 1: Data Layer (backend/app/adapters/data/)
- `base_adapter.py` — BaseDataAdapter (ABC), Registry, FallbackChain
- `binance_adapter.py` — BinanceAdapter (1m OHLCV, pagination)
- `coinglass_adapter.py` — CoinGlassAdapter V4 (funding, OI, liq, L/S)
- `coingecko_adapter.py` — CoinGeckoAdapter (hourly OHLCV, metadata)
- `data_models.py` — Pydantic: OHLCVCandle, FundingRate, OI, Liquidation, L/S
- `data_writer.py` — SQLite UPSERT через sqlalchemy.dialects.sqlite.insert
- `symbol_mapper.py` — OR-based canonical ↔ provider mapping
- `rate_limiter.py` — TokenBucket, CircuitBreaker, RetryPolicy
- `backfill_orchestrator.py` — ChunkedBackfill, gap detection

### Слой 2: Backtest Engine (backend/app/backtest/)
- `engine.py` — Bar-by-bar event loop, look-ahead bias elimination
- `fee_model.py` — Maker/taker per exchange
- `funding_model.py` — Exact settlement times (8h CEX, 1h HL)
- `slippage_model.py` — Token-specific two-component slippage
- `metrics.py` — 20+ metrics, PnL decomposition
- `strategies/funding_mean_reversion.py` — S01
- `strategies/basis_compression.py` — S02 (proxy basis, FIXME)
- `strategies/liquidation_cascade_fade.py` — S04

### Слой 3: Quality + Monitoring
- `quality_monitor.py` — check_ohlcv_gaps, check_stale_data, check_coverage, get_quality_score, run_all_checks
- `gate.py` — pre_backtest_gate (coverage > 95%, no gaps > 60min, not stale)

### Слой 4: Auth
- `schemas/auth.py` — UserCreate, UserLogin, Token, UserResponse
- `api/v1/auth.py` — POST /register, POST /login, GET /me
- `core/dependencies.py` — get_current_user_optional, get_current_user_required

### Слой 5: Scheduler
- `scheduler.py` — APScheduler: OHLCV каждые 5min, CoinGlass каждые 5min, quality каждые 15min
- `scripts/incremental_update.py` — Инкрементальное обновление
- `scripts/check_quality.py` — CLI quality check

### Слой 6: API
- `api/v1/backtest.py` — POST /backtest/run
- `api/v1/data.py` — GET /data/health, GET /data/quality/{symbol}

## Задача для Codex

Проведи полное код-ревью backend. Не пиши новый код — только анализ и отчёт.

### Что проверить

#### 1. Архитектура и дизайн
- [ ] Separation of concerns: adapters vs engine vs API vs auth — границы чёткие?
- [ ] Dependency injection: db_session передаётся явно, не глобальный import?
- [ ] Interface segregation: BaseDataAdapter правильно спроектирован?
- [ ] DRY: нет дублирования логики между модулями?

#### 2. Безопасность (критично)
- [ ] JWT SECRET_KEY берётся из .env, не хардкодится?
- [ ] Password hashing: bcrypt, не md5/sha1?
- [ ] SQL injection: SQLAlchemy ORM используется (не raw SQL)?
- [ ] No secrets в коде: API keys (CoinGlass, CoinGecko) только в .env?
- [ ] CORS настроен корректно? (allow_origins не "*" в production)
- [ ] Input validation: Pydantic models везде?
- [ ] Rate limiting на API endpoints? (не только на внешние API)

#### 3. Performance
- [ ] N+1 query problem: нет лишних запросов в циклах?
- [ ] Database indexes: composite indexes на (exchange, symbol, timestamp)?
- [ ] Batch operations: UPSERT batch'ами, не по одной записи?
- [ ] Async: правильное использование async/await (нет blocking I/O в async функциях)?
- [ ] Memory: не загружаются миллионы записей в DataFrame целиком?

#### 4. Надёжность
- [ ] Error handling: try/except на внешних API вызовах?
- [ ] Circuit breaker: реально работает? (OPEN → HALF_OPEN → CLOSED)
- [ ] Retry logic: exponential backoff + jitter?
- [ ] Database transactions: commit/rollback корректно?
- [ ] Graceful degradation: если CoinGlass падает — остальное работает?

#### 5. Конкретные риски в нашем коде
- [ ] `engine.py` — DataFrame загружается целиком. Сколько памяти занимает 90 дней 1m? (~100MB?). Это ок для MVP?
- [ ] `funding_model.py` — Exact settlement: правильно ли определяется 00:00/08:00/16:00 UTC для всех бирж? Что с DST?
- [ ] `metrics.py` — Sharpe calculation: annualization factor правильный? (365 или 252?)
- [ ] `basis_compression.py` — FIXME на реальный spot price. Насколько критичен proxy basis?
- [ ] `scheduler.py` — Что если job зависает? Есть timeout? Что если 2 job'а запускаются одновременно?
- [ ] `data_writer.py` — SQLite UPSERT: race condition при concurrent writes? (WAL mode решает?)

#### 6. Тестируемость
- [ ] Есть unit tests? Если нет — какие критичные пути нужно покрыть первыми?
- [ ] Можно ли mock'ать внешние API для тестов?
- [ ] Backtest engine: deterministic? (одинаковый результат при одинаковых входных данных)

#### 7. Сравнение с первым ревью
- [ ] Что было исправлено после первого ревью?
- [ ] Какие issues из первого ревью остались открытыми?
- [ ] Появились ли новые проблемы в новом коде?

### Формат отчёта

Создай файл `CODE_REVIEW_v2.md` в корне проекта со следующей структурой:

```markdown
# Code Review v2 — DeltaGrid Backend

## Executive Summary
- Общая оценка (0-10)
- Критичных проблем: N
- Серьёзных проблем: N
- Мелких проблем: N
- Рекомендаций: N

## Критичные проблемы (фиксить сразу)
| # | Модуль | Проблема | Риск | Как фиксить |
|---|--------|----------|------|-------------|
| 1 | | | | |

## Серьёзные проблемы (фиксить this week)
| # | Модуль | Проблема | Риск | Как фиксить |
|---|--------|----------|------|-------------|

## Мелкие проблемы (tech debt)
| # | Модуль | Проблема | Приоритет |
|---|--------|----------|-----------|

## Сравнение с ревью v1
- Исправлено: ...
- Осталось: ...
- Новое: ...

## Рекомендации
- Что делать срочно
- Что планировать
- Что игнорировать до Phase B
```

### Правила
- Не пиши код — только анализ
- Не ломай существующие модули
- Давай конкретные ссылки на файлы и строки
- Разделяй: баг / tech debt / security / performance
- Git commit с отчётом
