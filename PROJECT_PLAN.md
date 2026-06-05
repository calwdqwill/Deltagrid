# План проекта DeltaGrid

## Текущая фаза

**Production-ready MVP hardening** — подготовка backend/data-layer к локальному и серверному запуску на `deltagrid.pro` с PostgreSQL, Alembic migrations и стабильным `DATABASE_URL`.

## Что уже готово

- Frontend MVP terminal shell `v1.2.0`.
- FastAPI backend с routes для scanner, market, data-layer, auth, alerts, RWA/treasury и execution foundation.
- SQLAlchemy ORM-модели и линейная Alembic-цепочка миграций.
- PostgreSQL runtime через `DATABASE_URL`.
- Docker Compose с локальным PostgreSQL 16.

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

## Следующие шаги

- [x] Прогнать миграции на чистой PostgreSQL БД в локальном Docker.
- [x] Проверить основные backend routes после миграции: `/health`, `/data/health`, `/data/ohlcv`, `/market/trending`.
- [x] На реальном сервере создать `.env.production` с реальными secrets для `deltagrid.pro` и PostgreSQL `DATABASE_URL`.
- [x] Прогнать `DOMAIN=deltagrid.pro sh scripts/server-preflight.sh` на сервере.
- [x] Перенаправить DNS `deltagrid.pro`/`www.deltagrid.pro` на `2.25.143.143` и убрать старую `AAAA`-запись для корня.
- [x] Проверить reverse proxy/SSL на `deltagrid.pro` по `DEPLOYMENT.md`.
- [x] Выпустить Let's Encrypt SSL после DNS cutover.
- [x] Прогнать `scripts/server-smoke.sh` локально на сервере и через `https://deltagrid.pro`.
- [ ] Добавить email к Let's Encrypt account для уведомлений о продлении сертификата.
- [ ] Запланировать reboot сервера после pending kernel upgrade.
- [ ] Подключить frontend MVP adapter к backend/data-layer endpoint'ам после согласования контрактов.
- [ ] Реализовать CoinGlass data adapter для funding/OI/liquidations/L/S.
- [ ] Реализовать backtest engine и scheduler после data quality gate.

## Критерии готовности к деплою

- `python -m alembic upgrade head` проходит на пустой PostgreSQL.
- Backend стартует с `DEBUG=false`, сильным `SECRET_KEY` и заданным `VAULT_MASTER_KEY`.
- `GET /api/v1/health/readiness` возвращает `ready` и показывает актуальный Alembic head.
- Основные API routes возвращают 200 или ожидаемые пустые состояния.
- Нет production-зависимости от SQLite `.db` файла.
- Docker Compose или server deployment выполняет миграции до старта приложения.
