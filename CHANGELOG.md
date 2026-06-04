# Changelog — DeltaGrid

## [2026-06-05] — [DEPLOY] — Привязка deployment flow к `deltagrid.pro`
- `.env.production.example` обновлён под `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- `deploy/nginx/deltagrid.conf.example` теперь содержит `server_name deltagrid.pro www.deltagrid.pro`.
- `scripts/generate-production-env.sh` по умолчанию генерирует `.env.production` для `deltagrid.pro`.
- `DEPLOYMENT.md`, `README.md`, `PROJECT_PLAN.md` и `CURRENT_TASK.md` обновлены под реальный домен.
- DNS preflight: `deltagrid.pro` и `www.deltagrid.pro` сейчас резолвятся в `31.31.196.50` и `2a00:f940:2:2:1:1:0:266`; HTTP отдаёт parking page REG.RU, HTTPS требует настройки.

## [2026-06-05] — [DEPLOY] — Минимальный server deployment flow
- Добавлен `.env.production.example` с обязательными production-переменными: secrets, CORS, PostgreSQL credentials, provider keys и runtime tuning.
- `.env.production` добавлен в `.gitignore`, чтобы реальные секреты не попадали в репозиторий.
- Добавлены `backend/.dockerignore` и `frontend/.dockerignore`, чтобы production images не получали локальные env, SQLite DB, venv, `node_modules`, `.next` и cache artifacts.
- Добавлен `docker-compose.prod.yml`: PostgreSQL не публикуется наружу, backend/frontend слушают `127.0.0.1`, backend стартует через `alembic upgrade head`, backend/frontend имеют healthcheck.
- Добавлен `DEPLOYMENT.md` на русском языке: подготовка env, запуск, readiness checks, reverse proxy, SSL, backup PostgreSQL и rollback.
- Добавлен `deploy/nginx/deltagrid.conf.example` как переносимый Nginx-шаблон для домена и WebSocket upgrade.
- Добавлен `scripts/server-smoke.sh` для проверки backend health, readiness, data health и frontend локально или через домен.
- Добавлен `scripts/server-smoke.ps1` для локальной Windows-проверки.
- Добавлен `scripts/server-preflight.sh` для проверки server prerequisites, Docker daemon, compose config, DNS lookup и занятых портов.
- Добавлен `scripts/generate-production-env.sh` для безопасной генерации `.env.production` по домену без ручной сборки секретов.
- `frontend/next.config.js` больше не привязан к `http://127.0.0.1:8000`: rewrite использует `BACKEND_INTERNAL_URL` с локальным fallback, а Docker передаёт его на frontend build stage.
- `frontend/src/hooks/useRealtime.ts` больше не зашит только на `ws://127.0.0.1:8000`: локально остаётся прямое подключение к backend, а на домене используется same-origin WebSocket path или `NEXT_PUBLIC_WS_URL`.
- Проверка: `npm run build` проходит; Docker frontend пересобран; `http://127.0.0.1:3000/api/v1/health/readiness` через Next.js proxy возвращает `ready`.

## [2026-06-05] — [HARDENING] — Production readiness gate для env, DB и миграций
- Усилена startup validation при `DEBUG=false`: backend блокирует слабые/dev `SECRET_KEY`, короткий или пустой `VAULT_MASTER_KEY`, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS`.
- Добавлен `GET /api/v1/health/readiness`: endpoint проверяет локальное подключение к БД, читает `alembic_version` и сравнивает текущую revision с source head.
- В `Settings` добавлен `COINGLASS_STANDARD_API_KEY`, чтобы `.env.example` и runtime config не расходились.
- `docker-compose.yml` теперь прокидывает `COINGLASS_API_KEY` и `COINGLASS_STANDARD_API_KEY` в backend.
- Обновлены `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md` и `BACKLOG.md` с readiness flow и staging/prod рисками.
- Проверка: `venv\Scripts\python.exe -m pytest tests -q` — 6 passed; `venv\Scripts\python.exe -m compileall app` — успешно.
- Проверка Docker: backend пересобран, PostgreSQL healthy, frontend отвечает на `http://127.0.0.1:3000`, `/api/v1/health`, `/api/v1/data/health` и `/api/v1/health/readiness` возвращают ожидаемый статус; readiness показывает head `7c1f2a8d9e34`.

