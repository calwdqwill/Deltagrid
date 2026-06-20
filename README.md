# DeltaGrid — Crypto Arbitrage Scanner + RWA Intelligence

Production-ready crypto research terminal для анализа spot/perp рынков CEX и DEX, RWA, treasury, funding, market matrix и strategy research workflows.

**Текущая версия**: `v1.5.0`

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

`Funding` дополнительно показывает `Funding Data Quality Runway`: сводный read-only gate по `/data/health`, funding rows, source coverage, freshness/coverage/sync, history preview и `v1.5.0` preview readiness. В `QA` view добавлен compact `Funding QA Review Summary`, а Data Quality Runway, Release Checklist и QA Drilldown на узких экранах показываются карточками вместо широких таблиц. `Funding Source Status`: OKX funding history и CoinGlass funding snapshots сведены в read-only rows со статусом loaded rows, latest age, freshness, coverage, sync и boundary. `Funding Release Checklist` показывает release-readiness для funding QA smoke и preview rollout: data health, funding rows guard, source coverage, history workflow, panel contract, compare smoke и safety boundary. `Funding Freshness & Anomaly` показывает per-symbol data QA для `BTC/ETH/SOL`: rows, latest age, latest rate, last change, data status и statistical anomaly status. `Funding Anomaly Detail` показывает samples, latest rate, baseline average, observed range и z-score как QA-only detail. `Funding Source Comparison` сравнивает последние OKX/CoinGlass funding rows как provider QA: source delta, latest pair, data note и alignment status без сортировки по выгоде. `Funding QA Drilldown` показывает freshness reason, coverage reason, sync status и next action для каждого `BTC/ETH/SOL × OKX/CoinGlass`. Эти QA panels доступны в `Overview` и отдельном `QA` view (`/funding?view=qa`), но не перегружают остальные Funding views. `Funding History Diagnostics` дополнительно показывает observations/window/latest/interval/average/range/status/next action в `Overview` и `History`. `Funding History Controls` добавляет URL-driven `asset`/`source` controls, chart readiness, interval/range hints и next action в `Overview`/`History`. `Funding History Readiness` объясняет empty/thin history states для выбранных `asset`/`source`: persisted rows, selected asset/source coverage, chart points, numeric rates и next action. Эти панели используют уже загруженные `/data/funding` и `/data/health`; новых provider calls, backend endpoints, БД-записей, carry bps, route ranking, route selection или execution signals не добавляется.

`Perp DEX` показывает live Hyperliquid, dYdX, Lighter и Aster public snapshots, если backend/provider доступны: mark/display price, funding, open interest, 24h volume и metadata читаются через read-only endpoints. Lighter подключён через public `orderBooks`, `orderBookDetails`, `orderBookOrders` и `funding-rates`: rows показывают last trade price, funding, OI USD estimate, 24h volume, trades, maker/taker fee, margin fractions, tick/step size, best bid/ask, display spread и top-order depth summaries, но не участвуют в route scoring. Aster подключён через public Futures market-data endpoints `exchangeInfo`, `premiumIndex`, `ticker/24hr`, `openInterest`, `ticker/bookTicker` и `fapi/v3/depth`: rows показывают mark/index/mid price, funding, OI USD estimate, 24h volume, trades, top-of-book, top-level depth summaries, tick/step size и min notional, но fee tiers, slippage и carry conversion не считаются production signal. Route policy/model теперь отдельно показывают Lighter/Aster cost semantics metadata: Lighter `maker_fee`/`taker_fee` и top resting order depth, а также Aster top-of-book и depth ladder являются display fields, но не route-ready numeric cost inputs без account tier, order intent, depth aggregation policy, stale-depth policy, slippage model и carry horizon. GMX подключён как read-only raw snapshot через `markets/info`: rate fields сохраняются как raw strings, `poolAmountLong/Short` масштабируются в token units, а `openInterestLong/Short` и `availableLiquidityLong/Short` масштабируются через `1e30` в diagnostic-only USD fields. Для GMX rates endpoint также возвращает `rate_semantics_status`, `rate_relation_diagnostics`, `rate_relation_summary` и `rate_source_fields_summary`: offline guardrails проверяют ожидаемую source relation `netRate* = fundingRate* - borrowingRate*` и observed live-shape fixture, а live `/markets/info` сейчас показывает `raw_rate_relation_plus_with_zero_borrowing`: nonzero-borrowing sides совпадают с `funding+borrowing`, zero-borrowing sides помечаются ambiguous. Current `/markets/info` payload не содержит helper inputs `fundingFactorPerSecond`, `borrowingFactorPerSecondForLongs/Shorts` и `longsPayShorts`, поэтому всё это не конвертируется в percent, bps или carry cost. Эти GMX diagnostics не заполняют production `open_interest_usd` и не участвуют в liquidity ranking. Route/execution граница вынесена в `GET /api/v1/perp-dex/route-constraints`: текущий статус `research_only`, liquidity ranking, route-level pricing и execution заблокированы; policy также возвращает `gmx_formula_validation` с source-backed diagnostic notes и списком GMX fields, заблокированных для production signal. `GET /api/v1/perp-dex/route-model` добавляет read-only checklist/formula skeleton для route-level fees/slippage/routing и metadata `gmx_rate_semantics`: GMX interface считает ticker rates за 1h, а relation guardrail закрепляет ожидаемую `netRate* = fundingRate* - borrowingRate*`, но numeric cost estimates, carry conversion, route ranking и order submission остаются выключены. Историзация DEX snapshots пока не подключена, поэтому multi-DEX volume/OI/liquidity не выдаются за полный production signal. `Strategy Lab` показывает readiness live inputs, но не показывает fake PnL/trades до появления реального backtest engine. Order book aggregation, per-order liquidation tape и execution-grade slippage остаются отдельными provider задачами.

