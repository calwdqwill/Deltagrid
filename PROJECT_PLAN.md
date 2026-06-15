# План проекта DeltaGrid

## Текущая фаза

**MVP1 — Data Quality Gate и provider reliability** — следующая стадия после MVP0. Цель: сделать накопление рыночных данных наблюдаемым, свежим и устойчивым перед полноценными интерактивными графиками и backtest engine.

## Release / CI-CD baseline — 2026-06-14

- Production baseline зафиксирован как `v1.3.0`.
- `preview` используется как dev/staging ветка, `main` — как production ветка.
- Добавлен `RELEASES.md` с правилами SemVer и release flow.
- Добавлены GitHub Actions workflows: `CI`, `Deploy Preview`, `Deploy Production`.
- Deploy workflows используют SSH secrets и не выполняют deploy, если secrets ещё не настроены.
- Подготовлено dev/prod разделение на уровне deployment: production `/opt/deltagrid` + `.env.production` + ports `8000/3001`, preview `/opt/deltagrid-preview` + `.env.preview` + ports `8011/3012`.
- Preview/dev stack поднят на VPS локально: отдельный Compose project `deltagrid-preview`, отдельная PostgreSQL БД, smoke-check зелёный, 7d BTC/ETH/SOL data sync выполнен без ошибок.
- Preview auto-deploy через GitHub Actions проверен end-to-end: `PREVIEW_*` secrets, SSH login, deploy в `/opt/deltagrid-preview`, healthy containers и server smoke на ports `8011/3012`.
- После flaky SSH login failure preview deploy workflow усилен явными SSH timeout/retry options; commit `4c3dec0` прошёл CI, `Deploy Preview` run `27532247102` завершился `success`, `/opt/deltagrid-preview` обновился автоматически и остался healthy.
- Preview Nginx HTTP site заранее включён на VPS и проверен через `Host: preview.deltagrid.pro`; публичный HTTPS ждёт DNS-запись `preview -> 2.25.143.143`.
- Production deploy diagnostics подготовлены в `preview`, но ещё не активированы на `main`: `PROD_*` нужно проверить отдельной безопасной production-итерацией.
- Frontend security baseline обновлён до Next.js `15.5.19`; critical/high advisory из `next@14.1.0` закрыты, App Router страницы мигрированы на async `searchParams`.
- Подготовлены runbook'и для следующего ops-шагa: `deploy/github-actions-secrets.md` для GitHub deploy secrets и `deploy/dns/preview.deltagrid.pro.md` для публикации preview-домена через Nginx/SSL.

## Что уже готово

- Frontend MVP terminal shell и MVP1 data-layer baseline `v1.3.0`.
- FastAPI backend с routes для scanner, market, data-layer, auth, alerts, RWA/treasury и execution foundation.
- SQLAlchemy ORM-модели и линейная Alembic-цепочка миграций.
- PostgreSQL runtime через `DATABASE_URL`.
- Docker Compose с локальным PostgreSQL 16.
- MVP0 зафиксирован как production-ready demo: `deltagrid.pro`, PostgreSQL, Cloudflare/Nginx/SSL, live terminal screens, data-layer endpoints и честные readiness-состояния без fake PnL/DEX метрик.

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
- Preview frontend разделён на `CORE_SYMBOLS=BTC/ETH/SOL` для `Market Matrix`/`Arbitrage Scanner`/`Perp DEX` и `CANDIDATE_SYMBOLS=HYPE/XRP/DOGE/ADA/LINK` для `/charts` и `/assets`.
- Следующий milestone: закрыть history/policy gap для snapshot/enrichment streams и только после этого расширять full analytics universe или выкатывать candidates в production.

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
- [ ] Добавить и проверить GitHub repository secrets `PROD_*`, чтобы `Deploy Production` был готов к отдельной безопасной production-итерации.
- [ ] Перенести production deploy hardening в `main` и подтвердить реальный production auto-deploy через `/opt/deltagrid`.
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
- [ ] Закрыть `history_completion_required=5` по `open_interest`, `basis_premium`, `spot_perp_price` или явно зафиксировать policy-разделение `chart_ready` и full analytics universe.
- [x] Провести отдельный regression pass Next.js 16.x: stable `16.2.9` не убирает остаточный `moderate` audit по bundled `postcss <8.5.10`.
- [ ] Дождаться stable Next.js patch с bundled `postcss >=8.5.10`.
- [ ] Реализовать live Perp DEX venue adapter перед показом DEX volume/OI/liquidity как реальных данных.
- [ ] Расширить CoinGlass data adapter до дополнительных provider-specific L/S потоков, если Binance global L/S будет недостаточно для MVP.
- [ ] Реализовать backtest engine и scheduler после data quality gate.

## Критерии готовности к деплою

- `python -m alembic upgrade head` проходит на пустой PostgreSQL.
- Backend стартует с `DEBUG=false`, сильным `SECRET_KEY` и заданным `VAULT_MASTER_KEY`.
- `GET /api/v1/health/readiness` возвращает `ready` и показывает актуальный Alembic head.
- Основные API routes возвращают 200 или ожидаемые пустые состояния.
- Нет production-зависимости от SQLite `.db` файла.
- Docker Compose или server deployment выполняет миграции до старта приложения.