## [2026-06-05] — [DB] — PostgreSQL runtime для production-ready MVP
- Backend persistence переведён на PostgreSQL как основной runtime через `DATABASE_URL`.
- Добавлен sync PostgreSQL driver `psycopg[binary]`; async layer продолжает использовать `asyncpg`.
- Добавлена нормализация DB URL для sync engine, async engine и Alembic: `postgres://`, `postgresql://`, `postgresql+psycopg://`, `postgresql+asyncpg://`.
- `Base.metadata.create_all()` больше не создаёт production-схему для PostgreSQL; схема управляется через Alembic.
- Добавлена миграция `3f0c2e5a7b91_postgresql_mvp_hardening` для таблицы `backfill_jobs`, которая раньше создавалась только ручным SQLite-DDL внутри `DataWriter`.
- Добавлена миграция `7c1f2a8d9e34_bigint_market_timestamps`: Unix timestamp в миллисекундах для market/backtest/data-layer хранится в `BigInteger`, а не в PostgreSQL `integer`.
- `DataWriter` и `SymbolMapper` используют PostgreSQL-safe engine settings; SQLite fallback оставлен только для isolated tests.
- Старые migration seed'и обновлены для PostgreSQL-safe boolean values (`true/false` вместо `1/0` в boolean-колонках).
- `docker-compose.yml` теперь поднимает PostgreSQL 16, ждёт healthcheck и запускает `alembic upgrade head` перед стартом backend.
- Обновлены `README.md`, `DATA_ARCHITECTURE.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md` и `BACKLOG.md` с инструкциями PostgreSQL-запуска и рисками.
- Проверено на живом Docker Compose окружении: PostgreSQL healthy, backend применяет Alembic migrations при старте, `/api/v1/health`, `/api/v1/data/health`, `/api/v1/data/ohlcv` и `/api/v1/market/trending` возвращают 200, frontend отвечает на `http://127.0.0.1:3000`.

## [2026-06-04] — [v1.2.0] — Frontend MVP terminal shell и 6 ключевых экранов
- Frontend package version обновлён до `1.2.0`.
- Основной frontend shell переведён на тёмный terminal layout: left sidebar, top workspace tabs, search и компактные controls.
- Sidebar обновлён под MVP-информационную архитектуру: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
- Perp DEX и Funding получили nested navigation с визуальной tree-line.
- Добавлен typed mock data adapter в `frontend/src/lib/terminal`, чтобы UI работал на fixtures сейчас и мог быть заменён на CoinGecko/CoinGlass-backed providers позже.
- Реализованы экраны: Market Overview / Command Center, Perp DEX Intelligence, Funding Overview, Asset Deep Dive SOL, Market Matrix, Strategy Lab / Backtest.
- Добавлены routes `/arbitrage-scanner` и `/charts`; Charts пока реализован как аккуратный placeholder без новых зависимостей.
- Market Overview, Perp DEX, Arbitrage Scanner и Market Matrix очищены от полноценного funding-дублирования; Funding Matrix, Funding Arbitrage и Long/Short legs живут только в Funding.
- Корневой route `/` теперь ведёт на `/market`, чтобы MVP не открывал старый scanner flow с right drawer.
- Проверка: `npm run build` во frontend проходит успешно.

