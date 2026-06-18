# Backlog — DeltaGrid

## Рабочий pipeline — 2026-06-16

Текущий порядок итераций:

1. **CI/CD и release safety** — закрыть `PROD_*`, подтвердить реальный `Deploy Production`, затем держать deploy path зелёным перед новыми product/data изменениями.
2. **Production ops-наблюдаемость** — внешний uptime/readiness monitoring, backup PostgreSQL перед миграциями/деплоем, certbot email, отдельное окно reboot.
3. **Preview publication** — DNS `preview.deltagrid.pro`, SSL и public preview smoke, чтобы future data/product изменения проверять вне production.
4. **Data promotion gate** — оценить 7d ingestion/backfill для `open_interest`, `basis_premium`, `spot_perp_price` по `HYPE/XRP/DOGE/ADA/LINK`; текущий вывод: эти потоки snapshot-only в MVP ingestion, поэтому candidates остаются в chart/asset mode до 7d накопления или отдельного historical source.
5. **Product data adapters** — live Perp DEX venue adapters после стабильного data/ops слоя; Hyperliquid, dYdX, Lighter и Aster public snapshots v0 подключены read-only как normalized venue snapshots, GMX подключён как raw fixed-point snapshot с token decimals, pool token amount diagnostics, diagnostic USD OI/liquidity, source-backed rate semantics metadata, offline rate relation guardrails, `rate_relation_summary` и `rate_source_fields_summary`; live `/markets/info` показывает nonzero-borrowing relation `funding+borrowing`, zero-borrowing ambiguity и отсутствие helper inputs (`fundingFactorPerSecond`, `longsPayShorts`, side borrowing factors), поэтому требует отдельного mapping review до carry conversion. CoinGlass Perp DEX enrichment v0 добавлен как research-only third-party aggregate слой для DEX-like venues; `coverage_summary` показал `Lighter` и `Aster` как первые candidate hints, оба уже подключены как direct read-only adapters, но не являются ranking/execution input. Route model v0 добавлен как read-only checklist/formula skeleton; Lighter/Aster cost semantics metadata v0 уже различает display fee/top-of-book fields и route-ready inputs, а численный routing/execution остаются отдельными задачами.
   Diagnostic route-cost components v0 добавлен как компонентный read-only слой: Aster top-of-book spread и published fee defaults можно показывать в diagnostics, но total cost bps, ranking и execution остаются заблокированы.
   Lighter `orderBookOrders` depth diagnostics v0 добавлен как top resting order слой: best bid/ask, spread и top-order depth summaries можно показывать, но slippage/ranking требуют отдельной модели.
   Aster `fapi/v3/depth` diagnostics v0 добавлен как display-only depth ladder слой: best bid/ask, spread и top-level depth summaries можно показывать, но slippage/ranking требуют order-size aggregation, liquidity caps и stale-depth policy.
   Perp DEX diagnostics hardening v0 добавлен как UI/API safety layer: direct venue smoke script, таблица `Depth Diagnostics`, структурированные route blockers (`missing_inputs`, `blocked_by`, `safe_use`) и `Route Blockers Matrix` помогают проверять read-only готовность без включения route ranking/execution.
   Perp DEX policy smoke and output policy v0 добавлен как следующий safety layer: `scripts/perp-dex-policy-smoke.sh`, `Route Output Policy`, `Route Model Blockers` и regression-инварианты по структурированным blockers закрепляют, что numeric cost bps, ranking и execution остаются выключены.
   Perp DEX required inputs and direct smoke guardrails v0 добавлен как следующий маленький слой: direct venue smoke теперь проверяет read-only/ranking/production flags, а UI показывает `Route Required Inputs` как отдельный checklist перед route-ready моделью.
   Perp DEX route safety guardrails v0 добавлен как summary layer: `Route Safety Guardrails` показывает expected vs actual по верхнеуровневым flags, а policy smoke проверяет required inputs и formula skeleton keys.
   Perp DEX diagnostic components summary v0 добавлен как component-level summary layer: `Route Diagnostic Components Summary`, policy smoke и backend regression tests закрепляют структуру `diagnostic_cost_estimate_v0.components` без включения total cost bps, ranking или execution.
   Perp DEX diagnostic component summary contract v0 добавлен как backend contract layer: `diagnostic_cost_estimate_v0.summary` согласован с component list, UI читает summary из backend, а smoke/tests проверяют counts и id-списки без включения route scoring.
   Perp DEX diagnostic venue breakdown v0 добавлен как venue-level observability layer: `summary.venue_breakdown` и UI `Route Diagnostic Venue Breakdown` показывают Lighter/Aster/cross-venue readiness без route scoring.
   Perp DEX diagnostic blocker breakdown v0 добавлен как blocker-level observability layer: `summary.blocker_breakdown` и UI `Route Diagnostic Blocker Breakdown` показывают повторяющиеся blockers без route scoring.
   Perp DEX diagnostic required input breakdown v0 добавлен как required-input observability layer: `components[*].required_input_ids`, `summary.required_input_breakdown` и UI `Route Diagnostic Required Input Breakdown` показывают coverage обязательных входов без route scoring.
   Perp DEX diagnostic observability rollups v0 добавлены как source/safe-use/readiness layer: `summary.source_field_breakdown`, `summary.safe_use_breakdown`, `summary.readiness_rollup` и UI-таблицы показывают source fields, display boundaries и fee/depth/carry/risk readiness без route scoring.
   Perp DEX diagnostic depth policy and smoke compare v0 добавлен как следующий observability layer: `summary.depth_staleness_policy_checklist`, UI `Route Diagnostic Depth/Staleness Policy` и compact policy smoke contract/diff фиксируют stale-depth gates без slippage bps, route ranking или execution.
   Perp DEX diagnostic next actions breakdown v0 добавлен как planning observability layer: `summary.next_action_breakdown`, UI `Route Diagnostic Next Actions` и compact smoke `next_action_ids` показывают следующие research actions без route scoring.
   Perp DEX diagnostic policy input breakdown v0 добавлен как research-readiness layer: `summary.required_policy_input_breakdown`, UI `Route Diagnostic Policy Inputs` и compact smoke `required_policy_input_ids` показывают required policy inputs для depth/staleness gates без route scoring.
   Perp DEX diagnostic source input actions coverage v0 добавлен как research-readiness layer: `summary.source_input_action_coverage`, UI `Route Diagnostic Source Input Actions`, compact smoke `source_input_action_fields` и docs/smoke compare пример показывают связь source fields, required inputs и next actions без route scoring.
   Perp DEX route-ready evidence checklist v0 добавлен как pre-route-scoring readiness layer: `summary.route_ready_evidence_checklist`, UI `Route Diagnostic Evidence Checklist` и compact smoke `route_ready_evidence_gate_ids` показывают evidence gates по fee/order/depth/carry/risk без включения cost bps, ranking или execution.
   Perp DEX venue evidence and GMX mapping review v0 добавлен как pre-route-scoring safety layer: `summary.venue_evidence_status`, `gmx_rate_mapping_review_v0`, UI `Route Diagnostic Venue Evidence Status`/`GMX Rate Mapping Review` и compact smoke `venue_evidence_status_ids`/`gmx_rate_mapping_review_ids` разделяют venue-specific/cross-venue/GMX mapping gaps без carry conversion, ranking или execution.
   Perp DEX GMX mapping evidence hardening v0 добавлен как следующий read-only слой: `gmx_rate_mapping_review_v0.blocker_breakdown`, `fixture_readiness_matrix`, UI `GMX Rate Mapping Blockers`/`GMX Rate Fixture Readiness` и compact smoke `gmx_rate_mapping_status`/`gmx_rate_mapping_blocker_ids`/`gmx_rate_fixture_case_ids` показывают repeated blockers и side-aware fixture gaps без carry conversion, route scoring или execution.
   Perp DEX GMX fixture/source hardening v0 добавлен как следующий read-only слой: `gmx_rate_mapping_review_v0.side_aware_fixture_expectations`, `mapping_decision_checklist`, UI `GMX Rate Side-aware Fixtures`/`GMX Rate Mapping Decision Checklist` и compact smoke `gmx_rate_fixture_statuses`/`gmx_rate_mapping_decision_statuses` показывают fixture/status/manual-review gaps без diagnostic carry bps, route scoring или execution.
   Perp DEX GMX carry-readiness audit v0 добавлен как следующий read-only слой: `gmx_rate_mapping_review_v0.carry_readiness_summary`, `carry_input_checklist`, UI `GMX Rate Carry Readiness Summary`/`GMX Rate Carry Input Checklist` и compact smoke `gmx_rate_carry_*` показывают carry horizon/notional/sign/source/display gates без diagnostic carry bps, route scoring или execution.
   Perp DEX GMX carry-source evidence gate v0 добавлен как следующий read-only слой: `gmx_rate_mapping_review_v0.carry_source_evidence_summary`, `carry_source_evidence_checklist`, UI `GMX Rate Carry Evidence Summary`/`GMX Rate Carry Evidence Checklist` и compact smoke `gmx_rate_carry_evidence_*` показывают source/fixture/runtime/manual evidence gaps без diagnostic carry bps, route scoring или execution.
   Perp DEX Lighter/Aster fee schedule evidence v0 добавлен как следующий read-only слой: `summary.fee_schedule_evidence_summary`, `summary.fee_schedule_evidence_checklist`, UI `Route Diagnostic Fee Schedule Evidence`/`Route Diagnostic Fee Schedule Checklist` и compact smoke `fee_schedule_evidence_*` показывают account tier/order intent/manual approval gates без fee bps total, route scoring или execution.
   Perp DEX Source Status compare contract v0 добавлен как release/readiness слой: `scripts/perp-dex-source-status-smoke.sh` собирает direct venues, GMX raw, CoinGlass enrichment, route policy/model и release-smoke checklist в compact source-status contract, поддерживает `COMPARE_BASE_URL`/`FAIL_ON_DIFF=1` и показывает preview/prod drift без полного payload, ranking, route selection, cost bps или execution.
   Perp DEX provider state empty/error states v0 добавлен как UI-readiness слой: `Direct Perp DEX Market Snapshots`, `Depth Diagnostics` и `CoinGlass Perp DEX Enrichment` теперь показывают compact state rows по provider availability, partial data, missing symbols, depth freshness и research-only boundary даже при пустых detail rows; новых provider calls, route ranking, route selection, numeric route cost bps или execution не добавлено.
