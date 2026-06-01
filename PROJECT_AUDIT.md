# PROJECT AUDIT - DeltaGrid

Дата аудита: 2026-06-01  
Область: frontend, backend API, локальная SQLite БД, зависимости.  
Ограничения: код frontend/backend не менялся, реальные API не подключались, модули не удалялись.

## 1. Методика и факты проверки

| Проверка | Результат |
|---|---|
| Структура страниц | Найдены все `page.tsx` в `frontend/src/app/` |
| Frontend build | `npm run build` прошел успешно, сгенерировано 15 routes |
| Backend runtime | Не запускался, чтобы не делать startup warm-up и внешние API-запросы |
| База данных | Прочитана локальная `backend/deltagrid.db` в read-only режиме |
| Документы управления | В репозитории не найдены `AGENTS.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md`; частично заменены `CURRENT_TASK.md` и `DATA_ARCHITECTURE.md` |
| Git status до аудита | В рабочем дереве уже были изменения в коде и документах, не относящиеся к этому аудиту |

## 2. Frontend audit

Всего найдено 15 уникальных страниц App Router.

| Route | Файл | Назначение | Статус | Решение | Комментарий |
|---|---|---|---|---|---|
| `/` | `frontend/src/app/page.tsx` | Основной scanner/dashboard: таблица арбитражных возможностей, KPI, фильтры, избранное, pinned, detail drawer | работает | KEEP | Базовый экран продукта, сборка проходит |
| `/market` | `frontend/src/app/market/page.tsx` | Market dashboard: trending, gainers/losers, global stats, fear & greed, listings, funding rates | работает | EXTEND | Для backtesting добавить scanner table / opportunity scanner block прямо в market workflow |
| `/detail/[id]` | `frontend/src/app/detail/[id]/page.tsx` | Детальная карточка scanner record с venue breakdown и расчетами | работает | KEEP | Полезно для анализа сигналов и проверки формул |
| `/settings` | `frontend/src/app/settings/page.tsx` | Пользовательские настройки scanner, thresholds, fees, language | работает | KEEP | Нужно для настройки торговых допущений |
| `/profile` | `frontend/src/app/profile/page.tsx` | Профиль пользователя, план, account info | работает | KEEP | Вспомогательная auth-страница, не мешает backtesting |
| `/paper-trading` | `frontend/src/app/paper-trading/page.tsx` | Demo trading accounts, trades, portfolio | частично | HIDE | Не удалять, но скрыть из навигации на фазе backtesting; это paper trading, не исторический backtest |
| `/execution` | `frontend/src/app/execution/page.tsx` | Order intents, real orders, live sessions | частично | HIDE | Live execution foundation, требует auth и ключей; не нужен для schema/backtesting phase |
| `/exchange-accounts` | `frontend/src/app/exchange-accounts/page.tsx` | Подключение биржевых аккаунтов и API keys | частично | HIDE | Не трогать и не удалять; реальные ключи/API вне текущей задачи |
| `/risk-rules` | `frontend/src/app/risk-rules/page.tsx` | Live risk rules, kill switch, position limits | частично | HIDE | Относится к execution engine, не к offline backtesting |
| `/alerts` | `frontend/src/app/alerts/page.tsx` | Alert rules/events UI | частично | HIDE | Advanced alerts скрыть до появления стабильного data/backtest pipeline |
| `/notifications` | `frontend/src/app/notifications/page.tsx` | Preferences для email/web push/Telegram alerts | частично | HIDE | Delivery paths в основном stub/fallback, не нужны для backtesting |
| `/rwa` | `frontend/src/app/rwa/page.tsx` | RWA asset scanner | частично | HIDE | Есть seed/data layer, но продуктово вне текущего backtesting scope |
| `/rwa/[id]` | `frontend/src/app/rwa/[id]/page.tsx` | Детальная страница RWA asset | частично | HIDE | Скрыть вместе с RWA-разделом |
| `/treasury` | `frontend/src/app/treasury/page.tsx` | Treasury dashboard, BTC holdings, tokenization platforms | частично | HIDE | Есть seed/data layer, но вне текущего backtesting scope |
| `/treasury/[id]` | `frontend/src/app/treasury/[id]/page.tsx` | Детальная страница treasury entity | частично | HIDE | Скрыть вместе с treasury-разделом |

