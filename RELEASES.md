# Релизная политика DeltaGrid

## Стенды

- `preview` — dev/staging ветка. Сюда попадают рабочие итерации после локальной проверки.
- `main` — production ветка. Сюда попадает только проверенный код, который должен соответствовать `https://deltagrid.pro`.
- feature-ветки — короткие рабочие ветки для задач, например `codex/mvp1-provider-inventory`.

Рекомендуемая инфраструктура стендов:

- preview stack: `/opt/deltagrid-preview`, `.env.preview`, Compose project `deltagrid-preview`, local ports `8011/3012`;
- production stack: `/opt/deltagrid`, `.env.production`, Compose project `deltagrid`, local ports `8000/3001`.

Операционные чеклисты:

- `deploy/github-actions-secrets.md` — GitHub Actions secrets для auto-deploy;
- `deploy/dns/preview.deltagrid.pro.md` — DNS/Nginx/SSL публикация preview-домена.

## Версионирование

Используем SemVer:

- `MAJOR` — breaking changes в публичных API, данных или инфраструктуре.
- `MINOR` — новая функциональность без breaking changes.
- `PATCH` — исправления багов, документации и мелкие безопасные правки.

Примеры:

```text
v1.3.0       production release
v1.3.1       patch release
v1.4.0-rc.1  release candidate на preview
```

Корневая версия хранится в `VERSION`. Frontend package version должен соответствовать `VERSION`, если релиз затрагивает frontend или общую поставку продукта.

## Release flow

1. Внести изменения в feature-ветке или напрямую в `preview` для маленькой безопасной итерации.
2. Прогнать локально backend tests и frontend build.
3. Перед релизным bump проверить согласованность текущей версии и целевого preview release candidate:

```bash
RELEASE_BRANCH=preview RELEASE_TARGET=1.4.0-rc.1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh
```

4. Перед promotion выполнить release smoke на preview:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/release-smoke.sh
```

Перед RC commit/push для `v1.4.0-rc.1` дополнительно выполнить Browser QA preview через SSH tunnel для `/perp-dex`, `/charts`, `/data-health` и ключевых terminal screens на desktop/mobile: runtime errors, console errors и page-level horizontal overflow должны отсутствовать.

Если GitHub-hosted runner не может завершить SSH deploy, но тот же `scripts/deploy-compose-stack.sh` уже вручную доставил commit на preview и `scripts/release-smoke.sh` прошёл, `Deploy Preview` может использовать public HTTP fallback: `/version` через `Host: preview.deltagrid.pro` должен вернуть ожидаемую версию из `VERSION`, а `/api/v1/health` должен быть доступен. Этот fallback не включает production promotion и не заменяет production backup/deploy gate.

Для compact preview/prod diff `Perp DEX Source Status` можно отдельно выполнить:

```bash
BASE_URL=http://127.0.0.1:8011 COMPARE_BASE_URL=http://127.0.0.1:8000 sh scripts/perp-dex-source-status-smoke.sh
```

5. Закоммитить изменения и запушить в `preview`.
6. CI на GitHub и `Deploy Preview` должны пройти.
7. После проверки dev/staging стенда выполнить merge `preview` в `main`.
8. Production deploy выполняется из `main`; перед deploy нужен свежий PostgreSQL backup.
9. На чистом дереве повторить preflight без `ALLOW_DIRTY`:

```bash
RELEASE_BRANCH=main sh scripts/release-preflight.sh 1.4.0
```

10. Создать annotated tag:

```bash
git tag -a v1.4.0 -m "DeltaGrid v1.4.0"
git push origin v1.4.0
```

## Документация релиза

- `CHANGELOG.md` — фактически выполненные изменения по датам и версиям.
- `CURRENT_TASK.md` — текущая рабочая стадия и ближайший следующий шаг.
- `PROJECT_PLAN.md` — фазы, roadmap и milestone-статус.
- `BACKLOG.md` — P0/P1/P2 задачи.
- `ARCHITECTURE.md` — только реальные изменения архитектуры, data flows, API и инфраструктуры.

## Текущий baseline

`v1.4.0` — production minor release: зелёный preview/prod deploy path, Perp DEX read-only research cockpit, source-status/release smoke tooling, production backup tooling и `/version` verification endpoint.

Preview release runway для `v1.4.0` подтверждён на `preview@b257cc8`: CI `27746664616`, `Deploy Preview` `27746714283`, server release smoke на `8011/3012` зелёный. После Perp DEX depth freshness commit `4433f0b` GitHub CI `27761405255` зелёный, `Deploy Preview` `27761467202` упал на step `Deploy preview`, но ручной deploy тем же script и полный preview release smoke на `8011/3012` прошли. `main`, production deploy и tag `v1.3.2` не трогались.

Следующий production target: `v1.4.0` — minor release с зелёным deploy path, Perp DEX read-only research cockpit и production rollout на `deltagrid.pro`.

На 2026-06-18 Perp DEX research cockpit для `v1.4.0` дополнен provider state empty/error states: Direct/Depth/CoinGlass panels показывают compact provider/source rows поверх `availability_summary`/`coverage_summary`, чтобы preview/prod QA видела provider unavailable, partial data, missing symbols и CoinGlass unavailable без включения route ranking, route selection, numeric route cost bps или execution.

`v1.4.0` выпущен в production: `main@3936c83`, tag `v1.4.0`, `/opt/deltagrid` обновлён до `3936c83`/`VERSION=1.4.0`, backup `/opt/deltagrid/backups/deltagrid-v140-production_20260618T210020Z.sql.gz` создан перед deploy, production `scripts/release-smoke.sh` и Browser QA desktop/mobile прошли.