6. **Strategy/backtest** — настоящий backtest engine и scheduler после стабилизации исторических рядов и формального описания формул PnL/drawdown/trades.

### Следующий Perp DEX route-model observability блок

- [x] Добавить required-input breakdown для diagnostic components: связать `components[*].required_input_ids` с `required_inputs` и показать coverage в UI/smoke/tests.
- [x] Добавить source-fields breakdown: агрегировать sourced fields по component/venue/input, чтобы видеть, какие поля уже есть только как display diagnostics.
- [x] Добавить safe-use breakdown: агрегировать `safe_use`/display-only boundaries, чтобы быстро находить места, где UI может выглядеть как route signal.
- [x] Добавить staleness/depth policy checklist для Lighter/Aster depth diagnostics без расчёта slippage bps.
- [x] Добавить compact policy smoke diff summary для preview/prod сравнения route-model observability contract.
- [x] Добавить UI compact readiness rollup по fee/depth/carry/risk без numeric total bps и без сортировки venues.
- [x] Обновить route-model документацию после каждого нового observability слоя и явно сохранять запрет на route ranking/execution.
- [x] Добавить next-action breakdown: агрегировать planning actions из required inputs, readiness rollup и depth policy в backend/UI/smoke/tests без route scoring.

### Следующий Perp DEX research-readiness блок

