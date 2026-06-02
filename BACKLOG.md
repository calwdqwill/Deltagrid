# Backlog — DeltaGrid

## Standalone HTML Preview — 2026-06-02
- [x] Создать `frontend/preview/index.html` как backend-free Market Scanner preview с mock-данными, фильтрами и кликабельными строками.
- [x] Создать `frontend/preview/asset.html` с asset summary, табами и переходом в Strategy Lab.
- [x] Создать `frontend/preview/strategy-lab.html` с selector стратегий, параметрами backtest и disabled execution state.
- [x] Создать `frontend/preview/data-health.html` со статусом провайдеров данных.
- [x] Добавить `frontend/preview/styles.css` с dark theme, responsive rules, hover states и позитивной/негативной окраской метрик.
- [ ] Подключить preview-flow к реальному backtest engine после готовности Phase 7 data/backtesting layer.

## MVP UI Navigation — 2026-06-02
- [x] Скрыть из sidebar разделы вне текущего MVP: paper-trading, execution, exchange-accounts, risk-rules, RWA, treasury, billing, options, social/news, advanced-alerts.
- [x] Добавить placeholder-страницы `/strategy-lab`, `/backtests`, `/data-health`.
- [x] Показать в sidebar только Market, Strategy Lab, Backtests, Data Health, Watchlist и Settings.
- [x] Добавить простой mock-индикатор свежести данных на `/market`.

## Codex Technical Review — 2026-05-20
- [x] Проверить frontend production build (`npm run build`) и базовые TypeScript ошибки.
- [x] Проверить backend import/compile, `pip check`, Alembic current и `/api/v1/health` через TestClient.
- [x] Исправить persisted auth rehydration и JWT refresh response transform.
- [x] Исправить async SQLite URL в `async_database.py`.
- [x] Исправить Docker Compose persistence/CORS и отсутствие `frontend/public`.
- [ ] Настроить полноценный frontend lint: добавить ESLint config и devDependencies (`eslint`, `eslint-config-next`) с обновлением lock-файла.
- [ ] Восстановить проектные управляющие документы по текущим правилам: `AGENTS.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md` либо явно задокументировать замену на `CURRENT_TASK.md` и `DATA_ARCHITECTURE.md`.
- [ ] Подготовить отдельную задачу на разделение sync/async persistence перед реальным переходом на PostgreSQL.
- [ ] Добавить минимальные автоматические backend regression tests без требования предварительно запущенного сервера.
- [ ] Пройти UI/i18n sweep: убрать hardcoded English labels в защищённых dashboard-страницах.

## Phase 1 MVP Scanner ✅ DONE
- [x] Backend FastAPI scaffolding
- [x] CoinGecko adapter + mock fallback
- [x] Perp DEX adapters (HL/AST/LTR stubs via CG)
- [x] SpreadCalculator + SignalClassifier
- [x] Scanner API endpoints
- [x] Preferences API (favorites, pinned, settings)
- [x] SQLite persistence
- [x] Next.js 14 frontend setup
- [x] Scanner table with search/sort/filter
- [x] Detail drawer + detail page
- [x] Settings page (language, thresholds, fees)
- [x] RU/EN i18n
- [x] KPI cards
- [x] Docker + docker-compose

## Phase 1 — Known Issues / Tech Debt
- [ ] CoinGecko Demo tier rate limits — на production нужен Analyst ($103/mo)
- [ ] Perp DEX adapters сейчас CG-backed, нужны direct API в Phase 3
- [ ] Scanner table scroll performance при 100+ записях
- [ ] Добавить retry logic с exponential backoff для CG API
- [ ] Добавить логирование (structured logging)

## Phase 2 — Auth + Paper Trading + Revenue ✅ DONE
- [x] Auth: Email + password (JWT, register/login, bcrypt)
- [x] Auth: Telegram OAuth — POSTPONED to Phase 4
- [x] Auth: Web3 Wallet (MetaMask) — POSTPONED to Phase 4
- [x] JWT middleware (optional, non-blocking for public routes)
- [x] Paper Trading Dashboard ($10K demo)
- [x] VirtualBalance service
- [x] StrategyExecutor (Z-Score, Basis, Cross-exchange) — backend ready
- [x] PerformanceTracker (P&L, Sharpe, win rate, max drawdown) — backend ready
- [x] ReferralSystem (code generation) — backend ready
- [x] BillingService (plans definitions) — backend ready
- [x] PaymentProcessor (Cryptomus, Stripe) — POSTPONED to Phase 4
- [x] Signal Marketplace (buy/sell signals) — POSTPONED to Phase 4
- [x] User Profile (LК, 3 раздела)
- [x] PostgreSQL-ready engine + Alembic migrations
- [x] Redis cache abstraction (Upstash-ready)
- [x] Telegram Bot alerts — POSTPONED to Phase 4
- [x] **CRITICAL FIXES**: singleton cache, IPv6 timeout, auth argument order, JWT validation