## [2026-06-02] — [CRITICAL FIX] — Code Review v2: security, symbol contract, regression tests
- **Security**: Telegram/Web3 auth endpoint'ы (`/auth/telegram`, `/auth/web3/challenge`, `/auth/web3/verify`) теперь возвращают `501 Not Implemented` при `DEBUG=false`.
- **Security**: Добавлена fail-fast startup validation: в production-like режиме (`DEBUG=false`) приложение падает при старте, если `SECRET_KEY` оставлен дефолтным или `VAULT_MASTER_KEY` пустой.
- **Data layer symbol contract**: `BinanceAdapter.fetch_ohlcv` теперь принимает canonical symbol (например, `BTC`) и маппит в provider-native (`BTCUSDT`) внутри адаптера через `SymbolMapper`. Все записи в БД теперь используют canonical symbol.
- **Data layer**: Исправлен gap detection bug в `BackfillOrchestrator`: `expected` теперь считается до сдвига `current_start`.
- **Testing**: Добавлен `backend/tests/test_data_api.py` — regression tests на `TestClient` с in-memory SQLite, которые доказывают, что `/api/v1/data/ohlcv?symbol=BTC&exchange=binance` возвращает seeded данные.
- **Docs**: Обновлён `backend/.env.example` с секциями `Security` и комментариями о production secrets.

## [2026-06-02] — [UI] — Standalone HTML preview frontend
- Добавлен автономный preview-интерфейс в `frontend/preview/`, который открывается напрямую через `index.html` без Next.js, React, backend API и сборки.
- Реализованы страницы `index.html`, `asset.html`, `strategy-lab.html`, `data-health.html` и общий `styles.css` в тёмной dashboard-теме.
- Scanner содержит mock-данные по BTC, ETH, SOL и HYPE, фильтры по exchange/signal, кликабельные строки и переходы в asset/backtest flow.
- Asset preview поддерживает табы Overview/Funding/OI/Liquidations/Long/Short и переход в Strategy Lab с передачей `symbol` через query string.
- Strategy Lab показывает selector стратегий, параметры backtest и disabled-кнопку `Run Backtest` до появления engine.
- Data Health показывает mock-статусы CoinGlass, CoinGecko и Binance.

## [2026-06-02] — [UI] — MVP-навигация frontend
- Sidebar переведён на MVP-набор разделов: Market, Strategy Lab, Backtests, Data Health, Watchlist и Settings.
- Старые product-разделы скрыты только из навигации; route-файлы и существующая реализация не удалялись.
- Добавлены placeholder-страницы `/strategy-lab`, `/backtests`, `/data-health`.
- Добавлен route `/watchlist` как alias на текущий scanner/watchlist-интерфейс, чтобы новый пункт меню не вёл в 404.
- На `/market` добавлен mock-индикатор свежести данных `Updated 2 min ago`.

## [2026-06-02] — [API] — Read-only endpoint'ы проверки market data
- Добавлен роутер `backend/app/api/v1/data.py` с публичными read-only endpoint'ами `GET /api/v1/data/ohlcv`, `GET /api/v1/data/funding` и `GET /api/v1/data/health`.
- `ohlcv` и `funding` читают данные из SQLite через существующие SQLAlchemy-модели `DataOhlcv` и `DataFundingRate`, фильтруют по `symbol`, `exchange`, `start`, `end` и возвращают максимум 1000 строк.
- `data/health` возвращает статус `binance`/`coinglass`, последний sync по провайдерам, количество строк в data-layer таблицах и приближённый `data_quality.score` по логам качества данных за последние 24 часа.
- Роутер подключён в `app.main`; POST/DELETE операции не добавлялись.
- Проверка: `venv\Scripts\python.exe -m compileall app` и smoke-test через `TestClient` на in-memory SQLite для трёх новых endpoint'ов.