- [x] Добавить matrix по `required_policy_inputs` для depth/staleness checklist: где input нужен, какие policy rows его блокируют, какие components/venues затронуты.
- [x] Добавить coverage summary по `source_fields -> required_inputs -> next_actions`, чтобы видеть, какие display fields уже есть, но всё ещё не закрывают route-ready input.
- [x] Добавить compact docs/smoke пример для preview/prod diff с `next_action_ids` и `depth_policy_ids`.
- [x] Добавить route-ready evidence checklist: fee/order/depth/carry/risk gates, blocked outputs и явные `cost/rank/exec=false` до решения о numeric route model.

### Следующий Perp DEX pre-route-scoring safety блок

- [x] Добавить per-venue evidence status для Lighter/Aster/GMX, чтобы отличать venue-specific gaps от cross-venue gates без route ranking.
- [x] Добавить decision note в docs для будущего перехода от evidence checklist к numeric route-cost model: какие источники, fixture coverage и ручные подтверждения нужны до первой формулы bps.
- [x] Подготовить GMX rate mapping review как отдельный read-only блок поверх `rate_relation_summary`/`rate_source_fields_summary` без carry conversion.

### Следующий Perp DEX mapping/evidence hardening блок

- [x] Добавить per-review blocker breakdown для `gmx_rate_mapping_review_v0`, чтобы видеть, какие blockers повторяются между source helper inputs, live mapping и carry boundary.
- [x] Добавить compact compare fields для GMX mapping status/details без вывода full review payload.
- [x] Подготовить fixture-readiness matrix для GMX side-aware cases: nonzero borrowing, zero borrowing ambiguity, longsPayShorts direction, missing helper inputs.