## Phase 3 — Execution Foundation + Connectors ✅ DONE

### ✅ Quick Wins (A+B+F+G) — COMPLETED 2026-05-14
- [x] **Market Overview Dashboard** (trending, gainers, losers, global stats)
- [x] **Fear & Greed Index** (alternative.me API)
- [x] **New Listings** (filter from trending)
- [x] **Funding Rates** (placeholder/mock)

### ✅ Increment A — Foundation & Security — COMPLETED 2026-05-15
- [x] Alembic migrations (Phase 1/2 baseline + Phase 3 tables: 11 новых таблиц)
- [x] `SecretsVaultService` — Fernet AES-256 encryption для API ключей
- [x] `ExchangeAccountService` — CRUD аккаунтов + encrypted key storage (backend-only)
- [x] Connector capabilities registry — 5 бирж seeded (Binance, Bybit, OKX, Hyperliquid, Aster)
- [x] Frontend: `/exchange-accounts` page, `AddExchangeModal`, sidebar nav
- [x] Endpoints: `GET/POST/DELETE /exchange-accounts`, `POST /exchange-accounts/{id}/keys`, `GET /connectors/capabilities`

### ✅ Increment B — Order Intent Pipeline + Risk Manager — COMPLETED 2026-05-15
- [x] `RiskManager` — CRUD rules, kill-switch, position sizing, max exposure, dry-run checks
- [x] `ExecutionService` — order intent lifecycle (intent → risk_check → pending_confirmation → submitted/failed)
- [x] Safe defaults: `is_live=False` rejects orders, explicit opt-in required
- [x] Frontend: `/execution` dashboard, `/risk-rules` page, `OrderIntentModal` integrated into ScannerRow
- [x] Audit trail: `order_events` + `audit_logs` для каждого действия
- [x] Endpoints: `/execution/intents`, `/execution/orders`, `/risk/rules`, `/risk/check`

### ✅ Increment C — Connector Foundation — COMPLETED 2026-05-15
- [x] `ExchangeConnector` ABC + `ConnectorRegistry` runtime discovery
- [x] `BinanceConnector` — REST spot API (account info, ticker, place/cancel/get order)
- [x] `OrderManager` — retry 3x exponential backoff, partial fill handling, status sync
- [x] Execution-to-connector bridge через `confirm_intent(is_live=True)`

### ✅ Increment D — Additional CEX Connectors — COMPLETED 2026-05-15
- [x] `BybitConnector` — V5 unified API (ticker, account, place order, status)
- [x] `OKXConnector` — REST API с passphrase support

### ✅ Increment E — Perp DEX + Kill Switch + Sessions — COMPLETED 2026-05-15
- [x] `HyperliquidConnector` — direct REST (`allMids`, clearinghouse state, wallet signing placeholder)
- [x] `AsterConnector` stub для future expansion
- [x] Kill switch: `POST /risk/rules/{id}/toggle` быстрая активация
- [x] Execution sessions: `GET/POST /execution/sessions`, `POST /execution/sessions/{id}/stop`
- [x] Frontend: Session start/stop buttons на Execution dashboard

### Phase 3 Final Fixes — COMPLETED 2026-05-15
- [x] LoginModal `data.accessToken` fix (camelCase из transformResponse)
- [x] Sidebar fix — `/execution`, `/exchange-accounts`, `/risk-rules` обёрнуты в `<Shell>`
- [x] Port 8000 conflict — zombie python processes killed
- [x] Empty Alembic initial migration — fixed via seed + proper Phase 3 migration
- [x] Backend + frontend servers restarted and operational

## Phase 4 — Scale + Live Features ✅ DONE

