# Current Task — DeltaGrid

**Phase**: Production-ready MVP hardening ✅ PostgreSQL runtime READY
**Status**: Backend persistence переведён на PostgreSQL через `DATABASE_URL`, Alembic и Docker Compose. Добавлен production startup gate, readiness endpoint и минимальный server deployment flow для `deltagrid.pro`. Frontend MVP terminal `v1.2.0` сохранён без UI-изменений.
**Last Updated**: 2026-06-05

## PostgreSQL MVP Summary — 2026-06-05

- [x] PostgreSQL стал основным runtime persistence для backend.
- [x] Добавлен sync driver `psycopg[binary]`; async слой использует `asyncpg`.
- [x] Нормализованы DB URL для sync engine, async engine и Alembic.
- [x] `Base.metadata.create_all()` ограничен SQLite fallback для isolated tests.
- [x] Добавлена Alembic migration `3f0c2e5a7b91` для `backfill_jobs`.
- [x] Добавлена Alembic migration `7c1f2a8d9e34` для `BigInteger` timestamp-полей в data-layer/backtest.
- [x] `DataWriter` и `SymbolMapper` больше не создают production-схему вручную.
- [x] Docker Compose поднимает PostgreSQL 16 и запускает `alembic upgrade head` перед backend.
- [x] Обновлены инструкции запуска и архитектурная документация.
- [x] `DEBUG=false` блокирует слабые/dev secrets, пустой `VAULT_MASTER_KEY`, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS`.
- [x] `GET /api/v1/health/readiness` проверяет DB connectivity и соответствие Alembic revision source head.
- [x] Добавлены `.env.production.example`, `docker-compose.prod.yml` и `DEPLOYMENT.md`.
- [x] Frontend runtime proxy подготовлен к Docker deployment через `BACKEND_INTERNAL_URL`; WebSocket URL больше не привязан только к `127.0.0.1:8000`.
- [x] Docker build contexts очищены через `backend/.dockerignore` и `frontend/.dockerignore`.
- [x] Добавлены `deploy/nginx/deltagrid.conf.example` и `scripts/server-smoke.sh`.
- [x] Добавлены `scripts/server-preflight.sh` и `scripts/generate-production-env.sh`.
- [x] Deploy-шаблоны и документация привязаны к домену `deltagrid.pro`.
- [x] DNS preflight: `deltagrid.pro` и `www.deltagrid.pro` сейчас указывают на `31.31.196.50` / `2a00:f940:2:2:1:1:0:266`; HTTP отдаёт parking page REG.RU.
- [x] Серверный IP получен: `2.25.143.143`; SSH `22` открыт, HTTP `80` и HTTPS `443` пока закрыты.
- [x] Добавлены `scripts/bootstrap-ubuntu.sh`, `scripts/deploy-production.sh` и `deploy/dns/deltagrid.pro.md`.
- [x] Добавлен `scripts/configure-nginx-ssl.sh` для включения Nginx site и выпуска Let's Encrypt SSL.
- [x] SSH-доступ `root@2.25.143.143` по ключу подтверждён; production frontend port перенесён на `3001`, чтобы не трогать служебный процесс на `3000`.
- [x] DNS Cloudflare активирован: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`.
- [x] Реальный серверный rollout выполнен: `/opt/deltagrid`, `.env.production`, PostgreSQL, backend, frontend и Nginx.
- [x] HTTPS включён через Let's Encrypt; `https://deltagrid.pro` и `https://www.deltagrid.pro` отвечают.
- [x] Server smoke-check через HTTPS прошёл; основные frontend pages и API routes возвращают `200`.
- [x] Cloudflare proxy + SSL mode `Full (strict)` включены и проверены; WebSocket route проходит через Cloudflare.

## Следующая итерация

- [x] Прогнать `alembic upgrade head` на PostgreSQL БД в Docker.
- [x] Сделать smoke-check backend routes: `/health`, `/data/health`, `/data/ohlcv`, `/market/trending`.
- [x] Проверить frontend against backend после запуска PostgreSQL окружения.
- [x] Добавить production readiness gate для env/DB/migrations.
- [x] Подготовить server deployment checklist: migrations, readiness, reverse proxy, SSL, backups.
- [x] Получить SSH-команду и учётные данные для `2.25.143.143`.
- [x] Перенастроить DNS `deltagrid.pro` на `2.25.143.143`.
- [x] На реальном сервере создать staging/prod `.env.production` с production secrets (`SECRET_KEY`, `VAULT_MASTER_KEY`) для `deltagrid.pro`.
- [x] Прогнать server preflight на сервере.
- [x] Настроить Nginx/SSL на сервере после DNS cutover.
- [x] Проверить reverse proxy/SSL на `deltagrid.pro` по `DEPLOYMENT.md`.
- [x] Прогнать smoke-check на сервере локально и через домен.
- [x] Проверить Cloudflare proxy, `Full (strict)` и WebSocket после включения оранжевого облака.
- [ ] Добавить email к Let's Encrypt account для уведомлений о продлении сертификата.
- [ ] После согласования времени выполнить reboot сервера из-за pending kernel upgrade.

