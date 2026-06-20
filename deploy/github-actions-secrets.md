# GitHub Actions deploy secrets

Этот чеклист нужен, чтобы GitHub Actions мог автоматически деплоить:

- `preview` в `/opt/deltagrid-preview`;
- `main` в `/opt/deltagrid`.

CI уже работает без secrets. Deploy workflows безопасно делают skip, пока secrets не заведены в GitHub.

## Обязательные secrets

Preview:

```text
PREVIEW_SSH_HOST=2.25.143.143
PREVIEW_SSH_USER=root
PREVIEW_APP_DIR=/opt/deltagrid-preview
PREVIEW_SSH_KEY=<private SSH key>
```

Production:

```text
PROD_SSH_HOST=2.25.143.143
PROD_SSH_USER=root
PROD_APP_DIR=/opt/deltagrid
PROD_SSH_KEY=<private SSH key>
```

Опциональные secrets можно не задавать, потому что workflows уже имеют безопасные defaults:

```text
PREVIEW_ENV_FILE=.env.preview
PREVIEW_COMPOSE_PROJECT_NAME=deltagrid-preview
PREVIEW_SMOKE_BASE_URL=http://127.0.0.1:8011
PREVIEW_SMOKE_FRONTEND_URL=http://127.0.0.1:3012

PROD_ENV_FILE=.env.production
PROD_COMPOSE_PROJECT_NAME=deltagrid
PROD_SMOKE_BASE_URL=http://127.0.0.1:8000
PROD_SMOKE_FRONTEND_URL=http://127.0.0.1:3001
```

## Создание deploy-ключа

Для MVP можно использовать один dedicated SSH key для обоих стендов. Позже лучше заменить `root` на отдельного пользователя `deploy` с ограниченными правами.

Текущее состояние на 2026-06-20:

- dedicated key уже создан локально в `outputs/deploy-keys/github-actions-deltagrid-deploy`;
- public key добавлен на VPS в `/root/.ssh/authorized_keys`;
- non-interactive SSH-login этим ключом проверен;
- fingerprint: `SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg`;
- в GitHub repository secrets private key добавляется как `PREVIEW_SSH_KEY` и `PROD_SSH_KEY`.
- preview deploy probe `fdb08ec` подтвердил safe-skip без обязательных secrets.
- preview auto-deploy от 2026-06-14 проверен end-to-end: `PREVIEW_*` secrets, fingerprint deploy key, SSH login, `/opt/deltagrid-preview`, deploy step и server smoke прошли.
- после flaky GitHub runner preview workflow усилен: TCP port probe не блокирует deploy, а SSH login использует явные timeout/keepalive и retry; контрольный probe после hardening дошёл до `/opt/deltagrid-preview`.
- `Deploy Preview` run `27744161749` от 2026-06-18 упал на шаге `Deploy preview` из-за transient SSH reachability из GitHub runner: обязательные `PREVIEW_*` secrets, fingerprint и expected value checks были настроены, но SSH port/login/app-dir/deploy attempts были нестабильны. Ручной запуск того же deploy script по SSH после run успешно обновил `/opt/deltagrid-preview` до `d3de35e`.
- После этого workflow усилен remote diagnostic snapshot: при failed deploy attempt он печатает git status, последний commit, disk usage, `docker compose ps` и хвост backend/frontend logs, если SSH доступен; если SSH недоступен, лог явно фиксирует transport/reachability failure.
- Follow-up `preview@b257cc8` подтвердил preview auto-deploy end-to-end: GitHub CI `27746664616` и `Deploy Preview` `27746714283` прошли успешно, `/opt/deltagrid-preview` обновлён до `b257cc8`.
- production deploy hardening перенесён в `main`; real auto-deploy пока не считается подтверждённым, потому что обязательные `PROD_*` repository secrets ещё не заведены.
- production preflight от 2026-06-16: GitHub Actions run `27619159104` для `main@0716f6a` завершился успешным safe-skip. Шаги `Production secret SSH_HOST missing`, `SSH_USER missing`, `SSH_KEY missing`, `APP_DIR missing` прошли, а `Deploy production` был skipped.
- production release `v1.5.0` на `main@3f6f3f7` был доставлен вручную по SSH через `scripts/deploy-compose-stack.sh`: GitHub `Deploy Production` стартовал, но deploy step был skipped из-за отсутствующих `PROD_*`; `/opt/deltagrid` работает на `VERSION=1.5.0`, `/version` возвращает `1.5.0`.
- В `v1.6.0` workflow добавляет summary-статусы `skipped_missing_required_secrets`, `ready_for_real_deploy`, `real_deploy_succeeded` и `real_deploy_failed`, чтобы runbook не смешивал safe-skip с фактическим deploy.
- локальный read-only preflight от 2026-06-16 подтвердил deploy contract: fingerprint ключа `SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg`, SSH к `root@2.25.143.143`, `/opt/deltagrid` на `main@0716f6a`, production containers healthy и `scripts/server-smoke.sh` зелёный.
- deploy workflows логируют только readiness-состояние обязательных secrets как `configured/missing`; сами значения secrets в логах не печатаются.

## Production deploy readiness contract

Workflow `Deploy Production` проверяет следующие публичные expected values:

