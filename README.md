# DeltaGrid — Crypto Arbitrage Scanner + RWA Intelligence

Production-ready crypto research terminal для анализа spot/perp рынков CEX и DEX, RWA, treasury, funding, market matrix и strategy research workflows.

**Текущая версия**: `v1.3.0`

## Архитектура

- **Frontend**: Next.js 15 + React + TypeScript + Tailwind CSS + Zustand + TanStack Query + lightweight-charts
- **Backend**: FastAPI + Python 3.11 + SQLAlchemy + PostgreSQL
- **Data**: OKX public market data (primary perp), CoinGecko API, CoinGlass, GeckoTerminal, alternative.me
- **Cache**: In-memory LRU with TTL (Redis-ready interface)
- **Persistence**: PostgreSQL через `DATABASE_URL` и Alembic migrations
- **Auth**: JWT tokens, bcrypt hashing, optional auth middleware, dual-token refresh
- **Enterprise-ready**: Plan capabilities, feature flags, request tracing, API boundary markers

## Быстрый запуск

### Требования
- Python 3.11+
- Node.js 20+
- Docker Desktop или локальный PostgreSQL 16+

### Standalone HTML Preview
Для быстрого просмотра будущего scanner/backtest UX без backend и без Next.js откройте файл:

```text
frontend/preview/index.html
```

Preview работает как статический HTML: страницы связаны через обычные `<a href="">`, mock-данные находятся внутри HTML, фильтры и табы используют только минимальный inline JavaScript.

### PostgreSQL

Через Docker Compose:

```bash
docker compose up -d postgres
```

Локальная строка подключения из `backend/.env.example`:

```env
DATABASE_URL=postgresql://deltagrid:deltagrid@127.0.0.1:5432/deltagrid
```

SQLite больше не является production runtime. Его можно использовать только явно для isolated tests, например `sqlite:///:memory:`.

### Production env gate

При `DEBUG=false` backend теперь падает на старте, если:

- `SECRET_KEY` оставлен dev/default или короче 32 символов;
- `VAULT_MASTER_KEY` пустой или короче 32 символов;
- `DATABASE_URL` пустой или указывает на SQLite;
- `CORS_ORIGINS` пустой или содержит `*`.

Перед staging/prod запуском проверьте:

```bash
curl http://127.0.0.1:8000/api/v1/health/readiness
```

Endpoint проверяет локальное подключение к БД и соответствие текущей Alembic revision source head.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Проверьте DATABASE_URL и при необходимости добавьте COINGECKO_API_KEY
python -m alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend runs at `http://127.0.0.1:8000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:3000`

> **Windows note**: Use `http://127.0.0.1:3000` instead of `localhost` to avoid IPv6 timeout.

Текущий frontend открывается как тёмный terminal MVP с разделами Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts и Strategy Lab.

`Charts` имеет interactive v0 на `lightweight-charts`: OKX USDT Swap свечи, volume histogram, crosshair OHLC/volume, pan/zoom/scroll и контролы `BTC/ETH/SOL`, `1m/5m/1h`, `2h/8h/24h/7d`. Production deploy проверен через `/charts?symbol=BTC&interval=1m&range=7d` и мобильный сценарий `/charts?symbol=ETH&interval=5m&range=24h`.

`Market Overview`, `Assets`, `Funding`, `Charts`, `Market Matrix`, `Arbitrage Scanner` и `/data-health` уже читают live backend/PostgreSQL data-layer через backend API. `Market Overview` использует CoinGecko global/markets, alternative.me Fear & Greed, CoinGlass funding, price-first heatmap и логотипы CoinGecko. `Assets` поддерживает `BTC`, `ETH` и `SOL`, показывает live spot/funding/OHLCV и CoinGlass aggregated liquidations, когда в таблице `liquidations` есть строки; fake order book/liquidations не подмешиваются.

`Perp DEX` пока показывает статус `DEX data pending`, потому что live DEX venue adapter ещё не подключён; mock DEX volume/OI/liquidity не выдаются за production-данные. `Strategy Lab` показывает readiness live inputs, но не показывает fake PnL/trades до появления реального backtest engine. Order book и per-order liquidation tape остаются отдельными provider задачами.

### Docker Compose
```bash
docker compose up --build
```

Compose поднимает PostgreSQL, ждёт healthcheck, применяет `alembic upgrade head` и запускает backend.

### Runtime tuning live data

Live-страницы `Charts`, `Market Matrix`, `Arbitrage Scanner` и `Strategy Lab` читают несколько PostgreSQL-потоков через backend SSR-запросами. Для production используются явные лимиты:

```env
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT_SECONDS=10
BACKEND_FETCH_TIMEOUT_MS=5000
```

Если live-страницы начинают подвисать, сначала проверьте backend logs на `QueuePool` timeout и row counts через:

```bash
curl https://deltagrid.pro/api/v1/data/health
```

### Production deploy

Минимальный серверный сценарий для `deltagrid.pro` описан в [DEPLOYMENT.md](DEPLOYMENT.md): `.env.production`, `docker-compose.prod.yml`, reverse proxy, SSL, readiness checks, backup и rollback.

Текущее production-состояние от 2026-06-14:

- домен `https://deltagrid.pro` активен через Cloudflare DNS и указывает на сервер `2.25.143.143`;
- приложение развёрнуто на Ubuntu 22.04 в `/opt/deltagrid`; production branch для новых релизов — `main`, dev/staging branch — `preview`;
- PostgreSQL, backend и frontend запущены через `docker-compose.prod.yml`;
- внешний доступ идёт через Nginx и Let's Encrypt SSL;
- локальные server ports: backend `127.0.0.1:8000`, frontend `127.0.0.1:3001`, PostgreSQL наружу не опубликован.
- primary CEX perp data path переведён на OKX USDT Swap; Binance оставлен как legacy/diagnostic provider, потому что direct Binance FAPI на текущем VPS возвращает HTTP `451`.

### GitHub CI/CD и релизы

Release policy описана в [RELEASES.md](RELEASES.md). Базовая схема веток:

- `preview` — dev/staging ветка;
- `main` — production ветка;
- feature-ветки — короткие рабочие ветки для отдельных задач.

GitHub Actions:

- `CI` запускает backend tests, `compileall`, frontend `npm audit --audit-level=high` и frontend build на `preview`, `main` и pull requests;
- `Deploy Preview` деплоит `preview`, если в GitHub настроены `PREVIEW_SSH_HOST`, `PREVIEW_SSH_USER`, `PREVIEW_SSH_KEY`, `PREVIEW_APP_DIR`;
- `Deploy Production` деплоит `main`, если настроены `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR`.

Если SSH secrets не настроены, deploy workflow завершится успешным skip и не будет ломать CI.
На 2026-06-14 `Deploy Preview` проверен end-to-end: GitHub Actions деплоит ветку `preview` в `/opt/deltagrid-preview`, контейнеры становятся `healthy`, server smoke проходит на ports `8011/3012`.
Production auto-deploy пока не считается подтверждённым: hardening `Deploy Production` подготовлен в `preview`, перенос в `main` и проверка реального deploy в `/opt/deltagrid` остаются отдельной production-итерацией.
Подробный чеклист secrets: [deploy/github-actions-secrets.md](deploy/github-actions-secrets.md).

Рекомендуемая схема стендов на VPS:

- production: `/opt/deltagrid`, branch `main`, env `.env.production`, Compose project `deltagrid`, ports `8000/3001`, домен `https://deltagrid.pro`;
- preview: `/opt/deltagrid-preview`, branch `preview`, env `.env.preview`, Compose project `deltagrid-preview`, ports `8011/3012`, будущий домен `https://preview.deltagrid.pro`.

Шаблон preview env лежит в `.env.preview.example`. Общий deploy-скрипт `scripts/deploy-compose-stack.sh` используется и для production, и для preview.

Текущее preview-состояние от 2026-06-14: stack поднят на VPS, GitHub Actions auto-deploy проверен, smoke-check проходит, 7d BTC/ETH/SOL data sync выполнен в отдельную preview БД. Preview Nginx HTTP site `deltagrid-preview` уже включён и проверен через `Host: preview.deltagrid.pro`; внешний HTTPS-домен ждёт DNS-запись `preview -> 2.25.143.143` и выпуск SSL по чеклисту [deploy/dns/preview.deltagrid.pro.md](deploy/dns/preview.deltagrid.pro.md).

Для ручной загрузки свежих market data в production PostgreSQL:

```bash
cd /opt/deltagrid
sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 24 --ohlcv-intervals 1m,5m,1h
curl https://deltagrid.pro/api/v1/data/health
```

Sync по умолчанию пишет OKX USDT Swap OHLCV/funding/OI/L/S, CoinGlass v4 funding/OI snapshots с `exchange_list=OKX`, CoinGlass aggregated liquidation history с `exchange_list=OKX` и CoinGecko-derived basis snapshots. Binance можно проверить вручную через `--primary-perp-provider binance`, но на текущем production VPS direct Binance API возвращает HTTP `451`, поэтому он не является primary data path. Для регулярного запуска на сервере:

```bash
cd /opt/deltagrid
sudo sh scripts/install-market-sync-cron.sh
tail -100 /var/log/deltagrid-market-sync.log
```

На сервере используйте `docker compose`, `.env.production` и `docker-compose.prod.yml` из `/opt/deltagrid`. Старый SQLite-файл `deltagrid.db` не используется в production runtime.

## Features

