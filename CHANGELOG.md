# Changelog — DeltaGrid

## [2026-06-15] - [DATA] - Provider discovery v1 для expansion candidates
- Добавлен read-only CLI `python -m app.adapters.data.discover_provider_universe` для live discovery по OKX, CoinGlass, CoinGecko и legacy Binance без записи в PostgreSQL.
- CLI проверяет candidate symbols из MVP1 inventory: OKX USDT swap instrument/OHLCV/funding/OI/long-short, CoinGlass OKX snapshots/liquidations, CoinGecko spot price и Binance USD-M как legacy diagnostic.
- Добавлены retry/backoff и спокойный OKX pacing, чтобы discovery не ловил ложные `429` на long/short endpoint.
- Preview/VPS discovery выполнен внутри `deltagrid-preview-backend`: OKX/CoinGlass/CoinGecko `healthy`, Binance legacy `blocked_http_451`, все `20/20` symbols получили `eligible_for_24h_sync_dry_run`.
- Добавлены unit tests для parser/readiness/markdown report helpers.

## [2026-06-15] - [DATA] - Provider inventory v0 для расширения universe
- Добавлен read-only endpoint `GET /api/v1/data/provider-inventory`, который строит inventory кандидатов на расширение universe поверх уже сохранённых coverage/freshness сигналов.
- Default candidate set расширен за пределы `BTC/ETH/SOL`: `HYPE`, `XRP`, `DOGE`, `BNB`, `ADA`, `LINK`, `AVAX`, `SUI`, `TON`, `TRX`, `DOT`, `LTC`, `BCH`, `AAVE`, `UNI`, `APT`, `ARB`.
- Endpoint не вызывает OKX, CoinGlass, CoinGecko или legacy Binance: `inventory_mode=persisted_data_only`, `external_provider_calls=false`.
- Для каждого symbol возвращаются readiness status, 24h/7d coverage summary, freshness tracking, `promotion_candidate`, `next_action` и reason. Символы без persisted streams получают `backfill_required` и не попадают в promotion candidates.
- Добавлены regression tests для default candidate list и блокировки symbol без coverage.

## [2026-06-14] - [OPS] - Docker Compose deploy recreate стабилизирован
- `scripts/deploy-compose-stack.sh` больше не использует единый `docker compose up -d --build backend frontend`, который на preview дважды приводил к Docker Compose name-conflict при recreate backend.
- Новый порядок deploy: сначала `compose build backend frontend`, затем явный `compose rm -sf backend frontend`, затем `compose up -d --no-build backend frontend`.
- PostgreSQL container и volume не удаляются; изменение касается только пересоздания app containers `backend` и `frontend`.
- Добавлен `.gitattributes` с `*.sh text eol=lf`, чтобы shell-скрипты не получали CRLF/mixed line endings в Windows workspace.
- Проверка на `/opt/deltagrid-preview`: `sh -n scripts/deploy-compose-stack.sh` проходит, ручной preview deploy завершился без name-conflict, backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.

## [2026-06-14] - [CI/SECURITY] - Frontend audit gate для high/critical advisory
- Проверен Next.js 16 regression path: актуальный stable `next@16.2.9` требует Node `>=20.9.0`, но всё ещё содержит bundled `postcss 8.4.31`, поэтому не закрывает остаточный `moderate` advisory `postcss <8.5.10`.
- Fixed `postcss 8.5.10` найден только в `next@canary`; canary-версия не переводится в production/preview runtime без отдельного решения.
- В `CI` добавлен frontend-шаг `npm audit --audit-level=high`, который блокирует high/critical advisory и при этом не ломает pipeline из-за текущего известного moderate внутри Next.
- `README.md`, `PROJECT_PLAN.md` и `BACKLOG.md` обновлены под новый security baseline и оставшийся upstream follow-up.

## [2026-06-14] - [FRONTEND/SECURITY] - Next.js обновлён до 15.5.19
- Frontend dependency `next` обновлена с `14.1.0` до `15.5.19`, чтобы закрыть critical/high advisory из старой версии.
- App Router страницы `/assets`, `/charts`, `/funding` и `/perp-dex` мигрированы на async `searchParams`, который требуется Next.js 15 при production build.
- `scripts/server-smoke.sh` переключён с проверки корня frontend на `/market`, чтобы deploy smoke оставался строгим по HTTP `200` и не падал на ожидаемом redirect `/ -> /market`.
- `README.md` и `ARCHITECTURE.md` обновлены до актуального стека Next.js 15.
- Проверка локально: `npm run build` во `frontend` проходит на Next.js `15.5.19`.
- `npm audit --json` после апгрейда показывает `0 high`, `0 critical` и `2 moderate`; остаточный риск связан с bundled `postcss <8.5.10` внутри Next и вынесен в отдельный regression pass для Next.js 16.x или upstream patch.

## [2026-06-14] - [OPS] - Production deploy diagnostics подготовлены в preview
- В ветке `preview` подготовлен hardening для `Deploy Production`: явные `configured/missing` шаги для `PROD_*`, проверка fingerprint deploy key, expected values для `2.25.143.143/root//opt/deltagrid`, warning-only TCP port probe, SSH login retry и проверка production app dir перед deploy.
- Safe-skip семантика сохранена: если обязательный production secret отсутствует, workflow не должен падать на value-check шагах.
- Preview workflow также получил guard для value-check шагов, чтобы пустой secret не превращал safe-skip в failure.
- Изменение пока не активировано на `main`; production `/opt/deltagrid` не менялся и остаётся healthy.
- Проверка после preview auto-deploy: `/opt/deltagrid-preview` обновился до `9aab346`, backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.