`Route Diagnostic Components Summary`, `Route Diagnostic Venue Breakdown`, `Route Diagnostic Blocker Breakdown`, `Route Diagnostic Required Input Breakdown`, `Route Diagnostic Source Fields Breakdown`, `Route Diagnostic Source Input Actions`, `Route Diagnostic Evidence Checklist`, `Route Diagnostic Fee Schedule Evidence`, `Route Diagnostic Fee Schedule Checklist`, `Route Diagnostic Venue Evidence Status`, `GMX Rate Mapping Review`, `GMX Rate Mapping Blockers`, `GMX Rate Fixture Readiness`, `GMX Rate Side-aware Fixtures`, `GMX Rate Mapping Decision Checklist`, `GMX Rate Carry Readiness Summary`, `GMX Rate Carry Input Checklist`, `GMX Rate Carry Evidence Summary`, `GMX Rate Carry Evidence Checklist`, `GMX Rate Live Helper Source Review`, `Route Diagnostic Safe Use Breakdown`, `Route Diagnostic Readiness Rollup`, `Route Diagnostic Depth/Staleness Policy`, `Route Diagnostic Policy Inputs`, `Route Diagnostic Next Actions` и `Route Cost Diagnostics v0` в `Perp DEX` показывают только component-level readiness: backend `diagnostic_cost_estimate_v0.summary` даёт counts/id-списки по display-only/blocked/sourced components, `summary.venue_breakdown` группирует эти компоненты по Lighter/Aster/cross-venue, `summary.blocker_breakdown` группирует повторяющиеся `blocked_by` причины, `summary.required_input_breakdown` связывает components с обязательными входами route model, `summary.source_field_breakdown` показывает sourced display fields, `summary.source_input_action_coverage` связывает source fields с required inputs и mapped next actions, `summary.route_ready_evidence_checklist` группирует fee/order/depth/carry/risk evidence gates и явные `cost/rank/exec=false`, `summary.fee_schedule_evidence_summary` и `summary.fee_schedule_evidence_checklist` показывают Lighter/Aster account tier/order intent/manual approval gates перед любым fee bps, `summary.venue_evidence_status` разделяет Lighter/Aster/GMX/cross-venue evidence gaps, `gmx_rate_mapping_review_v0` показывает GMX mapping review поверх `rate_relation_summary`/`rate_source_fields_summary`, `gmx_rate_mapping_review_v0.blocker_breakdown` группирует repeated GMX mapping blockers, `gmx_rate_mapping_review_v0.fixture_readiness_matrix` показывает side-aware fixture cases, `gmx_rate_mapping_review_v0.side_aware_fixture_expectations` перечисляет `longsPayShorts` long/short paying/receiving cases, `gmx_rate_mapping_review_v0.mapping_decision_checklist` показывает source/fixture/review/manual approval checks перед diagnostic carry bps, `gmx_rate_mapping_review_v0.carry_readiness_summary` и `carry_input_checklist` показывают horizon/notional/sign/source/display gates перед carry bps, `gmx_rate_mapping_review_v0.carry_source_evidence_summary` и `carry_source_evidence_checklist` показывают source/fixture/runtime/manual evidence gates перед carry bps, а `gmx_rate_mapping_review_v0.live_helper_source_summary` и `live_helper_source_checklist` показывают live `/markets/info` rate output evidence, missing helper source inputs, side-direction fields и manual review gate перед carry conversion, `summary.safe_use_breakdown` группирует display boundaries, `summary.readiness_rollup` показывает compact fee/depth/carry/risk readiness, `summary.depth_staleness_policy_checklist` фиксирует freshness/stale-depth gates для Lighter/Aster depth diagnostics, `summary.required_policy_input_breakdown` показывает matrix required policy inputs для этих gates, а `summary.next_action_breakdown` группирует planning actions из этих слоёв. Детальная таблица показывает Aster display-only top-of-book spread, Aster depth ladder diagnostics, published USDT-perp fee defaults как metadata, Lighter raw fee fields и Lighter top resting order depth diagnostics. UI не считает total cost bps, не сортирует venues и не включает execution.

`Depth Diagnostics` в `Perp DEX` показывает только display-only orderbook/depth fields по direct venues: best bid/ask, spread, top bid/ask depth summaries и safe-use заметку. `Route Blockers Matrix` показывает структурированные blockers из backend policy: `missing_inputs`, `blocked_by`, `safe_use` и next action. `Route Safety Guardrails` показывает expected vs actual по верхнеуровневым safety-флагам route policy/model. `Route Output Policy` показывает, какие outputs route model разрешены только как diagnostics, а какие заблокированы для production scoring. `Route Model Blockers` отдельно выводит model-level blockers из `route-model.blockers`. `Route Required Inputs` выводит обязательные входы route model отдельным checklist перед любым numeric route cost. `Route Diagnostic Components Summary` показывает summary по `diagnostic_cost_estimate_v0.components`, `Route Diagnostic Venue Breakdown` показывает venue-level readiness, `Route Diagnostic Blocker Breakdown` показывает повторяющиеся blockers, `Route Diagnostic Required Input Breakdown` показывает coverage обязательных inputs, `Route Diagnostic Source Fields Breakdown` показывает source-field coverage, `Route Diagnostic Source Input Actions` показывает связь source fields с required inputs и next actions, `Route Diagnostic Evidence Checklist` показывает pre-route-scoring evidence gates и blocked outputs, `Route Diagnostic Fee Schedule Evidence` и `Route Diagnostic Fee Schedule Checklist` показывают Lighter/Aster account tier/order intent/manual approval gates без fee bps total, `Route Diagnostic Venue Evidence Status` отделяет direct venue gaps от cross-venue gates и GMX mapping review, `GMX Rate Mapping Review` показывает source relation/live mapping/helper input/carry boundary без carry conversion, `GMX Rate Mapping Blockers` показывает repeated blockers между review rows, `GMX Rate Fixture Readiness` показывает nonzero borrowing, zero borrowing ambiguity, `longsPayShorts` direction и missing helper inputs как отдельные cases, `GMX Rate Side-aware Fixtures` показывает long/short paying/receiving expectations для `longsPayShorts`, `GMX Rate Mapping Decision Checklist` показывает source fields, fixture cases, expectation ids, review ids и manual approval ids перед первым diagnostic carry bps, `GMX Rate Carry Readiness Summary` и `GMX Rate Carry Input Checklist` показывают `holding_period_hours`, `position_notional_usd`, sign convention, source helper inputs и display-unit policy как заблокированные gates, `GMX Rate Carry Evidence Summary` и `GMX Rate Carry Evidence Checklist` показывают runtime/source/fixture/policy/manual evidence gates для этих carry inputs, `GMX Rate Live Helper Source Review` показывает live raw rate outputs, missing helper source inputs, side-direction fixture expectations и manual review gate, `GMX Rate Helper Source Follow-up` показывает оставшиеся helper/source follow-up rows с missing source inputs и manual approvals, `Route Diagnostic Safe Use Breakdown` показывает boundary text, `Route Diagnostic Readiness Rollup` даёт compact fee/depth/carry/risk readiness, `Route Diagnostic Depth/Staleness Policy` показывает freshness policy inputs и blockers перед любым slippage bps, `Route Diagnostic Policy Inputs` показывает required policy input matrix для depth/staleness gates, а `Route Diagnostic Next Actions` группирует следующие research actions. Эти панели нужны для диагностики готовности, но не включают route ranking, slippage estimate, total cost bps, carry conversion или execution.

