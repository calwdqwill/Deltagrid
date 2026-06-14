# Current Task — DeltaGrid

**Phase**: MVP1 — Data Quality Gate и provider reliability
**Status**: MVP0 зафиксирован как production-ready demo: PostgreSQL runtime, Alembic, `deltagrid.pro`, Cloudflare/Nginx/SSL, live terminal screens и data-layer endpoints работают. На production VPS Binance Futures API возвращает HTTP `451`, поэтому primary CEX perp data path для MVP1 выбран как OKX USDT Swap без прокси/VPN. MVP1 data quality gate задеплоен на production: freshness SLA в `/api/v1/data/health`, health по `sync_type`, cron/data-sync diagnostics, coverage matrix и production universe readiness доступны в `/data-health`. 72h и 7d OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершены с `errors=0` и `gaps=0`. Charts v0 и OHLCV window endpoint задеплоены. Working production baseline `v1.3.0` зафиксирован в GitHub; `main` и `preview` синхронизированы на baseline. Preview/dev stack поднят отдельно от production, но публичный HTTPS `preview.deltagrid.pro` ещё ждёт DNS `A preview -> 2.25.143.143`. Provider inventory v0 добавлен как read-only persisted-data gate перед расширением universe.
**Last Updated**: 2026-06-15

## Обновление 2026-06-15 — Provider inventory v0

- Добавлен `GET /api/v1/data/provider-inventory` для кандидатов на расширение universe за пределы `BTC/ETH/SOL`.
- Endpoint использует только persisted coverage/freshness и не вызывает OKX, CoinGlass, CoinGecko или legacy Binance.
- Default candidate set: `BTC/ETH/SOL/HYPE/XRP/DOGE/BNB/ADA/LINK/AVAX/SUI/TON/TRX/DOT/LTC/BCH/AAVE/UNI/APT/ARB`.
- Для каждого symbol возвращаются readiness status, `promotion_candidate`, `next_action`, coverage summaries и freshness tracking.
- Следующий шаг: внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper`, sync-конфига и UI selector'ов.

## Обновление 2026-06-14 — Release baseline и CI/CD

- Добавлены `VERSION=1.3.0` и `RELEASES.md`.
- Frontend package version поднят до `1.3.0`.
- Добавлены GitHub Actions workflows: `CI`, `Deploy Preview`, `Deploy Production`.
- Branch policy: `preview` — dev/staging, `main` — production.
- Deploy workflows используют SSH secrets и безопасно пропускают deploy, если secrets ещё не настроены.
- Production `/opt/deltagrid` переведён на clean `main`.
- Подготовлен preview stack contract: `/opt/deltagrid-preview`, `.env.preview`, Compose project `deltagrid-preview`, ports `8011/3012`.

## Обновление 2026-06-14 — Preview/dev stand

- На VPS поднят отдельный preview stack в `/opt/deltagrid-preview` из ветки `preview`.
- Preview использует отдельный `.env.preview`, Compose project `deltagrid-preview`, PostgreSQL volume `deltagrid-preview_postgres_data`, backend `127.0.0.1:8011`, frontend `127.0.0.1:3012`.
- Выполнен 7d OKX/CoinGlass/CoinGecko sync BTC/ETH/SOL в preview БД: `errors=0`, OHLCV gaps по логам `0`.
- Preview `/api/v1/data/health`: OKX/CoinGlass/CoinGecko `healthy`, freshness `24/0/24`, `core_perp_ready=3`, `chart_ready=3`.
- Preview пока не опубликован через DNS/Nginx; внешний доступ к `3012` не открыт.
- Подготовлены preview publication assets: `deploy/nginx/deltagrid-preview.conf.example`, `scripts/configure-preview-nginx-ssl.sh`, `deploy/dns/preview.deltagrid.pro.md`.
- Подготовлен чеклист GitHub Actions deploy secrets: `deploy/github-actions-secrets.md`; сами secrets ещё нужно добавить в GitHub.
- Dedicated SSH deploy key создан локально в `outputs/deploy-keys/github-actions-deltagrid-deploy`; public key добавлен на VPS, non-interactive login проверен.
- `main` и `preview` синхронизированы на ops commit `104502e`, чтобы default-branch GitHub Actions использовал актуальные deploy workflows. Production checkout `/opt/deltagrid` fast-forward обновлён без пересборки контейнеров; smoke-check прошёл.
- CI/CD probe `fdb08ec` подтвердил: preview CI проходит, `Deploy Preview` workflow запускается, но deploy делает safe-skip на шаге `Skip when preview secrets are not configured`. Значит GitHub secrets `PREVIEW_*` ещё отсутствуют или заполнены не полностью.
- Восстановлен отсутствующий `AGENTS.md` с проектными правилами для Codex/AI-агентов.

## Обновление 2026-06-14 — Production universe v1

- Добавлен `GET /api/v1/data/universe`: derived read-only policy view поверх coverage/freshness.
- `/api/v1/data/health` теперь возвращает блок `universe`, а `/data-health` показывает таблицу `Production Universe`.
- Статусы universe: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`.
- MVP1 policy: symbol попадает в primary UI universe только если chart-critical streams покрыты, freshness зелёный и нет missing tracked streams.
- Fix задеплоен на `deltagrid.pro`; production показывает `core_perp_ready=3`, `chart_ready=3`, `ui_universe=BTC/ETH/SOL`, `deferred_symbols=[]`.
- Partial enrichment streams для всех трёх symbols: `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot`; missing streams нет.
- Локальная проверка: backend `pytest` — `26 passed`; frontend `npm run build` проходит.