## [2026-06-14] - [OPS] - Preview Nginx HTTP pre-stage
- На VPS заранее включён отдельный Nginx site `deltagrid-preview` для `preview.deltagrid.pro`: frontend проксируется на `127.0.0.1:3012`, backend/API/WebSocket — на `127.0.0.1:8011`.
- Production site `deltagrid` не изменялся; `nginx -t` прошёл успешно, Nginx reload выполнен.
- Проверка без публичного DNS через `Host: preview.deltagrid.pro` прошла: backend readiness возвращает `ready`, `/` и `/charts?symbol=BTC&interval=1m&range=7d` возвращают HTTP `200`.
- DNS `preview.deltagrid.pro` пока не резолвится, поэтому Let's Encrypt SSL ещё не выпускался. Следующий шаг: добавить DNS `A preview -> 2.25.143.143`, затем запустить `scripts/configure-preview-nginx-ssl.sh`.

## [2026-06-14] - [OPS] - Preview auto-deploy через GitHub Actions
- GitHub repository secrets `PREVIEW_SSH_HOST`, `PREVIEW_SSH_USER`, `PREVIEW_SSH_KEY` и `PREVIEW_APP_DIR` доведены до рабочего состояния для preview deploy.
- Workflow `Deploy Preview` прошёл end-to-end: readiness обязательных secrets, fingerprint deploy key, SSH port/login, проверка `/opt/deltagrid-preview` и сам deploy step.
- Preview VPS `/opt/deltagrid-preview` обновлён через GitHub Actions; контрольные probes `1e1371c` и `6e8edb2` подтвердили реальный deploy, backend/frontend/PostgreSQL в Compose project `deltagrid-preview` находятся в состоянии `healthy`.
- Preview workflow усилен после flaky GitHub runner: TCP port probe переведён в warning-only diagnostics, SSH login получил явные timeout/keepalive и retry.
- Проверка после auto-deploy: `BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/server-smoke.sh` прошёл.
- Production deploy в этой итерации не менялся; следующий ops-шаг — DNS/Nginx/SSL для `preview.deltagrid.pro` и отдельная проверка `PROD_*` secrets.

## [2026-06-14] - [RELEASE/OPS] - Preview domain и deploy runbooks
- Восстановлен `AGENTS.md` как проектный файл правил для Codex/AI-агентов; локально файла не было, хотя workflow проекта его требует.
- Добавлен preview Nginx template `deploy/nginx/deltagrid-preview.conf.example`: frontend `127.0.0.1:3012`, backend/API/WebSocket `127.0.0.1:8011`, домен `preview.deltagrid.pro`.
- Добавлен `scripts/configure-preview-nginx-ssl.sh` для безопасной публикации preview-домена: DNS-precheck, отдельный site `deltagrid-preview`, отдельный Let's Encrypt сертификат, без изменения production site `deltagrid`.
- Добавлен DNS-чеклист `deploy/dns/preview.deltagrid.pro.md` с Cloudflare/DNS записью, командами проверки и smoke-check после SSL.
- Добавлен чеклист `deploy/github-actions-secrets.md` для repository secrets `PREVIEW_*` и `PROD_*`, включая создание dedicated SSH key и проверку первого auto-deploy.
- Создан dedicated SSH deploy key `github-actions-deltagrid-deploy`; public key добавлен на VPS в `/root/.ssh/authorized_keys`, non-interactive login проверен. Private key сохранён локально в `outputs/deploy-keys/` и не коммитится.
- `main` fast-forward синхронизирован с `preview` на ops commit `104502e`, потому что `workflow_run` использует deploy workflows из default branch. Production checkout `/opt/deltagrid` также fast-forward обновлён без rebuild; local smoke-check прошёл.
- Preview deploy probe `fdb08ec` показал, что workflow запускается после preview CI, но deploy пока safe-skip из-за отсутствующих или неполных GitHub secrets `PREVIEW_*`.
- Deploy workflows получили безопасную диагностику readiness: логи показывают только `configured/missing` для обязательных SSH secrets, без вывода значений.
- Документация обновлена: `README.md`, `DEPLOYMENT.md`, `RELEASES.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md`, `BACKLOG.md`.
- Фактическая проверка перед правками: `preview.deltagrid.pro` ещё не резолвится; production и preview containers на VPS находятся в состоянии `healthy`.

## [2026-06-14] - [RELEASE/OPS] - Preview stack contract
- Добавлен `.env.preview.example` для отдельного dev/staging стенда: `preview.deltagrid.pro`, ports `8011/3012`, отдельные PostgreSQL credentials и runtime tuning.
- `.gitignore` дополнен `.env.preview`, чтобы реальные preview secrets не попадали в Git.
- Добавлен общий `scripts/deploy-compose-stack.sh`, который делает `git pull --ff-only`, запускает нужный Compose project и прогоняет smoke-check для выбранного стенда.
- `scripts/deploy-compose-stack.sh` ждёт healthcheck `postgres`, `backend` и `frontend` перед smoke-check, чтобы deploy не падал на race condition сразу после старта frontend.
- `scripts/sync-market-data.sh` теперь поддерживает `COMPOSE_PROJECT_NAME`, чтобы market sync можно было запускать против preview stack без риска затронуть production containers/volume.
- GitHub workflows `Deploy Preview` и `Deploy Production` переведены на общий deploy script и разные defaults: preview использует `.env.preview`/`deltagrid-preview`/`8011/3012`, production использует `.env.production`/`deltagrid`/`8000/3001`.
- Preview stack поднят на VPS в `/opt/deltagrid-preview`: backend `127.0.0.1:8011`, frontend `127.0.0.1:3012`, PostgreSQL volume `deltagrid-preview_postgres_data`.
- Preview 7d sync BTC/ETH/SOL завершён с `errors=0`; `/api/v1/data/health` показывает OKX/CoinGlass/CoinGecko `healthy`, freshness `24/0/24`, `core_perp_ready=3`, `chart_ready=3`.
- Production stack после preview rollout повторно проверен через local smoke; containers остаются healthy.
- Документация обновлена под dev/prod разделение: `README.md`, `DEPLOYMENT.md`, `RELEASES.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md`, `BACKLOG.md`.

