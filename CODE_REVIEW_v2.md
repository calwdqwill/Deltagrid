# Code Review v2 — DeltaGrid, текущая версия

Дата ревью: 2026-06-02  
Фокус: текущий workspace после прошлого ревью от 2026-05-20, с упором на Phase 7 data layer/backtesting, security, product readiness и регрессии.

## Executive Summary

- Общая оценка: 6.4/10.
- Критичных проблем: 3.
- Серьёзных проблем: 6.
- Мелких проблем / tech debt: 6.
- Статус сборки: backend compile, `pip check`, Alembic current и frontend production build проходят.
- Главный вывод: текущая версия собирается, но Phase 7 пока не является backtesting-ready продуктом. Есть read-only data API и OHLCV-таблицы, но ingest/API contract расходится по символам, backtest engine отсутствует, а часть auth endpoint'ов публично доступна как небезопасные stub'ы.

## Критичные проблемы

| # | Модуль | Проблема | Риск | Как фиксить |
|---|--------|----------|------|-------------|
| 1 | `backend/app/services/auth_service.py:75`, `backend/app/services/auth_service.py:108`, `backend/app/api/v1/auth.py:53`, `backend/app/api/v1/auth.py:74` | Telegram auth принимает `id` без HMAC-проверки, Web3 verify принимает любой непустой `wallet_address/signature/nonce`. Frontend-кнопки disabled, но backend endpoint'ы публичные. | Любой клиент может создать/получить JWT для произвольного Telegram ID или wallet address. Для trading/exchange-credentials продукта это production-blocker. | До реализации настоящей проверки отключить endpoint'ы фича-флагом/404 в production. Для Telegram добавить hash validation по bot token. Для Web3 хранить nonce server-side с TTL и проверять EIP-191 подпись через `eth-account`/аналог. |
| 2 | `backend/app/config.py:35`, `backend/app/config.py:47`, `backend/app/services/secrets/vault_service.py:41` | JWT `SECRET_KEY` по умолчанию `change-me-in-production`, `VAULT_MASTER_KEY` может быть пустым и заменяется deterministic dev key. Startup не падает в production-like режиме. | Если env не задан, JWT можно подделать, а exchange API keys шифруются предсказуемым ключом. | Добавить startup validation: при `DEBUG=false` запрещать default/empty secrets. Обновить `.env.example`, README и docker-compose env contract. |
| 3 | `backend/app/adapters/data/data_models.py:25`, `backend/app/adapters/data/binance_adapter.py:49`, `backend/app/adapters/data/binance_adapter.py:158`, `backend/app/adapters/data/demo.py:79`, `backend/app/api/v1/data.py:269` | Canonical model ожидает `symbol="BTC"`, но Binance adapter/backfill пишет provider-native `BTCUSDT`. Документированный запрос `/api/v1/data/ohlcv?symbol=BTC&exchange=binance` возвращает 0 строк, хотя `BTCUSDT` возвращает данные. | Data Health показывает строки, но продуктовый API/backtest workflow по canonical symbol получает пустые данные. Это ломает Strategy Lab/backtest wiring. | На ingest нормализовать `provider_symbol -> canonical symbol` через `SymbolMapper.from_provider()`, а provider symbol хранить отдельно или в metadata. API должен принимать canonical symbol и, опционально, provider symbol как явный параметр. |

Проверено локально: `GET /api/v1/data/ohlcv?symbol=BTC&exchange=binance` вернул `count=0`, а `symbol=BTCUSDT` вернул `count=61`.

## Серьёзные проблемы

