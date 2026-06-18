# План проекта DeltaGrid

## Текущая фаза

**MVP1 — Data Quality Gate и provider reliability** — следующая стадия после MVP0. Цель: сделать накопление рыночных данных наблюдаемым, свежим и устойчивым перед полноценными интерактивными графиками и backtest engine.

## Release / CI-CD baseline — 2026-06-14

- Production baseline зафиксирован как `v1.3.0`.
- `preview` используется как dev/staging ветка, `main` — как production ветка.
- Добавлен `RELEASES.md` с правилами SemVer и release flow.
- Добавлен `scripts/release-preflight.sh`, чтобы перед patch/minor release проверять согласованность `VERSION`, frontend package version и lockfile root version.
- Добавлены GitHub Actions workflows: `CI`, `Deploy Preview`, `Deploy Production`.
- Deploy workflows используют SSH secrets и не выполняют deploy, если secrets ещё не настроены.
- Подготовлено dev/prod разделение на уровне deployment: production `/opt/deltagrid` + `.env.production` + ports `8000/3001`, preview `/opt/deltagrid-preview` + `.env.preview` + ports `8011/3012`.
- Preview/dev stack поднят на VPS локально: отдельный Compose project `deltagrid-preview`, отдельная PostgreSQL БД, smoke-check зелёный, 7d BTC/ETH/SOL data sync выполнен без ошибок.
- Preview auto-deploy через GitHub Actions проверен end-to-end: `PREVIEW_*` secrets, SSH login, deploy в `/opt/deltagrid-preview`, healthy containers и server smoke на ports `8011/3012`.
- После flaky SSH login failure preview deploy workflow усилен явными SSH timeout/retry options; commit `4c3dec0` прошёл CI, `Deploy Preview` run `27532247102` завершился `success`, `/opt/deltagrid-preview` обновился автоматически и остался healthy.
- После `v1.3.2` GitHub `Deploy Preview` run `27744161749` классифицирован как transient SSH reachability failure из GitHub runner: ручной deploy тем же script прошёл. Deploy workflows и `scripts/deploy-compose-stack.sh` усилены stage-aware diagnostics и remote diagnostic snapshot, добавлен `scripts/release-smoke.sh`, а `scripts/release-preflight.sh` получил `RELEASE_TARGET=1.4.0-rc.1` для preview RC target.
- После product commit `4433f0b` с Perp DEX depth freshness GitHub CI `27761405255` прошёл, но `Deploy Preview` `27761467202` снова упал на шаге `Deploy preview` после успешных SSH prechecks; ручной deploy тем же script обновил `/opt/deltagrid-preview` до `4433f0b`, а полный preview release smoke на `8011/3012` прошёл.
- Preview Nginx HTTP site заранее включён на VPS и проверен через `Host: preview.deltagrid.pro`; публичный HTTPS ждёт DNS-запись `preview -> 2.25.143.143`.
- Production deploy hardening перенесён в `main`: workflow проверяет `PROD_*`, fingerprint deploy key, ожидаемые значения production VPS и app dir перед deploy step.
- Read-only preflight production auto-deploy от 2026-06-16 подтвердил, что deploy contract готов: local deploy key fingerprint совпадает, SSH к `/opt/deltagrid` проходит, production smoke зелёный. `Deploy Production` run `27619159104` сделал safe-skip, потому что обязательные GitHub secrets `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR` ещё отсутствуют.
- `Deploy Production` получил ручной `workflow_dispatch` для ветки `main`, чтобы после настройки `PROD_*` можно было выполнить контрольный deploy без пустого push.
- Подготовлен внешний production healthcheck через GitHub Actions schedule/manual workflow для `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend.
- Добавлен reusable backup-скрипт `scripts/backup-postgres.sh`, который делает PostgreSQL `pg_dump` через Docker Compose и сохраняет compressed dump в `backups/`.
- Первый production backup текущей PostgreSQL БД выполнен вручную: `/opt/deltagrid/backups/deltagrid_20260616T132922Z.sql.gz`, gzip integrity check прошёл.
- `scripts/deploy-compose-stack.sh` подключён к backup-скрипту: production deploy (`BRANCH=main`) создаёт backup по умолчанию, preview backup включается только явно.
- Frontend security baseline обновлён до Next.js `15.5.19`; critical/high advisory из `next@14.1.0` закрыты, App Router страницы мигрированы на async `searchParams`.
- Подготовлены runbook'и для следующего ops-шагa: `deploy/github-actions-secrets.md` для GitHub deploy secrets и `deploy/dns/preview.deltagrid.pro.md` для публикации preview-домена через Nginx/SSL.

- Patch release `v1.3.1` подготовлен поверх `preview`: provider inventory promotion gate, blocker breakdown, frontend audit repair и release preflight.

## Что уже готово

- Frontend MVP terminal shell и MVP1 data-layer baseline `v1.3.0`.
- FastAPI backend с routes для scanner, market, data-layer, auth, alerts, RWA/treasury и execution foundation.
- SQLAlchemy ORM-модели и линейная Alembic-цепочка миграций.
- PostgreSQL runtime через `DATABASE_URL`.
- Docker Compose с локальным PostgreSQL 16.
- MVP0 зафиксирован как production-ready demo: `deltagrid.pro`, PostgreSQL, Cloudflare/Nginx/SSL, live terminal screens, data-layer endpoints и честные readiness-состояния без fake PnL/DEX метрик.
- Perp DEX diagnostics hardening v0 готов: direct venue smoke script, `Depth Diagnostics`, структурированные route blockers и `Route Blockers Matrix` добавлены без включения total cost bps, liquidity ranking или execution.
- Perp DEX policy smoke and output policy v0 готов: `scripts/perp-dex-policy-smoke.sh`, `Route Output Policy`, `Route Model Blockers` и regression-инварианты закрепляют read-only route model safety без включения numeric cost bps, ranking или execution.
- Perp DEX required inputs and direct smoke guardrails v0 готов: direct venue smoke проверяет read-only/ranking/production safety flags, а `Route Required Inputs` выводит обязательные входы route model отдельным checklist.
- Perp DEX route safety guardrails v0 готов: `Route Safety Guardrails` показывает expected vs actual по верхнеуровневым safety-флагам, а policy smoke закрепляет required inputs и formula skeleton keys.
- Perp DEX diagnostic components summary v0 готов: `Route Diagnostic Components Summary`, policy smoke и backend regression tests закрепляют структуру `diagnostic_cost_estimate_v0.components` без включения total cost bps, ranking или execution.
- Perp DEX diagnostic component summary contract v0 готов: backend `diagnostic_cost_estimate_v0.summary`, UI fallback и smoke/test consistency checks закрепляют component summary как read-only контракт.
- Perp DEX diagnostic venue breakdown v0 готов: backend `summary.venue_breakdown`, UI `Route Diagnostic Venue Breakdown` и smoke/test consistency checks показывают readiness по Lighter/Aster/cross-venue без route scoring.
- Perp DEX diagnostic blocker breakdown v0 готов: backend `summary.blocker_breakdown`, UI `Route Diagnostic Blocker Breakdown` и smoke/test consistency checks показывают повторяющиеся blockers без route scoring.
- Perp DEX diagnostic required input breakdown v0 готов: backend `summary.required_input_breakdown`, UI `Route Diagnostic Required Input Breakdown` и smoke/test consistency checks связывают diagnostic components с обязательными route-model inputs без route scoring.
- Perp DEX diagnostic observability rollups v0 готовы: backend `summary.source_field_breakdown`, `summary.safe_use_breakdown`, `summary.readiness_rollup`, UI-таблицы и smoke/test consistency checks показывают source fields, safe-use boundaries и fee/depth/carry/risk readiness без route scoring.
- Perp DEX diagnostic depth policy and smoke compare v0 готов: backend `summary.depth_staleness_policy_checklist`, UI `Route Diagnostic Depth/Staleness Policy`, policy smoke validation и optional `COMPARE_BASE_URL` diff summary фиксируют stale-depth/depth freshness gates без slippage bps, route ranking или execution.
- Perp DEX diagnostic policy input breakdown v0 готов: backend `summary.required_policy_input_breakdown`, UI `Route Diagnostic Policy Inputs`, compact smoke `required_policy_input_ids` и smoke/test consistency checks показывают required policy inputs для depth/staleness gates без slippage bps, route ranking или execution.
- Perp DEX diagnostic next actions breakdown v0 готов: backend `summary.next_action_breakdown`, UI `Route Diagnostic Next Actions`, smoke/test consistency checks и compact contract `next_action_ids` показывают planning actions без route scoring.
- Perp DEX diagnostic source input actions coverage v0 готов: backend `summary.source_input_action_coverage`, UI `Route Diagnostic Source Input Actions`, compact smoke `source_input_action_fields` и docs/smoke compare пример связывают sourced display fields с required inputs и next actions без route scoring.
- Perp DEX route-ready evidence checklist v0 готов: backend `summary.route_ready_evidence_checklist`, UI `Route Diagnostic Evidence Checklist`, compact smoke `route_ready_evidence_gate_ids` и smoke/test consistency checks фиксируют pre-route-scoring evidence gates без cost bps, ranking или execution.
- Perp DEX venue evidence and GMX mapping review v0 готов: backend `summary.venue_evidence_status` и `gmx_rate_mapping_review_v0`, UI `Route Diagnostic Venue Evidence Status`/`GMX Rate Mapping Review`, compact smoke `venue_evidence_status_ids`/`gmx_rate_mapping_review_ids` и docs decision note разделяют venue-specific/cross-venue/GMX mapping gaps без carry conversion, route scoring или execution.
- Perp DEX GMX mapping evidence hardening v0 готов: backend `gmx_rate_mapping_review_v0.blocker_breakdown` и `fixture_readiness_matrix`, UI `GMX Rate Mapping Blockers`/`GMX Rate Fixture Readiness`, compact smoke `gmx_rate_mapping_status`/`gmx_rate_mapping_blocker_ids`/`gmx_rate_fixture_case_ids` и tests показывают repeated blockers и side-aware fixture gaps без carry conversion, route scoring или execution.
- Perp DEX GMX fixture/source hardening v0 готов: backend `gmx_rate_mapping_review_v0.side_aware_fixture_expectations` и `mapping_decision_checklist`, UI `GMX Rate Side-aware Fixtures`/`GMX Rate Mapping Decision Checklist`, compact smoke `gmx_rate_fixture_statuses`/`gmx_rate_mapping_decision_statuses` и tests фиксируют fixture/status/manual-review gaps без diagnostic carry bps, route scoring или execution.
- Perp DEX GMX carry-readiness audit v0 готов: backend `gmx_rate_mapping_review_v0.carry_readiness_summary` и `carry_input_checklist`, UI `GMX Rate Carry Readiness Summary`/`GMX Rate Carry Input Checklist`, compact smoke `gmx_rate_carry_*` и tests фиксируют carry horizon/notional/sign/source/display gates без diagnostic carry bps, route scoring или execution.
- Perp DEX GMX carry-source evidence gate v0 готов: backend `gmx_rate_mapping_review_v0.carry_source_evidence_summary` и `carry_source_evidence_checklist`, UI `GMX Rate Carry Evidence Summary`/`GMX Rate Carry Evidence Checklist`, compact smoke `gmx_rate_carry_evidence_*` и tests фиксируют source/fixture/runtime/manual evidence gates без diagnostic carry bps, route scoring или execution.
- Perp DEX GMX live helper source review v0 готов: backend `gmx_rate_mapping_review_v0.live_helper_source_summary` и `live_helper_source_checklist`, UI `GMX Rate Live Helper Source Review`, compact smoke `gmx_rate_live_helper_*` и tests фиксируют live `/markets/info` rate output evidence, missing helper source inputs, side-aware expectations и manual review gates без diagnostic carry bps, route scoring или execution.
- Perp DEX GMX helper/source follow-up rows v0 готовы: backend `gmx_rate_mapping_review_v0.helper_source_follow_up_summary` и `helper_source_follow_up_checklist`, UI `GMX Rate Helper Source Follow-up`, compact smoke `gmx_rate_helper_follow_up_*` и tests показывают, какие helper source inputs и manual approvals всё ещё блокируют carry conversion без включения diagnostic carry bps, route scoring или execution.
- Perp DEX Lighter/Aster fee schedule evidence v0 готов: backend `diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_summary` и `fee_schedule_evidence_checklist`, UI `Route Diagnostic Fee Schedule Evidence`/`Route Diagnostic Fee Schedule Checklist`, compact smoke `fee_schedule_evidence_*` и tests показывают account tier/order intent/manual approval gates без fee bps total, numeric route cost bps, ranking или execution.
- Perp DEX source status rollup v0 готов: UI-панель `Perp DEX Source Status` собирает direct venue snapshots, GMX raw, CoinGlass enrichment, route policy/model contract и last release smoke в compact read-only таблицу без новых provider calls, venue sorting, route ranking, numeric route cost bps или execution.
- Perp DEX Source Status compare contract v0 готов: `scripts/perp-dex-source-status-smoke.sh` собирает тот же read-only cockpit scope в compact contract, поддерживает `COMPARE_BASE_URL`/`FAIL_ON_DIFF=1` для preview/prod drift и не выводит raw provider payload или secrets.
- Perp DEX direct availability summary v0 готов: direct venue endpoints Hyperliquid, dYdX, Lighter, Aster и GMX отдают `availability_summary` с rows, requested/matched/missing symbols, status counts, depth diagnostics availability, read-only safety flags и `provider_error_class`; direct smoke и targeted tests проверяют taxonomy без raw payload.
- Perp DEX depth freshness evidence v0 готов: `availability_summary.depth_diagnostics.freshness` показывает timestamp, observed_at, age, display max-age policy, stale-depth action и blocked numeric/slippage flags для Lighter/Aster depth diagnostics без slippage bps, route ranking или execution.
- Perp DEX provider state empty/error states v0 готов: Direct/Depth/CoinGlass panels показывают compact provider/source state rows перед detail tables, чтобы provider unavailable, partial data, missing symbols, no-depth и CoinGlass unavailable были видны без route ranking, route selection, numeric route cost bps или execution.
- Preview runtime после depth freshness подтверждён ручным deploy и release smoke на `/opt/deltagrid-preview`; GitHub Deploy Preview требует повторного follow-up gate из-за transient runner/SSH failure, а не из-за product smoke failure.

## Аудит production data — 2026-06-13

- Public smoke-check зелёный: `https://deltagrid.pro`, `/api/v1/health`, `/api/v1/health/readiness` и `/api/v1/data/health` отвечают.
- Контейнеры на сервере healthy: backend, frontend и PostgreSQL работают через `docker-compose.prod.yml`; host-level cron активен и запускается каждые 15 минут.
- Данные в PostgreSQL реально накапливаются: `ohlcv=41000`, `funding_rates=2340`, `open_interest=4260`, `liquidations=1193`, `long_short_ratio=564`, `basis_premium=2271`, `provider_sync_runs=5260`.
- Свежие потоки: CoinGlass snapshots и CoinGecko-derived basis обновлялись примерно за 12 минут до аудита; CoinGlass aggregated liquidations — примерно за 1 час.
- Риск: Binance Futures API на текущем VPS возвращает HTTP `451`, поэтому Binance OHLCV/funding/OI/L/S не обновляются свежо. Последние выборочные Binance timestamps по BTC/ETH/SOL застряли около `2026-06-11 16:00–21:14 UTC`, а `/data/health` помечает `binance` как `degraded`.
- Вывод: MVP1 нужно начинать с provider reliability и freshness SLA, а не с новых визуальных слоёв поверх неполных данных.
- Решение по provider path: direct Binance FAPI не используем как primary на текущем VPS; MVP1 переводит primary CEX perp data path на OKX USDT swaps. Binance остаётся legacy/diagnostic provider.