## [2026-06-14] - [RELEASE/OPS] - Baseline `v1.3.0` и GitHub CI/CD
- Зафиксирована корневая версия `VERSION=1.3.0`; frontend package version поднят до `1.3.0`.
- Добавлен `RELEASES.md` с правилами SemVer, ветками `preview/main`, release flow и назначением файлов `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md`, `ARCHITECTURE.md`.
- Добавлен GitHub Actions workflow `CI`: backend tests, `compileall app`, frontend `npm ci` и `npm run build`.
- `CI` устанавливает `pytest` отдельно от backend runtime dependencies, чтобы production `requirements.txt` не раздувался тестовыми пакетами.
- Backend CI запускает `pytest tests`, чтобы legacy smoke scripts `test_api.py` и `regression_test.py` не исполнялись как unit tests без поднятого сервера.
- Добавлены GitHub Actions workflows `Deploy Preview` и `Deploy Production`; они деплоят `preview` и `main` по SSH после успешного CI, если соответствующие secrets настроены.
- Deploy workflows дополнительно проверяют `workflow_run.head_branch`, чтобы preview deploy не запускался от `main` CI и production deploy не запускался от `preview` CI.
- Deploy workflows безопасно пропускают deploy, если SSH secrets ещё не заведены в GitHub.
- `.gitignore` дополнен `outputs/`, чтобы локальные логи и временные deploy-архивы не попадали в release commit.

## [2026-06-14] - [DATA/FRONTEND] - Production universe v1
- Добавлен read-only endpoint `GET /api/v1/data/universe`, который классифицирует symbols поверх coverage/freshness сигналов.
- Universe readiness статусы: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`.
- `/api/v1/data/health` теперь включает блок `universe` с `policy.ui_universe`, `deferred_symbols` и per-symbol summary.
- `/data-health` получил таблицу `Production Universe`: symbol, status, chart readiness, 24h/7d coverage, partial/missing streams и reason.
- Правило MVP1: показывать symbol в primary UI universe только если chart-critical streams покрыты, freshness зелёный и нет missing tracked streams.
- Добавлен regression test: symbol без persisted coverage классифицируется как `not_ready` и попадает в `deferred_symbols`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/universe?symbols=BTC,ETH,SOL&exchange=okx` показывает `core_perp_ready=3`, `chart_ready=3`, `not_ready=0`; `policy.ui_universe=["BTC","ETH","SOL"]`.
- Все три symbol имеют partial enrichment streams на `7d`: `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot`; missing streams нет.
- SSR-проверка `/data-health` вернула `200` и подтвердила наличие блока `Production Universe`.
- Проверка локально: backend `pytest` — `26 passed`; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - Coverage matrix для data-layer
- Добавлен read-only endpoint `GET /api/v1/data/coverage` для инвентаризации покрытия истории по `symbol + exchange + stream + interval`.
- `/api/v1/data/health` расширен полем `coverage` без breaking changes: старые поля health, freshness и sync diagnostics сохранены.
- Coverage matrix считает регулярные потоки по ожидаемой cadence в окне `24h/7d`: OHLCV, funding, OI, long/short, basis и отдельный поток `spot_perp_price`.
- Для sparse stream `liquidations` coverage учитывает свежий успешный `coinglass/liquidations` sync-run, чтобы отсутствие событий не считалось отсутствием provider coverage.
- `/data-health` получил KPI `Coverage` и таблицу `Coverage Matrix` с rows/expected, coverage %, latest timestamp и reason.
- Добавлены regression tests для `/data/coverage`, unsupported range и включения `coverage` в `/data/health`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/coverage?symbols=BTC,ETH,SOL&exchange=okx&range=24h` показывает `covered=27/27`, `missing=0`.
- Production `7d` coverage показывает `covered=18`, `partial=9`, `missing=0`: partial сейчас у `open_interest` и `basis/spot_perp_price`, что даёт честный вход для production universe v1.
- SSR-проверка `/data-health` вернула `200` и подтвердила наличие блока `Coverage Matrix`.
- Проверка локально: backend `pytest` — `25 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - OHLCV window endpoint для charts
- Добавлен read-only endpoint `GET /api/v1/data/ohlcv/window` для interactive charts: он возвращает bounded OHLCV окно по `symbol`, `exchange`, `interval` и `range` без клиентской постраничной сборки через `/data/ohlcv`.
- Поддерживаемые интервалы: `1m`, `5m`, `1h`; диапазоны: `2h`, `8h`, `24h`, `7d`; максимальный размер окна ограничен `20000` строками.
- Если `end` не задан, endpoint сам использует последнюю доступную свечу в PostgreSQL как правый край окна, что сохраняет поведение Charts v0 при рассинхроне локального времени и production dataset.
- `/charts` переключён на `/data/ohlcv/window`; старая клиентская постраничная сборка оставлена fallback path, если endpoint временно недоступен.
- Добавлены regression tests для latest-anchored окна и unsupported interval.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/ohlcv/window?symbol=BTC&exchange=okx&interval=1m&range=7d` возвращает `count=10080`, `expected_rows=10080`, `limit=20000`, `window_source=latest_available`.
- Browser QA `/charts?symbol=BTC&interval=1m&range=7d` подтвердил chart container `935x520`, `7` canvas, `10,080` свечей и отсутствие `No candle data`.
- Проверка локально: backend `pytest` — `23 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - Sparse liquidation freshness
- Исправлена семантика freshness SLA для sparse event stream `liquidations`: старый timestamp последнего события больше не помечает поток как stale, если последний `coinglass/liquidations` sync-run свежий и завершён успешно.
- `/api/v1/data/health` теперь добавляет для sparse streams поля `freshness_mode`, `sync_provider`, `sync_type`, `latest_sync_status`, `latest_sync_at`, `latest_successful_sync_at`, `sync_age_minutes`, `sync_stale_after_minutes` и `sync_degraded_after_minutes`.
- `/data-health` показывает для sparse streams возраст как `event ... / sync ...`, чтобы было видно различие между отсутствием свежих ликвидационных событий и проблемой ingestion path.
- Добавлен regression test: старый `SOL/okx/liquidations/1h` event при свежем `coinglass/liquidations` sync остаётся `fresh` с reason `no recent liquidation events`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/health` после deploy показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`; `SOL/okx/liquidations/1h` имеет `status=fresh`, `freshness_mode=sparse_event`, `sync_provider=coinglass`, `sync_type=liquidations`.
- Browser QA `/data-health` подтвердил `24/24`, колонку `Event / sync age` и reason `no recent liquidation events`.
- Проверка локально: backend `pytest` — `21 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-13] - [DEPLOY/FRONTEND] - Production Interactive Charts v0
- Charts v0 задеплоен на `deltagrid.pro`: frontend image пересобран с `lightweight-charts`, stack поднят через `docker-compose.prod.yml`, backend/frontend/PostgreSQL находятся в состоянии `healthy`.
- Перед файловым deploy сохранён backup затрагиваемых серверных файлов в `/tmp/deltagrid-deploy-backups/charts-v0-predeploy-20260613_161655.tgz`.
- Локальный server smoke на VPS прошёл: backend health, readiness, data health и frontend вернули `ok`.
- Публичные smoke-checks прошли: `/api/v1/health/readiness`, `/api/v1/data/health`, `/charts?symbol=BTC&interval=1m&range=7d` и `/charts?symbol=ETH&interval=5m&range=24h` возвращают `200`.
- Browser QA на production подтвердил desktop `BTC 1m 7d`: chart container `935x520`, `10,080` свечей, canvas отрисован, `No candle data` отсутствует.
- Browser QA на production подтвердил mobile `ETH 5m 24h`: chart container `309x520`, `288` свечей, sidebar скрыт, горизонтального overflow нет.
- Production `/api/v1/data/health` после deploy показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, OKX/CoinGlass/CoinGecko `healthy`, Binance `degraded` как legacy/diagnostic provider.

## [2026-06-13] - [FRONTEND] - Interactive Charts v0 локально
- Добавлен первый production-oriented слой интерактивных графиков на `lightweight-charts`: OHLCV candles, volume histogram, crosshair OHLC/volume панель, pan/zoom/scroll и выбор `BTC/ETH/SOL`, интервала `1m/5m/1h`, диапазона `2h/8h/24h/7d`.
- `/charts` читает проверенную OKX USDT Swap историю через существующие read-only data-layer endpoints без изменения backend API-контракта. Для 7d `1m` режима frontend собирает окно постранично поверх текущего лимита `/data/ohlcv` в 1000 строк.
- Данные для окна строятся от последней доступной свечи в PostgreSQL, а не от локального `Date.now()`, чтобы интерфейс корректно работал при расхождении времени тестового окружения и production dataset.
- Исправлена мобильная ширина терминала: sidebar скрывается на малых viewport, поэтому chart canvas получает рабочую область вместо узкой колонки.
- Проверка: frontend `npm run build` проходит; Browser QA через SSH tunnel к production backend подтвердил `BTC 1m 7d` с `10,080` свечами на desktop и `ETH 5m 24h` с `288` свечами на mobile, без `No candle data`.
- Статус обновлён: production deploy выполнен отдельной итерацией выше.

## [2026-06-13] - [DEPLOY/DATA] - Production Data Quality Gate и 7d backfill
- Data Quality Gate diagnostics задеплоены на `deltagrid.pro`: `/api/v1/data/health` отдаёт `freshness`, `sync_health_by_type` и `sync_diagnostics`, а `/data-health` показывает `Freshness SLA`, `Sync Types`, `Cron Diagnostics` и `Recent Error Classes`.
- Production smoke-check прошёл локально на сервере и через домен: backend health, readiness, data health и frontend возвращают `ok`.
- После деплоя production health показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, cron-path `healthy`, OKX/CoinGlass/CoinGecko `healthy`; Binance остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451`.
- Первый host-level cron после деплоя и 7d backfill сработал в `2026-06-13 00:15 UTC` и завершился `fetched=465`, `inserted=460`, `errors=0`; health после cron показывает `last_run_age_minutes≈1` и cron status `healthy`.
- 72h OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `fetched=16239`, `inserted=16308`, `errors=0`; SQL-проверка покрытия показала `4320/864/72` строк на каждый символ и `gaps=0`.
- 7d OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `fetched=37875`, `inserted=38103`, `errors=0`; SQL-проверка покрытия показала `10080/2016/168` строк на каждый символ и `gaps=0`.
- Production row counts после 7d backfill и cron: `ohlcv=77819`, `funding_rates=2442`, `open_interest=4329`, `liquidations=1930`, `long_short_ratio=1068`, `basis_premium=2310`, `provider_sync_runs=5351`.