### Следующий Perp DEX GMX fixture/source hardening блок

- [x] Добавить side-aware fixture expectation notes для `longsPayShorts`: какие long/short cases должны покрыть paying/receiving direction до carry bps.
- [x] Добавить read-only GMX mapping decision checklist: какие source fields, fixture cases и manual review approvals нужны перед первым diagnostic carry bps.
- [x] Добавить compact smoke diff для GMX fixture statuses отдельно от ids, чтобы preview/prod drift ловил изменение статуса без full payload.

### Следующий Perp DEX GMX carry-readiness audit блок

- [x] Добавить read-only carry input checklist breakdown: `holding_period_hours`, `position_notional_usd`, side/sign convention и display unit decision без расчёта carry bps.
- [x] Добавить compact smoke fields для GMX decision checklist statuses и manual approval ids в preview/prod diff без full payload.
- [x] Подготовить docs decision gate для первого diagnostic carry bps: какие fixtures, approvals и tests нужны до отдельного явного решения.

### Следующий Perp DEX GMX carry-source evidence gate блок

- [x] Добавить evidence rows для GMX carry checklist: какие source/fixture/manual approval artifacts реально закрывают каждый carry input.
- [x] Добавить smoke/docs compare для `gmx_rate_carry_manual_approval_ids`, carry input statuses и `gmx_rate_carry_evidence_*` против preview/prod, не выводя full payload.
- [ ] Обсуждать первый diagnostic carry bps только после source helper inputs, side-aware fixtures, horizon/notional policy и отдельного явного решения.

### Следующий Perp DEX GMX live helper source review блок

- [x] Разобрать live GMX `/markets/info` nonzero-borrowing rate mapping поверх `rate_relation_summary` и `rate_source_fields_summary` без carry conversion.
- [x] Подготовить side-aware fixture artifacts для `longsPayShorts` и helper inputs, если live payload или fixtures дадут недостающие поля.
- [x] Оставить diagnostic carry bps, route cost bps, route ranking, route selection и execution заблокированными до отдельного явного решения.

### План новой версии `v1.3.2`: 2 итерации по 10 задач

#### Итерация 1 — Perp DEX GMX live helper source review v0

- [x] Изучить текущий GMX provider/client, normalizer, route-model builder, fixtures и tests, не меняя public API.
- [x] Найти, какие live `/markets/info` поля уже доступны в GMX rows: `fundingRate*`, `borrowingRate*`, `netRate*`, helper source fields и side-direction hints.
- [x] Добавить read-only backend review для live helper/source fields внутри `gmx_rate_mapping_review_v0` без carry conversion.
- [x] Зафиксировать nonzero-borrowing relation evidence как status/checklist rows, не переводя raw rates в percent/bps/carry.
- [x] Расширить side-aware fixture artifacts только для evidence/status: `longsPayShorts`, long/short paying/receiving cases и missing helper inputs.
- [x] Добавить compact smoke keys для live helper/source review ids, statuses и missing helper fields без вывода raw payload.
- [x] Добавить backend regression tests на consistency summary/checklist и неизменные safety flags.
- [x] Протянуть frontend types и небольшую observability-панель `GMX Rate Live Helper Source Review`.
- [x] Обновить русскую документацию: `CHANGELOG.md`, `CURRENT_TASK.md`, `BACKLOG.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `README.md`.
- [x] Прогнать проверки: backend compileall, `pytest backend/tests/test_perp_dex_policy.py`, `bash -n scripts/perp-dex-policy-smoke.sh`, HTTP policy smoke, frontend build/audit и Browser QA `/perp-dex?view=opportunities`.

#### Итерация 2 — release stabilization, version bump и GitHub push

- [x] Выполнить full regression pass по Perp DEX direct/policy smoke и core backend tests, не расширяя scope.
- [x] Проверить, что `may_emit_carry_bps`, `may_estimate_cost_bps`, `may_rank_routes`, `may_submit_orders`, route selection и execution остаются выключены.
- [x] Осмотреть `git diff` и исключить raw provider payloads, secrets, accidental large files и unrelated rewrites.
- [x] Обновить `VERSION`, frontend package version и lockfile root version до `v1.3.2`, если release-preflight требует синхронизации.
- [x] Обновить финальные release notes в `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и при необходимости `README.md`/`ARCHITECTURE.md`.
- [x] Запустить `scripts/release-preflight.sh` и исправить только релизные несоответствия.
- [x] Прогнать frontend `npm run build` и `npm audit --audit-level=high`.
- [x] Закоммитить scoped changes в текущей ветке без отката чужих изменений: `d3de35e`.
- [x] Push в GitHub на рабочую ветку `preview` и проверить GitHub CI: CI run `27744113125` прошёл `success`.
- [x] Получить зелёный GitHub `Deploy Preview` run для follow-up commit: run `27744161749` для `d3de35e` упал на шаге `Deploy preview`, но `b257cc8` прошёл CI `27746664616` и `Deploy Preview` `27746714283`; preview server обновлён до `1.3.2`.
- [x] После зелёного preview deploy не делать отдельный production patch rollout `v1.3.2`, а включить promotion/tag в финальный `v1.4.0` release path; production deploy останется зависимым от настроенных `PROD_*` secrets.