`Perp DEX Source Status` в `overview` и `venues` даёт compact rollup по текущему read-only cockpit: direct venue snapshots, GMX raw diagnostics, CoinGlass enrichment, route policy/model contract и last release smoke. Панель использует уже загруженные frontend snapshots и backend policy/model responses, не делает дополнительных provider calls, не сортирует venues и не превращает coverage hints в route ranking.

Для server-side проверки и preview/prod сравнения `Perp DEX Source Status` используйте `scripts/perp-dex-source-status-smoke.sh`. Скрипт собирает compact contract из direct venues, GMX raw, CoinGlass enrichment, route policy/model и release-smoke checklist, печатает только ids/statuses/flags/counts и не выводит raw provider payload или secrets:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 COMPARE_BASE_URL=http://127.0.0.1:8000 sh scripts/perp-dex-source-status-smoke.sh
```

Если нужно сделать preview/prod drift hard gate, добавьте `FAIL_ON_DIFF=1`. Compact `contract` включает `source_status_row_ids`, `source_status_statuses`, direct venue rows/statuses/depth freshness/provider error classes, CoinGlass matched exchanges/candidate hints/route-input statuses, route policy/model blocker ids и safety flags. Эти поля нужны только для release/readiness observability; они не являются route ranking, route selection, numeric route cost bps, diagnostic carry bps или execution signal.

Для server-side проверки Funding QA panels используйте `scripts/funding-qa-smoke.sh`. Скрипт проверяет `/data/health`, `/data/funding` для `BTC/ETH/SOL` по OKX/CoinGlass, опционально проверяет frontend `/funding` markers, печатает compact `funding_qa_v0` contract и не выводит full payload или secrets:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-qa-smoke.sh
```

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 COMPARE_BASE_URL=http://127.0.0.1:8000 RUN_FRONTEND_CHECK=0 sh scripts/funding-qa-smoke.sh
```

Для release-prep запуска используйте wrapper с тем же contract, но с воспроизводимыми soft/strict presets:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-release-smoke.sh
```

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 FUNDING_RELEASE_STRICT=1 sh scripts/funding-release-smoke.sh
```

`scripts/funding-release-smoke.sh` по умолчанию сохраняет soft mode. `FUNDING_RELEASE_STRICT=1` включает `FAIL_ON_DIFF=1` и `FAIL_ON_RELEASE_NOT_READY=1`, если эти флаги не заданы явно; это release/readiness preset, а не новый data contract.

Для CI/report artifacts можно включить чистый JSON output без human prefix/suffix:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 OUTPUT_JSON_ONLY=1 sh scripts/funding-release-smoke.sh > funding-release-smoke.json
```

Для короткого human-readable release artifact поверх того же JSON contract используйте:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-release-report.sh
```

`scripts/funding-release-report.sh` показывает readiness status, total/source rows, frontend marker count, compare status, safety status и `data_quality_runway_status`, но сохраняет exit code исходного smoke.

Compact report можно сохранить как JSON:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 FUNDING_RELEASE_REPORT_FORMAT=json sh scripts/funding-release-report.sh > funding-release-report.json
```

Если нужно сохранить compact JSON artifact в файл и оставить human-readable stdout, используйте `FUNDING_RELEASE_REPORT_OUTPUT`:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 FUNDING_RELEASE_REPORT_OUTPUT=funding-release-report.json sh scripts/funding-release-report.sh
```

Для production release evidence сохраняйте Funding report в отдельный каталог релиза:

```bash
cd /opt/deltagrid
mkdir -p artifacts/production-release/v1.6.0
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 FUNDING_RELEASE_REPORT_OUTPUT=artifacts/production-release/v1.6.0/funding-release-report.json sh scripts/funding-release-report.sh
sh scripts/funding-release-report-validate.sh artifacts/production-release/v1.6.0/funding-release-report.json
```

Для CI/release artifact можно использовать готовый профиль: он по умолчанию включает JSON report, require-ready и require-compare, а явные env overrides могут ослабить отдельный gate при локальной проверке:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 FUNDING_RELEASE_REPORT_PROFILE=ci sh scripts/funding-release-report.sh > funding-release-report.json
```