## [2026-05-20] — [AUDIT/FIX] — Техническое ревью Codex
- Проведён технический аудит структуры проекта, frontend build, backend import/compile, зависимостей, Alembic-состояния и базового health endpoint.
- Исправлено восстановление frontend auth-состояния после reload: валидный persisted JWT снова выставляет `isAuthenticated=true`.
- Исправлен auto-refresh JWT: ответ `/auth/refresh` теперь приводится к camelCase перед чтением `accessToken`.
- Исправлен импорт `async_database.py` на дефолтном SQLite URL через нормализацию async driver URL.
- Docker Compose теперь пишет SQLite базу в примонтированный volume `/app/data` и разрешает CORS для `localhost` и `127.0.0.1`.
- Убрано устаревшее поле `version` из `docker-compose.yml`.
- Добавлена пустая `frontend/public/.gitkeep`, чтобы production Dockerfile не падал на `COPY /app/public`.
- Исправлено двойное чтение HTTP error body в backend test helper scripts.
- Startup seeding и scanner warm-up теперь логируют warning при ошибке вместо полного silent failure.
- RWA/Treasury UI теперь безопаснее обрабатывает `null`/`undefined` в числовых snapshot-полях.
- Отложено: настройка ESLint, полноценные backend tests, проверка реальных API/рыночных данных, архитектурное разделение sync/async persistence перед PostgreSQL.

## [2026-05-13] — [ARCH] — Phase 1 MVP Scanner реализован
- Создана полная архитектура backend (FastAPI) + frontend (Next.js 14)
- Реализованы: Scanner, Detail View, Settings, KPI Cards, Search/Sort/Filter
- Добавлена RU/EN локализация через centralized dictionaries
- Настроены CoinGecko adapter + Perp DEX stubs (Hyperliquid, Aster, Lighter)
- Реализован SpreadCalculator + SignalClassifier (STRONG/BUY_SELL/MARGINAL/HOLD)
- Добавлен in-memory cache с TTL + stale/fallback logic
- SQLite persistence для favorites, pinned, preferences
- Созданы Docker + docker-compose конфигурации

## [2026-05-13] — [FIX] — Исправлена ошибка camelCase ↔ snake_case между backend/frontend
- Добавлены хелперы snakeToCamel / camelToSnake в frontend API client
- Исправлен Runtime Error в SettingsForm (undefined при toFixed)

## [2026-05-13] — [UI] — Первая сборка frontend
- Next.js build проходит без TypeScript ошибок
- Tailwind конфиг с кастомной дизайн-системой (light theme)
- Zustand stores + TanStack Query hooks

## [2026-05-13] — [API] — Backend endpoints активны
- GET /api/v1/scanner — список арбитражных возможностей (24 записи на mock)
- GET /api/v1/scanner/{id} — детальная карточка
- GET/POST /api/v1/preferences — настройки
- GET/POST /api/v1/preferences/favorites — избранное
- GET/POST /api/v1/preferences/pinned — закреплённые
- GET /api/v1/health + /status — health check + data source status

## [2026-05-13] — [ARCH] — Phase 2 Migration: Foundation + Auth + Paper Trading
- **Backend foundation**: PostgreSQL-ready async engine, Alembic migrations, Redis cache abstraction
- **Auth foundation**: JWT tokens, register/login endpoints, optional auth middleware, bcrypt password hashing
- **Paper Trading**: VirtualBalance, trade lifecycle (open/close), PnL calculation, portfolio state
- **Performance Tracking**: PnL, win rate, max drawdown, Sharpe-ready metrics structure
- **Billing/Referral hooks**: Plan definitions, subscription placeholders, referral code generation
- **Frontend**: authStore (Zustand + persist), LoginModal, UserMenu, PaperTrading page, Profile page
- **API Evolution**: 12 new endpoints under /api/v1/{auth,paper,performance,billing}
- **Compatibility**: All Phase 1 endpoints preserved, scanner/settings/favorites work for anonymous users
- **Regression**: Full test suite passes — Phase 1 baseline intact