## Обновление 2026-06-14 — Coverage matrix

- Добавлен `GET /api/v1/data/coverage` для read-only инвентаризации покрытия истории по `symbol + exchange + stream + interval`.
- `/api/v1/data/health` теперь возвращает поле `coverage`, а `/data-health` показывает KPI `Coverage` и таблицу `Coverage Matrix`.
- Матрица считает OHLCV, funding, OI, long/short, liquidations, basis и `spot_perp_price`; для sparse `liquidations` учитывается свежий `coinglass/liquidations` sync-run.
- Fix задеплоен на `deltagrid.pro`; production `24h` coverage показывает `27/27`, `7d` coverage показывает `18 covered / 9 partial / 0 missing`.
- Partial `7d` coverage сейчас у `open_interest` и `basis/spot_perp_price`, поэтому production universe v1 нужно формировать с явным разделением complete-history и partial-history активов/потоков.
- Локальная проверка: backend `pytest` — `25 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## Обновление 2026-06-14 — Sparse liquidation freshness

- После ночи production health показал `freshness.summary={fresh:23, stale:1, degraded:0}`; stale был только `SOL / okx / liquidations / 1h`.
- Диагностика показала, что `coinglass/liquidations` sync свежий и `healthy`, а stale возник из-за отсутствия свежих SOL liquidation events, то есть это sparse event stream, а не сбой ingestion.
- Локально реализована правка: `liquidations` freshness учитывает свежесть последнего `coinglass/liquidations` sync-run; `/data-health` показывает `event age / sync age`.
- Fix задеплоен на `deltagrid.pro`; production `/api/v1/data/health` снова даёт `fresh=24/stale=0/degraded=0`, если sync свежий.

## Обновление 2026-06-14 — OHLCV window endpoint

- Добавлен и задеплоен `GET /api/v1/data/ohlcv/window` для Charts v0: один backend-запрос возвращает окно `2h/8h/24h/7d` по `1m/5m/1h`, anchored от последней доступной свечи.
- `/charts` переключён на новый endpoint, а старая постраничная сборка через `/data/ohlcv` оставлена fallback path.
- Production проверка: `/api/v1/data/ohlcv/window?...range=7d` отдаёт `10080/10080` строк, `/charts?symbol=BTC&interval=1m&range=7d` рендерит canvas и показывает `10,080` свечей.

## Обновление 2026-06-13 — Interactive Charts v0

- Локально реализован первый слой `/charts` на `lightweight-charts`: свечи OKX USDT Swap, volume histogram, crosshair OHLC/volume панель, pan/zoom/scroll, выбор символа, интервала и диапазона.
- Для `7d`/`1m` окно собирается постранично через существующий `/api/v1/data/ohlcv` без изменения backend API. Окно строится от последней доступной свечи в PostgreSQL.
- Browser QA через SSH tunnel к production backend подтвердил desktop `BTC 1m 7d` (`10,080` свечей) и mobile `ETH 5m 24h` (`288` свечей); мобильная ширина исправлена скрытием sidebar на малых viewport.
- Charts v0 задеплоен на `deltagrid.pro`; domain smoke и Browser QA прошли для desktop `BTC 1m 7d` и mobile `ETH 5m 24h`.
- Следующий безопасный шаг: решить, нужен ли отдельный backend window endpoint для более чистой пагинации, и отдельно спланировать upgrade `next` до patched версии.

## Обзор 2026-06-13

- Public smoke-check зелёный: `https://deltagrid.pro`, `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend отвечают.
- Серверные контейнеры healthy: backend, frontend и PostgreSQL работают через production compose stack.
- Host-level cron активен: `/etc/cron.d/deltagrid-market-sync` запускает `scripts/sync-market-data.sh` каждые 15 минут с `--lookback-hours 2`.
- Data-layer rows на момент аудита: `ohlcv=41000`, `funding_rates=2340`, `open_interest=4260`, `liquidations=1193`, `long_short_ratio=564`, `basis_premium=2271`, `provider_sync_runs=5260`.
- Свежие потоки: CoinGlass snapshots и CoinGecko basis обновлялись примерно за 12 минут до аудита; CoinGlass liquidations — примерно за 1 час.
- Stale потоки: Binance OHLCV/funding/OI/L/S по BTC/ETH/SOL застряли примерно на `2026-06-11 16:00–21:14 UTC`.
- Причина по логам cron: `https://fapi.binance.com` возвращает HTTP `451`, после чего circuit breaker открывается и остальные Binance-запросы завершаются partial.
- Локальная проверка текущего дерева: backend tests `19 passed`, `compileall app` проходит, frontend `npm run build` проходит с `BACKEND_INTERNAL_URL=https://deltagrid.pro`.
- Принятое решение: не ставить VPN/proxy на сервер; использовать OKX как primary CEX perp provider, CoinGlass/CoinGecko оставить enrichment/cross-check слоями, Binance оставить legacy/diagnostic.
- Реализация OKX primary локально: backend tests `19 passed`, frontend build проходит, local OKX sync smoke записал BTC 1m candles/OI/L/S без ошибок.
- Production deploy OKX primary выполнен: backend/frontend пересобраны на `deltagrid.pro`, контейнеры healthy, backup изменяемых файлов сохранён на сервере в `/tmp/deltagrid-okx-predeploy-20260612_233017.tgz`.
- Ручной OKX sync `BTC,ETH,SOL` за 24 часа завершился `fetched=5421`, `inserted=5439`, `errors=0`; cron-path без явного provider flag тоже завершился `errors=0` и пишет OKX endpoints, CoinGlass liquidations `OKX` и CoinGlass snapshots `OKX` в `/var/log/deltagrid-market-sync.log`.
- `/api/v1/data/health` после деплоя показывает `okx healthy`; production row counts: `ohlcv=46277`, `funding_rates=2373`, `open_interest=4299`, `liquidations=1288`, `long_short_ratio=636`, `basis_premium=2295`, `provider_sync_runs=5316`.
- `/api/v1/data/health` расширен полями `freshness`, `sync_health_by_type` и `sync_diagnostics`; `/data-health` показывает freshness SLA, cron-path и error classes без изменения старых полей ответа.
- Production deploy data quality gate выполнен на `deltagrid.pro`; backend/frontend пересобраны, контейнеры healthy, локальный и доменный `server-smoke.sh` проходят.
- Production `/api/v1/data/health` после backfill показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, cron-path `healthy`, OKX/CoinGlass/CoinGecko `healthy`, Binance `degraded` только как legacy/diagnostic из-за HTTP `451`.
- Первый host-level cron после деплоя и 7d backfill сработал в `2026-06-13 00:15 UTC` и завершился `fetched=465`, `inserted=460`, `errors=0`; финальный health после cron показывает `row_counts.ohlcv=77819` и `provider_sync_runs=5351`.
- 72h backfill BTC/ETH/SOL через OKX завершён `fetched=16239`, `inserted=16308`, `errors=0`; независимая SQL-проверка показала `4320/864/72` строк по `1m/5m/1h` на каждый символ и `gaps=0`.
- 7d backfill BTC/ETH/SOL через OKX завершён `fetched=37875`, `inserted=38103`, `errors=0`; независимая SQL-проверка показала `10080/2016/168` строк по `1m/5m/1h` на каждый символ и `gaps=0`.

