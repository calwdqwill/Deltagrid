# Архитектура DeltaGrid

## Текущее состояние

DeltaGrid — аналитическое приложение для крипторынка с FastAPI backend, Next.js frontend и PostgreSQL persistence layer. Текущий MVP содержит market dashboard, scanner, data-layer endpoint'ы, auth, paper trading, execution foundation, alerts, RWA/treasury и backtesting foundation.

## Основные слои

- `frontend/` — Next.js 14, React, TypeScript, Tailwind CSS, Zustand и TanStack Query.
- `backend/app/api/v1/` — FastAPI routes и API boundary.
- `backend/app/services/` — бизнес-логика: market, scanner, alerts, execution, RWA, treasury, auth.
- `backend/app/adapters/` — внешние провайдеры и exchange/data adapters.
- `backend/app/adapters/data/sync_market_data.py` — production-safe команда для первичного и повторного наполнения data-layer из Binance USD-M, CoinGlass v4 и CoinGecko-derived spot snapshots.
- `backend/app/domain/models.py` — SQLAlchemy ORM-модели.
- `backend/app/persistence/` — sync/async DB engines и Alembic migrations.

## База данных

Основная БД для MVP — PostgreSQL. Подключение задаётся через `DATABASE_URL`.

- Sync API routes используют SQLAlchemy engine с `psycopg`.
- Async persistence helper использует `asyncpg`.
- Alembic использует sync URL и выполняет `upgrade head`.
- `Base.metadata.create_all()` оставлен только для SQLite fallback в isolated tests.
- Docker Compose поднимает PostgreSQL 16 и запускает миграции перед стартом backend.
- `GET /api/v1/health/readiness` проверяет локальное подключение к БД и совпадение текущей Alembic revision с source head.

SQLite больше не является production runtime. Он может использоваться только явно в тестах, например `sqlite:///:memory:`.

При `DEBUG=false` startup validation блокирует слабые/dev secrets, пустой `VAULT_MASTER_KEY`, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS`.

## Deployment Boundary

Локальный `docker-compose.yml` остаётся dev/staging-friendly и публикует PostgreSQL на `5432` для удобной проверки. Для сервера добавлен отдельный `docker-compose.prod.yml`: PostgreSQL не публикуется наружу, backend и frontend слушают только `127.0.0.1`, а внешний доступ должен идти через reverse proxy.

Frontend HTTP API использует относительный `/api/v1` и проксируется Next.js rewrite'ом на `BACKEND_INTERNAL_URL`. Так как Next.js запекает rewrites во время build, Docker Compose передаёт `BACKEND_INTERNAL_URL=http://backend:8000` через frontend build args. WebSocket stream выбирает `NEXT_PUBLIC_WS_URL`, если он задан, иначе использует `127.0.0.1:8000` локально и same-origin `/api/v1/stream/ws` на production-домене.

Для server-rendered frontend screens добавлен лёгкий helper `frontend/src/lib/server-api.ts`: он читает `BACKEND_INTERNAL_URL` или `NEXT_PUBLIC_API_URL` и обращается к backend без клиентского auth/Zustand слоя. Сейчас основные terminal screens читают live backend/data-layer вместо `terminalDataAdapter`: `Market Overview` использует `GET /api/v1/market/markets`, `/market/global`, `/market/fear-greed`, `/market/funding-rates` и `/data/health`, `Assets` использует `/market/markets`, `/market/funding-rates`, `/data/ohlcv`, `/data/liquidations` и `/data/health`, `Charts`, `Market Matrix` и `Arbitrage Scanner` используют persisted OHLCV/funding/OI/long-short/basis streams.

Data-layer API открыт read-only endpoint'ами: `/data/ohlcv`, `/data/funding`, `/data/open-interest`, `/data/long-short-ratio`, `/data/basis-premium`, `/data/liquidations` и `/data/health`.

`Perp DEX` не показывает mock DEX volume/OI/liquidity как реальные данные, пока не подключён отдельный live DEX venue adapter. `Strategy Lab` показывает readiness live inputs, но не показывает fake PnL/trades до появления реального backtest engine.