| # | Модуль | Проблема | Риск | Как фиксить |
|---|--------|----------|------|-------------|
| 1 | `BACKTEST_ENGINE_TASK.md`, `CODE_REVIEW_PROMPT.md`, `backend/app` | `CODE_REVIEW_PROMPT.md` описывает `backend/app/backtest/`, `api/v1/backtest.py`, `scheduler.py`, `quality_monitor.py`, `coinglass_adapter.py`, но в текущем коде этих модулей нет. | Документы создают впечатление реализованного backtesting layer, которого фактически нет. Планирование и тестирование уходят не в ту фазу. | Зафиксировать статус: Phase 7 сейчас только data schema + read API. Backtest engine вынести в отдельный milestone с чеклистом и не маркировать как готовый. |
| 2 | `backend/app/adapters/data/binance_adapter.py:73`, `backend/app/adapters/data/binance_adapter.py:78`, `backend/app/adapters/data/binance_adapter.py:83`, `backend/app/adapters/data/binance_adapter.py:88`, `backend/app/adapters/data/__init__.py:10` | Funding/OI/liquidations/long-short в data adapter'ах возвращают пустые списки; отдельного `CoinGlassAdapter` в data layer нет. | Funding/basis/liquidation стратегии невозможно валидно тестировать. Текущая БД подтверждает: `funding_rates`, `open_interest`, `liquidations`, `long_short_ratio` = 0 строк. | Реализовать CoinGlass data adapter для исторических funding/OI/liquidation/L/S и contract tests raw fixture -> model -> DB. |
| 3 | `frontend/src/app/strategy-lab/page.tsx:7`, `frontend/src/app/backtests/page.tsx:7`, `frontend/src/app/data-health/page.tsx:7`, `frontend/src/components/layout/Sidebar.tsx:21` | Sidebar ведёт в Strategy Lab/Backtests/Data Health, но Next.js страницы являются `Coming Soon`. Полноценный flow существует только как standalone `frontend/preview`. | Пользователь видит навигацию текущего MVP, но основные новые разделы не являются рабочими в приложении. | Либо подключить `/data-health` к `/api/v1/data/health` и сделать минимальный Strategy Lab disabled-state внутри Next.js, либо явно пометить preview как отдельный prototype. |
| 4 | `backend/app/adapters/data/rate_limiter.py:67`, `backend/app/adapters/data/rate_limiter.py:71`, `backend/app/adapters/data/rate_limiter.py:98`, `backend/app/adapters/data/binance_adapter.py:67` | Token bucket после ожидания сбрасывает tokens в `capacity - cost`, а retry не ловит `httpx.HTTPStatusError`, который даёт `raise_for_status()`. | Rate limiter может разрешать лишние burst'ы, а 429/5xx от провайдера не проходят через retry policy. Для backfill это повышает шанс банов и неполных данных. | После wait оставлять 0 tokens или пересчитывать refill корректно. В retry включить `httpx.TimeoutException`, `httpx.HTTPStatusError`, network errors и отдельную обработку 429/5xx. |
| 5 | `backend/app/adapters/data/backfill_orchestrator.py:114`, `backend/app/adapters/data/backfill_orchestrator.py:117` | Gap detection считает `expected` после сдвига `current_start` на `last_ts + interval_ms`. | Неполные чанки могут не попадать в gaps, data quality выглядит лучше реальности. | Считать `expected` до изменения `current_start` и проверять coverage по диапазону chunk'а. |
| 6 | `backend/test_api.py`, `backend/regression_test.py`, `BACKLOG.md:246` | Backend regression scripts требуют заранее запущенный сервер. Для data-layer endpoint'ов нет автоматических tests с временной SQLite БД и seed data. | Регрессии вроде `BTC` vs `BTCUSDT` не ловятся CI/локальным тестом. | Добавить pytest/TestClient tests с temp DB: seed OHLCV/funding, проверка canonical symbol, time range, row limit, data health. |

## Мелкие проблемы и tech debt

