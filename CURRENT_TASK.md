# Current Task — DeltaGrid

**Phase**: MVP1 — Data Quality Gate и provider reliability
**Status**: MVP0 зафиксирован как production-ready demo: PostgreSQL runtime, Alembic, `deltagrid.pro`, Cloudflare/Nginx/SSL, live terminal screens и data-layer endpoints работают. На production VPS Binance Futures API возвращает HTTP `451`, поэтому primary CEX perp data path для MVP1 выбран как OKX USDT Swap без прокси/VPN. MVP1 data quality gate задеплоен на production: freshness SLA в `/api/v1/data/health`, health по `sync_type`, cron/data-sync diagnostics, coverage matrix и production universe readiness доступны в `/data-health`. 72h и 7d OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершены с `errors=0` и `gaps=0`. Charts v0 и OHLCV window endpoint задеплоены. Working production baseline `v1.3.0` зафиксирован в GitHub; `main` и `preview` синхронизированы на baseline. Preview/dev stack поднят отдельно от production, но публичный HTTPS `preview.deltagrid.pro` ещё ждёт DNS `A preview -> 2.25.143.143`. Preview CI/CD снова подтверждён end-to-end после SSH hardening. Provider inventory v0, provider discovery v1, alias expansion, 24h preview sync dry-run, candidate freshness scope и 72h/7d preview backfill первой малой группы завершены. Preview chart/asset candidate selectors для `HYPE/XRP/DOGE/ADA/LINK` включены; full analytics universe promotion теперь явно отделён от `chart_ready` и требует `complete_history`.
**Last Updated**: 2026-06-16

## Обновление 2026-06-16 — Policy gate для chart-ready candidates

- В provider inventory зафиксировано разделение двух gate: `chart_ready_candidates` подходят только для preview `/charts` и `/assets`, а `promotion_candidates` относятся к full analytics universe.
- `promotion_candidate` теперь требует `complete_history`; статус `core_perp_ready` больше не считается full promotion, если `open_interest`, `basis_premium` или `spot_perp_price` остаются partial.
- В `policy.gates` добавлено машинно-читаемое описание правил для `chart_ready` и `promotion_candidate`, чтобы API сам объяснял, почему symbol можно смотреть на графиках, но нельзя продвигать в полный analytics universe.
- Добавлен regression test для chart-ready candidate с полной 7d OHLCV/funding/long-short coverage и partial snapshot/enrichment streams.
- Следующий безопасный шаг: отдельно решить, нужно ли добирать 7d snapshot/enrichment историю для full promotion или оставить candidates в chart/asset режиме до следующего набора data requirements.

## Обновление 2026-06-15 — OKX rate-limit retry для preview cron

- Первый реальный scheduled preview core cron после установки split cron подтвердил, что один split не полностью закрывает проблему: OKX `long_short_ratio` для `SOL` вернул HTTP `429`, sync завершился `errors=1`.
- Причина на уровне кода: `resp.raise_for_status()` поднимал `httpx.HTTPStatusError`, который не попадал в существующий `RetryPolicy`; поэтому transient `429` превращался в `partial` run без retry.
- `OkxAdapter` теперь переводит HTTP `429` и OKX rate-limit payload в `RateLimitExceeded`; этот тип уже поддержан общим retry/backoff.
- OKX default pacing в `GlobalRateLimiter` снижен до `capacity=5`, `refill_rate=2 req/sec`, чтобы cron-path меньше давил на публичные derived endpoints.
- Добавлен regression test на классификацию OKX HTTP `429`; локально из `backend` прошёл `backend\venv\Scripts\python.exe -m pytest tests\test_okx_adapter.py` (`6 passed`), также прошли `py_compile` и `git diff --check`.
- CI `27539771597` и `Deploy Preview` `27539817178` завершились успешно; `/opt/deltagrid-preview` обновился до `725387d`, контейнеры preview healthy.
- Контрольный scheduled core cron в `2026-06-15 10:30 UTC` подтвердил fix: OKX вернул `429` на `SOL long_short_ratio`, adapter сделал retry, повторный запрос вернул `200 OK`, итог cron-run `fetched=462`, `inserted=461`, `errors=0`.
- Финальный preview `/api/v1/data/health`: cron diagnostics `healthy`, latest `okx/long_short_ratio` `completed`, `recent_error_classes.rate_limit=2` остаётся только как 24h история старых partial-run до фикса.