### Phase 1 — MVP Scanner ✅
- Scanner with CEX-CEX, DEX-CEX, Spot-Perp tabs
- Search, sort, filter by spread/volume
- Favorite / Pin instruments
- Detail drawer with calculation breakdown
- Settings with RU/EN localization
- KPI cards (opportunities, best spread, avg spread, active signals)
- Cache with stale/fallback state handling
- Health and status endpoints

### Phase 2 — Auth + Paper Trading ✅
- **Auth**: JWT register/login with email/password, Telegram OAuth, Web3 Wallet
- **Paper Trading**: Demo accounts ($10K), portfolio state, trade lifecycle
- **Performance**: PnL, win rate, drawdown, Sharpe-ready metrics
- **Billing**: Plan definitions, referral code generation
- **User Profile**: Account info, plan status
- **PostgreSQL runtime**: `DATABASE_URL`, sync/async engines и Alembic migrations
- **Redis-ready**: Cache abstraction interface

### Phase 3 — Trade Execution + Real Data ✅
- Market Dashboard: trending, gainers, losers, fear & greed, funding rates
- Exchange Connectors: Binance, Bybit, OKX, Hyperliquid, Aster
- Order Intent Pipeline with Risk Manager
- Kill switch, position sizing, max exposure rules
- Encrypted API key storage (Fernet AES-256)
- Execution sessions with audit trail

### Phase 4 — Scale + Live Features ✅
- Realtime streaming: Binance WebSocket + SSE fallback
- Alerting Engine: rules CRUD, evaluation, deduplication, cooldown
- Notifications: email/web-push/Telegram with preference toggles
- Provider Health Monitor: CoinGlass, GeckoTerminal integration
- Dual-token auth with automatic refresh

### Phase 5 — RWA + Treasuries ✅
- **RWA Scanner**: Tokenized gold (XAUT, PAXG), treasuries (BUIDL, USDY), credit (CFG)
- **Treasury Dashboard**: BTC holdings tracker (MicroStrategy, MARA, Tesla, Block)
- **Tokenization Platforms**: Centrifuge, Figure, Maple Finance with TVL and governance tokens
- **Detail Views**: Issuer, blockchain, contract address, NAV, yield APR, premium/discount
- **Alert Integration**: `rwa_price_threshold`, `treasury_holdings_change` rule types

### Phase 6.0 — Architecture Hardening ✅
- **Plan Capabilities**: Database-driven feature gating (free/pro/enterprise)
- **Feature Flags**: User-level overrides with expiration support
- **Request Tracing**: `X-Request-ID` middleware on all requests
- **Global Exception Handler**: Consistent `{ error: { code, message, request_id } }` format
- **API Boundaries**: `@internal` / `@public_ready` endpoint markers
- **CORS Hardening**: Environment-aware restrictions

## API Endpoints

### Phase 1 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/scanner` | List scanner records |
| `GET /api/v1/scanner/{id}` | Record detail |
| `GET /api/v1/preferences` | User preferences |
| `POST /api/v1/preferences` | Update preferences |
| `GET /api/v1/health` | Health check |
| `GET /api/v1/health/readiness` | DB + Alembic readiness check |
| `GET /api/v1/health/status` | Data source status |

### Phase 2 Endpoints
| Endpoint | Description | Auth |
|----------|-------------|------|
| `POST /api/v1/auth/register` | Register new user | Public |
| `POST /api/v1/auth/login` | Login | Public |
| `GET /api/v1/auth/me` | Current user | Required |
| `GET /api/v1/paper/accounts` | List paper accounts | Required |
| `POST /api/v1/paper/accounts` | Create paper account | Required |
| `GET /api/v1/paper/accounts/{id}/trades` | List trades | Required |
| `POST /api/v1/paper/accounts/{id}/trades` | Open trade | Required |
| `POST /api/v1/paper/accounts/{id}/trades/{trade_id}/close` | Close trade | Required |
| `GET /api/v1/performance/accounts/{id}` | Performance metrics | Required |
| `GET /api/v1/billing/plans` | Available plans | Public |

### Phase 3 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/market/trending` | Trending coins |
| `GET /api/v1/market/gainers` | Top gainers |
| `GET /api/v1/market/losers` | Top losers |
| `GET /api/v1/market/fear-greed` | Fear & Greed index |
| `GET /api/v1/market/funding-rates` | Perp funding rates |
| `GET /api/v1/exchange-accounts` | Exchange accounts |
| `GET /api/v1/connectors/capabilities` | Connector registry |
| `GET /api/v1/execution/intents` | Order intents |
| `GET /api/v1/risk/rules` | Risk rules |

### Phase 4 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/stream/config` | Stream configuration |
| `WS /api/v1/stream/ws` | WebSocket stream |
| `GET /api/v1/stream/sse` | SSE fallback |
| `GET /api/v1/alerts/rules` | Alert rules |
| `GET /api/v1/alerts/events` | Alert events |
| `GET /api/v1/notifications/preferences` | Notification preferences |
| `GET /api/v1/health/providers` | Provider health status |