## [2026-06-13] - [DATA/FRONTEND] - Data Quality Gate diagnostics
- `/api/v1/data/health` расширен без breaking changes: старые поля `providers`, `last_sync`, `row_counts` и `data_quality` сохранены, добавлены `freshness`, `sync_health_by_type` и `sync_diagnostics`.
- `freshness` считает SLA по `BTC/ETH/SOL`, `exchange=okx`, streams `ohlcv`, `funding_rates`, `open_interest`, `long_short_ratio`, `liquidations`, `basis_premium` и интервалам `1m/5m/1h/8h/snapshot`.
- `sync_health_by_type` разделяет provider health по `provider_name + sync_type`, чтобы частичные ошибки одного потока не скрывали состояние остальных потоков.
- `sync_diagnostics` показывает cron-path состояние из `provider_sync_runs`: последний запуск, последний успешный запуск, records fetched/inserted и классы ошибок `http_451`, `rate_limit`, `circuit_breaker`, `empty_response`.
- `/data-health` получил таблицы `Freshness SLA`, `Sync Types`, `Cron Diagnostics` и `Recent Error Classes`.
- Проверка: backend `pytest` — `20 passed`; `compileall app` проходит; frontend `npm run build` проходит; локальный HTTP smoke `/data-health` через `next start` вернул `200`.

