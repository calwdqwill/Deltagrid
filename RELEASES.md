# Релизная политика DeltaGrid

## Стенды

- `preview` — dev/staging ветка. Сюда попадают рабочие итерации после локальной проверки.
- `main` — production ветка. Сюда попадает только проверенный код, который должен соответствовать `https://deltagrid.pro`.
- feature-ветки — короткие рабочие ветки для задач, например `codex/mvp1-provider-inventory`.

Рекомендуемая инфраструктура стендов:

- preview stack: `/opt/deltagrid-preview`, `.env.preview`, Compose project `deltagrid-preview`, local ports `8001/3002`;
- production stack: `/opt/deltagrid`, `.env.production`, Compose project `deltagrid`, local ports `8000/3001`.

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
3. Закоммитить изменения и запушить в `preview`.
4. CI на GitHub должен пройти.
5. После проверки dev/staging стенда выполнить merge `preview` в `main`.
6. Production deploy выполняется из `main`.
7. Создать annotated tag:

```bash
git tag -a v1.3.0 -m "DeltaGrid v1.3.0"
git push origin v1.3.0
```

## Документация релиза

- `CHANGELOG.md` — фактически выполненные изменения по датам и версиям.
- `CURRENT_TASK.md` — текущая рабочая стадия и ближайший следующий шаг.
- `PROJECT_PLAN.md` — фазы, roadmap и milestone-статус.
- `BACKLOG.md` — P0/P1/P2 задачи.
- `ARCHITECTURE.md` — только реальные изменения архитектуры, data flows, API и инфраструктуры.

## Текущий baseline

`v1.3.0` — production baseline после MVP1 Data Quality Gate, OKX primary provider, interactive charts v0, coverage matrix и production universe v1.