### План новой версии `v1.4.0`: 3 итерации, 36 задач

#### Итерация 1 — Release runway и deploy hardening

- [x] Разобрать причину красного GitHub `Deploy Preview` run `27744161749`: transient SSH reachability из GitHub runner.
- [x] Сделать GitHub `Deploy Preview` зелёным для маленького follow-up commit: `b257cc8`, CI `27746664616`, Deploy Preview `27746714283`.
- [x] Зафиксировать `v1.3.2` follow-up в docs: CI зелёный, manual preview deploy зелёный, follow-up Deploy Preview зелёный.
- [x] Усилить deploy diagnostics, чтобы transient SSH/deploy failure быстрее показывал причину.
- [x] Добавить release smoke checklist для direct/policy/coinglass/health/frontend checks.
- [x] Выполнить production backup через новый `scripts/backup-postgres.sh` из preview checkout против production Compose project, не пачкая production git checkout untracked script-файлом.
- [x] Подготовить checklist добавления `PROD_*` GitHub secrets.
- [ ] Проверить manual `Deploy Production` readiness после добавления `PROD_*`.
- [x] Добавить release preflight target для `1.4.0-rc.1` на preview.
- [x] Провести Browser QA smoke для preview key screens.
- [x] Обновить русскую release/deploy документацию.
- [x] Сохранить запрет на trading/execution/ranking/cost-bps capabilities.

#### Итерация 2 — Perp DEX research cockpit v1.4 read-only

- [x] Добавить compact Perp DEX source status rollup.
- [x] Добавить backend summary по direct venue availability и provider error classes.
- [x] Добавить UI-панель `Perp DEX Source Status`.
- [x] Расширить provider error taxonomy для direct venues.
- [x] Добавить smoke/test coverage на provider error taxonomy без raw payload.
- [x] Добавить GMX helper/source follow-up rows по missing inputs/manual approvals.
- [x] Добавить Lighter/Aster depth freshness evidence layer без slippage bps.
- [x] Добавить fee schedule evidence layer для Lighter/Aster без fee bps total.
- [x] Добавить compact compare contract для Perp DEX source status.
- [x] Улучшить empty/error states в Perp DEX UI.
- [x] Прогнать backend/frontend/smoke/Browser QA проверки.
- [x] Обновить русскую документацию по новым read-only panels/API fields/safety gates.

#### Итерация 3 — `v1.4.0` release candidate и production rollout

- [x] Поднять версию до `1.4.0`.
- [x] Подготовить `CHANGELOG.md` release block для `v1.4.0`.
- [x] Пройти release preflight на `preview` с `ALLOW_DIRTY=1` перед RC commit.
- [x] Выполнить full local regression/build/audit pass.
- [x] Выполнить HTTP smoke на preview backend.
- [x] Выполнить Browser QA preview desktop/mobile.
- [ ] Закоммитить и запушить `v1.4.0` release candidate в `preview`.
- [x] Повторить release preflight на чистом `preview` без `ALLOW_DIRTY` после RC commit.
- [ ] Дождаться зелёного GitHub CI и зелёного GitHub `Deploy Preview`.
- [ ] Выполнить финальный preview smoke после deploy.
- [ ] Merge/push `preview` в `main`.
- [ ] Запустить production deploy для `main` после обязательного PostgreSQL backup.
- [ ] Проверить production `https://deltagrid.pro`, создать annotated tag `v1.4.0` и обновить итоговые docs.

### Ближайшая итерация