## [2026-05-13] — [CRITICAL FIX] — Исправлены фатальные баги авторизации и scanner performance
- **FIX**: `LoginModal.tsx` передавал `user` и `token` в `authStore.login()` в обратном порядке → токен сохранялся как объект, API отправлял `Bearer [object Object]` → 401 → авто-логаут
- **FIX**: `LoginModal.tsx` искал `data.access_token`, но `api.ts` transformResponse превращает snake_case в camelCase → `data.accessToken` → токен был `undefined`
- **FIX**: `scanner.py` создавал новый `InMemoryCacheService` на каждый запрос → cache не работал → scanner endpoint занимал 12+ секунд (CoinGecko API каждый раз)
- **FIX**: `localhost` на Windows резолвится в IPv6 (`::1`), серверы слушали IPv4 → ~2 секунды таймаута на каждый запрос
  - Решение: Next.js dev server `-H 127.0.0.1`, rewrite proxy на `127.0.0.1:8000`
- **FIX**: Singleton cache/registry в scanner endpoint + warm-up при старте backend
- **FIX**: Увеличен cache TTL с 60 до 300 секунд
- **FIX**: `authStore` добавлен `onRehydrateStorage` валидатор JWT токена — очищает битые токены из localStorage
- **FIX**: Страницы `/paper-trading` и `/profile` защищены redirect'ом для анонимных пользователей
- **FIX**: `usePaperAccounts()` не делает запрос если пользователь не авторизован (`enabled: isAuthenticated`)
- **RESULT**: Scanner загружается за ~85ms, Paper Trading открывается без разлогина, auth работает стабильно

## [2026-05-14] — [ARCH] — Phase 3 Quick Wins: Market Dashboard (A+B+F+G)
- **Increment A — Market Overview Dashboard**: endpoints `/market/{trending,gainers,losers,global}`, CoinGeckoAdapter extensions, MarketService with caching, frontend page `/market` with 4 cards
- **Increment B — Fear & Greed Index**: endpoint `/market/fear-greed`, alternative.me API integration, `FearGreedCard` with 7-day history and color-coded indicator. Current value: 34 (Fear)
- **Increment F — New Listings**: endpoint `/market/new-listings`, filter from trending by market_cap_rank, `NewListingsCard` component
- **Increment G — Funding Rates (placeholder)**: endpoint `/market/funding-rates`, mock data for 8 perp pairs (BTC, ETH, SOL, XRP, DOGE, HYPE, LINK, SUI), `FundingRatesCard` with "Mock" badge
- **CoinGecko auth fix**: removed demo keys causing 401 on public API — free tier works without any key
- **Frontend**: `useMarketData` hook, `TrendingCard`, `GainersCard`, `LosersCard`, `GlobalStatsCard`, `FearGreedCard`, `NewListingsCard`, `FundingRatesCard`
- **i18n**: Added RU/EN translations for all market components (fearGreed, newListings, fundingRates, globalStats, etc.)
- **Sidebar**: Added "Market" navigation item with Activity icon
- **RESULT**: Full market dashboard at `/market` with real live data from CoinGecko + alternative.me

## [2026-05-15] — [ARCH] — Phase 3 Execution Foundation: Increments A+B+C+D+E COMPLETED
- **Increment A — Foundation & Security**:
  - Alembic initial migration for Phase 1/2 tables + Phase 3 migration (exchange_accounts, exchange_keys, connector_capabilities, real_orders, order_events, execution_runs, risk_rules, position_snapshots, live_trade_sessions, audit_logs)
  - `SecretsVaultService` (Fernet AES-256 encryption for API keys)
  - `ExchangeAccountService` with CRUD + encrypted key storage (backend-only, never exposed)
  - `GET/POST/DELETE /exchange-accounts`, `POST /exchange-accounts/{id}/keys`, `GET /connectors/capabilities`
  - Frontend: `/exchange-accounts` page, `AddExchangeModal`, `exchangeAccountStore`, sidebar navigation
  - Connector capabilities seeded for Binance, Bybit, OKX, Hyperliquid, Aster