## [2026-06-13] - [DEPLOY/DATA] - OKX primary на production
- OKX primary flow задеплоен на `deltagrid.pro`: backend и frontend Docker images пересобраны, `deltagrid-backend-1`, `deltagrid-frontend-1` и `deltagrid-postgres-1` находятся в состоянии `healthy`.
- Перед распаковкой на сервере создан backup изменяемых файлов: `/tmp/deltagrid-okx-predeploy-20260612_233017.tgz`.
- Ручной production sync `BTC,ETH,SOL` за 24 часа с `--primary-perp-provider okx` завершился без ошибок: `fetched=5421`, `inserted=5439`, `errors=0`.
- Проверен cron-path без явного provider flag: `/etc/cron.d/deltagrid-market-sync` вызывает `scripts/sync-market-data.sh`, а новый default пишет OKX OHLCV/OI/long-short, CoinGlass liquidations и CoinGlass snapshots с `exchange_list=OKX`; контрольный прогон завершился `errors=0`.
- `/api/v1/data/health` теперь показывает `okx healthy`; последние OKX sync-runs завершены успешно, Binance остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451` на текущем VPS.
- Production row counts после проверки: `ohlcv=46277`, `funding_rates=2373`, `open_interest=4299`, `liquidations=1288`, `long_short_ratio=636`, `basis_premium=2295`, `provider_sync_runs=5316`.
- Прямые API-проверки с `exchange=okx` возвращают данные для OHLCV, funding, open interest, long/short ratio, liquidations и basis; frontend routes `/market`, `/charts?symbol=BTC`, `/assets?symbol=BTC`, `/funding`, `/perp-dex`, `/data-health` отвечают `200`.

## [2026-06-13] - [DATA/FRONTEND] - OKX primary perp provider
- Добавлен `OkxAdapter` для public OKX USDT swap data: OHLCV candles, funding history, open interest snapshots и long/short account ratio.
- `sync_market_data` получил флаг `--primary-perp-provider` и по умолчанию использует `okx`; `binance` сохранён как legacy/diagnostic option.
- CoinGecko-derived `basis_premium` теперь может считаться от последнего primary perp close; для OKX это `CoinGecko spot vs OKX 1m perp close`.
- CoinGlass aggregated liquidations теперь получают exchange list по primary provider и могут записывать строки с `exchange=okx`.
- CoinGlass funding/OI snapshots теперь тоже принимают exchange list по primary provider, чтобы enrichment-слой не оставался скрыто привязанным к Binance.
- `/api/v1/data/health` начал отслеживать provider `okx` вместе с `binance`, `coinglass` и `coingecko`.
- Terminal frontend read-side переключён на `exchange=okx` для persisted OHLCV, funding, OI, long/short, basis и asset liquidations; UI captions больше не обещают Binance как primary source.
- Добавлены regression tests для OKX normalization: candle volume, funding realized rate, OI snapshot, long/short ratio conversion и interval mapping.
- Проверка: backend tests `19 passed`; `compileall app` проходит; frontend `npm run build` проходит. Local OKX sync smoke на in-memory SQLite записал 15 BTC 1m candles, 1 OI snapshot и 3 long/short points без ошибок.

## [2026-06-13] - [AUDIT/PLAN] - Production data health и старт MVP1
- Проведён обзор состояния после MVP0: public smoke-check `https://deltagrid.pro`, `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend проходят.
- Проверено состояние сервера по SSH: `cron` активен, `deltagrid-backend-1`, `deltagrid-frontend-1` и `deltagrid-postgres-1` healthy, host-level cron установлен на запуск market data sync каждые 15 минут.
- Зафиксировано накопление PostgreSQL data-layer: `ohlcv=41000`, `funding_rates=2340`, `open_interest=4260`, `liquidations=1193`, `long_short_ratio=564`, `basis_premium=2271`, `provider_sync_runs=5260`.
- Обнаружен production-блокер свежести CEX-данных: Binance Futures API на сервере возвращает HTTP `451`, из-за чего Binance OHLCV/funding/OI/L/S стали stale, а `/data/health` показывает `binance degraded`.
- Подтверждено, что CoinGlass/CoinGecko ветка продолжает обновляться: snapshots, basis и aggregated liquidations пишутся в PostgreSQL; проблема локализована в direct Binance FAPI path.
- `PROJECT_PLAN.md` и `BACKLOG.md` обновлены под новую стадию MVP1: data freshness SLA, provider health по потокам, cron diagnostics, backfill после восстановления provider path и только затем interactive charts/backtest foundation.
- Проверка локального дерева: backend `pytest` — `14 passed`; `compileall app` проходит; frontend `npm run build` проходит с `BACKEND_INTERNAL_URL=https://deltagrid.pro`.

## [2026-06-05] - [FRONTEND] - Presentation safety sweep
- Заменены грубые demo-формулировки в UI: `No mock fallback` -> `Live data only`, `No fake PnL` -> `Real PnL only`, `no fake DEX volume/OI` -> `direct DEX volume/OI pending`.
- `/backtests` заменён с `Coming Soon` на честный `Backtest History / Engine pending` readiness-state со ссылкой в `Strategy Lab`.
- `Strategy Lab` и provider screens сохраняют честную границу: реальные inputs показываются, synthetic PnL/performance скрыты до production backtest engine.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, контейнеры healthy, `server-smoke.sh` зелёный. HTML sweep подтвердил `200` и отсутствие `Application error`/грубых demo-labels на маршрутах `/market`, `/charts?symbol=BTC`, `/assets?symbol=ETH`, `/funding`, `/perp-dex`, `/arbitrage-scanner`, `/market-matrix`, `/strategy-lab`, `/backtests`; Browser QA подтвердил `Live data only`, `Real PnL only`, `Backtest Output Boundary`, `Backtest History / Engine pending` и heatmap без `USDT/USDE/USDH`.