- [x] Подготовить read-only production auto-deploy preflight и зафиксировать blocker по отсутствующим `PROD_*`.
- [x] Добавить ручной запуск `Deploy Production` через `workflow_dispatch`, чтобы после настройки `PROD_*` можно было проверить deploy без пустого push.
- [x] Подготовить внешний production healthcheck через GitHub Actions schedule/manual workflow для `https://deltagrid.pro`.
- [x] Добавить reusable `scripts/backup-postgres.sh` для PostgreSQL backup через Docker Compose.
- [x] Выполнить первый production backup текущей PostgreSQL БД: `/opt/deltagrid/backups/deltagrid_20260616T132922Z.sql.gz`, gzip integrity check прошёл.
- [x] Подключить backup-скрипт к `scripts/deploy-compose-stack.sh`: для `BRANCH=main` backup включён по умолчанию, для preview включается явно через `BACKUP_BEFORE_DEPLOY=1`.
- [ ] Добавить `PROD_*` repository secrets в GitHub.
- [ ] Запустить `Deploy Production` вручную с ветки `main` и подтвердить, что deploy step больше не skipped.
- [ ] После попадания backup-скрипта на сервер выполнить следующий backup уже через `scripts/backup-postgres.sh`.
- [ ] После успешного deploy обновить `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и `deploy/github-actions-secrets.md`.

## Release / CI-CD — 2026-06-14
- [x] Зафиксировать текущую production-ready версию как `v1.3.0`.
- [x] Добавить `VERSION` и `RELEASES.md`.
- [x] Добавить `scripts/release-preflight.sh` для проверки согласованности `VERSION`, frontend package version и lockfile root version перед patch-релизом.
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
- [x] Перенести production deploy hardening в `main`: workflow `Deploy Production` на `main@0716f6a` содержит secret diagnostics, fingerprint, expected values, SSH retry, app-dir check и deploy step.
- [x] Выполнить read-only preflight production auto-deploy: local deploy key fingerprint совпадает, SSH к `/opt/deltagrid` проходит, production smoke зелёный, GitHub run `27619159104` подтверждает safe-skip из-за отсутствующих обязательных `PROD_*`.
- [ ] Настроить GitHub repository secrets `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR` для production auto-deploy.
- [ ] После настройки `PROD_*` запустить контрольный `main` CI/deploy и проверить, что `Deploy Production` делает реальный deploy в `/opt/deltagrid`, а не safe-skip.
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
- [x] P1: Добавить summary-разбивку provider inventory blocker'ов по stream: `coverage_blockers_by_stream`, `freshness_blockers_by_stream`, `promotion_blockers_by_stream`.
- [x] P1: Добавить resolution strategy для provider inventory blocker'ов: `history_backfill_supported`, `snapshot_accumulation_required`, `provider_sync_required`, `freshness_sync_required`.
- [x] OPS/P1: Подготовить preview-safe market sync cron path через `ENV_FILE=.env.preview`, `COMPOSE_PROJECT_NAME=deltagrid-preview`, отдельный cron-файл и отдельный лог.
- [x] OPS/P1: Стабилизировать OKX preview cron при transient HTTP `429`: классифицировать rate-limit ответы как retriable `RateLimitExceeded` и снизить default OKX pacing.
- [x] P1: Закрыть `history_completion_required=5` для `HYPE/XRP/DOGE/ADA/LINK` по partial snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price` или явно утвердить policy-разделение `chart_ready` и full analytics universe: provider inventory теперь допускает `chart_ready_candidates` только для preview `/charts`/`/assets`, а `promotion_candidates` требует `complete_history`.
- [x] P1: Отдельно оценить backfill/ingestion для 7d `open_interest`, `basis_premium`, `spot_perp_price`: в текущем ingestion path это snapshot accumulation, а не честный historical backfill.
- [ ] P1: Если candidates нужно продвигать в full analytics universe быстрее, выбрать отдельный historical source для OI/basis/spot-perp или утвердить 7d окно накопления snapshot-стримов.
- [x] P1: Добавить CI audit gate `npm audit --audit-level=high`, чтобы high/critical frontend advisory снова не прошли в `preview/main`.
- [x] P1: Закрыть свежий frontend high advisory `form-data@4.0.5` через lockfile update до `form-data@4.0.6` без `npm audit fix --force`.
- [x] P1: Подключить первый direct Perp DEX venue slice: read-only Hyperliquid public `metaAndAssetCtxs` snapshot через backend endpoint и Perp DEX screen.
- [x] P1: Подключить второй direct Perp DEX venue slice: read-only dYdX Indexer `perpetualMarkets` snapshot через backend endpoint и Perp DEX screen.
- [x] P1: Подключить GMX public `markets/info` как read-only raw snapshot: raw fixed-point/token-unit поля сохраняются без пересчёта в USD/percent и отображаются в Perp DEX как `Raw`.
- [x] P1: Добавить machine-readable Perp DEX route constraints policy: `research_only`, normalized vs raw venues, blockers для GMX scale validation, fees/slippage model и execution boundary.
- [x] P1: Для GMX добавить token decimals diagnostics через `/tokens`: index/long/short token metadata резолвится и отображается как `Raw + Decimals` без конвертации raw metrics.
- [x] P1: Для GMX добавить pool token amount diagnostics: `poolAmountLong/Short` масштабируются в token units через decimals из `/tokens` и отображаются как `Raw + Pool Units`, но не как USD liquidity/OI.
- [x] P1: Для GMX зафиксировать source-backed fixed-point validation metadata v0 в `route-constraints`: `poolAmountLong/Short` diagnostic-only, `Precision=1e30`, `openInterest` и `openInterestInTokens` разделены, production liquidity/OI поля остаются заблокированы.
- [x] P1: Для GMX добавить diagnostic-only USD conversion layer для `openInterestLong/Short` и `availableLiquidityLong/Short` через `1e30` USD decimals без заполнения production `open_interest_usd`.
- [x] P1: Добавить route-level fees/slippage/routing model v0 как read-only checklist и formula skeleton без numeric estimates, ranking и execution.
- [x] P1: Для GMX описать funding/borrowing/net rate semantics как source-backed metadata без carry conversion: hourly ticker rates, `netRate=fundingRate-borrowingRate`, funding sign через paying/receiving side.
- [x] P1: Добавить offline GMX rate relation guardrail для `netRate=fundingRate-borrowingRate` без carry conversion.
- [x] P1: Добавить CoinGlass Perp DEX enrichment v0 для DEX-like venues (`Aster`, `Lighter`, `EdgeX`, `Drift` по умолчанию) как research-only third-party aggregate endpoint/UI без route ranking и execution.
- [x] P1: Добавить CoinGlass Perp DEX coverage summary v0: per-venue matched rows/symbols, field groups, candidate hints и UI-таблица без production ranking.
- [x] P1: Добавить reusable smoke script `scripts/coinglass-perp-dex-coverage-smoke.sh` для preview/prod проверки CoinGlass Perp DEX coverage compact result без raw payload и секретов.
- [x] P1: Выполнить live CoinGlass Perp DEX coverage smoke с real CoinGlass key и зафиксировать compact result: `Lighter`/`Aster` matched `BTC/ETH/SOL`, `EdgeX`/`Drift` request failed/no rows.
- [x] P1: Выбрать `Lighter` как следующий direct Perp DEX adapter candidate и добавить read-only snapshot v0 без ranking/execution.
- [x] P1: Провести Aster official API review и добавить direct read-only snapshot v0 поверх public Futures market-data endpoints без ranking/execution.
- [x] P1: Добавить diagnostic-only fee/depth/slippage semantics metadata для Lighter/Aster в `route-constraints`, `route-model` и UI без numeric cost estimates.
- [x] P1: Добавить diagnostic route-cost components v0 для Aster/Lighter: component readiness, Aster display spread и published fee defaults без total cost bps, ranking и execution.
- [x] P1: Добавить Lighter `orderBookOrders` depth diagnostics v0: best bid/ask, spread и top-order depth summaries без slippage bps, ranking и execution.
- [x] P1: Добавить Aster `fapi/v3/depth` depth diagnostics v0: best bid/ask, spread и top-level depth summaries без slippage bps, ranking и execution.
- [x] P1: Добавить direct Perp DEX smoke script для preview/prod проверки Hyperliquid, dYdX, Lighter, Aster и GMX endpoints без raw payload и секретов.
- [x] P1: Добавить `Depth Diagnostics` в Perp DEX UI для display-only orderbook/depth readiness без slippage bps, ranking и execution.
- [x] P1: Расширить route policy/model blockers структурированными `missing_inputs`, `blocked_by` и `safe_use`, а также вывести их в `Route Blockers Matrix`.
- [x] P1: Добавить policy/model smoke script, `Route Output Policy`, `Route Model Blockers` и regression-инварианты, чтобы read-only route model safety можно было проверять без включения numeric route cost, ranking и execution.
- [x] P1: Усилить direct Perp DEX smoke read-only/ranking/production guardrails и вывести `Route Required Inputs` в UI как отдельный checklist перед route-ready моделью.
- [x] P1: Добавить `Route Safety Guardrails` summary и усилить policy smoke проверками `required_inputs` / `formula_skeleton` перед будущим route scoring.
- [ ] P1: Разобрать live GMX `/markets/info` nonzero-borrowing rate mapping поверх `rate_relation_summary` и `rate_source_fields_summary`, расширить side-aware rate fixtures и подключить sourced fee/depth/carry inputs перед численным route-level scoring.
- [ ] P1: Подключить route-ready sourced depth/slippage model для Lighter: order-size-aware aggregation, liquidity caps, side и slippage math перед любым route-level scoring.
- [ ] P1: Подключить route-ready sourced fee schedule и slippage model для Aster: account tier, order-size-aware aggregation, liquidity caps, stale-depth policy, side и slippage math перед любым route-level scoring.
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
- [x] Подготовить минимальный внешний uptime/health monitoring через GitHub Actions для `https://deltagrid.pro/api/v1/health/readiness`, `/api/v1/health`, `/api/v1/data/health` и frontend.
- [x] Добавить reusable backup-скрипт PostgreSQL volume перед миграциями и деплоем: `scripts/backup-postgres.sh`.
- [x] Прогнать первый production backup вручную через текущий server command: `/opt/deltagrid/backups/deltagrid_20260616T132922Z.sql.gz`.
- [ ] Прогнать backup через `scripts/backup-postgres.sh` после доставки скрипта на `/opt/deltagrid`.
- [x] Подключить backup-скрипт к deploy/runbook как default-шаг для production deploy.
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
- [x] Реализовать read-only Hyperliquid public market snapshot v0 для Perp DEX без execution path.
- [x] Реализовать read-only dYdX Indexer market snapshot v0 для Perp DEX без execution path.
- [x] Реализовать read-only Lighter public market snapshot v0 для Perp DEX без execution path.
- [x] Реализовать read-only Aster public Futures market snapshot v0 для Perp DEX без execution path.
- [x] Реализовать GMX read-only raw market snapshot v0 для Perp DEX без execution path и без нормализации fixed-point liquidity/OI.
- [x] Добавить backend/UI policy для route/execution constraints, чтобы multi-DEX volume/OI/liquidity не выглядели как production signal до готовности модели.
- [x] Добавить GMX token decimals diagnostics через `/tokens` для index/long/short tokens.
- [x] Добавить GMX pool token amount diagnostics для `poolAmountLong/Short` без конвертации USD liquidity/OI.
- [x] Зафиксировать GMX fixed-point source validation metadata v0 в `GET /api/v1/perp-dex/route-constraints` без снятия blocker'ов с liquidity/OI.
- [x] Добавить diagnostic-only USD conversion для GMX `openInterestLong/Short` и `availableLiquidityLong/Short`, сохранив `open_interest_usd=null` и ranking blocker.
- [x] Добавить `GET /api/v1/perp-dex/route-model` и UI checklist для route-level fees/slippage/routing без numeric estimates, ranking и execution path.
- [x] Описать semantics GMX funding/borrowing/net rates как source-backed metadata без carry conversion.
- [x] Добавить offline GMX rate relation guardrail без carry conversion.
- [x] Добавить CoinGlass Perp DEX enrichment panel для DEX-like futures venues без смешивания с direct snapshots.
- [x] Добавить CoinGlass Perp DEX coverage panel для выбора следующего direct adapter без liquidity ranking.
- [x] Выполнить CoinGlass coverage smoke и подключить Lighter как следующий direct adapter v0.
- [x] Подключить Aster как следующий direct adapter v0 после official API review.
- [x] Добавить diagnostic-only fee/depth/slippage semantics metadata для Lighter/Aster без route ranking и execution.
- [x] Добавить UI/API diagnostics `diagnostic_cost_estimate_v0` для route-cost components без суммарного bps и scoring.
- [x] Добавить Lighter `orderBookOrders` top-order depth diagnostics без slippage/ranking.
- [x] Добавить Aster `fapi/v3/depth` depth ladder diagnostics без slippage/ranking.
- [ ] Разобрать live GMX `/markets/info` nonzero-borrowing rate mapping поверх `rate_relation_summary` и `rate_source_fields_summary`, расширить side-aware rate fixtures и подключить sourced fee/depth/carry inputs перед численным route-level scoring.
- [ ] Подключить route-ready sourced depth/slippage model для Lighter и fee/slippage model для Aster перед численным route-level scoring.
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