Для локального CI-like запуска с готовыми artifact defaults используйте wrapper:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 sh scripts/funding-release-ci-report.sh
```

Wrapper создаёт evidence bundle в `artifacts/funding-release`: `funding-release-index.md`, `funding-release-index.json`, `funding-release-verify.md`, `funding-release-verify.json`, `funding-release-notes.md`, `funding-release-notes.json`, `funding-release-archive.md`, `funding-release-archive.json`, `funding-release-ci-status.json`, `funding-release-report.json`, optional stdout JSON, `funding-release-validation.json`, `funding-release-manifest.json`, `funding-release-bundle-validation.json`, `funding-release-review.json`, `funding-release-summary.md`, `funding-release-handoff.md`, `funding-release-audit.json` и `funding-release-audit.md`. Он задаёт `FUNDING_RELEASE_REPORT_PROFILE=ci` и не меняет `funding_qa_v0`. Compact report включает `data_quality_runway` как release-evidence summary по Funding runway gates; локальный `blocked` статус при пустых rows считается валидным release blocker, если validator проходит. Для GitHub есть manual workflow `Funding Release Report`: он принимает base/frontend/compare URL, загружает artifact bundle и только после upload фейлит job при `release_gate_status=blocked|failed`. `funding-release-ci-status.json` показывает итог wrapper-а: `final_status`, `final_exit_code`, `final_stage` и exit codes всех evidence-стадий.

Compact artifact можно проверить отдельно без повторного smoke:

```bash
cd /opt/deltagrid-preview
sh scripts/funding-release-report-validate.sh artifacts/funding-release/funding-release-report.json
```

В CI wrapper validation включена по умолчанию через `FUNDING_RELEASE_CI_VALIDATE_ARTIFACT=1`. Валидатор проверяет обязательные поля, status enum'ы, consistency `release_gate_summary` с `release_gate_checks`, safety invariants и `run_context.ci`; он не требует `release_gate_status=passed`, если явно не задан `FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_PASSED=1`.

Bundle manifest и file checksums можно проверить отдельно:

```bash
cd /opt/deltagrid-preview
sh scripts/funding-release-bundle-validate.sh artifacts/funding-release/funding-release-manifest.json
```

В CI wrapper bundle validation включена по умолчанию через `FUNDING_RELEASE_CI_VALIDATE_BUNDLE=1` и пишет `funding-release-bundle-validation.json`. Валидатор проверяет `manifest_version`, bundle/report/validation exit-code semantics, required/optional blockers, наличие report/validation files, `size_bytes`, `sha256` и `json_valid`. Blocked report остаётся валидным bundle, если manifest и checksums корректны.

Runbook review можно вывести отдельно без повторного smoke:

```bash
cd /opt/deltagrid-preview
sh scripts/funding-release-bundle-review.sh artifacts/funding-release/funding-release-manifest.json
```

Markdown summary для GitHub step summary или release notes:

```bash
sh scripts/funding-release-review-summary.sh artifacts/funding-release/funding-release-review.json
```

В CI wrapper review включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_REVIEW=1` и пишет `funding-release-review.json`. Markdown summary включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_SUMMARY=1` и пишет `funding-release-summary.md`. Review собирает `review_status`, `recommended_next_action`, bundle/report/validation exit codes, validation statuses, required/optional blockers, first actions, run context и file integrity summary без чтения full smoke payload. Summary форматирует эти поля как `markdown`, `text` или `json`, не валидирует bundle заново и не читает full smoke payload. GitHub summary сначала использует `funding-release-summary.md`, затем fallback-читает review/manifest/report.

Release handoff для evidence bundle:

```bash
sh scripts/funding-release-evidence-handoff.sh artifacts/funding-release/funding-release-review.json
```

В CI wrapper handoff включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_HANDOFF=1` и пишет `funding-release-handoff.md`. Handoff читает `funding-release-review.json`, optional `funding-release-summary.md`, manifest и bundle validation, затем показывает `evidence_status`, `release_evidence_ready`, `debug_evidence_ready`, blockers, first actions, run context, artifact checklist и локальные follow-up команды. Это release/runbook handoff поверх уже готового bundle, а не повторный smoke или новый data contract.

Directory-level audit скачанного evidence bundle:

```bash
sh scripts/funding-release-evidence-audit.sh artifacts/funding-release
```

В CI wrapper audit включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_AUDIT=1` и пишет `funding-release-audit.json`; Markdown readout включён через `FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN=1` и пишет `funding-release-audit.md`. Audit проверяет ожидаемые файлы bundle, JSON-валидность, status consistency между compact report, validation, manifest, bundle validation и review, а также markdown markers summary/handoff. Blocked release report может иметь `audit_status=passed`, если evidence bundle целостный; audit падает только при поломке формы, файлов или consistency. GitHub workflow добавляет `funding-release-audit.md` в step summary после `funding-release-summary.md`, чтобы downloaded bundle и CI summary показывали один и тот же audit readout.

Evidence index для скачанного bundle:

```bash
sh scripts/funding-release-evidence-index.sh artifacts/funding-release
```

В CI wrapper index включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_INDEX=1` и пишет `funding-release-index.json`; Markdown entrypoint включён через `FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN=1` и пишет `funding-release-index.md`. Index читает только локальные artifact-файлы, показывает `index_status`, `evidence_status`, `audit_status`, `review_status`, ordered `Open First` список, blockers и локальные команды проверки. GitHub workflow сначала добавляет `funding-release-index.md` в step summary; если его нет, остаётся fallback на summary/audit parser.

Evidence verify для скачанного bundle:

```bash
sh scripts/funding-release-evidence-verify.sh artifacts/funding-release
```

В CI wrapper verify включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_VERIFY=1` и пишет `funding-release-verify.json`; Markdown readout включён через `FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN=1` и пишет `funding-release-verify.md`. Verify сверяет `funding-release-index.json` и `funding-release-audit.json`, при наличии сверяет review/manifest/report statuses и показывает `verification_status`, `blocking_mode`, `release_notes_ready`, `debug_review_ready` и `recommended_next_action`. По умолчанию valid blocked evidence не считается tooling failure; для release-notes gate можно добавить `FUNDING_RELEASE_VERIFY_REQUIRE_RELEASE_NOTES_READY=1`, а для debug-review gate — `FUNDING_RELEASE_VERIFY_REQUIRE_DEBUG_READY=1`. GitHub workflow показывает `funding-release-verify.md` сразу после index.

Evidence notes для release notes/debug review:

```bash
sh scripts/funding-release-evidence-notes.sh artifacts/funding-release
```

В CI wrapper notes включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_NOTES=1` и пишет `funding-release-notes.json`; Markdown snippet включён через `FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN=1` и пишет `funding-release-notes.md`. Notes читает `funding-release-verify.json`, optional index/audit/review/manifest/report artifacts, показывает `notes_status`, `notes_mode`, `release_notes_ready`, `debug_review_ready`, blockers и paste-ready snippet. По умолчанию valid blocked evidence даёт debug review snippet и не считается tooling failure; для строгого release-notes handoff можно задать `FUNDING_RELEASE_NOTES_REQUIRE_READY=1`. GitHub workflow добавляет `funding-release-notes.md` после verify.

Evidence archive для финальной фиксации downloaded bundle:

```bash
sh scripts/funding-release-evidence-archive.sh artifacts/funding-release
```

В CI wrapper archive включён по умолчанию через `FUNDING_RELEASE_CI_WRITE_ARCHIVE=1` и пишет `funding-release-archive.json`; Markdown readout включён через `FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN=1` и пишет `funding-release-archive.md`. Archive читает только локальные artifact-файлы, считает `size_bytes`, `sha256`, `json_valid`, сверяет `verify`/`notes` readiness и показывает `archive_status`, `archive_mode`, file counts, missing required files, blockers и next action. По умолчанию blocked valid evidence остаётся полноценным archive output для debug review; для строгого release-ready archive handoff можно задать `FUNDING_RELEASE_ARCHIVE_REQUIRE_RELEASE_READY=1`, тогда not-ready bundle вернёт exit `2`. Archive не включает сам себя в checksum table, чтобы итоговый файл оставался стабильным.

Offline compare двух evidence bundles:

```bash
sh scripts/funding-release-evidence-compare.sh artifacts/funding-release-base artifacts/funding-release
```