- **Increment B — Order Intent Pipeline + Risk Manager**:
  - `RiskManager` service: rule CRUD, kill-switch, position sizing, max exposure, dry-run checks
  - `ExecutionService`: order intent lifecycle (intent -> risk_check -> pending_confirmation -> submitted/failed)
  - Safe default: `is_live=False` rejects orders with safe message
  - Endpoints: `/execution/intents`, `/execution/orders`, `/risk/rules`, `/risk/check`
  - Frontend: `/execution` dashboard, `/risk-rules` page, `OrderIntentModal` integrated into ScannerRow
  - Audit trail: `order_events` + `audit_logs` for every action
- **Increment C — Connector Foundation**:
  - `ExchangeConnector` ABC with `ConnectorCapabilities`, `OrderRequest`, `OrderResult`, `OrderStatus`
  - `ConnectorRegistry` for runtime connector discovery
  - `BinanceConnector` with REST spot API (account info, ticker, place order, status)
  - `OrderManager`: retry logic (3x exponential backoff), partial fill handling, status sync
  - ExecutionService delegates to OrderManager on `confirm_intent(is_live=True)`
- **Increment D — Additional CEX Connectors**:
  - `BybitConnector` (V5 unified API): ticker, account, place order, status
  - `OKXConnector`: ticker, account, place order, status (passphrase support)
- **Increment E — Perp DEX + Kill Switch + Sessions**:
  - `HyperliquidConnector` (direct REST): ticker via `allMids`, clearinghouse state, placeholder trading (needs wallet signing)
  - `AsterConnector` stub for future expansion
  - Kill switch: `POST /risk/rules/{id}/toggle` for quick activation
  - Execution sessions: `GET/POST /execution/sessions`, `POST /execution/sessions/{id}/stop`
  - Frontend: Session start/stop buttons on Execution dashboard
- **Compatibility**: All Phase 1/2 endpoints preserved. Scanner, auth, paper trading, settings, i18n, favorites/pins unchanged.
- **Security**: Encrypted API keys, no secret exposure in frontend, explicit opt-in for live trading, safe defaults.

## [2026-05-15] — [FIX] — Phase 3 Final Polish: Login Modal, Sidebar, Port Conflicts
- **FIX**: `LoginModal.tsx` использовал `data.access_token` вместо `data.accessToken` — `transformResponse` конвертирует snake_case → camelCase → токен был `undefined` → 401 → авто-логаут loop
- **FIX**: Страницы `/execution`, `/exchange-accounts`, `/risk-rules` не обёрнуты в `<Shell>` → sidebar отсутствовал, нет навигации
- **FIX**: Конфликты порта 8000 — multiple zombie python процессы удерживали порт → backend не стартовал
- **FIX**: Пустая initial Alembic migration (`pass` в upgrade/downgrade) — пофикшено через ручной seed `alembic_version` + правильная Phase 3 migration
- **Backend restart**: `deltagrid.db` на SQLite с полной схемой Phase 3, Alembic `9cc9da229c47` применена
- **RESULT**: Frontend http://127.0.0.1:3000 и Backend http://127.0.0.1:8000 работают стабильно. Phase 3 готова к тестированию.

## [2026-05-16] — [ARCH] — Phase 4 Scale + Live Features COMPLETED
- **Increment A — Tech Debt Remediation**:
  - Fix `httpx.AsyncClient` leaks: explicit `close()` in all 5 connectors + `OrderManager` try/finally
  - Cache upgrade: FIFO → LRU via `OrderedDict`, cache invalidation on preference changes
  - `PreferenceService`: explicit session lifecycle, no unmanaged `SessionLocal()`
  - Dual-token auth: access + refresh tokens, `/auth/refresh` endpoint, frontend auto-refresh on 401
