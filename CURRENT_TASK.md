# Current Task — DeltaGrid

**Phase**: 6 (Architecture Hardening) ✅ IN PROGRESS  
**Status**: Phase 6.0 foundation complete. Capability system, middleware, and extension points delivered.  
**Last Updated**: 2026-05-16

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
- Scanner: http://127.0.0.1:3000/
- Market Dashboard: http://127.0.0.1:3000/market
- Exchange Accounts: http://127.0.0.1:3000/exchange-accounts
- Execution: http://127.0.0.1:3000/execution
- Risk Rules: http://127.0.0.1:3000/risk-rules
- Alerts: http://127.0.0.1:3000/alerts
- Notifications: http://127.0.0.1:3000/notifications
- RWA: http://127.0.0.1:3000/rwa
- Treasury: http://127.0.0.1:3000/treasury
