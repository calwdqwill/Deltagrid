# DNS-чеклист для `preview.deltagrid.pro`

Цель — опубликовать отдельный dev/staging стенд без открытия внутренних Docker-портов наружу.

## Текущее устройство preview

- Сервер: `2.25.143.143`.
- Код: `/opt/deltagrid-preview`.
- Ветка: `preview`.
- Env-файл: `.env.preview`.
- Compose project: `deltagrid-preview`.
- Backend: `127.0.0.1:8011`.
- Frontend: `127.0.0.1:3012`.
- Внешние порты `8011/3012` не должны открываться в firewall.
- Nginx HTTP site `deltagrid-preview` уже включён на VPS и проверен через `Host: preview.deltagrid.pro`.
- Публичный HTTPS пока ждёт DNS-запись `preview -> 2.25.143.143`; до этого certbot запускать рано.

## DNS

В Cloudflare или у текущего DNS-провайдера добавьте запись:

```text
Type: A
Name: preview
Value: 2.25.143.143
TTL: Auto
Proxy: можно включить, если для `deltagrid.pro` уже используется Cloudflare Full (strict)
```

Если для зоны есть `AAAA`-запись или wildcard IPv6, убедитесь, что `preview.deltagrid.pro` не уходит на старый хостинг.

Проверка с локальной машины:

```powershell
Resolve-DnsName preview.deltagrid.pro
```

Проверка на сервере:

```bash
getent hosts preview.deltagrid.pro
```

Проверка уже включённого HTTP reverse proxy без публичного DNS:

```bash
curl -H 'Host: preview.deltagrid.pro' http://127.0.0.1/api/v1/health/readiness
curl -o /dev/null -w '%{http_code}\n' -H 'Host: preview.deltagrid.pro' http://127.0.0.1/
curl -o /dev/null -w '%{http_code}\n' -H 'Host: preview.deltagrid.pro' 'http://127.0.0.1/charts?symbol=BTC&interval=1m&range=7d'
```

## Nginx и SSL

После того как DNS начал резолвиться, на VPS выполните:

```bash
cd /opt/deltagrid-preview
sudo LETSENCRYPT_EMAIL=you@example.com sh scripts/configure-preview-nginx-ssl.sh
```

Если email пока не задан, скрипт выпустит сертификат без уведомлений о продлении:

```bash
cd /opt/deltagrid-preview
sudo sh scripts/configure-preview-nginx-ssl.sh
```

Скрипт:

- проверяет наличие DNS-записи перед изменением Nginx;
- копирует `deploy/nginx/deltagrid-preview.conf.example` в `/etc/nginx/sites-available/deltagrid-preview`;
- включает site через `/etc/nginx/sites-enabled/deltagrid-preview`;
- проверяет `nginx -t`;
- выпускает Let's Encrypt сертификат только для `preview.deltagrid.pro`;
- не трогает production site `deltagrid`.

## Smoke-check

После выпуска сертификата:

```bash
cd /opt/deltagrid-preview
BASE_URL=https://preview.deltagrid.pro FRONTEND_URL=https://preview.deltagrid.pro sh scripts/server-smoke.sh
```

Дополнительные проверки:

```bash
curl https://preview.deltagrid.pro/api/v1/health/readiness
curl https://preview.deltagrid.pro/api/v1/data/health
curl "https://preview.deltagrid.pro/charts?symbol=BTC&interval=1m&range=7d"
```

Ожидаемо: preview показывает те же route-level capabilities, но читает отдельную preview PostgreSQL БД и не влияет на production `/opt/deltagrid`.