### Phase 5 Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/rwa/assets` | RWA assets (category filter) |
| `GET /api/v1/rwa/assets/{id}` | RWA asset detail |
| `GET /api/v1/rwa/assets/{id}/snapshots` | RWA asset history |
| `GET /api/v1/rwa/categories` | RWA category counts |
| `GET /api/v1/rwa/compare` | Compare two RWA assets |
| `GET /api/v1/treasury/entities` | Treasury entities |
| `GET /api/v1/treasury/entities/{id}` | Treasury entity detail |
| `GET /api/v1/treasury/entities/{id}/snapshots` | Treasury entity history |
| `GET /api/v1/treasury/btc-holdings` | BTC holdings leaderboard |
| `GET /api/v1/treasury/platforms` | Tokenization platforms |

### Data Layer Endpoints
| Endpoint | Описание |
|----------|----------|
| `GET /api/v1/data/ohlcv?symbol=BTC&exchange=okx&start=...&end=...` | Чтение OHLCV из PostgreSQL, максимум 1000 строк; `start`/`end` — Unix timestamp в миллисекундах. |
| `GET /api/v1/data/ohlcv/window?symbol=BTC&exchange=okx&interval=1m&range=7d` | Чтение bounded OHLCV окна для interactive charts одним запросом; поддерживает `1m/5m/1h`, `2h/8h/24h/7d`, максимум 20000 строк. |
| `GET /api/v1/data/funding?symbol=BTC&exchange=okx&start=...&end=...` | Чтение истории funding rate из PostgreSQL, максимум 1000 строк. |
| `GET /api/v1/data/coverage?symbols=BTC,ETH,SOL&exchange=okx&range=7d` | Coverage matrix по историческим потокам: rows/expected, coverage %, latest timestamp и reason для OHLCV/funding/OI/long-short/liquidations/basis/spot-perp price. |
| `GET /api/v1/data/universe?symbols=BTC,ETH,SOL&exchange=okx` | Production universe readiness поверх coverage/freshness: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`, `ui_universe` и `deferred_symbols`. |
| `GET /api/v1/data/provider-inventory?symbols=BTC,ETH,SOL,HYPE&exchange=okx` | Read-only inventory кандидатов на расширение universe поверх persisted coverage/freshness: `promotion_candidate`, `next_action`, readiness status и 24h/7d summaries без внешних API-вызовов. |
| `GET /api/v1/data/health` | Health snapshot data-layer: статусы провайдеров, последние sync, row counts, data quality score, freshness SLA, coverage matrix, universe readiness, health по `sync_type` и cron/data-sync diagnostics. |

Для sparse event streams вроде `liquidations` `/data/health` различает возраст последнего события и свежесть sync-run: отсутствие новых событий не считается stale, если `coinglass/liquidations` sync свежий и успешный.
`/data/coverage` и блок `coverage` внутри `/data/health` используют ту же семантику для sparse streams: свежий успешный sync-run подтверждает provider coverage даже при отсутствии новых liquidation events.

### Provider Discovery CLI

Read-only discovery перед расширением universe:

```bash
cd backend
python -m app.adapters.data.discover_provider_universe --env-file ../.env.providers.local --format markdown
```

На preview/VPS тот же CLI запускается внутри backend container:

```bash
cd /opt/deltagrid-preview
docker compose --env-file .env.preview -p deltagrid-preview -f docker-compose.prod.yml exec -T backend \
  python -m app.adapters.data.discover_provider_universe --format markdown
```

CLI не пишет в PostgreSQL и не меняет sync/UI-конфигурацию. Он проверяет OKX, CoinGlass, CoinGecko и legacy Binance, после чего выдаёт `eligible_for_24h_sync_dry_run`, `okx_core_only_review` или `do_not_expand_sync_yet`.

Idempotent seed aliases для core symbols и первой малой expansion group:

```bash
cd backend
python - <<'PY'
from app.adapters.data.symbol_mapper import SymbolMapper
SymbolMapper().seed_defaults()
PY
```

На preview эта команда выполняется внутри backend container перед sync dry-run. Она не расширяет UI universe сама по себе.

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| 1 | ✅ Done | MVP Scanner |
| 2 | ✅ Done | Auth + Paper Trading + Revenue hooks |
| 3 | ✅ Done | Trade Execution + Real Data Connectors + Market Dashboard |
| 4 | ✅ Done | Scale + Alerts + Realtime Streaming + Provider Health |
| 5 | ✅ Done | RWA + Treasuries + Tokenization Intelligence |
| 6 | 📋 Planned | Enterprise + B2B + Multi-tenancy + White-label |