## Обновление 2026-06-15 — Preview market sync cron path

- Причина stale/degraded freshness на preview: регулярный host cron был установлен только для production `/opt/deltagrid` и синкал `BTC/ETH/SOL`; отдельного `/etc/cron.d/deltagrid-preview-market-sync` не было.
- `scripts/install-market-sync-cron.sh` обновлён: cron-команда теперь может явно пробрасывать `ENV_FILE`, `COMPOSE_FILE` и `COMPOSE_PROJECT_NAME`.
- Для preview зафиксирован безопасный split contract: отдельный cron/log для core symbols и отдельный cron/log для candidates со сдвигом минут, чтобы снизить риск OKX `429` на derived streams.
- Production cron не менялся и не переустанавливался в рамках кодовой правки.
- На preview VPS установлены `/etc/cron.d/deltagrid-preview-market-sync-core` и `/etc/cron.d/deltagrid-preview-market-sync-candidates`; production `/etc/cron.d/deltagrid-market-sync` остался прежним.
- Ручной preview sync по split-path прошёл `errors=0` для core и `errors=0` для candidates. Provider inventory после проверки: `chart_ready_candidates=5`, `promotion_candidates=0`, `coverage_blockers=15`, `freshness_blockers=5`, `promotion_blockers=20`.
- Оставшийся freshness blocker у candidates — `funding_rates:8h:stale`; full promotion по-прежнему блокируют 15 coverage blockers по `open_interest`, `basis_premium`, `spot_perp_price`.

## Обновление 2026-06-15 — Promotion blocker diagnostics

- Provider inventory теперь возвращает явные blocker-поля для full analytics promotion: `coverage_blockers_7d`, `freshness_blockers` и объединённый `promotion_blockers` на уровне каждого symbol.
- В `summary` добавлены счётчики `coverage_blockers`, `freshness_blockers` и `promotion_blockers`, чтобы видеть масштаб причин блокировки без ручного разбора coverage/freshness rows.
- Диагностика использует только persisted data из уже рассчитанных coverage/freshness reports и не вызывает внешние provider API.
- Regression tests обновлены для symbol без coverage и fresh-but-partial candidate; локально через `backend/venv` пройдено `20 passed`.
- Статус full promotion не менялся: `HYPE/XRP/DOGE/ADA/LINK` остаются preview chart/asset candidates, а следующий продуктовый выбор — закрывать partial `open_interest`, `basis_premium`, `spot_perp_price` или формально утвердить разделение `chart_ready` и full analytics universe.

## Обновление 2026-06-15 — Candidate gate diagnostics batch

- Provider inventory получил additive-поля `chart_ready_candidates` в `summary` и `policy`, чтобы не смешивать chart/asset readiness с full analytics promotion.
- `/charts` и `/assets` теперь показывают компактный scope выбранного актива: `Core` или `Preview Candidate`.
- Добавлен `scripts/preview-candidate-smoke.sh` для ручной проверки preview candidate paths и core-only границы.
- Скрипт проверен против текущего preview VPS: candidate charts/assets и 7d OHLCV windows прошли, `/market-matrix`, `/arbitrage-scanner`, `/perp-dex` остались core-only.
- Локально: `python -m compileall backend\app` и `npm run build` прошли; локальный `pytest` недоступен в Windows-сессии из-за отсутствующего пакета `pytest`, финальный backend test прогон должен пройти в GitHub CI.

## Обновление 2026-06-15 — Deploy SSH diagnostics follow-up

