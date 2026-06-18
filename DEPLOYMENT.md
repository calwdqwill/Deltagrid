# Деплой DeltaGrid MVP

Этот документ описывает минимальный production-oriented запуск MVP на сервере с Docker Compose, PostgreSQL, reverse proxy и доменом. Цель — безопасный первый деплой без смены архитектуры и без добавления лишней инфраструктуры.

## Допущения

- Целевой сервер: `2.25.143.143`.
- ОС сервера: Ubuntu.
- Домен `deltagrid.pro` должен указывать на `2.25.143.143`.
- Reverse proxy запускается на хосте отдельно, например Nginx.
- PostgreSQL работает внутри `docker-compose.prod.yml` и не публикуется наружу.
- Секреты хранятся в `.env.production`, который не коммитится.

## Текущее состояние домена

На момент подготовки деплоя `deltagrid.pro` и `www.deltagrid.pro` резолвятся в:

- IPv4: `31.31.196.50`
- IPv6: `2a00:f940:2:2:1:1:0:266`

HTTP сейчас отдаёт parking page REG.RU, а не DeltaGrid. Перед финальным запуском нужно перенаправить A-запись `deltagrid.pro` на `2.25.143.143`. Если на сервере нет IPv6, удалите текущие AAAA-записи, иначе часть трафика может уходить на старый REG.RU hosting.

Подробный DNS-чеклист: `deploy/dns/deltagrid.pro.md`.

## Bootstrap Ubuntu

Если Docker/Nginx/Certbot ещё не установлены, после входа на сервер выполните:

```bash
sudo sh scripts/bootstrap-ubuntu.sh
```

Скрипт устанавливает `git`, `curl`, Docker, Docker Compose plugin, Nginx, Certbot и открывает OpenSSH/Nginx Full через `ufw`, если `ufw` доступен.

Проверка сервера:

```bash
DOMAIN=deltagrid.pro sh scripts/server-preflight.sh
```

Сейчас снаружи видно, что SSH на `2.25.143.143:22` открыт, а `80/443` закрыты. После bootstrap и настройки Nginx порты `80/443` должны открыться.

## Получение кода на сервере

Для production используйте ветку `main`. Ветка `preview` остаётся dev/staging веткой и не должна автоматически считаться production release без merge/tag.

```bash
git clone -b main https://github.com/calwdqwill/Deltagrid.git
cd Deltagrid
```

Для staging/dev стенда используйте отдельную директорию, отдельный домен или порт и ветку `preview`.

## GitHub CI/CD

Baseline `v1.3.0` фиксирует модель релизов:

- `preview` — dev/staging ветка для рабочих итераций после локальной проверки;
- `main` — production ветка для `https://deltagrid.pro`;
- `VERSION`, `frontend/package.json` и `CHANGELOG.md` фиксируют текущую версию и историю изменений;
- правила релизов описаны в `RELEASES.md`.

GitHub Actions:

- `CI` запускает backend tests, `compileall app` и frontend build на `preview`, `main` и pull requests;
- `Deploy Preview` деплоит `preview`, если настроены `PREVIEW_SSH_HOST`, `PREVIEW_SSH_USER`, `PREVIEW_SSH_KEY`, `PREVIEW_APP_DIR`;
- `Deploy Production` деплоит `main`, если настроены `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR`.

Если SSH secrets ещё не заведены, deploy workflow завершится успешным skip и не будет ломать CI.
Подробный чеклист создания dedicated SSH key и заполнения repository secrets: `deploy/github-actions-secrets.md`.

Deploy diagnostics:

- `scripts/deploy-compose-stack.sh` печатает этапы `git fetch`, `compose config`, `postgres backup`, `compose build`, `wait for backend/frontend` и `server smoke`;
- при падении deploy script выводит короткий git/compose/disk/logs snapshot без печати env-файла и secrets;
- `Deploy Preview` и `Deploy Production` после failed deploy attempt пытаются собрать remote diagnostic snapshot через SSH; если сам SSH transport недоступен, workflow явно пишет, что причина ближе к reachability, а не к app deploy logic.