## [2026-06-05] - [FRONTEND] - Strategy Lab readiness polish
- `Strategy Lab` больше не показывает пустой chart placeholder в `Backtest Output`: вместо этого добавлена таблица `Backtest Output Boundary` с PnL/equity, drawdown/Sharpe, trade log и execution как pending/disabled до реального engine.
- Price/funding input charts получили форматирование осей и hover-title с ценой/фандингом.
- Верхняя workspace-вкладка `/strategy-lab` переименована из `Backtest #1` в `Strategy Lab / Readiness`, чтобы не обещать fake backtest run.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. `/strategy-lab` возвращает `200`, Browser QA подтвердил `Strategy Lab / Readiness`, `Backtest Output Boundary`, `No fake PnL` и отсутствие `Backtest #1`.

## [2026-06-05] - [FRONTEND] - Final demo polish: Funding, Arbitrage, Matrix
- `Funding` получил source-плашки по assets/providers/storage, историю с реальными time labels вместо индексов и hover-title на funding chart.
- Funding matrix теперь показывает пустые ячейки нейтрально, а не как отрицательный сигнал; captions явно указывают persisted Binance/CoinGlass rows from PostgreSQL.
- `Arbitrage Scanner` убрал dev-like opportunity id из первой колонки: теперь таблица показывает candidate, type, legs, basis edge, funding, OI, evidence и risk note.
- `Market Matrix` получила колонку `Coverage` и status в source table, чтобы partial/missing streams выглядели как состояние данных, а не визуальная ошибка.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. Финальный route pass подтвердил `/market`, `/charts?symbol=BTC`, `/assets?symbol=ETH`, `/funding`, `/perp-dex`, `/arbitrage-scanner`, `/market-matrix` без runtime error; Browser QA подтвердил новые панели Funding/Arbitrage/Matrix.

## [2026-06-05] - [FRONTEND] - Assets symbol polish перед демо
- `Assets` больше не показывает hardcoded `SOLUSDT` в блоке order book: заголовок и empty-state строятся от выбранного `BTC/ETH/SOL`.
- Liquidation progress bars в `Assets` теперь рассчитываются от реальных long/short totals, а не от фиксированных demo widths.
- Верхняя workspace-вкладка для `/assets` переименована из `SOL` в `Assets`, а `/charts` больше не помечается как `Placeholder`.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. `/assets?symbol=BTC`, `/assets?symbol=ETH`, `/assets?symbol=SOL` возвращают правильные `BTCUSDT/ETHUSDT/SOLUSDT` labels без чужих pair labels; Browser QA подтвердил `Assets / Deep Dive` и `Charts / Live Streams`.

## [2026-06-05] - [FRONTEND] - Perp DEX live readiness screen
- `Perp DEX` больше не выглядит как пустой pending-экран: страница переиспользует live `Market Matrix`, `Arbitrage Scanner` и `Data Health` потоки без добавления fake DEX volume/OI.
- Добавлены KPI по live perp inputs, pending direct DEX adapters, largest OI, funding rows, liquidation rows и largest basis/funding edge.
- Добавлены таблицы `Perp Universe Readiness`, `Venue Adapter Status`, `Persisted Perp Data Coverage`, `Provider Health` и `Perp Research Candidates`.
- Direct Hyperliquid/dYdX/GMX adapters явно остаются `Pending`, а Binance/CoinGlass/CoinGecko показываются как live providers.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный, `/perp-dex` и `/perp-dex?view=opportunities` возвращают `200` без runtime error. Browser QA подтвердил новые панели и `Perp inputs live`.

## [2026-06-05] - [FRONTEND] - Быстрые hover-графики и stablecoin filter перед демо
- `Market Overview` теперь фильтрует stablecoin-like активы (`USDT`, `USDC`, `USDE`, `USDS`, `USDH`, `DAI`, `FDUSD`, `TUSD` и похожие USD-символы) до формирования heatmap, top gainers/losers и top assets.
- Heatmap берёт до 80 CoinGecko markets, после фильтрации оставляет top-30 и показывает первые 12 non-stable активов, чтобы вместо стоимости стейблов в демо были BTC/ETH/BNB/XRP/SOL/TRX/HYPE/DOGE и другие рыночные активы.
- `Charts` расширил видимый historical slice с 96 до 240 точек для line charts и до 120 точек для quote volume, а bar labels теперь разрежаются автоматически.
- `LineChart`, `BarChart` и свечной chart в `Assets` получили hover-title: время и значение по точке, для свечей - `Open/High/Low/Close/Volume`.
- `Assets` показывает до 240 1m свечей и использует `quote_volume` как основной volume для USD-контекста.
- В `BACKLOG.md` добавлена следующая крупная задача: полноценный слой historical charts на `lightweight-charts` с crosshair, pan/zoom/scroll, диапазонами и backend pagination/backfill.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный, `/market`, `/charts?symbol=BTC` и `/assets?symbol=ETH` возвращают `200` без runtime error. Browser QA подтвердил `display: grid` у heatmap, отсутствие стейблов и наличие SVG hover-title в Charts/Assets.

## [2026-06-05] - [FRONTEND] - Демо-доводка графиков и Market Overview
- Общие terminal-графики получили числовой контекст: `Last`, `Range`, Y-шкалу и X-подписи для line charts; bar charts теперь показывают максимум и диапазон.
- `Charts` показывает price, volume, OI, basis, funding и long/short с разными форматами осей: цена/доллары/проценты больше не выглядят как безымянные линии.
- `Assets` больше не захардкожен только на SOL: экран поддерживает переключение `BTC`, `ETH`, `SOL` через `?symbol=...`, показывает логотип CoinGecko и цену/диапазон на свечном графике.
- `Assets` ограничивает OHLCV-запрос последним рабочим окном через `start`, чтобы SSR не тянул тяжёлый 1000-row payload перед демо и не падал в пустой график при живых backend-данных.
- `Market Overview` теперь показывает цену в heatmap как основной сигнал, капитализацию как вторичный контекст, логотипы CoinGecko в top assets и реальные OHLCV sparkline для BTC/ETH/SOL, где история уже есть в PostgreSQL.
- В `BACKLOG.md` добавлена следующая data coverage итерация по perp/RWA universe: CoinGlass/CoinGecko/Binance coverage matrix, top-30 crypto и RWA-кандидаты.
- Проверка: `npm run build` проходит; локальный visual QA с `BACKEND_INTERNAL_URL=https://deltagrid.pro` подтвердил `/market`, `/charts?symbol=BTC`, `/assets?symbol=SOL`, `/assets?symbol=BTC` и `/perp-dex` без runtime error.
- Production deploy выполнен на `deltagrid.pro`: frontend image пересобран, stack healthy, `server-smoke.sh` через домен прошёл, `/market`, `/charts?symbol=BTC`, `/assets?symbol=SOL`, `/assets?symbol=BTC` и `/perp-dex` возвращают `200` без runtime error.