Не найдены отдельные frontend-страницы: `/billing`, `/options`, `/social`, `/news`.

### Frontend summary

| Решение | Количество | Routes |
|---|---:|---|
| KEEP | 4 | `/`, `/detail/[id]`, `/settings`, `/profile` |
| HIDE | 10 | `/paper-trading`, `/execution`, `/exchange-accounts`, `/risk-rules`, `/alerts`, `/notifications`, `/rwa`, `/rwa/[id]`, `/treasury`, `/treasury/[id]` |
| EXTEND | 1 | `/market` |

## 3. Backend API audit

Всего найдено 16 router-модулей в `backend/app/api/v1/`. Служебный `__init__.py` не считается API-модулем.

| Модуль | Prefix | Назначение | Статус | Решение | Комментарий |
|---|---|---|---|---|---|
| `auth.py` | `/auth` | Register/login/refresh/me, Telegram/Web3 auth hooks | active | REUSE | Базовая auth-инфраструктура нужна; Web3 signature verification отмечен как TODO в сервисе |
| `billing.py` | `/billing` | Plans, subscriptions, referrals, plan capabilities | active | REUSE | Использовать как источник plan/capability metadata; billing UI не нужен |
| `health.py` | `/health` | Health/status/provider health | active | REUSE | Нужно для monitoring и проверки data providers |
| `preferences.py` | `/preferences` | Scanner preferences, favorites, pinned | active | REUSE | Нужно для scanner/backtesting UX |
| `scanner.py` | `/scanner` | Arbitrage scanner list/detail | active | REUSE | Базовый источник opportunity records; расширять лучше вокруг market/backtesting flow |
| `market.py` | `/market` | Trending, gainers/losers, global, fear & greed, funding rates, enrichments | active | MODIFY | Для backtesting нужен более детерминированный market-data слой; funding rates сейчас имеют fallback |
| `performance.py` | `/performance` | Paper-account performance metrics/history | active | MODIFY | Можно переиспользовать идеи метрик, но schema привязана к paper accounts, не к backtest runs |
| `alerts.py` | `/alerts` | Alert rules/events | active | IGNORE | Оставить, но не трогать в schema phase |
| `notifications.py` | `/notifications` | Notification preferences и web-push subscribe stubs | active | IGNORE | Delivery не является частью backtesting ядра |
| `paper.py` | `/paper` | Demo accounts, paper trades, strategy evaluate | active | IGNORE | Не заменяет исторический backtesting; оставить скрытым |
| `exchange_accounts.py` | `/exchange-accounts` | Биржевые аккаунты, encrypted keys, connector capabilities | active | IGNORE | Execution/key management вне текущей задачи |
| `execution.py` | `/execution` | Order intents, orders, sessions | active | IGNORE | Live execution engine оставить нетронутым |
| `risk.py` | `/risk` | Live risk rules и dry-run check | active | IGNORE | Риск-движок для execution, не для offline backtest schema |
| `stream.py` | `/stream` | WebSocket/SSE stream config and transport | active | IGNORE | Live streaming не нужен для начальной backtesting schema |
| `rwa.py` | `/rwa` | RWA assets/categories/compare | active | IGNORE | Скрытый продуктовый слой, не трогать |
| `treasury.py` | `/treasury` | Treasury entities, BTC holdings, tokenization platforms | active | IGNORE | Скрытый продуктовый слой, не трогать |

Отдельно от `api/v1`: `backend/app/adapters/coingecko_adapter.py` и `backend/app/services/market_service.py` являются главными кандидатами на MODIFY для backtesting market data. Сейчас они ориентированы на текущие HTTP-запросы, cache/fallback и не дают полноценного исторического OHLCV/funding dataset.

### Backend summary