## Frontend MVP Summary — 2026-06-04

- [x] App shell: left sidebar + top workspace tabs.
- [x] Sidebar MVP: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
- [x] Nested nav для Perp DEX и Funding.
- [x] Typed mock data adapter под будущие CoinGecko/CoinGlass integrations.
- [x] Market Overview / Command Center без funding-heavy блоков.
- [x] Perp DEX Intelligence без полноценного Funding dashboard.
- [x] Funding Overview как first-class module.
- [x] Asset Deep Dive SOL.
- [x] Market Matrix без funding metric / Funding Matrix.
- [x] Strategy Lab / Backtest.
- [x] Charts placeholder без новых зависимостей.
- [x] Frontend build: `npm run build` проходит.

## Следующая frontend-итерация

- [ ] Подключить `lightweight-charts` и реализовать полноценный Charts screen.
- [ ] Согласовать frontend adapter contracts с backend/data-layer endpoint'ами.
- [ ] Добавить ручной visual QA checklist по 6 MVP-экранам.

## Phase 6 Summary (ARCHITECTURE HARDENING)

Phase 6 is split into incremental sub-phases:

### Phase 6.0 — Foundation & Boundaries ✅ COMPLETED
- [x] Alembic migration `b19c6344f081` — `plan_capabilities`, `feature_flags` tables + `users` alterations
- [x] `CapabilityService` — plan-based feature gating with user-level overrides
- [x] `RequestIDMiddleware` — `X-Request-ID` tracing on all requests
- [x] Global exception handler — `DeltaGridException` hierarchy wired into FastAPI
- [x] CORS hardening — env-aware method/header restrictions + `expose_headers`
- [x] Health endpoint enhanced with `api_version`, `api_tier`
- [x] Billing `/plans` now returns capabilities per plan
- [x] Auth response includes `feature_flags` for authenticated users
- [x] Frontend: `useFeatureFlag` hook, `hasFeature` in authStore, `X-API-Version` header
- [x] API boundary markers — `@internal` / `@public_ready` docstrings on endpoints

### Phase 6.1 — B2B API Foundation 📋 DEFERRED
- [ ] API key generation and storage
- [ ] API key auth middleware
- [ ] Rate limiting by tier
- [ ] B2B router prefix `/api/b2b/v1/`
- [ ] Webhook subscription system

### Phase 6.2 — Multi-Tenancy 📋 DEFERRED
- [ ] `organizations` and `organization_members` tables
- [ ] Tenant-scoped query filter
- [ ] Org admin endpoints

### Phase 6.3 — White-Label 📋 DEFERRED
- [ ] `BrandConfig` abstraction
- [ ] Config-driven sidebar theming
- [ ] Custom domain support

### Phase 6.4 — Enterprise Admin Suite 📋 DEFERRED
- [ ] Admin dashboard
- [ ] Usage analytics and quotas

## Phase 6 Database Schema (2 New Tables + 1 Altered)
- `plan_capabilities` — Plan → feature mapping (41 seeded rows: free/pro/enterprise)
- `feature_flags` — User-level feature overrides with expiration
- `users` — altered: `feature_flags_json`, `plan_started_at`, `plan_expires_at`

## Regression Test Results
- [x] Scanner: GET /api/v1/scanner — operational
- [x] Market Dashboard: all endpoints respond
- [x] Auth: register, login, refresh, me — all pass (feature_flags included)
- [x] Execution: exchange accounts, risk rules, order intents — preserved
- [x] Stream: config, WebSocket, SSE — operational
- [x] Alerts: rules CRUD, events list — operational
- [x] Notifications: preferences CRUD — operational
- [x] RWA: GET /rwa/assets, categories, compare — operational
- [x] Treasury: GET /treasury/entities, btc-holdings, platforms — operational
- [x] Billing: GET /billing/plans — now includes capabilities
- [x] Health: GET /health — returns api_version, api_tier, X-Request-ID header
- [x] Frontend Build: `npm run build` — 0 TS errors
- [x] Backend Startup: `uvicorn app.main:app` — clean start
- [x] Alembic: all 9 migrations applied successfully

## URL разработки
- Frontend: http://127.0.0.1:3000
- Backend API: http://127.0.0.1:8000
- Readiness: http://127.0.0.1:8000/api/v1/health/readiness
- Scanner: http://127.0.0.1:3000/
- Market Dashboard: http://127.0.0.1:3000/market
- Exchange Accounts: http://127.0.0.1:3000/exchange-accounts
- Execution: http://127.0.0.1:3000/execution
- Risk Rules: http://127.0.0.1:3000/risk-rules
- Alerts: http://127.0.0.1:3000/alerts
- Notifications: http://127.0.0.1:3000/notifications
- RWA: http://127.0.0.1:3000/rwa
- Treasury: http://127.0.0.1:3000/treasury
