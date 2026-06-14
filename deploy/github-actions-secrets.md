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

Текущее состояние от 2026-06-14:

- dedicated key уже создан локально в `outputs/deploy-keys/github-actions-deltagrid-deploy`;
- public key добавлен на VPS в `/root/.ssh/authorized_keys`;
- non-interactive SSH-login этим ключом проверен;
- fingerprint: `SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg`;
- в GitHub repository secrets ещё нужно вручную добавить private key как `PREVIEW_SSH_KEY` и `PROD_SSH_KEY`.

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
BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/server-smoke.sh
```