## [2026-06-05] - [DATA] - CoinGlass liquidation ingestion
- `CoinGlassClient` получил v4 endpoint `/api/futures/liquidation/aggregated-history` для агрегированной истории ликвидаций по монетам.
- `sync_market_data` теперь поддерживает `--include-liquidations` и пишет CoinGlass long/short liquidation history в таблицу `liquidations` с `exchange=binance`, чтобы существующие data endpoints и frontend-фильтры продолжали работать без изменения контракта.
- `scripts/sync-market-data.sh` по умолчанию включает загрузку ликвидаций вместе с OHLCV/funding/OI/L/S, CoinGlass snapshots и CoinGecko basis.
- Добавлены regression tests для нормализации CoinGlass liquidation payload: nested `Binance`/`all` поля, seconds/ms timestamps и пустые строки.
- Production deploy проверен: ручной sync на `deltagrid.pro` записал `144` строки в `liquidations`, публичный `/api/v1/data/health` показывает `row_counts.liquidations=144`, а `/api/v1/data/liquidations` отдаёт BTC long/short `value_usd`.
- Ограничение: поток хранит агрегированный `value_usd`; `quantity` и `price` остаются `0.0`, пока не подключён отдельный per-order liquidation tape.

## [2026-06-05] - [FIX/DATA] - Устойчивость live data SSR
- Backend SQLAlchemy pool стал управляемым через env: `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_TIMEOUT_SECONDS`.
- Frontend server-side API client получил таймаут `BACKEND_FETCH_TIMEOUT_MS`, чтобы live-страница не зависала бесконечно при проблемном backend-запросе.
- Live stream loader снизил параллельность запросов на один символ: `Charts`, `Market Matrix`, `Arbitrage Scanner` и `Strategy Lab` больше не открывают десятки DB-сессий одномоментно.
- Production-риск: таблица `liquidations` пока пустая, поэтому liquidation-блоки остаются в честном pending-состоянии до подключения ingestion.

## [2026-06-05] - [DATA/FRONTEND] - Live data streams для Charts, Matrix и Scanner
- Добавлены read-only backend endpoint'ы для уже сохраняемых PostgreSQL потоков: `GET /api/v1/data/open-interest`, `/data/long-short-ratio`, `/data/basis-premium` и `/data/liquidations`.
- Расширены regression tests `backend/tests/test_data_api.py`: новые data endpoints должны возвращать `200` даже при пустых таблицах.
- `Charts` заменён с placeholder на live stream workspace: price, volume, open interest, basis, funding и long/short читаются через backend data-layer.
- `Market Matrix` больше не использует `terminalDataAdapter`: BTC/ETH/SOL matrix строится из CoinGecko spot, Binance perp close, basis, funding, OI и long/short.
- `Arbitrage Scanner` больше не показывает mock opportunities: таблица строится из persisted `basis_premium` и `funding_rates` как read-only research candidates.
- `Strategy Lab` очищен от fake backtest PnL/trades: экран показывает readiness live inputs и блокирует backtest output до появления реального engine.
- `Assets` теперь читает `/data/liquidations`; пока строк нет, блок остаётся pending, но будущий ingestion автоматически появится в UI.
- Проверка: `venv\Scripts\python.exe -m pytest tests/test_data_api.py -q` — `10 passed`; `python -m compileall backend/app` и `npm run build` проходят успешно.

## [2026-06-05] - [FRONTEND] - Live Market Overview и Assets
- Добавлен backend endpoint `GET /api/v1/market/markets` для топовых spot markets из CoinGecko с `24h` и `7d` изменениями.
- `Market Overview` больше не читает `terminalDataAdapter`: global cap/volume, BTC/ETH dominance, heatmap, top assets, gainers/losers и `Fear & Greed Index` строятся из live backend API.
- `Assets` больше не использует mock SOL fixture: цена, market cap, volume, open interest, funding и OHLCV читаются через backend/data-layer.
- Fake order book, fake liquidations и fake venue breakdown убраны из production UI; вместо них показаны явные pending-состояния до подключения live endpoints.
- Общие terminal chart/table компоненты получили безопасные empty-state'ы для пустых ответов provider'ов.
- Проверка: `python -m compileall backend/app` и `npm run build` проходят успешно.

## [2026-06-05] - [FRONTEND] - Live Funding tabs и Data Health
- Исправлена вложенная навигация в `Funding` и `Perp DEX`: sidebar и верхние segmented tabs теперь используют стабильный `view` query-param, активное состояние больше не привязано к первому пункту.
- `SegmentedControl` получил поддержку ссылок без поломки старого режима с кнопками.
- `Funding` больше не читает mock fixture: KPI, matrix, history, arbitrage baseline, legs и predicted baseline строятся из persisted PostgreSQL rows через `GET /api/v1/data/funding` и `GET /api/v1/data/health`.
- `/data-health` заменён с placeholder на live-экран provider/storage health по `GET /api/v1/data/health`.
- `Perp DEX` больше не показывает mock DEX volumes/OI как реальные данные: экран помечает DEX venue data как pending и показывает реальные row counts/provider health из PostgreSQL.
- Проверка: `npm run build` во frontend проходит успешно.