| Решение | Количество | Модули |
|---|---:|---|
| REUSE | 5 | `auth`, `billing`, `health`, `preferences`, `scanner` |
| MODIFY | 2 | `market`, `performance` |
| IGNORE | 9 | `alerts`, `notifications`, `paper`, `exchange_accounts`, `execution`, `risk`, `stream`, `rwa`, `treasury` |

## 4. Database audit

Локальная база: `backend/deltagrid.db`.  
Фактически найдено 37 таблиц: 36 прикладных таблиц плюс `alembic_version`. Это больше, чем 33 таблицы, указанные в текущем README/CHANGELOG.

| Таблица | Row count | Назначение | Решение |
|---|---:|---|---|
| `alembic_version` | 1 | Текущая версия миграций Alembic | KEEP |
| `alert_deliveries` | 0 | Delivery attempts для alert events | IGNORE |
| `alert_events` | 0 | История срабатывания alerts | IGNORE |
| `alert_rules` | 0 | Пользовательские alert rules | IGNORE |
| `audit_logs` | 0 | Аудит действий пользователей и execution events | KEEP |
| `connector_capabilities` | 5 | Capabilities биржевых коннекторов | KEEP |
| `exchange_accounts` | 0 | Подключенные exchange accounts | IGNORE |
| `exchange_keys` | 0 | Зашифрованные API keys | IGNORE |
| `execution_runs` | 0 | Запуски execution strategies | IGNORE |
| `favorites` | 0 | Избранные scanner instruments | KEEP |
| `feature_flags` | 0 | User-level feature overrides | KEEP |
| `live_trade_sessions` | 0 | Live trading sessions | IGNORE |
| `market_enrichments` | 0 | Provider enrichments по символам и метрикам | ALTER |
| `notification_preferences` | 0 | User notification preferences | IGNORE |
| `order_events` | 0 | Events жизненного цикла real orders | IGNORE |
| `paper_accounts` | 0 | Demo paper trading accounts | IGNORE |
| `paper_trades` | 0 | Paper trades | IGNORE |
| `payments` | 0 | Payment/subscription hooks | IGNORE |
| `performance_snapshots` | 0 | Performance snapshots для paper accounts | ALTER |
| `pinned` | 0 | Закрепленные scanner instruments | KEEP |
| `plan_capabilities` | 41 | Plan-to-feature mapping | KEEP |
| `position_snapshots` | 0 | Live position snapshots | IGNORE |
| `preferences` | 8 | Scanner/settings key-value preferences | KEEP |
| `provider_health` | 0 | Health state внешних providers | KEEP |
| `provider_sync_logs` | 0 | Logs provider sync attempts | KEEP |
| `real_orders` | 0 | Live/pending real orders | IGNORE |
| `realtime_feed_sessions` | 0 | Realtime feed sessions | IGNORE |
| `referrals` | 0 | Referral codes/stats | IGNORE |
| `risk_rules` | 0 | Live execution risk rules | IGNORE |
| `rwa_asset_snapshots` | 0 | Historical RWA asset snapshots | IGNORE |
| `rwa_assets` | 5 | Seeded RWA assets | IGNORE |
| `strategy_runs` | 0 | Strategy runs, сейчас привязаны к paper accounts | ALTER |
| `stream_events` | 0 | Persisted realtime stream events | IGNORE |
| `tokenization_platforms` | 3 | Seeded tokenization platforms | IGNORE |
| `treasury_entities` | 4 | Seeded treasury entities | IGNORE |
| `treasury_snapshots` | 0 | Historical treasury snapshots | IGNORE |
| `users` | 0 | Users/auth identities/plans | KEEP |

### Database summary

| Решение | Количество |
|---|---:|
| KEEP | 11 |
| ALTER | 3 |
| DROP | 0 |
| IGNORE | 23 |

### Таблицы, важные для будущей backtesting schema