Compare читает только локальные artifact-файлы двух директорий: обязательный `funding-release-verify.json` и optional notes/index/audit/review/manifest/report artifacts. Он показывает `compare_status=aligned|drift_detected|failed`, `comparison_mode`, diff count, blocking diff count, readiness/status drift, blocker drift и artifact presence drift. По умолчанию drift является runbook signal и не считается tooling failure; для strict compare handoff можно задать `FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED=1`, тогда drift вернёт exit `2`. Это offline проверка скачанных bundles, а не новый smoke, backend/API call или data contract.

`funding-release-manifest.json` является индексом evidence bundle: он содержит `bundle_exit_code`, `report_exit_code`, `validation_exit_code`, release/validation statuses, required/optional blockers, first blocking/optional action, `run_context`, а также `size_bytes` и `sha256` для report/stdout/validation files. Для runbook сначала смотрите manifest, затем compact report, если нужно раскрыть blockers подробнее.

Compact report включает `report_version`, `gate_status`, `release_gate_status`, `report_exit_code`, `exit_reason`, `release_gate_summary`, `release_gate_checks`, `readiness_gate_status`, `blocking_reasons`, `next_actions`, `run_context` с profile, format, output path, `ci` context, base/frontend/compare URL, strict mode и effective hard-gate flags, а также evidence fields: `readiness_checks`, `sources_with_rows`, `source_pair_statuses` и `compare_diff_fields`. `gate_status` отражает exit code smoke, `release_gate_status` даёт итоговый artifact status `passed|blocked|failed`, `report_exit_code` совпадает с итоговым кодом report, `exit_reason` объясняет его как `passed`, `smoke_failed`, `readiness_not_ready` или `compare_not_aligned`, а `release_gate_summary` показывает required/blocking ids, required/optional blockers, category blocker groups, first blocking action, action map и status counts по checks; эти поля не меняют `funding_qa_v0`.

Если нужен report-level CI gate без strict smoke preset, добавьте `FUNDING_RELEASE_REPORT_REQUIRE_READY=1`: report вернёт non-zero при `readiness_gate_status=not_ready`, сохранив обычное поведение underlying smoke.

Если preview/prod report должен обязательно включать compare, добавьте `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE=1`: report вернёт non-zero, когда `COMPARE_BASE_URL` не задан или `compare_status` не равен `aligned`.

`COMPARE_BASE_URL` добавляет compact `compare.summary`: `status`, `diff_count`, `diff_fields`, `ignored_fields`, `fail_on_diff`, base/compare row totals, base/compare `panel_ids` и `safety_flags_aligned`. Для hard gate можно добавить `FAIL_ON_DIFF=1`; volatile frontend/latest timestamp fields игнорируются, чтобы diff показывал contract drift, а не шум рендера или времени.

Для локального окружения без накопленных funding rows можно временно задать `MIN_TOTAL_ROWS=0`. В preview/prod дефолтный `MIN_TOTAL_ROWS=1` должен оставаться guard against пустого funding data path. Contract фиксирует `panel_ids` (`funding_release_checklist`, `funding_source_status`, `funding_freshness_anomaly`, `funding_anomaly_detail`, `funding_history_diagnostics`, `funding_history_controls`, `funding_history_readiness`, `funding_source_comparison`, `funding_qa_drilldown`), frontend marker `funding_qa_view`, row counts, freshness/coverage/sync statuses, source-pair statuses и safety flags: `trading_enabled=false`, `execution_enabled=false`, `route_ranking_enabled=false`, `route_selection_enabled=false`, `numeric_route_cost_bps_enabled=false`, `diagnostic_carry_bps_enabled=false`. `contract.release_readiness` дополнительно даёт machine-readable release-prep summary: общий статус, checks по health/rows/source/frontend/compare/safety, missing frontend markers и sources with rows. Для release hard gate можно явно задать `FAIL_ON_RELEASE_NOT_READY=1`; тогда smoke падает, если `release_readiness.status` не равен `ready_for_preview_smoke`.

Direct venue endpoints Hyperliquid, dYdX, Lighter, Aster и GMX дополнительно отдают `availability_summary`: rows, requested/matched/missing symbols, status counts, depth diagnostics availability, read-only safety flags, `provider_error_class` и `safe_use`. Для depth-capable Lighter/Aster summary включает `depth_diagnostics.freshness`: snapshot timestamp, observed timestamp, `age_ms`, display max-age policy, required stale-depth inputs и `may_emit_slippage_bps=false`. Error path остаётся compact: provider failures классифицируются как `timeout`, `rate_limit`, `empty_response`, `schema_drift`, `unavailable_endpoint`, `provider_unavailable` или `provider_http_error`, но raw provider payload и секреты не выводятся. Этот summary нужен для release smoke и UI/readiness диагностики; он не включает slippage bps, route ranking, route selection, numeric route cost bps или execution.

`Direct Perp DEX Market Snapshots`, `Depth Diagnostics` и `CoinGlass Perp DEX Enrichment` в UI показывают compact state rows перед detail tables. Эти строки читают уже загруженные `availability_summary`/`coverage_summary` и помогают отличить provider unavailable, request failed/empty response, partial data, missing symbols, no-depth и CoinGlass unavailable. Это presentation layer: новых provider calls, backend endpoints, route ranking, route selection, numeric route cost bps или execution он не добавляет.

CoinGlass Perp DEX enrichment доступен отдельно через `GET /api/v1/perp-dex/venues/coinglass/markets`: это third-party futures `coins-markets` aggregate rows для DEX-like venues (`Aster`, `Lighter`, `EdgeX`, `Drift` по умолчанию). В UI эти rows показаны отдельной таблицей `CoinGlass Perp DEX Enrichment` и не смешиваются с direct venue snapshots. Response также возвращает `coverage_summary`: per-venue matched rows/symbols, available field groups и `direct_adapter_candidate_hints`. Контракт явно возвращает `ranking_enabled=false`, `production_signal_enabled=false`, `execution_enabled=false`; coverage hints не являются liquidity ranking.

Для server-side проверки CoinGlass Perp DEX coverage используйте reusable smoke-скрипт. Он печатает compact coverage summary и не выводит raw payload или секреты:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 sh scripts/coinglass-perp-dex-coverage-smoke.sh
```

```bash
cd /opt/deltagrid
BASE_URL=http://127.0.0.1:8000 sh scripts/coinglass-perp-dex-coverage-smoke.sh
```

Для server-side проверки direct Perp DEX venue endpoints используйте отдельный smoke-скрипт. Он вызывает Hyperliquid, dYdX, Lighter, Aster и GMX market endpoints, печатает compact `availability_summary` по rows/depth/read-only flags/provider error classes, проверяет `read_only=true`, `execution_enabled=false` и отсутствие включённых `ranking_enabled` / `production_signal_enabled`, не выводя raw payload:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 sh scripts/perp-dex-direct-smoke.sh
```