## Production OKX deploy — 2026-06-13

- OKX primary flow задеплоен на `deltagrid.pro`; backend/frontend пересобраны и перезапущены, production containers healthy.
- Ручной OKX sync `BTC,ETH,SOL` за 24 часа завершился без ошибок: `fetched=5421`, `inserted=5439`, `errors=0`.
- Cron-path проверен без явного provider flag: `/etc/cron.d/deltagrid-market-sync` вызывает общий `scripts/sync-market-data.sh`, новый default использует `okx`; контрольный прогон завершился `errors=0` и пишет CoinGlass liquidations/snapshots с `exchange_list=OKX`.
- `/api/v1/data/health` показывает `okx healthy`, `coinglass healthy`, `coingecko healthy`; `binance` остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451`.
- Production row counts после проверки: `ohlcv=46277`, `funding_rates=2373`, `open_interest=4299`, `liquidations=1288`, `long_short_ratio=636`, `basis_premium=2295`, `provider_sync_runs=5316`.
- MVP1 data quality gate задеплоен на production: `/data/health` возвращает freshness SLA по `symbol + exchange + stream + interval`, health по `sync_type` и cron/data-sync diagnostics. `/data-health` показывает freshness SLA, sync types, cron diagnostics и recent error classes.

## Production Data Quality Gate — 2026-06-13

- Data quality gate задеплоен на `deltagrid.pro`; backend/frontend пересобраны через `docker-compose.prod.yml`, production containers healthy.
- Production `/api/v1/data/health` после деплоя и backfill показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, cron-path `healthy`, OKX/CoinGlass/CoinGecko `healthy`; Binance остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451`.
- `/data-health` через домен показывает `Freshness SLA`, `Sync Types`, `Cron Diagnostics` и `Recent Error Classes`.
- Первый host-level cron после деплоя и 7d backfill сработал в `2026-06-13 00:15 UTC` и завершился `fetched=465`, `inserted=460`, `errors=0`; финальный health после cron показывает `row_counts.ohlcv=77819` и `provider_sync_runs=5351`.
- 72h OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `errors=0`; SQL-проверка покрытия показала `4320/864/72` строк на каждый символ и `gaps=0`.
- 7d OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `fetched=37875`, `inserted=38103`, `errors=0`; SQL-проверка покрытия показала `10080/2016/168` строк на каждый символ и `gaps=0`.

