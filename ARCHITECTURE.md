# Архитектура DeltaGrid

## Текущее состояние

DeltaGrid — аналитическое приложение для крипторынка с FastAPI backend, Next.js frontend и PostgreSQL persistence layer. Текущий MVP содержит market dashboard, scanner, data-layer endpoint'ы, auth, paper trading, execution foundation, alerts, RWA/treasury и backtesting foundation.

## Основные слои

- `frontend/` — Next.js 15, React, TypeScript, Tailwind CSS, Zustand, TanStack Query и `lightweight-charts` для interactive charts.
- `backend/app/api/v1/` — FastAPI routes и API boundary.
- `backend/app/services/` — бизнес-логика: market, scanner, alerts, execution, RWA, treasury, auth.
- `backend/app/adapters/` — внешние провайдеры и exchange/data adapters.
- `backend/app/adapters/data/sync_market_data.py` — production-safe команда для первичного и повторного наполнения data-layer из OKX USDT swaps, CoinGlass v4 и CoinGecko-derived spot snapshots. Binance adapter сохранён как legacy/diagnostic path, но на текущем production VPS direct Binance API возвращает HTTP `451`.
- `backend/app/adapters/data/okx_adapter.py` — primary CEX perp adapter для MVP1: OHLCV candles, funding history, open interest snapshots и long/short account ratio.
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

`/charts` теперь имеет отдельный client-side слой `InteractiveCandlestickChart` на `lightweight-charts`. Server-side workspace собирает OKX OHLCV окно через `/data/ohlcv/window`, а старая постраничная сборка поверх `/data/ohlcv` оставлена fallback path. Client layer отвечает только за визуализацию candles, volume, crosshair и pan/zoom/scroll; расчёты data quality, freshness и coverage остаются в backend/data-layer.

Data-layer API открыт read-only endpoint'ами: `/data/ohlcv`, `/data/ohlcv/window`, `/data/funding`, `/data/open-interest`, `/data/long-short-ratio`, `/data/basis-premium`, `/data/liquidations`, `/data/coverage`, `/data/universe`, `/data/provider-inventory` и `/data/health`.

Для interactive charts добавлен отдельный read-only endpoint `/data/ohlcv/window`. Он возвращает bounded OHLCV окно по `symbol + exchange + interval + range`, ограничивает размер ответа `20000` строками и, если `end` не задан, использует последнюю доступную свечу в PostgreSQL как правый край окна. Старый `/data/ohlcv` сохраняет лимит `1000` строк для общих read-side сценариев.

`/data/health` остаётся read-only health snapshot без внешних API-вызовов. Помимо provider-level статусов и row counts он возвращает:

- `freshness` — SLA по `symbol + exchange + stream + interval` для `BTC/ETH/SOL` на primary exchange `okx`, включая `latest_timestamp`, `age_minutes`, expected cadence и статус `fresh/stale/degraded`;
- `coverage` — инвентаризацию исторического покрытия по `symbol + exchange + stream + interval`: фактические строки, expected rows, coverage %, latest timestamp и reason для OHLCV/funding/OI/long-short/liquidations/basis/spot-perp price;
- `universe` — policy view для текущего MVP universe: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`, `policy.ui_universe` и `deferred_symbols`;
- `sync_health_by_type` — последние sync-runs по `provider_name + sync_type`, чтобы OHLCV, funding, OI, long/short, liquidations и basis были видны отдельно;
- `sync_diagnostics` — cron-path диагностику по `provider_sync_runs`: последний запуск, последний успешный запуск, fetched/inserted records и классы ошибок вроде `http_451`, `rate_limit`, `circuit_breaker`, `empty_response`.

`/data/provider-inventory` — отдельный read-only endpoint для MVP1 expansion gate. Он строит inventory candidate symbols поверх persisted coverage/freshness, возвращает `promotion_candidate`, `chart_ready_candidates`, `policy.gates`, `next_action`, readiness status и summaries по 24h/7d. Для объяснения strict gate endpoint также возвращает `coverage_blockers_7d`, `freshness_blockers` и объединённый `promotion_blockers`, чтобы было видно, какие persisted signals блокируют full analytics promotion. `chart_ready` и `chart_ready_candidates` означают только готовность для preview `/charts` и `/assets`; `promotion_candidate` для full analytics universe требует `complete_history` и не выдаётся для `core_perp_ready`, если snapshot/enrichment streams ещё partial. В отличие от `/data/health`, который остаётся scoped к текущему UI universe `BTC/ETH/SOL`, provider inventory считает freshness по запрошенным candidate symbols и возвращает `scope.freshness_scope=requested_symbols`. Endpoint не вызывает внешние API и не меняет sync-конфигурацию; внешний discovery OKX/CoinGlass/CoinGecko/legacy Binance остаётся отдельным CLI-шагом перед расширением `SymbolMapper` и UI universe.

Для внешнего discovery добавлен CLI `python -m app.adapters.data.discover_provider_universe`. Он не является API endpoint'ом и не пишет в PostgreSQL: задача CLI — проверить live provider availability для candidate symbols перед изменением aliases/sync universe. Проверяются OKX USDT swap instrument/OHLCV/funding/OI/long-short, CoinGlass OKX snapshots/liquidations, CoinGecko spot price и Binance USD-M как legacy diagnostic. На VPS Binance остаётся `blocked_http_451`, поэтому не используется как primary path.

`SymbolMapper.seed_defaults()` теперь идемпотентно поддерживает core symbols `BTC/ETH/SOL` и первую малую expansion group `HYPE/XRP/DOGE/ADA/LINK`. Эти aliases нужны для preview sync dry-run и CoinGecko-derived basis, но сами по себе не расширяют UI universe: `/data/provider-inventory` и freshness SLA остаются gate перед показом новых symbols в product screens.

Для sparse event streams, сейчас это `liquidations`, freshness разделяет два сигнала: возраст последнего события и возраст последнего успешного sync-run. Если новых liquidation events нет, но `coinglass/liquidations` sync свежий и успешный, поток остаётся `fresh` с reason `no recent liquidation events`; `/data-health` показывает это как `event age / sync age`.

`Perp DEX` не показывает mock DEX volume/OI/liquidity как реальные данные, пока не подключён отдельный live DEX venue adapter. `Strategy Lab` показывает readiness live inputs, но не показывает fake PnL/trades до появления реального backtest engine.

Фактический production rollout на `deltagrid.pro` выполнен на Ubuntu 22.04 сервере `2.25.143.143`: код расположен в `/opt/deltagrid`, Docker Compose поднимает PostgreSQL/backend/frontend, frontend опубликован на `127.0.0.1:3001`, backend на `127.0.0.1:8000`, а Nginx обслуживает `https://deltagrid.pro` и `https://www.deltagrid.pro` с сертификатом Let's Encrypt.