```bash
cd /opt/deltagrid
BASE_URL=http://127.0.0.1:8000 sh scripts/perp-dex-direct-smoke.sh
```

Для server-side проверки policy/model safety-инвариантов используйте отдельный smoke-скрипт. Он вызывает `route-constraints` и `route-model`, проверяет read-only flags, выключенные ranking/execution, запрет numeric total bps, структурированность blockers, required inputs и formula skeleton keys:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 sh scripts/perp-dex-policy-smoke.sh
```

```bash
cd /opt/deltagrid
BASE_URL=http://127.0.0.1:8000 sh scripts/perp-dex-policy-smoke.sh
```

Для компактного сравнения preview/prod route-model observability contract можно передать второй backend как `COMPARE_BASE_URL`. По умолчанию diff только печатается в JSON summary; `FAIL_ON_DIFF=1` превращает расхождения в ошибку smoke:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 COMPARE_BASE_URL=http://127.0.0.1:8000 FAIL_ON_DIFF=1 sh scripts/perp-dex-policy-smoke.sh
```

Compact `contract` в этом smoke включает `depth_policy_ids`, `required_policy_input_ids`, `next_action_ids`, `source_input_action_fields`, `route_ready_evidence_gate_ids`, `venue_evidence_status_ids`, `gmx_rate_mapping_review_ids`, `gmx_rate_mapping_status`, `gmx_rate_mapping_blocker_ids`, `gmx_rate_fixture_case_ids`, `gmx_rate_fixture_statuses`, `gmx_rate_side_expectation_ids`, `gmx_rate_mapping_decision_check_ids`, `gmx_rate_mapping_decision_statuses`, `gmx_rate_mapping_decision_manual_approval_ids`, `gmx_rate_carry_readiness_status`, `gmx_rate_carry_input_ids`, `gmx_rate_carry_input_statuses`, `gmx_rate_carry_manual_approval_ids`, `gmx_rate_carry_evidence_status`, `gmx_rate_carry_evidence_ids`, `gmx_rate_carry_evidence_statuses`, `gmx_rate_carry_evidence_types`, `gmx_rate_carry_evidence_manual_approval_ids`, `gmx_rate_live_helper_review_status`, `gmx_rate_live_helper_review_ids`, `gmx_rate_live_helper_review_statuses`, `gmx_rate_live_helper_missing_source_inputs` и `gmx_rate_live_helper_manual_approval_ids`. Эти ключи нужны для preview/prod diff route-model observability; они не являются route ranking или execution signal.

Decision note перед numeric route-cost model: первую формулу `estimated_cost_bps` нельзя включать только на основании текущих display diagnostics. До этого нужны source-backed fee tiers/account tier, явный `order_intent`, `order_size_usd`, side/notional, order-size-aware depth aggregation, stale-depth policy, liquidity caps, GMX side-aware mapping fixtures, carry horizon/notional/sign convention, risk limits и regression/smoke coverage. Даже после отдельного решения о numeric bps route ranking, route selection и execution остаются отдельными выключенными решениями.

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

Для локальной проверки `Perp DEX` на холодном dev-рендере можно временно поднять `BACKEND_FETCH_TIMEOUT_MS` до `30000`, потому что страница параллельно читает direct venue snapshots и route-policy/model panels. Это не меняет route model contract и не включает route ranking или execution.

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
- `Production Healthcheck` по расписанию и вручную проверяет public production endpoints: `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend.

Перед релизным bump используйте `scripts/release-preflight.sh`, чтобы проверить согласованность `VERSION`, `frontend/package.json` и `frontend/package-lock.json`:

```bash
RELEASE_BRANCH=preview RELEASE_TARGET=1.4.0-rc.1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh
```

Для docs-only подготовки следующего target до bump можно добавить `RELEASE_CHECK_DOCS=1`, например `RELEASE_TARGET=1.6.0 RELEASE_CHECK_DOCS=1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh`.

Если SSH secrets не настроены, deploy workflow завершится успешным skip и не будет ломать CI.
На 2026-06-18 `Deploy Preview` для `preview@d3de35e` показал transient SSH reachability failure из GitHub runner: SSH port/login/app-dir diagnostics были нестабильны, а ручной запуск того же `scripts/deploy-compose-stack.sh` по SSH успешно обновил `/opt/deltagrid-preview` до `VERSION=1.3.2`. Workflow и deploy script усилены stage-aware diagnostics: при падении deploy выводит текущий этап, git/compose snapshot и последние backend/frontend logs без печати secrets. Для ручной проверки preview chart/asset candidates добавлен `scripts/preview-candidate-smoke.sh`; он проверяет `/charts`, `/assets`, OHLCV window endpoint для `HYPE/XRP/DOGE/ADA/LINK` и отсутствие candidate symbols на core-only страницах `Market Matrix`, `Arbitrage Scanner`, `Perp DEX`.
Production auto-deploy пока не считается подтверждённым: `v1.5.0` на `main@3f6f3f7` доставлен вручную по SSH через `scripts/deploy-compose-stack.sh`, потому что GitHub `Deploy Production` сделал safe-skip из-за отсутствующих `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR`. Workflow теперь пишет в `$GITHUB_STEP_SUMMARY` явный readiness/result status: `skipped_missing_required_secrets` означает не-деплой, `ready_for_real_deploy` разрешает SSH checks, `real_deploy_succeeded` подтверждает настоящий GitHub SSH deploy, а `real_deploy_failed` фиксирует неуспешную попытку real deploy. Read-only preflight к `/opt/deltagrid` зелёный; workflow поддерживает ручной `Run workflow` на ветке `main`, поэтому после добавления `PROD_*` можно проверить deploy без пустого push.
Подробный чеклист secrets: [deploy/github-actions-secrets.md](deploy/github-actions-secrets.md).

Рекомендуемая схема стендов на VPS:

- production: `/opt/deltagrid`, branch `main`, env `.env.production`, Compose project `deltagrid`, ports `8000/3001`, домен `https://deltagrid.pro`;
- preview: `/opt/deltagrid-preview`, branch `preview`, env `.env.preview`, Compose project `deltagrid-preview`, ports `8011/3012`, будущий домен `https://preview.deltagrid.pro`.

