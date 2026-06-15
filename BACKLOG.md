# Backlog — DeltaGrid

## Release / CI-CD — 2026-06-14
- [x] Зафиксировать текущую production-ready версию как `v1.3.0`.
- [x] Добавить `VERSION` и `RELEASES.md`.
- [x] Добавить GitHub Actions CI для backend tests, `compileall` и frontend build.
- [x] Добавить GitHub Actions deploy workflows для `preview` и `main`.
- [x] Подготовить отдельный preview stack contract: `.env.preview.example`, Compose project `deltagrid-preview`, ports `8011/3012`.
- [x] Добавить общий `scripts/deploy-compose-stack.sh` для ручного и GitHub deploy production/preview.
- [x] Подготовить runbook для GitHub deploy secrets: `deploy/github-actions-secrets.md`.
- [x] Создать dedicated SSH deploy key и добавить public key на VPS для GitHub Actions.
- [x] Перенести актуальные deploy workflows и ops runbooks в `main`, чтобы default-branch GitHub Actions использовал корректный preview/prod deploy path.
- [x] Проверить preview deploy workflow probe: workflow запускается после CI, но безопасно пропускает deploy без GitHub secrets.
- [x] Настроить и проверить GitHub repository secrets `PREVIEW_*` для preview auto-deploy.
- [x] Проверить preview auto-deploy end-to-end через GitHub Actions: deploy key fingerprint, SSH login, `/opt/deltagrid-preview`, deploy step и server smoke.
- [x] Усилить preview deploy workflow после flaky GitHub runner: TCP port probe warning-only, SSH login с timeout/keepalive и retry.
- [x] Стабилизировать preview deploy SSH retry path после flaky `Test preview SSH login`: commit `4c3dec0`, CI success, `Deploy Preview` run `27532247102` success, `/opt/deltagrid-preview` healthy.
- [x] Перевести diagnostic SSH login/app-dir checks в deploy workflows в warning-only режим и оставить реальным gate сам deploy step с 3 retry.
- [x] Подготовить hardening `Deploy Production` workflow в `preview`: secret diagnostics, fingerprint, expected values, SSH retry и app-dir check.
- [ ] Настроить и проверить GitHub repository secrets `PROD_*` для production auto-deploy отдельной безопасной итерацией.
- [ ] Перенести production deploy hardening в `main` и проверить, что `Deploy Production` делает реальный deploy, а не safe-skip.
- [x] Поднять отдельный dev/staging стенд на VPS в `/opt/deltagrid-preview`.
- [x] Подготовить DNS/Nginx/SSL runbook и template для `preview.deltagrid.pro`.
- [x] Включить preview Nginx HTTP site `deltagrid-preview` на VPS и проверить routing через `Host: preview.deltagrid.pro`.
- [ ] Добавить DNS-запись `preview.deltagrid.pro` и выпустить Let's Encrypt SSL через `scripts/configure-preview-nginx-ssl.sh`.
- [x] Разобраться с Docker Compose name-conflict при ручном preview deploy/recreate backend: deploy script теперь делает build до остановки сервисов и явно пересоздаёт только `backend/frontend`.
- [x] Перевести production `/opt/deltagrid` на чистый `main` checkout после push baseline.
- [x] Восстановить `AGENTS.md` как проектные правила для Codex/AI-агентов.