| Таблица | Текущее состояние | Что нужно для backtesting |
|---|---|---|
| `market_enrichments` | Generic metric storage, пустая | Либо расширить, либо не трогать и добавить отдельные `market_candles`/`funding_rates`/`open_interest_snapshots` |
| `strategy_runs` | Есть, но tied to `paper_accounts` | Нужны независимые `backtest_runs` с strategy config, universe, time range, fees/slippage assumptions |
| `performance_snapshots` | Есть paper-account metrics | Нужны backtest metrics: CAGR/Sharpe/Sortino/max drawdown/win rate/exposure/turnover |
| `scanner` data | Не хранится как таблица | Нужны persisted signal/opportunity snapshots для воспроизводимости |

## 5. Dependencies audit

### Frontend `frontend/package.json`

| Dependency | Version | Роль |
|---|---|---|
| `next` | `14.1.0` | App Router, frontend framework |
| `react` | `^18.2.0` | UI |
| `react-dom` | `^18.2.0` | React DOM renderer |
| `@tanstack/react-query` | `^5.18.1` | Server-state cache, API queries |
| `zustand` | `^4.5.0` | Client state stores |
| `axios` | `^1.6.7` | HTTP client |
| `lucide-react` | `^0.323.0` | Icons |
| `clsx` | `^2.1.0` | CSS class composition |
| `tailwind-merge` | `^2.2.1` | Tailwind class merge |
| `tailwindcss` | `^3.4.1` | Styling |
| `typescript` | `^5.3.3` | Types |

### Backend `backend/requirements.txt`

| Dependency | Version | Роль |
|---|---|---|
| `fastapi` | `0.109.2` | API framework |
| `uvicorn[standard]` | `0.27.1` | ASGI server |
| `pydantic` | `2.6.1` | DTO/schema validation |
| `pydantic-settings` | `2.1.0` | Settings/env config |
| `sqlalchemy` | `2.0.25` | ORM |
| `alembic` | `1.13.1` | DB migrations |
| `httpx` | `0.26.0` | Async HTTP client |
| `aiosqlite` | `0.19.0` | Async SQLite driver |
| `asyncpg` | `0.29.0` | PostgreSQL async driver |
| `redis` | `5.0.1` | Redis-ready cache |
| `pyjwt` | `2.8.0` | JWT support |
| `passlib[bcrypt]` | `1.7.4` | Password hashing |
| `python-jose[cryptography]` | `3.3.0` | JWT/crypto utilities |
| `python-multipart` | `0.0.9` | Form/multipart support |

### Наличие инфраструктурных зависимостей

| Вопрос | Ответ |
|---|---|
| ORM | Да, SQLAlchemy |
| Migration tool | Да, Alembic |
| Scheduler | Нет, APScheduler/Celery/RQ не найдены |
| HTTP client | Да, `httpx`; `requests` не найден |
| Cache backend | In-memory cache есть; Redis dependency есть |
| Async DB path | Есть `async_database.py`, `aiosqlite`, `asyncpg`, но основная DI сейчас использует sync `SessionLocal` |
| Analytics stack | `pandas`, `numpy`, `duckdb`, `pyarrow` не найдены |
| Backend test runner | `pytest` не найден в `requirements.txt` |

## 6. Критичные зависимости для backtesting

Уже есть и можно использовать:

| Зависимость/слой | Почему важен |
|---|---|
| SQLAlchemy + Alembic | Нужны для backtest schema и миграций |
| FastAPI + Pydantic | Подходят для backtest API и строгих DTO |
| httpx | Нужен для provider adapters, если позже подключать исторические API |
| TanStack Query | Подходит для таблиц backtests/scanner/results |
| Zustand | Подходит для локальных фильтров, selected strategy/run |
| Existing scanner components | Можно переиспользовать table/filter UX |

Отсутствует и потребуется отдельно оценить перед реализацией:

| Зависимость/слой | Зачем может понадобиться |
|---|---|
| Scheduler | Регулярная загрузка market snapshots/candles |
| Historical data model | OHLCV, funding, open interest, signal snapshots |
| Analytics stack | Быстрые расчеты backtest metrics и агрегации |
| Deterministic data cache | Повторяемые backtests без внешних API во время расчета |