GitHub branch boundary после baseline `v1.3.0`: `preview` используется как dev/staging ветка для проверяемых итераций, `main` — как production ветка для кода, соответствующего `deltagrid.pro`. CI запускает backend tests, `compileall app` и frontend build для `preview`, `main` и pull requests. Deploy workflows запускаются только после успешного CI и выполняют SSH-deploy соответствующей ветки, если в GitHub настроены secrets `PREVIEW_*` или `PROD_*`; без secrets deploy безопасно пропускается.

Dev/prod разделение не требует отдельной архитектуры приложения: оба стенда используют один `docker-compose.prod.yml`, но разные директории, env-файлы, host ports и Compose project names. Production использует `/opt/deltagrid`, `.env.production`, project `deltagrid`, ports `8000/3001`; preview использует `/opt/deltagrid-preview`, `.env.preview`, project `deltagrid-preview`, ports `8011/3012`. Это разделяет контейнеры, PostgreSQL volumes и deploy cadence без изменения backend/frontend контрактов.

Для публикации preview подготовлен отдельный Nginx template `deploy/nginx/deltagrid-preview.conf.example`: `preview.deltagrid.pro` проксирует frontend на `127.0.0.1:3012`, API и WebSocket на `127.0.0.1:8011`. Скрипт `scripts/configure-preview-nginx-ssl.sh` включает site `deltagrid-preview` и выпускает отдельный Let's Encrypt сертификат после DNS-precheck, не затрагивая production site `deltagrid`.

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
- CoinGlass funding snapshots сохраняются в `funding_rates.funding_rate` как decimal; v4 percent-like значения делятся на `100`. При OKX primary snapshot-запросы идут с `exchange_list=OKX`.
- CoinGlass aggregated liquidation history сохраняется в `liquidations.value_usd` как long/short USD-снимки с exchange primary provider (`okx` для MVP1); `quantity` и `price` равны `0.0`, потому что этот источник не является per-order tape.
- `basis_premium` — approximate snapshot: CoinGecko spot price сравнивается с последним 1m close primary perp provider. Для MVP1 primary provider — OKX USDT Swap. Это аналитический MVP-снимок, не execution-grade pricing.

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
- Market data ingestion для production MVP запускается через `scripts/sync-market-data.sh`; на сервере используется host-level cron `/etc/cron.d/deltagrid-market-sync`. По умолчанию sync использует `--primary-perp-provider okx`.
- Основной frontend terminal больше не использует `terminalDataAdapter` в app routes. Оставшийся долг — не mock UI, а отсутствующие production-grade источники для DEX venues, order book, per-order liquidations tape и backtest engine.
- Для `Perp DEX` нужен отдельный live venue adapter, иначе нельзя корректно показывать DEX volume/OI/liquidity как production-данные.