## MVP1 — Data Quality Gate / Provider Reliability — 2026-06-13
- [x] P0: Устранить production-блокер Binance Futures API `451` на текущем VPS: primary CEX perp provider выбран как OKX USDT Swap без прокси/VPN.
- [x] P0: Добавить `OkxAdapter` для OHLCV, funding history, OI snapshots и long/short account ratio.
- [x] P0: Переключить terminal frontend read-side с `binance` на `okx` для primary persisted streams.
- [x] P0: Задеплоить OKX primary flow на `deltagrid.pro` и выполнить ручной sync `BTC,ETH,SOL` за 24 часа.
- [x] P0: Проверить, что `/api/v1/data/health` показывает provider `okx`, свежие `provider_sync_runs` и что `/data/ohlcv?exchange=okx` отдаёт актуальные BTC/ETH/SOL candles.
- [x] P0: Перевести CoinGlass liquidation и snapshot-запросы на `exchange_list=OKX` при OKX primary, чтобы enrichment-слой не оставался скрыто привязанным к Binance.
- [x] P0: Выполнить контрольный 24h backfill BTC/ETH/SOL по `1m/5m/1h` через OKX и проверить `gaps=0`.
- [x] P0: Добавить freshness SLA в `/api/v1/data/health`: latest timestamp, age minutes, expected cadence и статус `fresh/stale/degraded` по `symbol + exchange + stream + interval`.
- [x] P0: Разделить health по `sync_type`, чтобы `/data/health` показывал состояние OHLCV, funding, OI, long/short, liquidations и basis отдельно, а не только последний sync провайдера.
- [x] P0: Добавить cron/data-sync diagnostics для `/data-health`: последний запуск, последний успешный запуск, records fetched/inserted, error class (`451`, rate limit, circuit breaker, empty response).
- [x] P0: Задеплоить data quality gate на `deltagrid.pro` и проверить production `/api/v1/data/health`, `/data-health` и cron-path после деплоя.
- [x] P1: Расширить backfill BTC/ETH/SOL до 72h/7d и проверить gaps по `1m/5m/1h` перед interactive charts.
- [x] P1: Провести инвентаризацию coverage matrix по BTC/ETH/SOL: OHLCV, funding, OI, long/short, liquidations, basis, spot/perp price.
- [x] P1: Сформировать production universe v1 для текущего MVP universe: readiness статусы `complete_history/core_perp_ready/partial_history/not_ready` поверх coverage/freshness.
- [x] P1: Реализовать локальный interactive charts v0 на `lightweight-charts` после прохождения data freshness gate.
- [x] P1: Задеплоить charts v0 на `deltagrid.pro` и проверить `/charts?symbol=BTC&interval=1m&range=7d` через домен.
- [x] P1: Задеплоить sparse liquidation freshness fix: для `liquidations` различать отсутствие свежих событий и свежесть `coinglass/liquidations` sync-run.
- [x] P1: Задеплоить отдельный backend window endpoint для OHLCV и убрать client-side pagination из основного `/charts` path.
- [x] P1: Обновить `next` до `15.5.19` и мигрировать App Router `searchParams`; critical/high advisory для `next@14.1.0` закрыты, production build проходит.
- [x] P1: Проверить Next.js 16 stable для остаточного PostCSS advisory: `next@16.2.9` всё ещё использует bundled `postcss 8.4.31`, поэтому production-safe апгрейд не закрывает `moderate`.
- [x] P1: Добавить provider inventory v0 через `GET /api/v1/data/provider-inventory`: read-only persisted-data кандидаты на расширение universe без внешних API-вызовов.
- [x] P1: Провести внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper` и sync universe: preview/VPS показал `20/20 eligible_for_24h_sync_dry_run`, Binance legacy остаётся `HTTP 451`.
- [x] P1: Подготовить `SymbolMapper`/alias expansion plan для первой малой группы `HYPE/XRP/DOGE/ADA/LINK`.
- [x] P1: Выполнить 24h sync dry-run первой малой группы на preview без расширения UI и проверить errors/gaps/coverage: `fetched=9035`, `inserted=8986`, `errors=0`, OHLCV gaps `0`, 24h coverage `missing=0`.
- [x] P1: Расширить freshness SLA scope для первой малой группы или явно отделить candidate freshness от current UI universe freshness: `/data/provider-inventory` использует `freshness_scope=requested_symbols`, а `/data/health` остаётся scoped к текущему UI universe `BTC/ETH/SOL`.
- [x] P1: Выполнить 72h/7d preview backfill первой малой группы и проверить gaps/coverage перед расширением UI universe: 72h `errors=0`, 7d `errors=0`, OHLCV gaps `0`, chart path готов.
- [x] P1: Включить `HYPE/XRP/DOGE/ADA/LINK` как preview chart/asset candidates в `/charts` и `/assets`; оставить `Market Matrix`, `Arbitrage Scanner` и `Perp DEX` scoped к `BTC/ETH/SOL` до full promotion.
- [x] P1: Добавить явную диагностику `chart_ready_candidates` в provider inventory и ручной `scripts/preview-candidate-smoke.sh` для проверки preview candidate paths.
- [x] P1: Добавить детальные `promotion_blockers` в provider inventory: `coverage_blockers_7d`, `freshness_blockers` и summary-счётчики причин, блокирующих full analytics promotion.
- [x] OPS/P1: Подготовить preview-safe market sync cron path через `ENV_FILE=.env.preview`, `COMPOSE_PROJECT_NAME=deltagrid-preview`, отдельный cron-файл и отдельный лог.
- [ ] P1: Закрыть `history_completion_required=5` для `HYPE/XRP/DOGE/ADA/LINK` по partial snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price` или явно утвердить policy-разделение `chart_ready` и full analytics universe.
- [x] P1: Добавить CI audit gate `npm audit --audit-level=high`, чтобы high/critical frontend advisory снова не прошли в `preview/main`.
- [ ] P1: Дождаться stable Next.js с bundled `postcss >=8.5.10` или другого upstream patch; `next@canary` не использовать в production path без отдельного решения.
- [ ] P2: Подготовить настоящий backtest engine после стабилизации исторических рядов и формального описания формул PnL/drawdown/trades.