| # | Модуль | Проблема | Приоритет |
|---|--------|----------|-----------|
| 1 | Корень проекта | В корне отсутствуют `AGENTS.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md`, хотя правила проекта требуют их читать перед новой фазой. | P2 |
| 2 | `CURRENT_TASK.md:1`, `BACKLOG.md:244`, `CHANGELOG.md:19` | `CURRENT_TASK.md` всё ещё говорит Phase 6, а остальные документы уже Phase 7. | P2 |
| 3 | `frontend/src/components/market/FundingRatesCard.tsx:23` | Funding card всегда показывает `Mock`, даже если backend вернёт реальные CoinGlass данные. | P2 |
| 4 | `frontend/src/components/auth/LoginModal.tsx:38`, `frontend/src/stores/authStore.ts:11`, `backend/app/schemas/auth.py` | `feature_flags` из auth response не сохраняются в `authStore`; `useFeatureFlag` нигде не используется. | P2 |
| 5 | `backend/app/adapters/data/data_writer.py:39`, `backend/app/adapters/data/symbol_mapper.py:27` | Data scripts создают таблицы через `CREATE TABLE IF NOT EXISTS` / `Base.metadata.create_all`, что может обходить Alembic. | P2 |
| 6 | `backend/app/adapters/data/data_writer.py:307`, `backend/app/adapters/data/data_writer.py:317` | Имена таблиц подставляются через f-string. Сейчас это internal helper, но лучше allowlist. | P3 |

## Сравнение с ревью v1

Исправлено после прошлого ревью:

- Frontend production build проходит.
- Backend import/compile проходит.
- `pip check` проходит.
- Alembic находится на head `eacf4f46c7ce`.
- Auth refresh camelCase issue и persisted auth rehydration уже не воспроизводились в этой проверке.
- Docker/CORS/public folder fixes из changelog сохранены.

Осталось открытым:

- Нет полноценного frontend lint setup (`eslint`, `eslint-config-next`) как отдельной проверки.
- Нет нормальных backend regression tests без заранее запущенного сервера.
- Документы управления проектом неполные/рассинхронизированы.
- Реальные provider/backfill data flows ещё не покрыты тестами.

Новое в текущей версии:

- Добавлен Phase 7 read-only data API и data schema.
- Добавлен standalone preview frontend.
- Появился критичный canonical/provider symbol mismatch в data API.
- Выявлены публичные auth stub endpoint'ы, которые нельзя оставлять доступными в production.
- Backtest engine, scheduler и quality gate пока отсутствуют, несмотря на формулировки в review/task документах.

## Проверки

Выполнено:

```text
backend: python -m compileall app
Результат: OK

backend: python -m pip check
Результат: No broken requirements found.

backend: python -m alembic current
Результат: eacf4f46c7ce (head)

frontend: npm run build
Результат: Compiled successfully, 19 routes generated

TestClient: GET /api/v1/data/health
Результат: 200; row_counts: ohlcv=121, funding_rates=0, open_interest=0, liquidations=0, long_short_ratio=0

TestClient: GET /api/v1/data/ohlcv?symbol=BTC&exchange=binance
Результат: count=0

TestClient: GET /api/v1/data/ohlcv?symbol=BTCUSDT&exchange=binance
Результат: count=61
```

Не выполнялось:

- Реальные внешние API проверки CoinGlass/Binance/CoinGecko, потому что ревью не должно зависеть от network/API keys.
- `npm run lint` как отдельная проверка, потому что ESLint setup всё ещё не оформлен как полноценная dev-зависимость/config.
- Backtest strategy runs, потому что `backend/app/backtest/` и `backend/scripts/run_backtest.py` отсутствуют.

## Рекомендации

Срочно:

- Закрыть или реально защитить Telegram/Web3 auth endpoint'ы.
- Добавить production startup validation для `SECRET_KEY` и `VAULT_MASTER_KEY`.
- Исправить canonical symbol contract в data ingest/API и добавить regression test на `BTC`.

На эту неделю:

- Реализовать `/data-health` в Next.js на базе `/api/v1/data/health`.
- Добавить temp-DB tests для `/api/v1/data/*`.
- Исправить retry/rate limiter/gap detection перед большими backfill job'ами.
- Явно обновить roadmap: Phase 7 сейчас data-read layer, backtest engine — следующий milestone.

Планировать:

- CoinGlass historical adapter и persistence для funding/OI/liquidations/long-short.
- Backtest engine только после data quality gate и coverage tests.
- Feature gate enforcement не только в frontend store, но и на backend endpoint/service уровне.

Игнорировать до следующей фазы:

- Полную B2B API/multitenancy/white-label часть.
- Сложные UI-улучшения Strategy Lab до появления валидного backtest backend.
- PostgreSQL/TimescaleDB migration, пока не стабилизированы canonical contracts и tests на SQLite.