- Docs commit `e8ddb1f` прошёл CI, но `Deploy Preview` run `27533723576` упал на диагностическом шаге `Test preview SSH login`; deploy step не дошёл до выполнения.
- Preview VPS в этот момент оставался healthy, локальный SSH к `root@2.25.143.143` проходил, `/opt/deltagrid-preview` оставался на рабочем commit `57e743a`.
- `deploy-preview.yml` и `deploy-production.yml` обновлены: `Test SSH login` и `Check app directory` теперь warning-only diagnostics, а реальным gate остаётся deploy step.
- Deploy step теперь делает 3 попытки вместо 2 и использует нарастающую паузу между попытками.

## Обновление 2026-06-15 — Preview chart candidates scope

- В preview frontend разделены `CORE_SYMBOLS=BTC/ETH/SOL` и `CANDIDATE_SYMBOLS=HYPE/XRP/DOGE/ADA/LINK`.
- `/charts` и `/assets` теперь допускают candidate symbols, чтобы смотреть 7d OHLCV и asset deep dive на preview без изменения production.
- `Market Matrix`, `Arbitrage Scanner` и `Perp DEX` оставлены scoped к `BTC/ETH/SOL`, потому текущий strict gate для full promotion показывает `promotion_candidates=0`, `ready_for_ui_review=0`, `history_completion_required=5`.
- Причина блокировки full promotion: у всех 5 candidates есть `chart_ready=true`, но 7d history остаётся partial для snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- CI/CD проверен: commit `57e743a`, CI `success`, `Deploy Preview` run `27533404025` `success`, `/opt/deltagrid-preview` на `57e743a`, backend/frontend/PostgreSQL healthy.
- Smoke-check preview: `/charts?symbol=HYPE&interval=1m&range=7d`, `/assets?symbol=ADA`, `/market-matrix`, `/arbitrage-scanner`, `/perp-dex` возвращают HTTP `200`; candidates видны только в chart/asset paths.
- Следующий шаг: закрыть policy/history gap для `open_interest`, `basis_premium`, `spot_perp_price` или явно утвердить правило, что chart-ready candidates можно держать отдельно от full analytics universe.

## Обновление 2026-06-15 — Preview deploy SSH hardening

- Последний flaky `Deploy Preview` падал на шаге `Test preview SSH login`, хотя preview stack на VPS оставался healthy.
- В `deploy-preview.yml` и `deploy-production.yml` добавлены более строгие SSH options, явные `timeout` и controlled retries для login, app-dir check и deploy.
- GitHub Actions проверка: CI commit `4c3dec0` прошёл успешно, `Deploy Preview` run `27532247102` завершился `success`.
- `/opt/deltagrid-preview` автоматически обновился до `4c3dec0`; backend/frontend/PostgreSQL healthy.
- Следующий шаг по продукту закрыт частично и безопасно: `HYPE/XRP/DOGE/ADA/LINK` включены как preview chart/asset candidates, full analytics universe promotion ждёт закрытия history gate.

## Обновление 2026-06-15 — 72h/7d preview backfill первой группы

- 72h backfill `HYPE/XRP/DOGE/ADA/LINK` на preview завершён: `fetched=27065`, `inserted=26902`, `errors=0`.
- 7d backfill той же группы завершён: `fetched=63125`, `inserted=62858`, `errors=0`.
- OHLCV gaps по `1m/5m/1h` для всех 5 symbols равны `0`; chart window проверен: `HYPE 1m 7d = 10080` свечей, `LINK 5m 7d = 2016` свечей.
- 7d coverage: `covered=30`, `partial=15`, `missing=0`; partial остаётся только у snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Для chart path группа готова: OHLCV gaps `0`, `HYPE 1m 7d = 10080` свечей, `LINK 5m 7d = 2016` свечей.
- Full promotion gate при повторной проверке показывает `history_completion_required=5` из-за partial `open_interest`, `basis_premium`, `spot_perp_price`; поэтому candidates включены только в `/charts` и `/assets`.