## Production Ops — 2026-06-05
- [x] Развернуть `deltagrid.pro` на сервере `2.25.143.143` с PostgreSQL, backend, frontend, Nginx и Let's Encrypt SSL.
- [x] Проверить HTTPS smoke-check, основные frontend pages и API routes.
- [x] В Cloudflare включить proxy + SSL mode `Full (strict)` и проверить frontend/API/WebSocket.
- [x] Добавить ручной production sync market data из Binance USD-M в PostgreSQL.
- [x] Выполнить первый production sync market data и проверить `/api/v1/data/health` через домен.
- [x] Задеплоить демо-доводку live UI на `deltagrid.pro`: графики со шкалами, price-first heatmap и переключение BTC/ETH/SOL в `Assets`.
- [x] Добавить CoinGecko/CoinGlass provider API keys в server `.env.production`.
- [x] Перевести CoinGlass client на v4 endpoint/header для production health и funding enrichments.
- [x] Расширить production sync до CoinGlass funding/OI snapshots и CoinGecko-derived basis snapshots.
- [x] Добавить host-level cron для регулярного market data sync.
- [x] Стабилизировать live SSR-потоки: снизить параллельность frontend-запросов, добавить timeout и env-настройки DB pool.
- [x] Подключить CoinGlass aggregated liquidation history к production sync и таблице `liquidations`.
- [ ] Добавить email к Let's Encrypt account для уведомлений о продлении сертификата.
- [ ] После согласования окна обслуживания выполнить reboot сервера из-за pending kernel upgrade.
- [ ] Настроить минимальный внешний uptime/health monitoring для `https://deltagrid.pro/api/v1/health/readiness`.
- [ ] Ввести регулярный backup PostgreSQL volume перед миграциями и деплоем.
- [ ] Если для стратегии потребуется точность выше MVP, подключить отдельный per-order liquidation tape вместо агрегированных CoinGlass USD-снимков.

## Data Coverage / Next Iteration — 2026-06-05
- [x] Реализовать первый interactive historical charts layer на `lightweight-charts`: crosshair tooltip, pan/zoom/scroll, выбор диапазона `2h/8h/24h/7d`, чтение проверенной OKX истории и честный empty-state для потоков без истории.
- [x] Пройти production QA для charts layer: доменный smoke-check и Browser QA desktop/mobile.
- [x] Довести charts layer после production QA: backend window endpoint добавлен, `/charts` проверен, coverage matrix подготовлена перед расширением universe.
- [x] Провести provider inventory v0 по persisted data: `GET /api/v1/data/provider-inventory` показывает candidate symbols, coverage/freshness readiness, `promotion_candidate` и `next_action`.
- [x] Провести внешнюю инвентаризацию perp-инструментов по CoinGlass, CoinGecko, OKX и legacy Binance: для каждого symbol зафиксировать OKX core, CoinGlass enrichment, CoinGecko spot и Binance legacy status.
- [x] Засеять aliases и выполнить 24h preview dry-run для первой малой группы `HYPE/XRP/DOGE/ADA/LINK` без изменения UI.
- [ ] Сформировать production universe для дашборда: топ-30 crypto assets плюс RWA-кандидаты, отдельно пометить активы с полной историей и активы только со spot/market данными.
- [ ] Расширить `SymbolMapper` и sync-конфигурацию только после coverage-матрицы, чтобы не показывать в UI активы без честных backend data streams.
- [ ] Подготовить RWA coverage map: tokenized commodities, treasuries, equities/stock-like assets, доступные источники CoinGecko/CoinGlass/прочие provider'ы и ограничения по истории.