- **Increment B — Provider Layer & Enrichments**:
  - `CoinGlassClient` + `GeckoTerminalClient` with rate-limit awareness and graceful fallback
  - `ProviderHealthMonitor` + `provider_health` table + `provider_sync_logs`
  - Hardcoded funding rates replaced with CoinGlass-backed data + fallback mock with `data_status: fallback`
  - New endpoints: `GET /market/enrichments`, `GET /health/providers`
- **Increment C — Realtime Streaming Foundation**:
  - `WebSocketManager`: Binance public ticker stream, reconnect/backoff, heartbeat
  - `NormalizedStreamEvent`: unified ticker DTO across exchanges
  - WebSocket endpoint `/api/v1/stream/ws` + SSE fallback `/api/v1/stream/sse`
  - Frontend: `useRealtime` hook, `streamStore` (isolated from polling), `RealtimeIndicator` component
  - Tables: `realtime_feed_sessions`, `stream_events`
- **Increment D — Alerting Engine**:
  - `AlertService`: rule CRUD, evaluation, deduplication (hash-based), cooldown
  - `NotificationService`: email/web-push/Telegram delivery stubs with logged fallback
  - New endpoints: `/alerts/rules`, `/alerts/events`, `/notifications/preferences`, `/notifications/web-push/*`
  - Frontend: `/alerts` page, `/notifications` page, `useAlerts` + `useNotifications` hooks
  - Tables: `alert_rules`, `alert_events`, `alert_deliveries`, `notification_preferences`
- **Increment E — Security Hardening & Auth Extensions**:
  - `User.session_version` for global logout capability
  - Telegram OAuth: `/auth/telegram` endpoint
  - Web3 login: `/auth/web3/challenge` + `/auth/web3/verify` endpoints
  - Frontend: Telegram + Web3 login buttons in `LoginModal` (Coming Soon stubs)
- **Compatibility**: All Phase 1/2/3 endpoints preserved. Scanner, auth, paper trading, execution, risk controls, settings, i18n unchanged.
- **Schema**: 4 Alembic migrations added (`69bd5d1e4711`, `2583b2f128b1`, `8d4a2b9ab83a`, `bd43594cd747`) → 29 total tables.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.

## [2026-05-16] — [FIX] — Phase 4 Final Polish: UI snakeToCamel, Alerts Form, Server Restarts
- **FIX**: `useNotifications.ts` не применял `snakeToCamel` к ответу API → `emailEnabled` был всегда `undefined` → toggle застревал в `true` (fallback `?? true`)
  - Backend возвращал `email_enabled`, frontend искал `emailEnabled` → mismatch
  - Экспортирован `snakeToCamel` из `api.ts`, применён в `useNotifications.ts` и `useAlerts.ts`
- **FIX**: `useAlerts.ts` — та же проблема с `snakeToCamel` для rules/events
- **FIX**: Alerts page (`/alerts`) — добавлена кнопка "Add Rule" и полноценная форма создания правила (name, ruleType, symbol, threshold, comparison, cooldown, severity)
- **FIX**: Frontend сервер не подхватывал изменения в `/alerts/page.tsx` без перезагрузки (Next.js dev cache)
- **RESULT**: Notifications toggles работают корректно, Alerts page позволяет создавать правила. Оба сервера перезапущены.

## [2026-05-16] — [ARCH] — Phase 5 RWA / Treasuries COMPLETED
- **Increment A — Foundation & Provider Wiring**:
  - Alembic migration `b6fa1801e11d_phase_5_rwa_treasuries`: 5 new tables (`rwa_assets`, `rwa_asset_snapshots`, `treasury_entities`, `treasury_snapshots`, `tokenization_platforms`)
  - Alembic migration `f99eef8f0f6c_add_rwa_alerts_enabled`: `rwa_alerts_enabled` on `notification_preferences`
  - `BaseRwaAdapter` ABC in `adapters/rwa/`
  - `RwaAssetService` + `TreasuryService` with async cache, CRUD, seeding
  - `CoinGeckoRwaAdapter` for XAUT/PAXG via `/coins/{id}`
  - Pydantic schemas: `RwaAssetSchema`, `RwaAssetSnapshotSchema`, `TreasuryEntitySchema`, `TreasurySnapshotSchema`, `TokenizationPlatformSchema`