Шаблон preview env лежит в `.env.preview.example`. Общий deploy-скрипт `scripts/deploy-compose-stack.sh` используется и для production, и для preview. Для `BRANCH=main` он по умолчанию создаёт PostgreSQL backup в `backups/deploy/` перед пересозданием backend/frontend containers; для preview backup включается только явно через `BACKUP_BEFORE_DEPLOY=1`. После server smoke deploy-скрипт проверяет frontend `/version` против файла `VERSION`, печатает compact строку `Deploy summary` и при заданном `DEPLOY_SUMMARY_OUTPUT` сохраняет JSON `deploy_compose_stack_summary_v0` с commit, method, smoke/version/backup status и backup path.

Текущее preview-состояние от 2026-06-14: stack поднят на VPS, GitHub Actions auto-deploy проверен, smoke-check проходит, 7d BTC/ETH/SOL data sync выполнен в отдельную preview БД. Preview Nginx HTTP site `deltagrid-preview` уже включён и проверен через `Host: preview.deltagrid.pro`; внешний HTTPS-домен ждёт DNS-запись `preview -> 2.25.143.143` и выпуск SSL по чеклисту [deploy/dns/preview.deltagrid.pro.md](deploy/dns/preview.deltagrid.pro.md).

Для release smoke на preview или production используйте общий wrapper:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/release-smoke.sh
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/release-smoke.sh
```

Он последовательно запускает `server-smoke`, `perp-dex-policy-smoke`, `perp-dex-direct-smoke` и `coinglass-perp-dex-coverage-smoke`. Raw provider payload и secrets не печатаются.

Минимальный production evidence после deploy:

```bash
cd /opt/deltagrid
curl -fsS http://127.0.0.1:3001/version
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/server-smoke.sh
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/release-smoke.sh
```

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

Для backup PostgreSQL перед деплоем или рискованной миграцией:

```bash
cd /opt/deltagrid
sh scripts/backup-postgres.sh
```

Скрипт сохраняет сжатый `pg_dump` в `backups/` и читает `POSTGRES_USER`/`POSTGRES_DB` из `.env.production`.

Для preview/dev стека используются отдельные cron-файлы и логи, чтобы не смешивать его с production и не запускать core/candidate symbols одним большим burst:

```bash
cd /opt/deltagrid-preview
sudo SCHEDULE="*/15 * * * *" PROJECT_DIR=/opt/deltagrid-preview ENV_FILE=.env.preview COMPOSE_PROJECT_NAME=deltagrid-preview \
  CRON_FILE=/etc/cron.d/deltagrid-preview-market-sync-core \
  LOG_FILE=/var/log/deltagrid-preview-market-sync-core.log \
  SYMBOLS=BTC,ETH,SOL \
  sh scripts/install-market-sync-cron.sh