## 7. Архитектурные проблемы

| Проблема | Влияние | Риск для backtesting |
|---|---|---|
| Навигация перегружена экспериментальными модулями | Пользователь видит RWA, Treasury, Execution, Risk, Alerts до стабилизации ядра | Размывает продуктовый фокус |
| Нет dedicated backtesting schema | Исторические прогоны, сделки и метрики нельзя хранить воспроизводимо | Блокер для Phase 2 schema |
| Нет исторической market data schema | Scanner и market работают вокруг live/fallback data | Блокер для корректных backtests |
| `market_service` ориентирован на live HTTP/cache | Расчеты зависят от текущего ответа provider | Backtest может стать невоспроизводимым |
| Startup warm-up scanner может обращаться к external API | Запуск backend может неявно дергать provider | Нужно контролировать в dev/test/backtest режимах |
| Sync/async persistence смешаны | Есть async engine, но DI в API в основном sync | Не блокер сейчас, но важно перед PostgreSQL/scale |
| Реальные execution-модули присутствуют в продукте | Есть UI/API для ключей, ордеров, live sessions | Нужно скрыть и не трогать во время schema phase |
| Часть интеграций stub/fallback | Web3 signature TODO, Aster stub, notifications delivery stubs, funding fallback | Нельзя считать production-ready без маркировки |
| Документы управления неполные | Нет корневых `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `AGENTS.md` | Сложнее вести фазы и решения |
| Документация по числу таблиц устарела | README/CHANGELOG говорят про 33, локально 36 app tables | Риск ошибок при планировании миграций |

## 8. Что готово к Phase 2 (schema), а что чинить

Готово:

| Готовый слой | Как использовать |
|---|---|
| Auth/users | Привязка backtest runs к пользователю |
| Feature flags / plan capabilities | Гейтить лимиты backtests по планам |
| Scanner UI/components | Основа scanner table для `/market` |
| Preferences/favorites/pinned | Пользовательские настройки universe/thresholds |
| SQLAlchemy/Alembic | Безопасное добавление новых таблиц |
| Performance service ideas | Формулы и DTO можно использовать как reference, но не как готовую schema |

Нужно чинить/добавить перед полноценным backtesting:

| Задача | Почему |
|---|---|
| Скрыть из навигации HIDE-страницы | Сфокусировать продукт на market/scanner/backtesting |
| Добавить scanner table в `/market` | По задаче `/market` должен стать рабочим backtesting/scanner entrypoint |
| Спроектировать `backtest_runs`, `backtest_trades`, `backtest_equity_curve`, `backtest_metrics` | Нужна воспроизводимая история прогонов |
| Спроектировать `market_candles`/`funding_rates`/`open_interest_snapshots` | Нужна историческая база для расчетов |
| Разделить live data и historical/test data | Не смешивать mock/fallback с production/backtest flow |
| Добавить scheduler или явный ingestion command | Без этого исторические данные не будут пополняться регулярно |
| Обновить project docs | Вернуть `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `AGENTS.md` либо явно документировать замену |
| Уточнить backend tests | Сейчас нет `pytest` в requirements, runtime API не проверялся в этом аудите |

## 9. Финальный summary

| Метрика | Значение |
|---|---:|
| Frontend pages total | 15 |
| Frontend KEEP | 4 |
| Frontend HIDE | 10 |
| Frontend EXTEND | 1 |
| Backend API modules total | 16 |
| Backend REUSE | 5 |
| Backend MODIFY | 2 |
| Backend IGNORE | 9 |
| DB tables total | 37 |
| DB app tables | 36 |
| DB KEEP | 11 |
| DB ALTER | 3 |
| DB DROP | 0 |
| DB IGNORE | 23 |

Главный вывод: DeltaGrid уже имеет сильную основу для scanner/market/auth/schema-management, но для backtesting пока нет dedicated historical data model и backtest result model. Следующая безопасная итерация - не переписывать проект, а скрыть лишние разделы из навигации, расширить `/market` scanner table и спроектировать минимальную backtesting schema через Alembic.