## Обновление 2026-06-15 — Candidate freshness scope

- `/api/v1/data/provider-inventory` теперь считает freshness по запрошенным candidate symbols и явно возвращает `scope.freshness_scope=requested_symbols`.
- `/api/v1/data/health` не расширялся и остаётся production SLA snapshot для текущего UI universe `BTC/ETH/SOL`.
- Preview deploy проверен на `HYPE/XRP/DOGE/ADA/LINK`: `freshness_tracking_required=0`, все 5 symbols имеют `freshness.worst_status=fresh`.
- По readiness все 5 symbols пока остаются `history_completion_required`, потому 7d coverage ещё partial.
- Следующий шаг: выполнить 72h/7d preview backfill первой группы и проверить gaps/coverage перед UI universe expansion.

## Обновление 2026-06-15 — Alias expansion и 24h preview dry-run

- `SymbolMapper.seed_defaults()` стал идемпотентным и расширен aliases для `HYPE/XRP/DOGE/ADA/LINK`.
- Preview DB засеяна aliases; OKX/CoinGlass/CoinGecko mappings проверены внутри backend container.
- 24h sync dry-run `HYPE/XRP/DOGE/ADA/LINK` на preview завершён без расширения UI: `fetched=9035`, `inserted=8986`, `errors=0`.
- OHLCV gaps по `1m/5m/1h` для всех 5 symbols равны `0`.
- `/api/v1/data/coverage?symbols=HYPE,XRP,DOGE,ADA,LINK&exchange=okx&range=24h` показывает `covered=30`, `partial=15`, `missing=0`.
- До отдельного candidate freshness scope `/api/v1/data/provider-inventory` оставлял symbols вне promotion candidates с `next_action=freshness_tracking_required`, потому freshness SLA формально покрывал только `BTC/ETH/SOL`.
- Следующий шаг закрыт отдельной итерацией candidate freshness scope; далее нужен 72h/7d preview backfill и проверка gaps/coverage перед UI universe expansion.

## Обновление 2026-06-15 — Provider discovery v1

- Добавлен CLI `python -m app.adapters.data.discover_provider_universe` для read-only live discovery по OKX, CoinGlass, CoinGecko и legacy Binance.
- Preview/VPS discovery выполнен внутри `deltagrid-preview-backend`: OKX/CoinGlass/CoinGecko `healthy`, Binance legacy `blocked_http_451`.
- Все `20/20` candidate symbols получили `eligible_for_24h_sync_dry_run`.
- Discovery не пишет в PostgreSQL, не расширяет sync и не меняет UI.
- Следующий шаг: `SymbolMapper`/alias expansion plan для `HYPE/XRP/DOGE/ADA/LINK`, затем 24h sync dry-run на preview и проверка errors/gaps/coverage.

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
- [x] P1: провести внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper` и sync universe.
- [x] P1: подготовить `SymbolMapper`/alias expansion plan для первой малой группы `HYPE/XRP/DOGE/ADA/LINK`.
- [x] P1: выполнить 24h sync dry-run первой малой группы на preview без расширения UI.
- [x] P1: расширить freshness SLA scope для первой малой группы или явно отделить candidate freshness от current UI universe freshness.
- [x] P1: выполнить 72h/7d preview backfill первой малой группы и проверить gaps/coverage перед UI universe expansion.
- [x] OPS/P1: стабилизировать preview deploy SSH retry path и подтвердить успешный `Deploy Preview` после CI.
- [x] P1: включить первую малую группу как preview chart/asset candidates и проверить HTTP smoke `/charts`/`/assets` на preview.
- [x] P1: закрыть `history_completion_required=5` для `HYPE/XRP/DOGE/ADA/LINK` или явно зафиксировать policy-разделение `chart_ready` и full analytics universe promotion.
- [ ] P1: отдельно оценить backfill/ingestion для 7d `open_interest`, `basis_premium`, `spot_perp_price`, если решим продвигать candidates в full analytics universe.
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