Опциональные secrets позволяют явно переопределить env-файл, Compose project и smoke URLs:

- preview: `PREVIEW_ENV_FILE`, `PREVIEW_COMPOSE_PROJECT_NAME`, `PREVIEW_SMOKE_BASE_URL`, `PREVIEW_SMOKE_FRONTEND_URL`;
- production: `PROD_ENV_FILE`, `PROD_COMPOSE_PROJECT_NAME`, `PROD_SMOKE_BASE_URL`, `PROD_SMOKE_FRONTEND_URL`.

Рекомендуемые значения по умолчанию:

| Стенд | Директория | Ветка | Env | Compose project | Backend | Frontend |
|-------|------------|-------|-----|-----------------|---------|----------|
| production | `/opt/deltagrid` | `main` | `.env.production` | `deltagrid` | `127.0.0.1:8000` | `127.0.0.1:3001` |
| preview | `/opt/deltagrid-preview` | `preview` | `.env.preview` | `deltagrid-preview` | `127.0.0.1:8011` | `127.0.0.1:3012` |

Для ручного deploy любого стенда используйте общий скрипт:

```bash
BRANCH=main ENV_FILE=.env.production COMPOSE_PROJECT_NAME=deltagrid sh scripts/deploy-compose-stack.sh
BRANCH=preview ENV_FILE=.env.preview COMPOSE_PROJECT_NAME=deltagrid-preview sh scripts/deploy-compose-stack.sh
```

Для `BRANCH=main` скрипт перед deploy по умолчанию создаёт PostgreSQL backup через `scripts/backup-postgres.sh` в `backups/deploy/`. Для preview backup по умолчанию выключен, чтобы не плодить дампы на каждом dev/staging push. Поведение можно переопределить:

```bash
BACKUP_BEFORE_DEPLOY=0 BRANCH=main ENV_FILE=.env.production COMPOSE_PROJECT_NAME=deltagrid sh scripts/deploy-compose-stack.sh
BACKUP_BEFORE_DEPLOY=1 BRANCH=preview ENV_FILE=.env.preview COMPOSE_PROJECT_NAME=deltagrid-preview sh scripts/deploy-compose-stack.sh
```

Скрипт сначала делает backup, затем собирает `backend` и `frontend`, и только после успешного build явно пересоздаёт app containers через `compose rm -sf backend frontend` и `compose up -d --no-build backend frontend`. PostgreSQL container и volume при этом не удаляются.

Фактический preview rollout от 2026-06-14:

- `/opt/deltagrid-preview` развёрнут из ветки `preview`;
- `.env.preview` создан отдельно от production env; реальные secrets не коммитятся;
- Compose project `deltagrid-preview` поднял отдельные containers и PostgreSQL volume;
- backend доступен только локально на `127.0.0.1:8011`, frontend — на `127.0.0.1:3012`;
- 7d BTC/ETH/SOL sync в preview БД завершён без ошибок, local smoke-check проходит;
- DNS/Nginx для `preview.deltagrid.pro` ещё не настроены, но подготовлены `deploy/nginx/deltagrid-preview.conf.example`, `scripts/configure-preview-nginx-ssl.sh` и `deploy/dns/preview.deltagrid.pro.md`.

## Подготовка env

Автоматический вариант для сервера:

```bash
sh scripts/generate-production-env.sh
```

Скрипт создаёт `.env.production` для `deltagrid.pro`, генерирует `SECRET_KEY`, `VAULT_MASTER_KEY`, `POSTGRES_PASSWORD`, выставляет `chmod 600` и подставляет домен в `PUBLIC_APP_URL`/`CORS_ORIGINS`.

Ручной вариант:

```bash
cp .env.production.example .env.production
```

После копирования замените все placeholder-значения.

Для preview-стенда используйте отдельный env-файл:

```bash
cp .env.preview.example .env.preview
```

Минимальные отличия preview от production: `PUBLIC_APP_URL=https://preview.deltagrid.pro`, `CORS_ORIGINS=https://preview.deltagrid.pro`, `BACKEND_HOST_PORT=8011`, `FRONTEND_HOST_PORT=3012`, отдельные `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` и `DATABASE_URL`.