```text
expected_host=2.25.143.143
expected_user=root
expected_app_dir=/opt/deltagrid
expected_deploy_key_fingerprint=SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg
```

Readiness/result статусы в `$GITHUB_STEP_SUMMARY`:

- `skipped_missing_required_secrets` — один или несколько обязательных `PROD_*` отсутствуют; это успешный safe-skip и **не** реальный production deploy.
- `ready_for_real_deploy` — обязательные `PROD_*` заведены; workflow переходит к SSH/fingerprint/target checks.
- `real_deploy_succeeded` — `Deploy production` реально выполнил SSH deploy и remote `scripts/deploy-compose-stack.sh` завершился успешно.
- `real_deploy_failed` — workflow попытался выполнить real deploy, но deploy step не прошёл после retry.

При `real_deploy_succeeded` remote script дополнительно проверяет `/version` после `server-smoke` и пишет compact JSON `deploy_compose_stack_summary_v0` в `/tmp/deltagrid-deploy-summary.json`; workflow печатает этот файл в job log. При `skipped_missing_required_secrets` такого файла быть не должно, потому что deploy не выполнялся.

В логах и summary разрешено показывать только names/statuses, expected host/user/app dir и fingerprint публичного deploy key. Private key, `.env.production`, raw secrets и provider payload печатать нельзя.

На локальной машине:

```powershell
mkdir outputs\deploy-keys
ssh-keygen -t ed25519 -C "github-actions-deltagrid-deploy" -f outputs\deploy-keys\github-actions-deltagrid-deploy
```

Добавить public key на VPS:

```powershell
type outputs\deploy-keys\github-actions-deltagrid-deploy.pub | ssh root@2.25.143.143 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Private key из файла `outputs\deploy-keys\github-actions-deltagrid-deploy` нужно вставить в GitHub secrets как `PREVIEW_SSH_KEY` и `PROD_SSH_KEY`.

Не коммитьте private key. Директория `outputs/` игнорируется Git.

## Текущий production шаг

Для перевода `Deploy Production` из safe-skip в реальный deploy добавьте в GitHub repository secrets:

```text
PROD_SSH_HOST=2.25.143.143
PROD_SSH_USER=root
PROD_APP_DIR=/opt/deltagrid
PROD_SSH_KEY=<private key from outputs/deploy-keys/github-actions-deltagrid-deploy>
```

Опциональные `PROD_ENV_FILE`, `PROD_COMPOSE_PROJECT_NAME`, `PROD_SMOKE_BASE_URL`, `PROD_SMOKE_FRONTEND_URL` можно не задавать: workflow использует production-safe defaults.

После добавления secrets запустите контрольный `Deploy Production` вручную:

```text
GitHub -> Actions -> Deploy Production -> Run workflow -> Branch: main
```

Workflow также продолжит запускаться автоматически после успешного `CI` на `main`.

Контрольный `Deploy Production` должен пройти следующие признаки:

- `Deploy Production Readiness` в summary показывает `status=ready_for_real_deploy` и `missing_required=none`;
- `Validate production deploy key fingerprint` — success;
- `Validate production target values` — success для `2.25.143.143`, `root`, `/opt/deltagrid`;
- `Test production SSH login` и `Check production app directory` — success или понятный warning с последующим успешным deploy;
- `Deploy production` — success, не skipped;
- `Deploy Production Result` в summary показывает `result=real_deploy_succeeded`, `deploy method=github_actions_ssh`, `real deploy performed=true` и path `/tmp/deltagrid-deploy-summary.json`;
- deploy log содержит JSON summary с `deploy_status=succeeded`, `deploy_method=github_actions_ssh`, `version_status=matched`, `smoke_status=passed` и backup status/path.

Перед реальным production deploy выполните свежий backup на сервере:

```bash
cd /opt/deltagrid
sh scripts/backup-postgres.sh
gzip -t backups/*.sql.gz
```

Если backup script ещё не попал в `/opt/deltagrid`, сначала доставьте его через merge/pull `main` или согласованный ручной copy из проверенного commit; private key и `.env.production` при этом не печатать в logs.

## Где завести secrets

GitHub repository:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

После добавления secrets:

1. Сделайте push в `preview`.
2. Дождитесь успешного `CI`.
3. Workflow `Deploy Preview` должен выполнить SSH deploy в `/opt/deltagrid-preview`.
4. После merge `preview` в `main` и успешного `CI` workflow `Deploy Production` выполнит deploy в `/opt/deltagrid`.

## Проверка после первого auto-deploy

Preview:

```bash
cd /opt/deltagrid-preview
git status --short --branch
docker compose -p deltagrid-preview --env-file .env.preview -f docker-compose.prod.yml ps
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/server-smoke.sh
```

Production:

```bash
cd /opt/deltagrid
git status --short --branch
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:3001/version
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/server-smoke.sh
mkdir -p artifacts/production-release/v1.6.0
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 FUNDING_RELEASE_REPORT_OUTPUT=artifacts/production-release/v1.6.0/funding-release-report.json sh scripts/funding-release-report.sh
sh scripts/funding-release-report-validate.sh artifacts/production-release/v1.6.0/funding-release-report.json
```