### ✅ Increment A — Tech Debt Remediation
- [x] Fix `httpx.AsyncClient` leaks: explicit `close()` in all 5 connectors + `OrderManager`
- [x] Cache upgrade: FIFO → LRU via `OrderedDict`, cache invalidation on preference changes
- [x] `PreferenceService`: explicit session lifecycle, no unmanaged `SessionLocal()`
- [x] Dual-token auth: access + refresh tokens, `/auth/refresh` endpoint, frontend auto-refresh on 401

### ✅ Increment B — Provider Layer & Enrichments
- [x] `CoinGlassClient` + `GeckoTerminalClient` with rate-limit awareness and graceful fallback
- [x] `ProviderHealthMonitor` + `provider_health` table + `provider_sync_logs`
- [x] Hardcoded funding rates replaced with CoinGlass-backed data + fallback mock with `data_status: fallback`
- [x] New endpoints: `GET /market/enrichments`, `GET /health/providers`

### ✅ Increment C — Realtime Streaming Foundation
- [x] `WebSocketManager`: Binance public ticker stream, reconnect/backoff, heartbeat
- [x] `NormalizedStreamEvent`: unified ticker DTO across exchanges
- [x] WebSocket endpoint `/api/v1/stream/ws` + SSE fallback `/api/v1/stream/sse`
- [x] Frontend: `useRealtime` hook, `streamStore` (isolated from polling), `RealtimeIndicator` component
- [x] Tables: `realtime_feed_sessions`, `stream_events`

### ✅ Increment D — Alerting Engine
- [x] `AlertService`: rule CRUD, evaluation, deduplication (hash-based), cooldown
- [x] `NotificationService`: email/web-push/Telegram delivery stubs with logged fallback
- [x] New endpoints: `/alerts/rules`, `/alerts/events`, `/notifications/preferences`, `/notifications/web-push/*`
- [x] Frontend: `/alerts` page with "Add Rule" form, `/notifications` page with working toggles
- [x] Frontend: `useAlerts`, `useNotifications` hooks (snakeToCamel fix applied)
- [x] Tables: `alert_rules`, `alert_events`, `alert_deliveries`, `notification_preferences`

### ✅ Increment E — Security Hardening & Auth Extensions
- [x] `User.session_version` for global logout capability
- [x] Telegram OAuth: `/auth/telegram` endpoint
- [x] Web3 login: `/auth/web3/challenge` + `/auth/web3/verify` endpoints
- [x] Frontend: Telegram + Web3 login buttons in `LoginModal` (Coming Soon stubs)

### Phase 4 Final Fixes — COMPLETED 2026-05-16
- [x] `useNotifications.ts` — `snakeToCamel` transform fix для toggle responsiveness
- [x] `useAlerts.ts` — `snakeToCamel` transform fix
- [x] `/alerts` page — форма создания правила с кнопкой "Add Rule"
- [x] Frontend сервер перезапущен для применения изменений

## Phase 5 — RWA + Treasuries ✅ DONE

### ✅ Increment A — Foundation & Provider Wiring
- [x] Alembic migration `b6fa1801e11d` — 5 новых таблиц (`rwa_assets`, `rwa_asset_snapshots`, `treasury_entities`, `treasury_snapshots`, `tokenization_platforms`)
- [x] Alembic migration `f99eef8f0f6c` — `rwa_alerts_enabled` в `notification_preferences`
- [x] `BaseRwaAdapter` ABC + `CoinGeckoRwaAdapter`
- [x] `RwaAssetService` + `TreasuryService` с async cache
- [x] Pydantic schemas: `rwa.py` + `treasury.py`
- [x] Header route-aware: title по pathname, status badge только на scanner

### ✅ Increment B — RWA Asset Data & Gold Tokens
- [x] `GET /rwa/assets`, `GET /rwa/assets/{id}`, `GET /rwa/assets/{id}/snapshots`, `GET /rwa/categories`, `GET /rwa/compare`
- [x] Seeded: XAUT, PAXG, BUIDL, USDY, CFG
- [x] Frontend: `/rwa` page с категориями, таблица, source/freshness badges
- [x] Detail page: `/rwa/[id]`