## MVP1 — ближайший рабочий план

- [x] P0: решить production path для CEX candles/funding/OI/L/S после Binance `451`: выбран OKX primary.
- [x] P0: добавить `OkxAdapter` и переключить sync/frontend defaults на `okx`.
- [x] P0: задеплоить OKX primary flow на `deltagrid.pro` и выполнить ручной sync `BTC,ETH,SOL`.
- [x] P0: выполнить контрольный 24h backfill BTC/ETH/SOL по `1m/5m/1h` через OKX и проверить `gaps=0` в sync-логах.
- [x] P0: добавить freshness SLA в `/api/v1/data/health` по потокам, символам и интервалам.
- [x] P0: разделить provider health по `sync_type`, чтобы отдельно видеть OHLCV, funding, OI, long/short, liquidations и basis.
- [x] P0: добавить cron/data-sync diagnostics в backend/API и `/data-health`.
- [x] P0: задеплоить data quality gate на production и проверить `/api/v1/data/health` через `deltagrid.pro`.
- [x] P1: расширить backfill до 72h/7d и проверить gaps перед interactive charts.
- [x] P1: после data quality gate перейти к `lightweight-charts` и собрать локальный Charts v0.
- [x] P1: задеплоить Charts v0 на production и проверить `/charts` через домен.
- [x] P1: оценить backend OHLCV window endpoint вместо клиентской постраничной сборки 7d/1m.
- [x] P1: задеплоить sparse liquidation freshness fix и проверить `/data-health`.
- [x] P1: задеплоить OHLCV window endpoint и переключение `/charts`.
- [x] P1: добавить coverage matrix для BTC/ETH/SOL по OHLCV/funding/OI/long-short/liquidations/basis/spot-perp.
- [x] P1: сформировать production universe v1 на основе coverage matrix.
- [x] P1: провести provider inventory v0 для расширения universe за пределы BTC/ETH/SOL через read-only persisted-data endpoint.
- [ ] P1: провести внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper` и sync universe.
- [ ] P2: backtest engine и scheduler делать только после стабилизации исторических рядов.

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
- [x] DNS Cloudflare активен: `deltagrid.pro` и `www.deltagrid.pro` проходят через Cloudflare edge к серверу `2.25.143.143`.
- [x] Серверный IP получен: `2.25.143.143`; SSH `22` открыт, HTTP `80` и HTTPS `443` пока закрыты.
- [x] Добавлены `scripts/bootstrap-ubuntu.sh`, `scripts/deploy-production.sh` и `deploy/dns/deltagrid.pro.md`.
- [x] Добавлен `scripts/configure-nginx-ssl.sh` для включения Nginx site и выпуска Let's Encrypt SSL.
- [x] SSH-доступ `root@2.25.143.143` по ключу подтверждён; production frontend port перенесён на `3001`, чтобы не трогать служебный процесс на `3000`.
- [x] DNS Cloudflare активирован: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`.
- [x] Реальный серверный rollout выполнен: `/opt/deltagrid`, `.env.production`, PostgreSQL, backend, frontend и Nginx.
- [x] HTTPS включён через Let's Encrypt; `https://deltagrid.pro` и `https://www.deltagrid.pro` отвечают.
- [x] Server smoke-check через HTTPS прошёл; основные frontend pages и API routes возвращают `200`.
- [x] Cloudflare proxy + SSL mode `Full (strict)` включены и проверены; WebSocket route проходит через Cloudflare.
- [x] Добавлена команда `python -m app.adapters.data.sync_market_data` и wrapper `scripts/sync-market-data.sh` для первичного заполнения data-layer.
- [x] Первый production sync Binance market data выполнен: `6837` rows inserted, `/api/v1/data/health` через домен показывает `binance healthy`.
- [x] Provider API keys добавлены в server `.env.production`; CoinGlass v4 health/funding endpoints работают через production-домен.
- [x] Sync-команда расширена до CoinGlass funding/OI snapshots и CoinGecko-derived `basis_premium`.
- [x] Sync-команда расширена до CoinGlass aggregated liquidation history с записью в таблицу `liquidations`.
- [x] Host-level cron `/etc/cron.d/deltagrid-market-sync` установлен; cron service активен.
- [x] `/api/v1/data/health` показывает `binance`, `coinglass` и `coingecko` healthy.
- [x] `Funding` читает persisted PostgreSQL funding rows и data health вместо mock fixture.
- [x] `/data-health` заменён с placeholder на live frontend screen.
- [x] Nested tabs в `Funding` и `Perp DEX` кликабельны через `view` query-param.
- [x] `Market Overview` читает live CoinGecko/CoinGlass/alternative.me backend endpoints вместо mock fixture.
- [x] `Assets` читает live SOL spot/funding/OHLCV и показывает pending-состояния вместо fake order book/liquidations.
- [x] Backend открыл read-only endpoints для `open_interest`, `long_short_ratio`, `basis_premium` и `liquidations`.
- [x] `/data/liquidations` теперь получает реальные агрегированные CoinGlass rows после production sync.
- [x] Production smoke после деплоя: `/api/v1/data/health` показывает `row_counts.liquidations=144`, `/api/v1/data/liquidations` отдаёт BTC long/short `value_usd`.
- [x] `Charts`, `Market Matrix` и `Arbitrage Scanner` читают live persisted data streams вместо mock fixture.
- [x] `Strategy Lab` больше не показывает fake PnL/trades; экран показывает readiness live inputs до реального backtest engine.

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
- [x] Выполнить `sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 24 --ohlcv-intervals 1m,5m,1h` на сервере.
- [x] Проверить, что `/api/v1/data/health` показывает `row_counts.ohlcv > 0` и последний Binance sync.
- [x] Установить `scripts/install-market-sync-cron.sh` на сервере.
- [ ] Проверить первый cron-triggered market data sync по `/var/log/deltagrid-market-sync.log`.
- [x] Задеплоить live data streams fix на сервер и проверить `https://deltagrid.pro/charts`, `/market-matrix`, `/arbitrage-scanner`, `/strategy-lab`.
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
- [x] Market Overview/Assets/Funding/Charts/Market Matrix/Arbitrage Scanner/Data Health подключены к backend data-layer.
- [x] Perp DEX не показывает mock DEX volume/OI/liquidity как production-данные до live DEX adapter.
- [x] Asset Deep Dive SOL.
- [x] Market Matrix без funding metric / Funding Matrix.
- [x] Strategy Lab / Backtest.
- [x] Charts placeholder без новых зависимостей.
- [x] Frontend build: `npm run build` проходит.

## Следующая frontend-итерация

- [x] Подключить `lightweight-charts` и реализовать первый production-oriented Charts v0.
- [x] Задеплоить Charts v0 на `deltagrid.pro` и пройти visual/smoke QA.
- [x] Подключить Funding/Data Health к backend/data-layer endpoint'ам.
- [x] Подключить Market Matrix, Arbitrage Scanner, Charts и Strategy Lab к backend/data-layer endpoint'ам или честным pending/readiness states.
- [ ] Реализовать live Perp DEX venue adapter.
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