## [2026-06-05] — [DATA] — Multi-provider ingestion и регулярный sync
- `sync_market_data` расширен до multi-provider flow: Binance USD-M продолжает писать OHLCV/funding/OI/L/S, CoinGlass v4 пишет funding/OI snapshots, CoinGecko даёт spot price для approximate `basis_premium`.
- `DataWriter` получил безопасную вставку `basis_premium` и чтение последнего Binance 1m close без изменения схемы БД.
- `GET /api/v1/data/health` теперь отслеживает provider `coingecko` вместе с `binance` и `coinglass`.
- `scripts/sync-market-data.sh` по умолчанию включает `--include-coinglass` и `--include-coingecko-basis`.
- Добавлен `scripts/install-market-sync-cron.sh`, который создаёт `/etc/cron.d/deltagrid-market-sync` для запуска sync каждые 15 минут.
- CoinGecko API key больше не передаётся в query params, чтобы HTTP logs не содержали секреты.
- Production deploy выполнен: cron service активен, `/api/v1/data/health` показывает `binance`, `coinglass` и `coingecko` healthy; row counts после ручной проверки: `ohlcv=5376`, `funding_rates=15`, `open_interest=1509`, `long_short_ratio=75`, `basis_premium=6`.
- `DEPLOYMENT.md`, `ARCHITECTURE.md`, `BACKLOG.md`, `PROJECT_PLAN.md` и `CURRENT_TASK.md` обновлены под регулярный multi-provider sync.

## [2026-06-05] — [DATA] — Provider API keys и CoinGlass v4
- Provider API keys добавлены в `/opt/deltagrid/.env.production` без вывода секретов; backend container перечитал env после recreate.
- `CoinGecko` ключ активен: `market/trending` и `market/global` отвечают через production-домен.
- `CoinGlassClient` переведён на v4 base URL `https://open-api-v4.coinglass.com`, header `CG-API-KEY` и endpoint `/api/futures/coins-markets`.
- `GET /api/v1/market/enrichments` теперь может проверять CoinGlass v4 health, а `GET /api/v1/market/funding-rates` нормализует live-поля `avg_funding_rate_by_oi`, `open_interest_usd` и `current_price`.

## [2026-06-05] — [DATA] — Ручной production sync market data
- Добавлена backend-команда `python -m app.adapters.data.sync_market_data` для загрузки свежих Binance USD-M данных в PostgreSQL без нового scheduler/cron.
- `BinanceAdapter` теперь реально загружает funding history, open interest history и global long/short account ratio; liquidations остаются отдельной задачей.
- Добавлен wrapper `scripts/sync-market-data.sh` для запуска синка внутри production Compose stack из `/opt/deltagrid`.
- Sync пишет OHLCV, funding, open interest, long/short ratio, `backfill_jobs` и `provider_sync_runs`, поэтому `/api/v1/data/health` может показывать актуальные `row_counts` и последний sync.
- Первый production sync выполнен на сервере `2.25.143.143`: загружено `6837` rows, `/api/v1/data/health` через `https://deltagrid.pro` показывает `binance healthy`, `ohlcv=5256`, `funding_rates=9`, `open_interest=1500`, `long_short_ratio=72`, `data_quality.score=100`.
- `DEPLOYMENT.md`, `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и `CURRENT_TASK.md` обновлены с инструкциями по заполнению market data и текущими ограничениями.

## [2026-06-05] — [DEPLOY] — Реальный запуск `deltagrid.pro` на сервере
- DNS Cloudflare активирован: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`, старая `AAAA`-запись для корня отсутствует.
- SSH-доступ `root@2.25.143.143` по ключу подтверждён; код развёрнут в `/opt/deltagrid` из ветки `preview`.
- На Ubuntu 22.04 установлен Nginx/Certbot, Docker Compose stack поднят с PostgreSQL, backend и frontend.
- `.env.production` создан на сервере с production secrets; файл не коммитится.
- Приложение работает через Nginx: `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- Let's Encrypt сертификат выпущен для `deltagrid.pro` и `www.deltagrid.pro`, срок действия до `2026-09-03`; `certbot renew --dry-run` прошёл успешно.
- Проверки: server smoke-check через HTTPS прошёл; страницы `/`, `/market`, `/data-health`, `/watchlist`, `/settings`, `/funding`, `/perp-dex`, `/assets`, `/charts`, `/strategy-lab` возвращают `200`; API `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health`, `/api/v1/market/trending` возвращают `200`.
- Cloudflare proxy включён обратно, SSL mode `Full (strict)` проверен: edge отдаёт `Server: cloudflare`, frontend/API возвращают `200`, WebSocket `/api/v1/stream/ws` отдаёт `101 Switching Protocols`.
- `scripts/deploy-production.sh` теперь ждёт healthcheck сервисов перед smoke-check, чтобы убрать race condition первого запуска frontend.

## [2026-06-05] — [DEPLOY] — Привязка deployment flow к `deltagrid.pro`
- `.env.production.example` обновлён под `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- `deploy/nginx/deltagrid.conf.example` теперь содержит `server_name deltagrid.pro www.deltagrid.pro`.
- `scripts/generate-production-env.sh` по умолчанию генерирует `.env.production` для `deltagrid.pro`.
- `DEPLOYMENT.md`, `README.md`, `PROJECT_PLAN.md` и `CURRENT_TASK.md` обновлены под реальный домен.
- DNS preflight: `deltagrid.pro` и `www.deltagrid.pro` сейчас резолвятся в `31.31.196.50` и `2a00:f940:2:2:1:1:0:266`; HTTP отдаёт parking page REG.RU, HTTPS требует настройки.
- Целевой сервер пользователя: `2.25.143.143`; SSH `22` открыт, HTTP `80` и HTTPS `443` пока закрыты.
- Добавлены `scripts/bootstrap-ubuntu.sh`, `scripts/deploy-production.sh` и `deploy/dns/deltagrid.pro.md` для Ubuntu/VPS rollout.
- Добавлен `scripts/configure-nginx-ssl.sh` для включения Nginx site и выпуска Let's Encrypt SSL после DNS cutover.
- Production frontend host port переключён на `127.0.0.1:3001`, чтобы не конфликтовать со служебным процессом хостинга на `3000`.

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
