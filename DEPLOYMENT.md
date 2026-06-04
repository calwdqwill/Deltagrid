# Деплой DeltaGrid MVP

Этот документ описывает минимальный production-oriented запуск MVP на сервере с Docker Compose, PostgreSQL, reverse proxy и доменом. Цель — безопасный первый деплой без смены архитектуры и без добавления лишней инфраструктуры.

## Допущения

- Сервер уже имеет Docker и Docker Compose plugin.
- Домен указывает на сервер.
- Reverse proxy запускается на хосте отдельно, например Nginx.
- PostgreSQL работает внутри `docker-compose.prod.yml` и не публикуется наружу.
- Секреты хранятся в `.env.production`, который не коммитится.

## Подготовка env

Автоматический вариант для сервера:

```bash
sh scripts/generate-production-env.sh your-domain.com
```

Скрипт создаёт `.env.production`, генерирует `SECRET_KEY`, `VAULT_MASTER_KEY`, `POSTGRES_PASSWORD`, выставляет `chmod 600` и подставляет домен в `PUBLIC_APP_URL`/`CORS_ORIGINS`.

Ручной вариант:

```bash
cp .env.production.example .env.production
```

После копирования замените все placeholder-значения.

Обязательные переменные:

- `DEBUG=false`
- `PUBLIC_APP_URL=https://your-domain.com`
- `CORS_ORIGINS=https://your-domain.com`
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
DOMAIN=your-domain.com sh scripts/server-preflight.sh
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
curl http://127.0.0.1:3000
```

`/api/v1/health/readiness` должен вернуть `status: ready`, а `current_revision` должен совпадать с `expected_heads`.

## Reverse proxy

Минимальная схема:

- `https://your-domain.com/` → `127.0.0.1:3000`
- `https://your-domain.com/api/` → `127.0.0.1:8000/api/`
- `wss://your-domain.com/api/v1/stream/ws` → `127.0.0.1:8000/api/v1/stream/ws`

Готовый шаблон лежит в `deploy/nginx/deltagrid.conf.example`. Скопируйте его в Nginx и замените домен:

```bash
sudo cp deploy/nginx/deltagrid.conf.example /etc/nginx/sites-available/deltagrid
sudo sed -i 's/example.com/your-domain.com/g' /etc/nginx/sites-available/deltagrid
sudo ln -s /etc/nginx/sites-available/deltagrid /etc/nginx/sites-enabled/deltagrid
sudo nginx -t
sudo systemctl reload nginx
```

Пример Nginx-конфига:

```nginx
server {
    listen 80;
    server_name your-domain.com;

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
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

После настройки Nginx выпустите SSL-сертификат, например через Certbot, и обновите `PUBLIC_APP_URL`/`CORS_ORIGINS` на HTTPS-домен.

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
BASE_URL=https://your-domain.com FRONTEND_URL=https://your-domain.com sh scripts/server-smoke.sh
```

Для Windows/PowerShell:

```powershell
$env:BASE_URL="https://your-domain.com"
$env:FRONTEND_URL="https://your-domain.com"
.\scripts\server-smoke.ps1
```

## Backup PostgreSQL

Перед каждым деплоем и перед рискованными миграциями сделайте backup:

```bash
mkdir -p backups
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres pg_dump -U deltagrid deltagrid > backups/deltagrid_$(date +%F_%H%M).sql
```

Восстановление из backup:

```bash
cat backups/deltagrid_YYYY-MM-DD_HHMM.sql | docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres psql -U deltagrid deltagrid
```

Если в `.env.production` используются другие `POSTGRES_USER` или `POSTGRES_DB`, замените `deltagrid` в командах.

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
- [ ] `DOMAIN=your-domain.com sh scripts/server-preflight.sh` проходит.
- [ ] `docker compose --env-file .env.production -f docker-compose.prod.yml config` проходит.
- [ ] PostgreSQL volume создан и не публикует порт наружу.
- [ ] `alembic upgrade head` прошёл внутри backend startup.
- [ ] `/api/v1/health/readiness` возвращает `ready`.
- [ ] `/api/v1/data/health` возвращает ожидаемые row counts и provider status.
- [ ] `sh scripts/server-smoke.sh` проходит локально на сервере.
- [ ] Frontend открывается через домен.
- [ ] `/api/*` routes проходят через reverse proxy.
- [ ] `BASE_URL=https://your-domain.com FRONTEND_URL=https://your-domain.com sh scripts/server-smoke.sh` проходит через домен.
- [ ] WebSocket `/api/v1/stream/ws` проходит через reverse proxy.
- [ ] Создан свежий backup PostgreSQL.
- [ ] Проверены логи backend/frontend/postgres после старта.