## Frontend MVP Terminal — 2026-06-04
- [x] Перевести основной frontend shell на тёмный terminal layout: left sidebar, top workspace tabs, search и compact controls.
- [x] Обновить sidebar под MVP-разделы: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
- [x] Добавить nested navigation с tree-line для Perp DEX и Funding.
- [x] Добавить typed mock data adapter в `frontend/src/lib/terminal`, подготовленный под будущую замену на CoinGecko/CoinGlass data providers.
- [x] Реализовать Market Overview / Command Center без Funding Heatmap, Funding Arbitrage, Funding Matrix и Long/Short funding legs.
- [x] Реализовать Perp DEX Intelligence без полноценного Funding dashboard; оставить только link-card в Funding.
- [x] Реализовать Funding Overview как first-class module с funding matrix, history, arbitrage opportunities, predicted funding и long/short legs.
- [x] Реализовать Asset Deep Dive для SOL с compact funding metric без полноценного funding screen.
- [x] Реализовать Market Matrix без funding metric и Funding Matrix.
- [x] Реализовать Strategy Lab / Backtest на mock data.
- [x] Добавить Charts placeholder без новых зависимостей.
- [x] Добавить Arbitrage Scanner route как non-funding scanner.
- [x] Реализовать Charts v0 на `lightweight-charts`: price candles, volume, OI, basis и Funding/long-short панели без превращения Charts в funding strategy module.
- [x] Подключить Funding frontend screen к persisted backend/data-layer endpoint'ам для `funding_rates` и data health.
- [x] Подключить `/data-health` frontend screen к `GET /api/v1/data/health` вместо placeholder/mock-состояния.
- [x] Сделать nested tabs в `Funding` и `Perp DEX` кликабельными через стабильный `view` query-param.
- [x] Подключить `Market Overview` к live backend endpoints вместо `terminalDataAdapter`.
- [x] Подключить `Assets` к live SOL spot/funding/OHLCV и убрать fake order book/liquidations из production UI.
- [x] Открыть read-only endpoint'ы для `open_interest`, `long_short_ratio`, `basis_premium` и `liquidations`.
- [x] Подключить Charts, Market Matrix и Arbitrage Scanner к live persisted data streams.
- [x] Демо-доводка графиков: добавить `Last`/`Range`, числовые оси, price-first heatmap, логотипы CoinGecko и переключение BTC/ETH/SOL в `Assets`.
- [x] Быстрая демо-доводка Market Overview и графиков: убрать stablecoin-like активы из heatmap, расширить видимый historical slice до 240 точек и добавить hover-title для line/bar/candle charts.
- [x] Быстрая демо-доводка `Perp DEX`: показать live readiness по BTC/ETH/SOL perp inputs, coverage таблиц, provider health и research candidates без fake DEX volume/OI.
- [x] Быстрая демо-доводка `Assets`: убрать hardcoded `SOLUSDT`, привести workspace tab к `Assets` и рассчитывать liquidation bars от реальных long/short totals.
- [x] Финальный демо-polish `Funding`, `Arbitrage Scanner` и `Market Matrix`: source-плашки, time labels, readable candidate rows и coverage/status columns.
- [x] Быстрая демо-доводка `Strategy Lab`: заменить пустой output chart на честный `Backtest Output Boundary`, отформатировать input charts и убрать `Backtest #1` tab label.
- [x] Presentation safety sweep: убрать грубые `mock/fake/coming soon` формулировки из видимых демо-экранов и заменить `/backtests` на readiness-state.
- [x] Убрать fake backtest results из Strategy Lab и заменить их на live input readiness.
- [ ] Реализовать live Perp DEX venue adapter для Hyperliquid/dYdX/GMX, прежде чем показывать DEX volume/OI/liquidity как реальные данные.
- [ ] Добавить live order book endpoint для ключевых CEX pairs, начиная с Binance `BTCUSDT`, `ETHUSDT`, `SOLUSDT`.
- [x] Добавить live liquidations ingestion/API через CoinGlass aggregated history, прежде чем возвращать блок `Liquidations (24h)` в режим с реальными значениями.
- [ ] Реализовать настоящий backtest engine для Strategy Lab: расчёт PnL/drawdown/trades только из PostgreSQL inputs.
- [ ] Добавить visual regression/screenshot checklist для 6 MVP-экранов после стабилизации layout.

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