Фактический production rollout на `deltagrid.pro` выполнен на Ubuntu 22.04 сервере `2.25.143.143`: код расположен в `/opt/deltagrid`, Docker Compose поднимает PostgreSQL/backend/frontend, frontend опубликован на `127.0.0.1:3001`, backend на `127.0.0.1:8000`, а Nginx обслуживает `https://deltagrid.pro` и `https://www.deltagrid.pro` с сертификатом Let's Encrypt.

## Миграции

Схема управляется через `backend/app/persistence/migrations`.

Текущий head: `7c1f2a8d9e34_bigint_market_timestamps`.

Ключевые группы таблиц:

- пользовательские и auth-таблицы: `users`, `preferences`, `favorites`, `pinned`;
- paper trading и performance: `paper_accounts`, `paper_trades`, `performance_snapshots`;
- execution и risk: `exchange_accounts`, `exchange_keys`, `real_orders`, `order_events`, `risk_rules`;
- alerts/notifications: `alert_rules`, `alert_events`, `alert_deliveries`, `notification_preferences`;
- RWA/treasury: `rwa_assets`, `rwa_asset_snapshots`, `treasury_entities`, `treasury_snapshots`;
- data-layer: `ohlcv`, `funding_rates`, `open_interest`, `liquidations`, `long_short_ratio`, `provider_sync_runs`, `data_quality_logs`, `backfill_jobs`;
- backtesting: `backtest_configs`, `backtest_results`, `backtest_trades`, `backtest_equity`.

## Типы данных

- Даты в ORM сейчас хранятся как UTC-naive `DateTime`.
- Market time-series и backtest time windows используют Unix timestamp в миллисекундах в `BigInteger`-полях.
- JSON-like поля сохраняются как `Text` с суффиксом `_json`, чтобы не менять существующую сериализацию.
- Финансовые значения PnL, balances, RWA/treasury используют `DECIMAL`.
- OHLCV/funding/OI market data пока используют `Float`; это допустимо для MVP-аналитики, но требует пересмотра перед точными расчётами PnL/execution.
- CoinGlass funding snapshots сохраняются в `funding_rates.funding_rate` как decimal, чтобы совпадать с Binance convention; v4 percent-like значения делятся на `100`.
- `basis_premium` — approximate snapshot: CoinGecko spot price сравнивается с последним Binance 1m perp close. Это аналитический MVP-снимок, не execution-grade pricing.

## Data Flow

```text
External APIs / Exchange APIs
    ↓
Adapters
    ↓
Services
    ↓
Manual sync command / DataWriter
    ↓
SQLAlchemy ORM / DataWriter
    ↓
PostgreSQL
    ↓
FastAPI routes
    ↓
Frontend hooks / pages
```

## Риски и tech debt

- Исторические JSON-поля пока не переведены на PostgreSQL `JSONB`.
- Часть data-layer чисел использует `Float`; для финансово-критичных расчётов нужны `DECIMAL` и отдельная проверка формул.
- Перед следующими production-итерациями нужно добавлять backup PostgreSQL перед миграциями и проверять `certbot renew --dry-run`.
- Старые SQLite `.db` файлы не мигрируются автоматически; если нужны исторические данные, потребуется отдельный экспорт/импорт.
- Нужно регулярно проверять `GET /api/v1/health/readiness` в staging/prod, чтобы ловить рассинхрон Alembic до открытия пользовательского трафика.
- Market data ingestion для production MVP запускается через `scripts/sync-market-data.sh`; на сервере используется host-level cron `/etc/cron.d/deltagrid-market-sync`.
- Основной frontend terminal больше не использует `terminalDataAdapter` в app routes. Оставшийся долг — не mock UI, а отсутствующие production-grade источники для DEX venues, order book, liquidations ingestion и backtest engine.
- Для `Perp DEX` нужен отдельный live venue adapter, иначе нельзя корректно показывать DEX volume/OI/liquidity как production-данные.