Обязательные переменные:

- `DEBUG=false`
- `PUBLIC_APP_URL=https://deltagrid.pro`
- `CORS_ORIGINS=https://deltagrid.pro,https://www.deltagrid.pro`
- `SECRET_KEY` — сильная строка минимум 32 символа
- `VAULT_MASTER_KEY` — ключ для шифрования exchange API credentials
- `POSTGRES_PASSWORD` — сильный пароль PostgreSQL
- `DATABASE_URL=postgresql://...@postgres:5432/...`
- `NEXT_PUBLIC_WS_URL` — опционально; оставьте пустым, если reverse proxy проксирует `/api/v1/stream/ws` на том же домене

Генерация секретов:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Проверка compose-конфига

Сначала можно прогнать общий preflight:

```bash
DOMAIN=deltagrid.pro sh scripts/server-preflight.sh
```

Перед запуском проверьте, что Compose видит все переменные:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

Для проверки структуры без реальных секретов можно использовать example-файл:

```bash
ENV_FILE=.env.production.example docker compose --env-file .env.production.example -f docker-compose.prod.yml config
```

## Запуск

Автоматический локальный deploy stack:

```bash
sh scripts/deploy-production.sh
```

Ручной вариант:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Backend при старте выполняет:

```bash
alembic upgrade head
```

Frontend build получает `BACKEND_INTERNAL_URL=http://backend:8000` через build args, чтобы Next.js rewrite `/api/*` проксировал запросы на backend внутри Docker network.

После запуска проверьте:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/health/readiness
curl http://127.0.0.1:8000/api/v1/data/health
curl http://127.0.0.1:3001
```

`/api/v1/health/readiness` должен вернуть `status: ready`, а `current_revision` должен совпадать с `expected_heads`.

## Заполнение market data

После первого production deploy PostgreSQL создаётся пустым: миграции поднимают схему, но не загружают рыночные данные. Чтобы вручную загрузить свежие market data в MVP data-layer:

```bash
cd /opt/deltagrid
sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 24 --ohlcv-intervals 1m,5m,1h
```

Скрипт запускает backend-команду внутри production Compose stack и пишет в PostgreSQL:

- `ohlcv`;
- `funding_rates`;
- `open_interest`;
- `long_short_ratio`;
- `basis_premium`;
- `provider_sync_runs`;
- `backfill_jobs`.

Источники текущего MVP sync:

- OKX USDT Swap: OHLCV, funding history, open interest snapshots, long/short account ratio.
- CoinGlass v4: funding/OI snapshots и aggregated liquidation history с `exchange_list=OKX`.
- CoinGecko: spot price для расчёта approximate `basis_premium` против последнего OKX perp close.
- Binance USD-M сохранён как legacy/diagnostic provider; на текущем production VPS direct Binance Futures API возвращает HTTP `451`, поэтому он не является primary data path.

Проверка после синка:

```bash
curl http://127.0.0.1:8000/api/v1/data/health
curl "http://127.0.0.1:8000/api/v1/data/ohlcv?symbol=BTC&exchange=okx&interval=1m"
curl https://deltagrid.pro/api/v1/data/health
```

Ожидаемо: `row_counts.ohlcv`, `row_counts.open_interest`, `row_counts.funding_rates`, `row_counts.liquidations` и `row_counts.basis_premium` больше `0`, у `providers.okx`, `providers.coinglass` и `providers.coingecko` появляется последний `last_sync`, а `/api/v1/data/health` показывает freshness/coverage/universe для `BTC/ETH/SOL` на `okx`. `providers.binance` может оставаться `degraded` как legacy/diagnostic provider.

Ручной вариант без wrapper-скрипта:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T backend \
  python -m app.adapters.data.sync_market_data \
  --symbols BTC,ETH,SOL \
  --lookback-hours 24 \
  --ohlcv-intervals 1m,5m,1h \
  --include-funding \
  --include-open-interest \
  --include-long-short \
  --include-coinglass \
  --include-coingecko-basis
```

## Регулярный market data sync

Для production MVP используется host-level cron без отдельного scheduler-сервиса:

```bash
cd /opt/deltagrid
sudo sh scripts/install-market-sync-cron.sh
```

По умолчанию cron создаёт `/etc/cron.d/deltagrid-market-sync` и запускает:

```bash
sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 2 --ohlcv-intervals 1m,5m,1h
```

Расписание по умолчанию: каждые 15 минут. Лог:

```bash
tail -100 /var/log/deltagrid-market-sync.log
```

Изменить расписание можно через env при установке:

```bash
sudo SCHEDULE="*/30 * * * *" LOOKBACK_HOURS=4 sh scripts/install-market-sync-cron.sh
```

Для отдельного preview/dev стека cron нужно ставить отдельными файлами и явно передавать preview env/project, чтобы не затронуть production контейнеры и volume. Core symbols и candidate symbols лучше разносить по минутам, чтобы не собирать все OKX derived-запросы в один burst:

```bash
cd /opt/deltagrid-preview
sudo SCHEDULE="*/15 * * * *" \
  PROJECT_DIR=/opt/deltagrid-preview \
  ENV_FILE=.env.preview \
  COMPOSE_PROJECT_NAME=deltagrid-preview \
  CRON_FILE=/etc/cron.d/deltagrid-preview-market-sync-core \
  LOG_FILE=/var/log/deltagrid-preview-market-sync-core.log \
  SYMBOLS=BTC,ETH,SOL \
  LOOKBACK_HOURS=2 \
  OHLCV_INTERVALS=1m,5m,1h \
  sh scripts/install-market-sync-cron.sh

sudo SCHEDULE="5,20,35,50 * * * *" \
  PROJECT_DIR=/opt/deltagrid-preview \
  ENV_FILE=.env.preview \
  COMPOSE_PROJECT_NAME=deltagrid-preview \
  CRON_FILE=/etc/cron.d/deltagrid-preview-market-sync-candidates \
  LOG_FILE=/var/log/deltagrid-preview-market-sync-candidates.log \
  SYMBOLS=HYPE,XRP,DOGE,ADA,LINK \
  LOOKBACK_HOURS=2 \
  OHLCV_INTERVALS=1m,5m,1h \
  sh scripts/install-market-sync-cron.sh
```

Проверка preview cron:

```bash
tail -100 /var/log/deltagrid-preview-market-sync-core.log
tail -100 /var/log/deltagrid-preview-market-sync-candidates.log
curl http://127.0.0.1:8011/api/v1/data/provider-inventory?symbols=HYPE,XRP,DOGE,ADA,LINK\&exchange=okx
```

Важно:

- на сервере рабочая директория проекта — `/opt/deltagrid`, не `/root`;
- используется Docker Compose v2: команда `docker compose`, а не `docker-compose`;
- production env лежит в `/opt/deltagrid/.env.production`, а не в `backend/.env`;
- production БД — PostgreSQL, поэтому проверять нужно таблицы `ohlcv`, `funding_rates`, `open_interest`, а не SQLite-файл `deltagrid.db`.

## Reverse proxy

Минимальная схема:

- `https://deltagrid.pro/` → `127.0.0.1:3001`
- `https://deltagrid.pro/api/` → `127.0.0.1:8000/api/`
- `wss://deltagrid.pro/api/v1/stream/ws` → `127.0.0.1:8000/api/v1/stream/ws`

Автоматическая настройка Nginx и SSL после того, как DNS указывает на `2.25.143.143`:

```bash
sudo LETSENCRYPT_EMAIL=you@example.com sh scripts/configure-nginx-ssl.sh
```

Email рекомендован для уведомлений о продлении сертификата. Если `LETSENCRYPT_EMAIL` не задан, скрипт выпустит сертификат без email-уведомлений через `--register-unsafely-without-email`.

Скрипт копирует `deploy/nginx/deltagrid.conf.example`, включает site, проверяет `nginx -t`, перезагружает Nginx и выпускает сертификат Let's Encrypt для `deltagrid.pro` и `www.deltagrid.pro`.

Готовый шаблон лежит в `deploy/nginx/deltagrid.conf.example` и уже настроен на `deltagrid.pro`:

```bash
sudo cp deploy/nginx/deltagrid.conf.example /etc/nginx/sites-available/deltagrid
sudo ln -s /etc/nginx/sites-available/deltagrid /etc/nginx/sites-enabled/deltagrid
sudo nginx -t
sudo systemctl reload nginx
```

Пример Nginx-конфига:

```nginx
server {
    listen 80;
    server_name deltagrid.pro www.deltagrid.pro;

    location /api/v1/stream/ws {
        proxy_pass http://127.0.0.1:8000/api/v1/stream/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Reverse proxy для preview

Preview использует отдельные upstream-порты и отдельный Nginx site:

- `https://preview.deltagrid.pro/` → `127.0.0.1:3012`
- `https://preview.deltagrid.pro/api/` → `127.0.0.1:8011/api/`
- `wss://preview.deltagrid.pro/api/v1/stream/ws` → `127.0.0.1:8011/api/v1/stream/ws`

Перед выпуском SSL добавьте DNS-запись из `deploy/dns/preview.deltagrid.pro.md`. Когда `preview.deltagrid.pro` начал резолвиться, выполните на VPS:

```bash
cd /opt/deltagrid-preview
sudo LETSENCRYPT_EMAIL=you@example.com sh scripts/configure-preview-nginx-ssl.sh
```

Скрипт делает DNS-precheck, включает site `deltagrid-preview`, выпускает сертификат только для `preview.deltagrid.pro` и не трогает production site `deltagrid`.

Если используете ручную настройку Nginx, после неё выпустите SSL-сертификат через Certbot. `PUBLIC_APP_URL`/`CORS_ORIGINS` уже должны указывать на `https://deltagrid.pro`.

## Smoke-check

После запуска контейнеров и после настройки reverse proxy прогоните smoke-check:

```bash
sh scripts/server-smoke.sh
```

Локально на Windows можно использовать PowerShell-версию:

```powershell
.\scripts\server-smoke.ps1
```

Для проверки через домен:

```bash
BASE_URL=https://deltagrid.pro FRONTEND_URL=https://deltagrid.pro sh scripts/server-smoke.sh
```

Для release smoke перед preview/main rollout используйте:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/release-smoke.sh
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/release-smoke.sh
```

`release-smoke` объединяет backend health, readiness, `/data/health`, frontend, Perp DEX route policy, direct venue smoke и CoinGlass Perp DEX coverage. Если CoinGlass временно недоступен и проверка нужна только для non-CoinGlass release gate, задайте `RUN_COINGLASS=0` и отдельно зафиксируйте риск в release notes.

Для ручной проверки preview chart/asset candidates на VPS:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 MIN_CANDIDATE_OHLCV_ROWS=1000 sh scripts/preview-candidate-smoke.sh
```

Для проверки CoinGlass Perp DEX coverage на стенде с настроенным CoinGlass API key:

```bash
cd /opt/deltagrid-preview
BASE_URL=http://127.0.0.1:8011 sh scripts/coinglass-perp-dex-coverage-smoke.sh
```

```bash
cd /opt/deltagrid
BASE_URL=http://127.0.0.1:8000 sh scripts/coinglass-perp-dex-coverage-smoke.sh
```

Скрипт выводит только compact summary по coverage, candidate hints и field groups; raw provider payload и секреты не печатаются.

Фактический production rollout от 2026-06-05, обновлённый baseline от 2026-06-14:

- DNS Cloudflare активен: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`.
- `/opt/deltagrid` развёрнут как production checkout; после baseline `v1.3.0` production release должен идти из ветки `main`, dev/staging — из `preview`.
- Docker Compose stack запущен: PostgreSQL, backend и frontend healthy.
- Frontend опубликован локально как `127.0.0.1:3001`, backend как `127.0.0.1:8000`.
- Nginx reverse proxy обслуживает `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- Let's Encrypt сертификат выпущен для `deltagrid.pro` и `www.deltagrid.pro`; автообновление `certbot renew --dry-run` прошло успешно.
- `BASE_URL=https://deltagrid.pro FRONTEND_URL=https://deltagrid.pro sh scripts/server-smoke.sh` прошёл успешно.
- Cloudflare proxy включён, SSL mode установлен в `Full (strict)`, API и WebSocket `/api/v1/stream/ws` проверены через Cloudflare edge.
- Primary CEX perp provider переключён на OKX USDT Swap из-за Binance HTTP `451` на VPS; CoinGlass запросы идут с `exchange_list=OKX`.
- 72h/7d backfill BTC/ETH/SOL по `1m/5m/1h` выполнен без gaps; `/api/v1/data/coverage` и `/api/v1/data/universe` доступны для production readiness.
- Multi-provider sync включает OKX, CoinGlass v4 и CoinGecko-derived basis snapshots; `/etc/cron.d/deltagrid-market-sync` установлен и cron service активен.

Для Windows/PowerShell:

```powershell
$env:BASE_URL="https://deltagrid.pro"
$env:FRONTEND_URL="https://deltagrid.pro"
.\scripts\server-smoke.ps1
```

## Backup PostgreSQL

Перед каждым деплоем и перед рискованными миграциями сделайте backup:

```bash
sh scripts/backup-postgres.sh
```

По умолчанию скрипт читает `.env.production`, использует `docker-compose.prod.yml`, сервис `postgres`, значения `POSTGRES_USER`/`POSTGRES_DB` из env-файла и сохраняет сжатый dump в `backups/deltagrid_YYYYMMDDTHHMMSSZ.sql.gz`.

Для preview/dev стенда используйте явные параметры:

```bash
ENV_FILE=.env.preview COMPOSE_PROJECT_NAME=deltagrid-preview BACKUP_PREFIX=deltagrid-preview sh scripts/backup-postgres.sh
```

Восстановление из backup:

```bash
gzip -dc backups/deltagrid_YYYYMMDDTHHMMSSZ.sql.gz | docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres psql -U deltagrid deltagrid
```

Если `COMPRESS=0`, скрипт создаст обычный `.sql`, тогда восстановление можно выполнить через `cat backups/file.sql | ... psql ...`. Если в `.env.production` используются другие `POSTGRES_USER` или `POSTGRES_DB`, скрипт прочитает их автоматически.

## Rollback

Безопасный минимальный rollback:

1. Остановить входящий трафик на reverse proxy или включить maintenance page.
2. Сделать backup текущей БД.
3. Вернуть предыдущую версию кода.
4. Пересобрать backend/frontend:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build backend frontend
```

5. Проверить `/api/v1/health/readiness`.

`alembic downgrade` не выполнять автоматически. Для MVP безопаснее откатывать схему только по отдельному плану: с backup, проверкой совместимости данных и ручным решением по каждой миграции.

## Минимальный чеклист перед открытием трафика

- [ ] `.env.production` создан и не содержит dev/default secrets.
- [ ] `DOMAIN=deltagrid.pro sh scripts/server-preflight.sh` проходит.
- [ ] `docker compose --env-file .env.production -f docker-compose.prod.yml config` проходит.
- [ ] PostgreSQL volume создан и не публикует порт наружу.
- [ ] `alembic upgrade head` прошёл внутри backend startup.
- [ ] `/api/v1/health/readiness` возвращает `ready`.
- [ ] Первый `sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 24 --ohlcv-intervals 1m,5m,1h` прошёл без критических ошибок.
- [ ] `/api/v1/data/health` возвращает ожидаемые row counts и provider status.
- [ ] `sh scripts/server-smoke.sh` проходит локально на сервере.
- [ ] Frontend открывается через домен.
- [ ] `/api/*` routes проходят через reverse proxy.
- [ ] `BASE_URL=https://deltagrid.pro FRONTEND_URL=https://deltagrid.pro sh scripts/server-smoke.sh` проходит через домен.
- [ ] `sudo LETSENCRYPT_EMAIL=... sh scripts/configure-nginx-ssl.sh` прошёл после DNS cutover.
- [ ] WebSocket `/api/v1/stream/ws` проходит через reverse proxy.
- [ ] Создан свежий backup PostgreSQL.
- [ ] Проверены логи backend/frontend/postgres после старта.