## Phase 7 — Data Layer / Backtesting 📋 IN PROGRESS
- [x] Добавить read-only API для проверки market data из persistence layer: `GET /api/v1/data/ohlcv`, `GET /api/v1/data/funding`, `GET /api/v1/data/health`.
- [x] Добавить regression tests для data-layer endpoint'ов с временной SQLite БД и seed-данными OHLCV/funding.
- [x] Исправить canonical/provider symbol mismatch: ingest и API работают с canonical symbol (`BTC`), адаптер маппит в provider-native внутри себя.
- [x] Закрыть небезопасные auth stub'ы (Telegram/Web3) в production — возвращать 501 при `DEBUG=false`.
- [x] Добавить fail-fast startup validation для `SECRET_KEY` и `VAULT_MASTER_KEY` в production.
- [x] Перевести production runtime persistence с SQLite на PostgreSQL через `DATABASE_URL`, `psycopg` и Alembic.
- [x] Усилить production startup validation: блокировать слабые/dev secrets, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS` при `DEBUG=false`.
- [x] Добавить `GET /api/v1/health/readiness` для проверки DB connectivity и актуального Alembic head.
- [x] Подготовить минимальный server deployment flow: `.env.production.example`, `docker-compose.prod.yml`, `DEPLOYMENT.md`.
- [x] Убрать frontend deploy-риск из hardcoded `127.0.0.1:8000` для Next.js API rewrite и WebSocket stream.
- [ ] Расширить CoinGlass data adapter до дополнительных provider-specific L/S потоков, если Binance global L/S будет недостаточно для MVP.
- [ ] Реализовать backtest engine и scheduler (следующий milestone после data quality gate).

## Known Tech Debt (не блокирует разработку)
- [x] `httpx.AsyncClient` leaks — FIXED in Phase 4A
- [x] Sync DB sessions в async endpoints — acceptable for current scale
- [x] `PreferenceService` создаёт свой `SessionLocal()` — FIXED in Phase 4A
- [x] FIFO eviction в кэше вместо LRU — FIXED in Phase 4A
- [x] Кэш не инвалидируется при изменении preferences — FIXED in Phase 4A
- [ ] Binance WebSocket heartbeat timeouts — reconnect works, non-critical
- [x] `deltagrid.db` SQLite — migrate to PostgreSQL for production
- [ ] Перевести `_json` Text-поля на PostgreSQL `JSONB` после стабилизации API-сериализации.
- [ ] Пересмотреть `Float` в market data там, где значения начнут использоваться для финансово-критичных расчётов.
- [ ] Подготовить отдельный one-off export/import, если потребуется перенос исторических данных из старого SQLite `.db`.
- [x] Обновить Next.js до `15.5.19`: critical/high advisory для `next@14.1.0` закрыты, frontend production build проходит.
- [x] Проверить Next.js 16.x для полного снятия остаточного `moderate` audit: stable `16.2.9` всё ещё содержит bundled `postcss 8.4.31`, fixed `8.5.10` пока только в canary.
- [ ] Дождаться stable Next.js patch с bundled `postcss >=8.5.10`.
- [ ] Перевести оставшиеся `datetime.utcnow()` на timezone-aware UTC timestamps.
- [ ] Перевести Pydantic class-based `Config` на `ConfigDict`, чтобы убрать deprecation warnings перед Pydantic v3.
- [ ] Разобраться с локальными permission warning для `.pytest_cache` в OneDrive workspace.
- [ ] После первого staging-деплоя проверить, поддерживает ли выбранный reverse proxy WebSocket upgrade для `/api/v1/stream/ws`.