### ✅ Increment C — Treasury Entities & BTC Holdings
- [x] `GET /treasury/entities`, `GET /treasury/entities/{id}`, `GET /treasury/entities/{id}/snapshots`, `GET /treasury/btc-holdings`, `GET /treasury/platforms`
- [x] Seeded: MicroStrategy, MARA, Tesla, Block
- [x] Frontend: `/treasury` page с Companies/Platforms tabs, leaderboard
- [x] Detail page: `/treasury/[id]`

### ✅ Increment D — Tokenization Platforms & Detail Views
- [x] Seeded: Centrifuge, Figure, Maple Finance
- [x] Platform cards: TVL, blockchain, governance token
- [x] Detail views for RWA assets + Treasury entities

### ✅ Increment E — Alert Compatibility & Polish
- [x] Migration: `rwa_alerts_enabled` в `notification_preferences`
- [x] Frontend toggle на `/notifications`
- [x] AlertService поддерживает `rwa_price_threshold`, `treasury_holdings_change`
- [x] RU/EN i18n для RWA/Treasury
- [x] Sidebar: RWA + Treasury links
- [x] Frontend build: 0 TS errors

## Phase 6 — Enterprise + B2B 🚀 IN PROGRESS

### ✅ Phase 6.0 — Architecture Hardening — COMPLETED 2026-05-16
- [x] Audit текущей архитектуры и risk map
- [x] Alembic migration `b19c6344f081` — `plan_capabilities`, `feature_flags` tables + `users` alterations
- [x] `CapabilityService` — plan-based feature gating (`check`, `get_limit`, `list_capabilities`)
- [x] `FeatureFlagService` — user-level overrides with expiration
- [x] `RequestIDMiddleware` — `X-Request-ID` tracing on all requests
- [x] Global exception handler — `DeltaGridException` hierarchy wired into FastAPI
- [x] CORS hardening — env-aware method/header restrictions + `expose_headers`
- [x] Health endpoint enhanced with `api_version`, `api_tier`
- [x] Billing `/plans` now returns capabilities per plan (41 seeded rows)
- [x] Auth response includes `feature_flags` for authenticated users
- [x] Frontend: `useFeatureFlag` hook, `hasFeature` in authStore, `X-API-Version` header
- [x] API boundary markers — `@internal` / `@public_ready` docstrings

### Phase 6.1 — B2B API Foundation 📋 DEFERRED
- [ ] API key generation and storage (`api_keys` table)
- [ ] API key auth middleware (alternative to JWT)
- [ ] Rate limiting by tier (SlowAPI or custom)
- [ ] Mark public-ready endpoints with `@public_api` decorator
- [ ] B2B router prefix `/api/b2b/v1/`
- [ ] Webhook subscription system (`webhook_endpoints` table)
- [ ] Request/response logging for external API calls

### Phase 6.2 — Multi-Tenancy 📋 DEFERRED
- [ ] `organizations` table
- [ ] `organization_members` table
- [ ] Add `organization_id` nullable FK to tenant-scoped tables
- [ ] `TenantScopeService` for query filtering
- [ ] Org admin endpoints (invite members, remove members, set roles)
- [ ] Row-level security enforcement
- [ ] Organization-level billing (subscription per org, not per user)

### Phase 6.3 — White-Label 📋 DEFERRED
- [ ] `brand_configs` table (org-scoped)
- [ ] `BrandProvider` React context
- [ ] Config-driven sidebar branding
- [ ] Custom domain CORS and routing
- [ ] Injected custom CSS endpoint
- [ ] White-label feature gate (Enterprise plan only)

### Phase 6.4 — Enterprise Admin Suite 📋 DEFERRED
- [ ] Admin dashboard (/admin)
- [ ] User management (impersonation, deactivation)
- [ ] Org provisioning workflow
- [ ] Usage analytics and quotas
- [ ] Priority support ticketing integration

## Known Tech Debt (не блокирует разработку)
- [x] `httpx.AsyncClient` leaks — FIXED in Phase 4A
- [x] Sync DB sessions в async endpoints — acceptable for current scale
- [x] `PreferenceService` создаёт свой `SessionLocal()` — FIXED in Phase 4A
- [x] FIFO eviction в кэше вместо LRU — FIXED in Phase 4A
- [x] Кэш не инвалидируется при изменении preferences — FIXED in Phase 4A
- [ ] Binance WebSocket heartbeat timeouts — reconnect works, non-critical
- [ ] `deltagrid.db` SQLite — migrate to PostgreSQL for production