## Interactive Charts v0 — 2026-06-13

- Локальный `/charts` переведён на `lightweight-charts`: свечи, volume histogram, crosshair, pan/zoom/scroll и контролы `symbol + interval + range`.
- График читает OKX USDT Swap историю из существующего read-only data-layer API. Для 7d `1m` режима frontend постранично собирает окно поверх лимита `/data/ohlcv=1000` строк, не меняя backend контракт.
- Browser QA через SSH tunnel к production backend подтвердил desktop `BTC 1m 7d` с `10,080` свечами и mobile `ETH 5m 24h` с `288` свечами.
- Production deploy charts v0 выполнен на `deltagrid.pro`; доменный smoke-check и Browser QA подтвердили desktop `BTC 1m 7d` и mobile `ETH 5m 24h`.
- Следующий milestone по charts backend window endpoint выполнен; security upgrade `next` выполнен до `15.5.19`. Next.js 16 stable проверен и пока не закрывает остаточный `moderate` audit, потому что `next@16.2.9` всё ещё содержит bundled `postcss 8.4.31`; high/critical baseline защищён CI-шагом `npm audit --audit-level=high`.

## Sparse liquidation freshness — 2026-06-14

- Production health после ночи показал один stale поток: `SOL / okx / liquidations / 1h`.
- Причина: `liquidations` является sparse event stream, поэтому отсутствие свежих событий не равно проблеме ingestion, если `coinglass/liquidations` sync-run свежий и успешный.
- Локальная правка разделяет event freshness и sync freshness: `/api/v1/data/health` отдаёт дополнительные sync-поля для sparse streams, а `/data-health` показывает `event age / sync age`.
- Fix задеплоен на `deltagrid.pro`; при свежем sync production freshness summary вернулся к `fresh=24/stale=0/degraded=0`.

## OHLCV window endpoint — 2026-06-14

- Добавлен и задеплоен `GET /api/v1/data/ohlcv/window`, чтобы interactive charts читали `2h/8h/24h/7d` окна одним backend-запросом.
- Endpoint ограничен поддерживаемыми chart-интервалами `1m/5m/1h`, диапазонами `2h/8h/24h/7d` и лимитом `20000` строк.
- Если `end` не задан, правый край окна берётся из последней доступной свечи PostgreSQL, а не из wall-clock времени.
- `/charts` переключён на новый endpoint с fallback на старую постраничную сборку.
- Production smoke-check `/api/v1/data/ohlcv/window?symbol=BTC&exchange=okx&interval=1m&range=7d` вернул `10080/10080` строк; Browser QA `/charts` подтвердил рендер графика.