sudo SCHEDULE="5,20,35,50 * * * *" PROJECT_DIR=/opt/deltagrid-preview ENV_FILE=.env.preview COMPOSE_PROJECT_NAME=deltagrid-preview \
  CRON_FILE=/etc/cron.d/deltagrid-preview-market-sync-candidates \
  LOG_FILE=/var/log/deltagrid-preview-market-sync-candidates.log \
  SYMBOLS=HYPE,XRP,DOGE,ADA,LINK \
  sh scripts/install-market-sync-cron.sh
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
| `GET /api/v1/data/provider-inventory?symbols=BTC,ETH,SOL,HYPE&exchange=okx` | Read-only inventory кандидатов на расширение universe поверх persisted coverage/freshness: `promotion_candidate`, `chart_ready_candidates`, `policy.gates`, `next_action`, readiness status, 24h/7d summaries, `coverage_blockers_7d`, `freshness_blockers`, `promotion_blockers`, summary-разбивку blocker'ов по stream, summary-разбивку по `resolution_strategy` и `freshness_scope=requested_symbols` без внешних API-вызовов. |
| `GET /api/v1/perp-dex/venues/hyperliquid/markets?symbols=BTC,ETH,SOL` | Read-only live Hyperliquid public snapshot через `metaAndAssetCtxs`: mark/mid/oracle price, funding, open interest, 24h volume, premium, impact prices и leverage metadata. Endpoint делает внешний provider call, не пишет в БД и возвращает `execution_enabled=false`. |
| `GET /api/v1/perp-dex/venues/dydx/markets?symbols=BTC,ETH,SOL` | Read-only live dYdX v4 Indexer snapshot через `perpetualMarkets`: oracle price как mark proxy, 24h price change, funding, open interest, 24h volume, trades, margin fractions, tick/step size и leverage estimate. Endpoint делает внешний provider call, не пишет в БД и возвращает `execution_enabled=false`. |
| `GET /api/v1/perp-dex/venues/lighter/markets?symbols=BTC,ETH,SOL` | Read-only live Lighter snapshot через public `orderBooks`, `orderBookDetails`, `orderBookOrders` и `funding-rates`: last trade price как display price, funding, OI USD estimate, 24h volume, trades, maker/taker fee, margin fractions, tick/step size, best bid/ask, display spread и top-order depth summaries. Endpoint делает внешний provider call, не пишет в БД, не включает route scoring и возвращает `execution_enabled=false`. |
| `GET /api/v1/perp-dex/venues/aster/markets?symbols=BTC,ETH,SOL` | Read-only live Aster snapshot через public Futures `exchangeInfo`, `premiumIndex`, `ticker/24hr`, `openInterest`, `ticker/bookTicker` и `fapi/v3/depth`: mark/index/mid price, funding, OI USD estimate, 24h volume, trades, top-of-book, top-level depth summaries, tick/step size и min notional. Endpoint делает внешний provider call, не пишет в БД, не включает route scoring и возвращает `execution_enabled=false`. |
| `GET /api/v1/perp-dex/venues/gmx/markets?symbols=BTC,ETH,SOL` | Read-only GMX Arbitrum `markets/info` raw snapshot плюс `/tokens` diagnostics: `fundingRate*`, `borrowingRate*`, `netRate*` возвращаются как raw strings, index/long/short token decimals возвращаются как diagnostic fields, `poolAmountLong/Short` масштабируются в token units, а `openInterestLong/Short` и `availableLiquidityLong/Short` масштабируются через `1e30` в diagnostic-only USD strings с `diagnostic_usd_scale_status`. Endpoint возвращает `rate_relation_summary` для counts по source/raw-sum/zero-borrowing diagnostics и `rate_source_fields_summary` для проверки отсутствующих helper inputs. Endpoint делает внешний provider call, не пишет в БД, не заполняет production `open_interest_usd` для GMX и возвращает `execution_enabled=false`. |
| `GET /api/v1/perp-dex/venues/coinglass/markets?symbols=BTC,ETH,SOL` | Read-only CoinGlass Perp DEX enrichment через futures `coins-markets`: third-party aggregate rows для DEX-like venues (`Aster`, `Lighter`, `EdgeX`, `Drift` по умолчанию; `exchanges=` можно ограничить supported candidate list). Endpoint делает внешний CoinGlass call, не пишет в БД, возвращает `normalization_status=coinglass_coin_market_enrichment`, `ranking_enabled=false`, `production_signal_enabled=false`, `execution_enabled=false`. |
| `GET /api/v1/perp-dex/route-constraints` | Read-only policy для Perp DEX route/execution boundary: `research_only`, normalized vs raw venues, blockers для GMX scale validation, fees/slippage model и execution. Возвращает `gmx_formula_validation` с source-backed diagnostic notes: `poolAmountLong/Short` можно показывать только как token-unit diagnostics, `openInterest*`/`availableLiquidity*` доступны только как diagnostic USD fields, а rates остаются raw до route-level cost model. Endpoint не делает внешних provider calls. |
| `GET /api/v1/perp-dex/route-model` | Read-only route model v0 для fees/slippage/routing: checklist обязательных входов, venue readiness, Lighter/Aster cost semantics metadata, formula skeleton, `diagnostic_cost_estimate_v0` для component readiness без total cost bps и `gmx_rate_semantics` metadata по hourly `fundingRate*`/`borrowingRate*`/`netRate*`, включая offline guardrail для ожидаемой relation `netRate=fundingRate-borrowingRate` и live blocker по nonzero-borrowing `/markets/info` mapping. `diagnostic_cost_estimate_v0.summary` отдаёт machine-readable counts/id-списки по components для `Route Diagnostic Components Summary`, `summary.venue_breakdown` группирует readiness по venue для `Route Diagnostic Venue Breakdown`, `summary.blocker_breakdown` группирует repeated blockers для `Route Diagnostic Blocker Breakdown`, `summary.required_input_breakdown` связывает components с required inputs для `Route Diagnostic Required Input Breakdown`, `summary.source_field_breakdown` показывает sourced display fields, `summary.source_input_action_coverage` связывает source fields с required inputs и next actions для `Route Diagnostic Source Input Actions`, `summary.route_ready_evidence_checklist` группирует pre-route-scoring evidence gates для `Route Diagnostic Evidence Checklist`, `summary.venue_evidence_status` разделяет Lighter/Aster/GMX/cross-venue evidence gaps для `Route Diagnostic Venue Evidence Status`, `gmx_rate_mapping_review_v0` выносит GMX `rate_relation_summary`/`rate_source_fields_summary` в read-only review для `GMX Rate Mapping Review`, `gmx_rate_mapping_review_v0.blocker_breakdown` группирует repeated GMX mapping blockers для `GMX Rate Mapping Blockers`, `gmx_rate_mapping_review_v0.fixture_readiness_matrix` показывает side-aware GMX fixture cases для `GMX Rate Fixture Readiness`, `gmx_rate_mapping_review_v0.side_aware_fixture_expectations` показывает `longsPayShorts` long/short paying/receiving cases для `GMX Rate Side-aware Fixtures`, `gmx_rate_mapping_review_v0.mapping_decision_checklist` показывает read-only source/fixture/review/manual-approval checks для `GMX Rate Mapping Decision Checklist`, `gmx_rate_mapping_review_v0.carry_readiness_summary` и `carry_input_checklist` показывают read-only carry horizon/notional/sign/source/display gates для `GMX Rate Carry Readiness Summary` и `GMX Rate Carry Input Checklist`, `gmx_rate_mapping_review_v0.carry_source_evidence_summary` и `carry_source_evidence_checklist` показывают source/fixture/runtime/manual evidence gates для `GMX Rate Carry Evidence Summary` и `GMX Rate Carry Evidence Checklist`, `gmx_rate_mapping_review_v0.live_helper_source_summary` и `live_helper_source_checklist` показывают live `/markets/info` rate output evidence, missing helper source inputs, side-direction fields и manual review gate для `GMX Rate Live Helper Source Review`, `summary.safe_use_breakdown` группирует boundary text, `summary.readiness_rollup` даёт compact fee/depth/carry/risk readiness, `summary.depth_staleness_policy_checklist` фиксирует freshness/stale-depth policy gates для Lighter/Aster depth diagnostics перед любым slippage bps, `summary.required_policy_input_breakdown` группирует required policy inputs для этих gates, а `summary.next_action_breakdown` группирует planning actions из этих слоёв; policy smoke проверяет consistency summary/components и умеет печатать compact compare diff через `COMPARE_BASE_URL`. Numeric cost estimates, carry conversion, route ranking, production liquidity signal и execution отключены; endpoint не делает внешних provider calls. |
| `GET /api/v1/data/health` | Health snapshot data-layer: статусы провайдеров, последние sync, row counts, data quality score, freshness SLA, coverage matrix, universe readiness, health по `sync_type` и cron/data-sync diagnostics. |

Для sparse event streams вроде `liquidations` `/data/health` различает возраст последнего события и свежесть sync-run: отсутствие новых событий не считается stale, если `coinglass/liquidations` sync свежий и успешный.
`/data/coverage` и блок `coverage` внутри `/data/health` используют ту же семантику для sparse streams: свежий успешный sync-run подтверждает provider coverage даже при отсутствии новых liquidation events.

`/data/health` остаётся production SLA snapshot для текущего UI universe `BTC/ETH/SOL`. Для кандидатов на расширение используйте `/data/provider-inventory`: он считает freshness по запрошенным symbols, но сам не расширяет UI universe и не запускает внешние provider calls.
В provider inventory `chart_ready_candidates` — это только готовность для preview `/charts` и `/assets`; `promotion_candidates` для full analytics universe требуют `complete_history`, поэтому `core_perp_ready` с partial snapshot/enrichment streams не считается full promotion.
Blocker rows в provider inventory содержат `resolution_strategy`: `open_interest`, `basis_premium` и `spot_perp_price` в текущем MVP ingestion path требуют `snapshot_accumulation_required`, а не обычный historical backfill; для быстрого full promotion нужен отдельный historical source или 7d окно накопления snapshots.

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