- **Increment B — RWA Asset Data & Gold Tokens**:
  - `GET /rwa/assets` with category filter, `GET /rwa/assets/{id}`, `GET /rwa/categories`, `GET /rwa/compare`
  - Seeded: XAUT, PAXG, BUIDL, USDY, CFG
  - Frontend: `/rwa` page with category filters, asset table, source/freshness badges
- **Increment C — Treasury Entities & BTC Holdings**:
  - `GET /treasury/entities`, `GET /treasury/entities/{id}`, `GET /treasury/btc-holdings`, `GET /treasury/platforms`
  - Seeded: MicroStrategy, MARA, Tesla, Block
  - Frontend: `/treasury` page with Companies/Platforms tabs, BTC holdings summary cards
- **Increment D — Tokenization Platforms & Detail Views**:
  - Seeded: Centrifuge, Figure, Maple Finance
  - Detail pages: `/rwa/[id]`, `/treasury/[id]` with issuer, blockchain, contract, snapshots
- **Increment E — Alert Compatibility & Polish**:
  - `AlertService` supports `rwa_price_threshold`, `treasury_holdings_change` rule types
  - `rwa_alerts_enabled` toggle on `/notifications` page
  - Frontend i18n: RU/EN translations for RWA/Treasury domain
  - Header: route-aware title, scanner status badge scoped to scanner page only
- **Compatibility**: All Phase 1-4 endpoints preserved. Zero breaking changes.
- **Schema**: 2 Alembic migrations added → 31 total tables, 8 total migrations.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.

## [2026-05-16] — [ARCH] — Phase 6.0 Architecture Hardening COMPLETED
- **Architecture Audit & Risk Map**: Full codebase audit, bounded contexts identified, tight coupling documented, enterprise-readiness gaps catalogued
- **Alembic Migration `b19c6344f081_phase_6_capability_foundation`**:
  - New table `plan_capabilities` — 41 seeded rows mapping plans (free/pro/enterprise) to features with limits
  - New table `feature_flags` — user-level feature overrides with expiration support
  - Altered `users` — added `feature_flags_json`, `plan_started_at`, `plan_expires_at` (all nullable)
- **CapabilityService** (`app/services/capability_service.py`): Plan-based feature gating with user-level override support. `check()`, `get_limit()`, `list_capabilities()`
- **RequestIDMiddleware** (`app/core/middleware.py`): ASGI middleware injecting `X-Request-ID` into all requests/responses
- **Global Exception Handler**: `DeltaGridException` hierarchy wired into FastAPI. Consistent `{ error: { code, message, request_id } }` format
- **CORS Hardening**: Env-aware method/header restrictions. `expose_headers=["X-Request-ID"]`. Debug mode keeps permissive defaults
- **Health Endpoint**: Now returns `api_version: "v1"`, `api_tier: "internal"`
- **Billing Plans**: `/billing/plans` now includes `capabilities` array per plan
- **Auth Response**: `UserResponse` now includes `feature_flags` dictionary
- **Frontend**:
  - `authStore.ts` enhanced with `featureFlags` on `User` and `hasFeature(key)` method
  - New hook: `useFeatureFlag.ts`
  - `api.ts` sends `X-API-Version: v1` header on all requests
- **API Boundary Markers**: `@internal` and `@public_ready` docstrings added to endpoints
- **Deferred to Phase 6.1–6.4**: B2B API, multi-tenancy, white-label, enterprise admin suite (backlogged with prerequisites)
- **Compatibility**: All Phase 1-5 endpoints preserved. Zero breaking changes.
- **Schema**: 1 Alembic migration added → 33 total tables, 9 total migrations.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.