## Coverage matrix — 2026-06-14

- Добавлен `GET /api/v1/data/coverage` для read-only инвентаризации исторического покрытия по `symbol + exchange + stream + interval`.
- `/api/v1/data/health` теперь включает блок `coverage`; `/data-health` показывает KPI `Coverage` и таблицу `Coverage Matrix`.
- Для регулярных потоков coverage сравнивает фактическое число строк с ожидаемой cadence в окне `24h/7d`: OHLCV, funding, open interest, long/short, basis и `spot_perp_price`.
- Для sparse `liquidations` отсутствие событий не считается отсутствием покрытия, если свежий успешный `coinglass/liquidations` sync-run подтверждает работу ingestion path.
- Production deploy выполнен на `deltagrid.pro`: `/api/v1/data/coverage?...range=24h` показывает `27/27`, а `7d` coverage показывает `18 covered / 9 partial / 0 missing`.
- Следующий milestone после coverage matrix: сформировать production universe v1 и не расширять UI universe активами без честного backend-покрытия.

## Production universe v1 — 2026-06-14

- Добавлен `GET /api/v1/data/universe`, который классифицирует текущий MVP universe поверх coverage/freshness без новых внешних API-вызовов.
- `/api/v1/data/health` включает `universe`, а `/data-health` показывает таблицу `Production Universe`.
- Статусы universe: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`.
- Для MVP1 primary UI universe допускает symbols, у которых chart-critical streams покрыты, freshness зелёный и нет missing tracked streams; partial enrichment streams остаются видимым ограничением, а не скрытым допущением.
- Production deploy выполнен на `deltagrid.pro`: BTC/ETH/SOL классифицированы как `core_perp_ready`, `chart_ready=3/3`, missing streams отсутствуют, partial enrichment streams видны явно.
- Следующий milestone: provider inventory по расширяемому universe до изменения sync-конфигурации и UI selector'ов.

## Provider inventory v0 — 2026-06-15

- Добавлен `GET /api/v1/data/provider-inventory` для read-only проверки кандидатов на расширение universe поверх persisted coverage/freshness.
- Endpoint работает без внешних API-вызовов и не меняет sync-конфигурацию, `SymbolMapper` или UI selector'ы.
- Default candidate set: `BTC/ETH/SOL/HYPE/XRP/DOGE/BNB/ADA/LINK/AVAX/SUI/TON/TRX/DOT/LTC/BCH/AAVE/UNI/APT/ARB`.
- Для каждого symbol возвращаются `promotion_candidate`, `next_action`, readiness status, coverage summaries и freshness tracking.
- Следующий milestone: внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance и только затем расширение aliases/sync universe.

## Provider discovery v1 — 2026-06-15

- Добавлен CLI `python -m app.adapters.data.discover_provider_universe`, который выполняет read-only live discovery без записи в PostgreSQL.
- Проверяются OKX USDT swaps, CoinGlass OKX futures snapshots/liquidations, CoinGecko spot price и Binance USD-M как legacy diagnostic.
- Preview/VPS результат: OKX/CoinGlass/CoinGecko `healthy`, Binance legacy заблокирован `HTTP 451`.
- Все `20/20` MVP1 candidate symbols получили `eligible_for_24h_sync_dry_run`: `BTC/ETH/SOL/HYPE/XRP/DOGE/BNB/ADA/LINK/AVAX/SUI/TON/TRX/DOT/LTC/BCH/AAVE/UNI/APT/ARB`.
- Следующий milestone: `SymbolMapper`/alias expansion plan и 24h sync dry-run малой группы без расширения UI.

## Alias expansion и preview dry-run — 2026-06-15

- `SymbolMapper.seed_defaults()` переведён на идемпотентный upsert и расширен aliases для `HYPE/XRP/DOGE/ADA/LINK`.
- Preview DB засеяна aliases; OKX/CoinGlass/CoinGecko mappings проверены вручную внутри backend container.
- 24h sync dry-run первой малой группы на preview завершён `errors=0`: `fetched=9035`, `inserted=8986`.
- OHLCV по `1m/5m/1h` для `HYPE/XRP/DOGE/ADA/LINK` прошёл с `gaps=0`.
- 24h coverage после dry-run: `covered=30`, `partial=15`, `missing=0`; partial ожидаем у snapshot-потоков `open_interest`, `basis_premium`, `spot_perp_price`.
- Candidate freshness scope вынесен в `/data/provider-inventory`: endpoint считает freshness по запрошенным symbols (`freshness_scope=requested_symbols`), а `/data/health` остаётся scoped к текущему UI universe `BTC/ETH/SOL`.
- Preview-проверка после deploy: `freshness_tracking_required=0`, `history_completion_required=5`, у `HYPE/XRP/DOGE/ADA/LINK` `freshness.worst_status=fresh`, но 7d coverage ещё partial.
- 72h preview backfill завершён `fetched=27065`, `inserted=26902`, `errors=0`; 7d preview backfill завершён `fetched=63125`, `inserted=62858`, `errors=0`.
- 7d coverage первой группы: `covered=30`, `partial=15`, `missing=0`; OHLCV/funding/long-short/liquidations covered, partial остаётся только у snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Preview chart path после 7d backfill готов: OHLCV gaps `0`, `/charts` может читать `HYPE/XRP/DOGE/ADA/LINK` через OKX window endpoint.
- Повторная strict gate-проверка перед full UI promotion показала `promotion_candidates=0`, `ready_for_ui_review=0`, `history_completion_required=5`: у всех 5 symbols `chart_ready=true`, но full analytics universe блокируют partial snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Policy-разделение зафиксировано в provider inventory: `chart_ready_candidates` подходят только для preview `/charts` и `/assets`, а `promotion_candidates` для full analytics universe требуют `complete_history`; `core_perp_ready` с partial snapshot/enrichment streams не считается full promotion.
- Provider inventory теперь классифицирует blocker'ы по способу устранения: `ohlcv`, `funding_rates`, `long_short_ratio` — `history_backfill_supported`, `liquidations` — `provider_sync_required`, а `open_interest`, `basis_premium`, `spot_perp_price` — `snapshot_accumulation_required` в текущем MVP ingestion path.
- Preview frontend разделён на `CORE_SYMBOLS=BTC/ETH/SOL` для `Market Matrix`/`Arbitrage Scanner`/`Perp DEX` и `CANDIDATE_SYMBOLS=HYPE/XRP/DOGE/ADA/LINK` для `/charts` и `/assets`.
- Preview market sync получил отдельный split cron path, но первый реальный scheduled core run выявил transient OKX HTTP `429` на `long_short_ratio`; адаптер стабилизирован через retriable `RateLimitExceeded` и более консервативный OKX pacing.
- Следующий milestone: оставить candidates в chart/asset режиме до 7d накопления snapshot-стримов или отдельно выбрать historical source для OI/basis/spot-perp перед full analytics promotion.
- Product adapter milestone продолжен безопасными read-only slices: Hyperliquid public `metaAndAssetCtxs`, dYdX Indexer `perpetualMarkets`, Lighter public `orderBooks`/`orderBookDetails`/`funding-rates` и Aster public Futures market-data endpoints подключены как normalized snapshots, GMX `markets/info` подключён как raw fixed-point snapshot, а GMX `/tokens` используется для token decimals и pool token amount diagnostics. Perp DEX screen показывает эти источники при доступности backend/provider, `GET /api/v1/perp-dex/route-constraints` фиксирует `research_only` policy без execution, БД-миграций и multi-DEX routing, а `GET /api/v1/perp-dex/route-model` добавляет read-only checklist/formula skeleton для route-level fees/slippage/routing. В route policy добавлены `lighter_direct_snapshot` и `aster_direct_snapshot`: оба разрешены только как display/research context, без route ranking и execution. Lighter/Aster cost semantics metadata v0 теперь явно различает sourced display fields (`maker_fee`/`taker_fee` для Lighter, top-of-book для Aster) и отсутствующие route-ready inputs: account fee tier, order intent, depth curve, slippage model, carry horizon и execution boundary. В route policy также есть `gmx_formula_validation`: официальные sources и diagnostic-only scale notes зафиксированы. GMX `openInterestLong/Short` и `availableLiquidityLong/Short` теперь масштабируются в diagnostic-only USD fields через `1e30`; GMX `fundingRate*`/`borrowingRate*`/`netRate*` описаны как source-backed metadata по hourly ticker semantics, а offline guardrails проверяют ожидаемую relation `netRate=fundingRate-borrowingRate` и observed live-shape fixture. Live smoke показал `raw_rate_relation_plus_with_zero_borrowing`: nonzero-borrowing sides совпали с `funding+borrowing`, zero-borrowing sides ambiguous; `rate_relation_summary` теперь отдаёт эти counts в snapshot/API meta. `rate_source_fields_summary` дополнительно фиксирует, что current `/markets/info` payload не содержит helper inputs `fundingFactorPerSecond`, `borrowingFactorPerSecondForLongs/Shorts` и `longsPayShorts`, поэтому live mapping остаётся blocker перед carry conversion. Production `open_interest_usd`, liquidity ranking и численное route-level pricing остаются заблокированы.
- Route-cost diagnostics продвинуты на один безопасный шаг: `diagnostic_cost_estimate_v0` показывает component readiness, Aster display-only top-of-book spread и published USDT-perp fee defaults, но запрещает суммарный `cost_bps`, route ranking, carry conversion и execution.
- Route-cost diagnostics дополнительно получили summary/guard layer: `Route Diagnostic Components Summary` показывает count display-only и blocked numeric components, а policy smoke/regression tests проверяют обязательные component ids и component-level blockers.
- Route-cost diagnostic summary теперь закреплён в backend response: `diagnostic_cost_estimate_v0.summary` является machine-readable контрактом для UI/smoke и должен совпадать с `components` по counts и id-спискам.
- Route-cost diagnostic summary дополнен venue breakdown: `summary.venue_breakdown` группирует diagnostic components по venue, чтобы видеть, где есть sourced display diagnostics и где numeric components остаются заблокированы.
- Route-cost diagnostic summary дополнен blocker breakdown: `summary.blocker_breakdown` группирует `blocked_by` причины по components/venues, чтобы видеть, какие inputs чаще всего блокируют numeric route cost.
- Route-cost diagnostic summary дополнен required input breakdown: `summary.required_input_breakdown` связывает `components[*].required_input_ids` с обязательными входами route model, чтобы видеть coverage по fee schedule, order intent, depth/impact, carry horizon и risk limits без route scoring.
- Route-cost diagnostic summary дополнен observability rollups: `summary.source_field_breakdown`, `summary.safe_use_breakdown` и `summary.readiness_rollup` показывают sourced display fields, UI boundary text и compact fee/depth/carry/risk readiness без route scoring.
- Lighter depth diagnostics продвинуты на один безопасный шаг: `orderBookOrders` top resting orders дают best bid/ask, display spread и top-order depth summaries, но не дают slippage bps без order size, side, aggregation policy, liquidity cap и risk boundary.
- Aster depth diagnostics продвинуты на один безопасный шаг: `fapi/v3/depth` даёт best bid/ask, display spread и top-level depth summaries, но не даёт slippage bps без order size, side, aggregation policy, liquidity caps, stale-depth policy и risk boundary.
- CoinGlass Perp DEX enrichment v0 добавлен как отдельный research-only слой: `GET /api/v1/perp-dex/venues/coinglass/markets` читает CoinGlass futures `coins-markets` для DEX-like venues (`Aster`, `Lighter`, `EdgeX`, `Drift` по умолчанию) и показывает third-party aggregate rows в отдельной UI-таблице. Эти данные помогают выбрать следующие direct adapters, но не пишутся в PostgreSQL, не считаются direct snapshots, не включают route ranking/execution и явно помечены `production_signal_enabled=false`.
- CoinGlass Perp DEX enrichment получил `coverage_summary`: per-venue matched rows/symbols, available field groups, field coverage, `route_input_status=not_route_input` и `direct_adapter_candidate_hints`. Это подсказка для выбора следующего direct adapter, а не production ranking.
- Для preview/prod добавлен reusable smoke-скрипт `scripts/coinglass-perp-dex-coverage-smoke.sh`: он проверяет CoinGlass Perp DEX coverage endpoint, печатает compact summary без raw payload/секретов и поддерживает thresholds через env.
- Live coverage smoke выбрал `Lighter` и `Aster`; Lighter direct snapshot v0 добавлен первым, а затем Aster direct snapshot v0 добавлен поверх public Futures market-data endpoints. Оба источника остаются read-only research/display context без production route scoring.

## Текущая итерация

- [x] Перевести runtime persistence с SQLite на PostgreSQL.
- [x] Добавить sync PostgreSQL driver `psycopg`.
- [x] Нормализовать `DATABASE_URL` для sync/async/Alembic слоёв.
- [x] Убрать production-зависимость от `Base.metadata.create_all()`.
- [x] Добавить миграцию для `backfill_jobs`.
- [x] Перевести data-layer/backtest timestamp-поля на `BigInteger` для Unix timestamp в миллисекундах.
- [x] Обновить Docker Compose и инструкции запуска.
- [x] Добавить production startup validation для `SECRET_KEY`, `VAULT_MASTER_KEY`, `DATABASE_URL` и `CORS_ORIGINS`.
- [x] Добавить readiness endpoint для проверки PostgreSQL подключения и Alembic head.
- [x] Проверить Docker Compose smoke: backend, frontend, PostgreSQL, `/health`, `/health/readiness`, `/data/health`.
- [x] Подготовить минимальный server deployment flow: `.env.production.example`, `docker-compose.prod.yml`, `DEPLOYMENT.md`.
- [x] Убрать frontend deploy-зависимость от hardcoded `127.0.0.1:8000` в Next.js rewrite и WebSocket URL.
- [x] Добавить Docker ignore-файлы, чтобы production images не тянули локальные env/cache/SQLite/build artifacts.
- [x] Добавить Nginx template и server smoke-check script.
- [x] Добавить server preflight и генератор `.env.production`.
- [x] Добавить Ubuntu bootstrap/deploy scripts и DNS checklist для `deltagrid.pro`.
- [x] Добавить скрипт настройки Nginx и Let's Encrypt SSL для `deltagrid.pro`.
- [x] Учесть занятый порт `3000` на сервере и перевести production frontend binding на `127.0.0.1:3001`.
- [x] Развернуть приложение на сервере `2.25.143.143` в `/opt/deltagrid`.
- [x] Выпустить SSL и проверить `https://deltagrid.pro`.
- [x] Добавить ручную production-safe команду синка Binance market data в PostgreSQL.
- [x] Расширить sync до CoinGlass v4 snapshots и CoinGecko-derived basis snapshots.
- [x] Подготовить host-level cron для регулярного market data sync.
- [x] Установить host-level cron на сервере `2.25.143.143` и проверить `cron` service.
- [x] Подключить `Funding` и `/data-health` frontend screens к persisted backend/data-layer endpoint'ам.
- [x] Исправить кликабельность nested tabs в `Funding` и `Perp DEX`.
- [x] Подключить `Market Overview` к live backend endpoints: CoinGecko global/markets, alternative.me Fear & Greed, CoinGlass funding и data health.
- [x] Подключить `Assets` к live SOL spot/funding/OHLCV и убрать fake order book/liquidations из production UI.
- [x] Открыть read-only data endpoints для `open_interest`, `long_short_ratio`, `basis_premium` и `liquidations`.
- [x] Подключить `Charts`, `Market Matrix` и `Arbitrage Scanner` к persisted backend/data-layer streams.
- [x] Убрать fake backtest output из `Strategy Lab` и заменить его на readiness live inputs.
- [x] Стабилизировать live data SSR: снизить параллельность потоков, добавить backend fetch timeout и env-настройки SQLAlchemy pool.
- [x] Подключить CoinGlass aggregated liquidation history к production sync и существующему `/data/liquidations` endpoint.
- [x] Выполнить демо-доводку live UI: добавить числовые шкалы/диапазоны на графики, переключение BTC/ETH/SOL в `Assets`, price-first heatmap и логотипы CoinGecko в `Market Overview`.
- [x] Задеплоить демо-доводку live UI на `deltagrid.pro` и проверить `/market`, `/charts`, `/assets`, `/perp-dex` через домен.
- [x] Выполнить быструю преддемо-доводку: убрать stablecoin-like активы из `Market Overview`, расширить видимый historical slice графиков до 240 точек и добавить hover-title для line/bar/candle charts.
- [x] Перевести `Perp DEX` из почти пустого pending-экрана в live readiness screen по текущим Binance/CoinGlass/CoinGecko потокам без fake DEX venue metrics.
- [x] Выполнить `Assets` symbol polish: убрать hardcoded `SOLUSDT`, привести workspace tab к нейтральному `Assets` и считать liquidation bars от live totals.
- [x] Выполнить финальный демо-polish `Funding`, `Arbitrage Scanner` и `Market Matrix`: source-плашки, time labels, readable research candidates и coverage/status columns.
- [x] Выполнить `Strategy Lab` readiness polish: заменить пустой output chart на честный boundary state, отформатировать input charts и убрать `Backtest #1` tab label.
- [x] Выполнить presentation safety sweep: заменить грубые `mock/fake/coming soon` UI-формулировки на production-oriented readiness labels.

## Следующие шаги

- [x] MVP1/P0: выбрать production-safe решение для Binance HTTP `451`: primary CEX perp provider переключён на OKX без прокси/VPN.
- [x] MVP1/P0: добавить backend `OkxAdapter` для OHLCV, funding history, OI snapshots и long/short account ratio.
- [x] MVP1/P0: переключить frontend terminal read-side на `exchange=okx` для primary persisted streams.
- [x] MVP1/P0: задеплоить OKX primary flow на `deltagrid.pro`, выполнить ручной sync и проверить свежие OKX row timestamps.
- [x] MVP1/P0: выполнить контрольный 24h backfill BTC/ETH/SOL по `1m/5m/1h` через OKX и проверить `gaps=0`.
- [x] MVP1/P0: добавить freshness SLA в `/api/v1/data/health` по потокам, символам и интервалам: `latest_timestamp`, `age_minutes`, expected cadence, stale/degraded reason.
- [x] MVP1/P0: разделить provider health по `sync_type`, чтобы частичный `long_short_ratio` не скрывал состояние OHLCV/funding/OI и наоборот.
- [x] MVP1/P0: добавить cron/data-sync monitor: последние успешные/частичные запуски, счётчик ошибок HTTP `451`/rate limit/circuit breaker, понятный alert в `/data-health`.
- [x] MVP1/P0: задеплоить data quality gate на `deltagrid.pro` и проверить production JSON/UI после следующего cron-triggered run.
- [x] MVP1/P1: расширить backfill до 72h/7d перед интерактивными графиками и отдельно проверить gaps/freshness.
- [x] MVP1/P1: после data quality gate реализовать локальный interactive historical charts v0 на `lightweight-charts`.
- [x] MVP1/P1: задеплоить charts v0 на `deltagrid.pro` и проверить доменный `/charts` на desktop/mobile.
- [x] MVP1/P1: задеплоить sparse liquidation freshness fix и проверить production `/data-health`.
- [x] MVP1/P1: задеплоить backend OHLCV window endpoint для 7d/1m и проверить production `/charts`.
- [x] MVP1/P1: добавить coverage matrix для BTC/ETH/SOL по основным persisted streams.
- [x] MVP1/P1: сформировать production universe v1 поверх coverage/freshness.
- [x] MVP1/P1: обновить frontend Next.js до `15.5.19` и закрыть critical/high audit advisory для `next@14.1.0`.
- [x] Прогнать миграции на чистой PostgreSQL БД в локальном Docker.
- [x] Проверить основные backend routes после миграции: `/health`, `/data/health`, `/data/ohlcv`, `/market/trending`.
- [x] На реальном сервере создать `.env.production` с реальными secrets для `deltagrid.pro` и PostgreSQL `DATABASE_URL`.
- [x] Прогнать `DOMAIN=deltagrid.pro sh scripts/server-preflight.sh` на сервере.
- [x] Перенаправить DNS `deltagrid.pro`/`www.deltagrid.pro` на `2.25.143.143` и убрать старую `AAAA`-запись для корня.
- [x] Проверить reverse proxy/SSL на `deltagrid.pro` по `DEPLOYMENT.md`.
- [x] Выпустить Let's Encrypt SSL после DNS cutover.
- [x] Прогнать `scripts/server-smoke.sh` локально на сервере и через `https://deltagrid.pro`.
- [x] Выполнить первый ручной sync market data на сервере и проверить `row_counts` в `/api/v1/data/health`.
- [ ] Добавить email к Let's Encrypt account для уведомлений о продлении сертификата.
- [ ] Запланировать reboot сервера после pending kernel upgrade.
- [ ] Проверить первый cron-triggered market data sync по `/var/log/deltagrid-market-sync.log`.
- [x] Включить preview Nginx HTTP site `deltagrid-preview` и проверить routing через `Host: preview.deltagrid.pro`.
- [ ] Добавить DNS-запись `preview.deltagrid.pro` и выпустить SSL через `scripts/configure-preview-nginx-ssl.sh`.
- [x] Создать dedicated SSH deploy key и добавить public key на VPS для GitHub Actions.
- [x] Синхронизировать `main` и `preview` на актуальных ops/deploy workflows после проверки CI.
- [x] Добавить и проверить GitHub repository secrets `PREVIEW_*`, чтобы `Deploy Preview` выполнял реальный deploy вместо skip.
- [x] Подготовить production deploy diagnostics/hardening в `preview` без изменения production runtime.
- [x] Перенести production deploy hardening в `main` и выполнить read-only preflight против `/opt/deltagrid`.
- [x] Добавить ручной запуск `Deploy Production` через `workflow_dispatch` для контрольного deploy после настройки secrets.
- [x] Подготовить внешний production healthcheck workflow.
- [x] Добавить reusable PostgreSQL backup script.
- [x] Выполнить первый production backup текущей PostgreSQL БД и проверить gzip integrity.
- [x] Подключить backup-скрипт к production deploy path как default safety step.
- [ ] Добавить GitHub repository secrets `PROD_*`, чтобы `Deploy Production` перестал safe-skip.
- [ ] Подтвердить реальный production auto-deploy через `/opt/deltagrid` после настройки `PROD_*`, запустив `Deploy Production` вручную на `main`.
- [ ] Выполнить следующий production backup через `scripts/backup-postgres.sh` после доставки скрипта на сервер.
- [x] Подключить Funding/Data Health frontend screens к backend/data-layer endpoint'ам.
- [x] Подключить Market Matrix, Arbitrage Scanner, Charts и Strategy Lab к backend/data-layer endpoint'ам или честным pending/readiness states.
- [x] Задеплоить live data SSR fix и проверить `/charts`, `/market-matrix`, `/arbitrage-scanner`, `/strategy-lab` через Cloudflare.
- [x] Довести interactive historical charts после production QA: доменный smoke-check, backend window endpoint и coverage matrix выполнены.
- [x] Сформировать production universe v1 на основе coverage matrix.
- [x] Провести provider inventory v0 для расширения universe за пределы BTC/ETH/SOL через read-only persisted-data endpoint.
- [x] Провести внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper` и sync universe.
- [x] Подготовить `SymbolMapper`/alias expansion plan для первой малой группы `HYPE/XRP/DOGE/ADA/LINK`.
- [x] Выполнить 24h sync dry-run первой малой группы на preview без расширения UI.
- [x] Расширить freshness SLA scope для первой малой группы или явно отделить candidate freshness от current UI universe freshness.
- [x] Выполнить 72h/7d preview backfill первой малой группы и проверить gaps/coverage перед расширением UI universe.
- [x] Включить первую малую группу как preview chart/asset candidates в `/charts` и `/assets`; full analytics screens оставить на `BTC/ETH/SOL` до строгого promotion gate.
- [x] Добавить provider-inventory `chart_ready_candidates` и ручной preview candidate smoke для проверки `/charts`/`/assets` без расширения full analytics universe.
- [x] Добавить provider-inventory `promotion_blockers`: отдельные coverage/freshness blockers и summary-счётчики причин, почему symbol ещё не проходит full analytics promotion.
- [x] Добавить provider-inventory summary-разбивку blocker'ов по stream, чтобы быстро видеть, какие persisted streams блокируют full analytics promotion.
- [x] Добавить provider-inventory resolution strategy для blocker'ов, чтобы отличать historical backfill от snapshot accumulation.
- [x] Подготовить отдельный preview market sync cron path, чтобы candidate freshness не зависела только от one-off backfill/sync.
- [x] Стабилизировать OKX rate-limit handling для preview cron: HTTP `429` теперь retriable, default OKX pacing снижен.
- [x] Закрыть `history_completion_required=5` по `open_interest`, `basis_premium`, `spot_perp_price` или явно зафиксировать policy-разделение `chart_ready` и full analytics universe.
- [x] Отдельно оценить backfill/ingestion для 7d `open_interest`, `basis_premium`, `spot_perp_price`: текущий ingestion пишет snapshots, поэтому один historical backfill не закрывает эти 7d blockers.
- [ ] Если full analytics promotion нужен быстрее 7d окна накопления, выбрать отдельный historical source для OI/basis/spot-perp и описать его data quality constraints.
- [x] Подключить read-only Hyperliquid public market snapshot v0 для Perp DEX.
- [x] Подключить read-only dYdX Indexer market snapshot v0 для Perp DEX.
- [x] Подключить read-only GMX public `markets/info` raw snapshot v0 для Perp DEX без нормализации fixed-point liquidity/OI.
- [x] Добавить Perp DEX route constraints policy endpoint и UI-таблицу, чтобы явно блокировать liquidity ranking, route-level pricing и execution до готовности модели.
- [x] Добавить GMX token decimals diagnostics через `/tokens`: index/long/short token metadata резолвится, но raw fixed-point metrics остаются без конвертации.
- [x] Добавить GMX pool token amount diagnostics: `poolAmountLong/Short` масштабируются в token units через decimals из `/tokens`, но не используются как USD liquidity/OI.
- [x] Зафиксировать GMX fixed-point source validation metadata v0 в `route-constraints`: diagnostic-only notes без включения GMX liquidity/OI в production signal.
- [x] Добавить GMX OI/liquidity USD diagnostics: `openInterestLong/Short` и `availableLiquidityLong/Short` масштабируются через `1e30` в diagnostic-only поля, но не в production `open_interest_usd`.
- [x] Добавить route-level fees/slippage/routing model v0 как read-only checklist/formula skeleton без numeric estimates, ranking и execution.
- [x] Описать GMX funding/borrowing/net rate semantics как source-backed metadata без carry conversion.
- [x] Добавить offline GMX rate relation guardrail без carry conversion.
- [x] Добавить CoinGlass Perp DEX enrichment v0 для DEX-like venues как research-only third-party aggregate слой без ranking/execution.
- [x] Добавить CoinGlass Perp DEX coverage summary v0 и UI-таблицу coverage hints без включения liquidity ranking.
- [x] Добавить reusable smoke script `scripts/coinglass-perp-dex-coverage-smoke.sh` для preview/prod проверки CoinGlass Perp DEX coverage без вывода raw payload и секретов.
- [x] Выполнить live CoinGlass Perp DEX coverage smoke локально через FastAPI endpoint с real CoinGlass key: candidate hints `Lighter`, `Aster`, `6` rows, `2` venues with matches.
- [x] Добавить Lighter direct read-only Perp DEX snapshot v0 поверх public `orderBooks`, `orderBookDetails` и `funding-rates` без ranking/execution.
- [x] Провести Aster official API review и добавить direct read-only Perp DEX snapshot v0 поверх public Futures market-data endpoints без ranking/execution.
- [x] Добавить diagnostic-only fee/depth/slippage semantics metadata для Lighter/Aster перед любым numeric route-cost layer.
- [x] Добавить diagnostic route-cost components v0: Aster top-of-book spread display-only, published fee defaults metadata и UI-компоненты без total bps/ranking/execution.
- [x] Добавить Lighter `orderBookOrders` depth diagnostics v0: top resting orders, spread и top-order depth summaries без slippage/ranking/execution.
- [x] Добавить Aster `fapi/v3/depth` depth diagnostics v0: top depth levels, spread и top-level depth summaries без slippage/ranking/execution.
- [x] Добавить direct Perp DEX smoke script для preview/prod проверки direct venue endpoints без raw payload и секретов.
- [x] Добавить `Depth Diagnostics` и `Route Blockers Matrix` в Perp DEX UI поверх существующего route policy/model.
- [x] Расширить route policy/model blockers структурированными `missing_inputs`, `blocked_by` и `safe_use` без включения ranking/execution.
- [x] Добавить `Route Diagnostic Components Summary` и проверки `diagnostic_cost_estimate_v0.components` в policy smoke/backend tests без включения total route cost bps.
- [x] Добавить backend `diagnostic_cost_estimate_v0.summary` и consistency checks между summary и components в policy smoke/backend tests.
- [x] Добавить `summary.venue_breakdown` и UI `Route Diagnostic Venue Breakdown` для venue-level readiness без route scoring.
- [x] Добавить `summary.blocker_breakdown` и UI `Route Diagnostic Blocker Breakdown` для blocker-level readiness без route scoring.
- [x] Добавить `summary.required_input_breakdown` и UI `Route Diagnostic Required Input Breakdown` для required-input coverage без route scoring.
- [x] Добавить `summary.source_field_breakdown` и UI `Route Diagnostic Source Fields Breakdown` для source-field coverage без route scoring.
- [x] Добавить `summary.safe_use_breakdown` и UI `Route Diagnostic Safe Use Breakdown`, чтобы display diagnostics не смешивались с route signals.
- [x] Добавить `summary.readiness_rollup` и UI `Route Diagnostic Readiness Rollup` для compact fee/depth/carry/risk readiness без route scoring.
- [x] Провести отдельный regression pass Next.js 16.x: stable `16.2.9` не убирает остаточный `moderate` audit по bundled `postcss <8.5.10`.
- [x] Закрыть свежий frontend high advisory `form-data@4.0.5` через lockfile update до `form-data@4.0.6`; `npm audit --audit-level=high` снова проходит без `--force`.
- [ ] Дождаться stable Next.js patch с bundled `postcss >=8.5.10`.
- [x] Добавить GMX carry-readiness audit: `carry_readiness_summary`, `carry_input_checklist`, UI panels и compact smoke fields без diagnostic carry bps.
- [x] Добавить GMX carry-source evidence gate: `carry_source_evidence_summary`, `carry_source_evidence_checklist`, UI panels и compact smoke fields без diagnostic carry bps.
- [x] Добавить GMX live helper source review: `live_helper_source_summary`, `live_helper_source_checklist`, UI panel и compact smoke fields без diagnostic carry bps.
- [ ] Подключить sourced fee/depth/carry inputs перед численным route-level scoring только после отдельного явного решения и сохранения safety gates.
- [ ] Подключить route-ready sourced depth/slippage model для Lighter: order-size-aware top-order aggregation, liquidity caps и slippage math перед любым route-level scoring.
- [ ] Подключить route-ready sourced fee schedule и slippage model для Aster перед любым route-level scoring.
- [ ] Расширить CoinGlass data adapter до дополнительных provider-specific L/S потоков, если Binance global L/S будет недостаточно для MVP.
- [ ] Реализовать backtest engine и scheduler после data quality gate.

### Follow-up по версии `v1.3.2`

- `preview` находится на `d3de35e`, `VERSION=1.3.2`, GitHub CI run `27744113125` прошёл `success`.
- GitHub `Deploy Preview` run `27744161749` завершился `failure` на шаге `Deploy preview`, но ручной запуск того же `scripts/deploy-compose-stack.sh` по SSH успешно обновил `/opt/deltagrid-preview` до `d3de35e`; backend/frontend containers healthy, server smoke прошёл.
- Follow-up `preview@b257cc8` прошёл GitHub CI `27746664616` и `Deploy Preview` `27746714283`; `/opt/deltagrid-preview` обновлён до `b257cc8`, preview release smoke на `8011/3012` прошёл.
- Итерация release runway усилила diagnostics, добавила release smoke wrapper, выполнила preview smoke/Browser QA через SSH tunnel и создала production backup `/opt/deltagrid/backups/deltagrid-v140-runway_20260618T081912Z.sql.gz`.
- `main`, production deploy и tag `v1.3.2` пока не трогались. Следующий production target — minor release `v1.4.0`.

### План новой версии `v1.4.0`

- Итерация 1: release runway и deploy hardening — зелёный GitHub `Deploy Preview` получен на follow-up `b257cc8`, deploy diagnostics усилены, `PROD_*` checklist подготовлен, production backup выполнен через новый script, release smoke checklist зафиксирован.
- Итерация 2: Perp DEX research cockpit v1.4 read-only — source status rollup, provider availability/error taxonomy, GMX helper/source follow-up, Lighter/Aster depth/fee evidence layers и улучшенные UI empty/error states без route scoring.
- Итерация 3: `v1.4.0` release candidate и production rollout — version bump, full regression/smoke/build/audit pass, preview deploy gate, merge в `main`, production backup/deploy, production smoke и annotated tag `v1.4.0`.
- Граница `v1.4.0`: trading, execution, route ranking, route selection и numeric route cost bps не включаются без отдельного явного решения; итог релиза — production-ready research/observability слой и зелёный deploy path.

## Критерии готовности к деплою

- `python -m alembic upgrade head` проходит на пустой PostgreSQL.
- Backend стартует с `DEBUG=false`, сильным `SECRET_KEY` и заданным `VAULT_MASTER_KEY`.
- `GET /api/v1/health/readiness` возвращает `ready` и показывает актуальный Alembic head.
- Основные API routes возвращают 200 или ожидаемые пустые состояния.
- Нет production-зависимости от SQLite `.db` файла.
- Docker Compose или server deployment выполняет миграции до старта приложения.
