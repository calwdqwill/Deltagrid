# Current Task — DeltaGrid

**Phase**: MVP1 — Data Quality Gate и provider reliability
**Status**: Production baseline `v1.4.0` выпущен на `deltagrid.pro`: tag `v1.4.0` указывает на release commit `3936c83`, runtime `/opt/deltagrid` работает на `3936c83` с `VERSION=1.4.0`, production release smoke и Browser QA прошли. Текущий `origin/main` находится на `2b6c830` с docs-only follow-up по `v1.4.0`. Ветка `codex/v1.4.1-funding-release-tooling` содержит `v1.4.1` tooling commit `1f84fab`, локальный `v1.5.0` RC commit `0a43813`, handoff/regression evidence и pre-merge validation; PR ещё не открыт, tags `v1.4.1`/`v1.5.0` не созданы, production deploy `v1.5.0` не запускался. Локальный `v1.5.0` RC готов к ручному PR; финальный release gate остаётся после PR/review, preview evidence, merge, production backup/deploy, smoke, Browser QA и tag.
**Last Updated**: 2026-06-20

## Обновление 2026-06-20 — v1.5.0 pre-merge validation

- Выполнен pre-merge validation против `origin/main`: merge-base совпадает с `origin/main=2b6c830`, `git merge-tree origin/main HEAD` проходит без conflict output.
- `git diff --check origin/main...HEAD` не нашёл whitespace errors; generated artifact paths в PR diff отсутствуют.
- Backend files в PR diff отсутствуют; изменений API, БД, миграций и provider adapters нет.
- Secret-like additions не найдены; targeted scan на включение forbidden capabilities пустой.
- Handoff обновлён pre-merge результатами; merge/deploy/tag не выполнялись.

## Обновление 2026-06-20 — v1.5.0 full local regression pass

- Выполнен полный локальный regression pass поверх `v1.5.0` RC: release preflight, docs-check preflight, backend compileall, backend pytest, frontend build, frontend high-level audit, funding shell syntax и temp evidence bundle.
- Backend tests запускались через проектный venv: `backend\\venv\\Scripts\\python.exe -m pytest tests -q`; результат `59 passed`.
- Системный Python 3.12 не содержит `pytest`, поэтому backend regression в этом workspace нужно запускать через `backend\\venv\\Scripts\\python.exe`.
- Funding CI-like temp evidence bundle прошёл с `ci_final_status=passed`, локальный `runway_status=blocked` остаётся корректным release blocker для среды без funding rows.
- Production deploy/tag не выполнялись; следующий внешний шаг остаётся PR и GitHub CI.

## Обновление 2026-06-20 — v1.5.0 PR/release handoff readiness

- Проверено remote состояние: `origin/main=2b6c830`, ветка `codex/v1.4.1-funding-release-tooling=0a43813`, merge-base совпадает с `origin/main`, tag `v1.5.0` отсутствует.
- Открытый PR для ветки не найден; `gh` CLI и `GITHUB_TOKEN`/`GH_TOKEN` в локальной сессии недоступны, поэтому реальный PR нужно открыть вручную.
- Добавлен handoff: `deploy/v1.5.0-release-handoff.md` с PR URL, готовым PR body, checks, preview evidence path, production release gate и safety boundary.
- GitHub CI не стартует на push в `codex/*`: текущий `CI` workflow запускается на PR к `preview`/`main` и push в `preview`/`main`.
- Production deploy/tag не выполнялись; следующий безопасный внешний шаг - открыть PR и дождаться CI.

## Обновление 2026-06-20 — v1.5.0 local RC/version bump

- Итерация 4 закрыта локально: `VERSION`, `frontend/package.json`, root version в `frontend/package-lock.json` и текущая версия в `README.md` подняты до `1.5.0`.
- `v1.5.0` локально включает накопленный `v1.4.1` Funding release tooling scope, `Funding Data Quality Runway` и `data_quality_runway` release evidence contract.
- Проверки: `ALLOW_DIRTY=1 ./scripts/release-preflight.sh 1.5.0` прошёл; `npm run build` во `frontend` прошёл; `npm audit --audit-level=high` не нашёл high/critical blocker; funding compact report + validator прошли на temp artifact.
- Финальный release gate не выполнялся из feature branch: preview deploy/smoke, production backup/deploy, production Browser QA и annotated tag `v1.5.0` остаются шагами после review/merge.
- Граница сохранена: backend API, БД, provider calls, торговые/routing outputs и численные route/carry outputs не включались.

## Обновление 2026-06-20 — v1.5.0 Funding runway evidence contract batch

- Итерация 3 закрыта одним release-evidence batch: `scripts/funding-qa-smoke.sh` добавляет `contract.data_quality_runway` с gate ids/statuses, blockers, missing sources, history preview rows, next action и safe boundary.
- `scripts/funding-release-report.sh` выводит `data_quality_runway` как top-level compact report field, добавляет release gate check и учитывает runway blockers в `blocking_reasons`/`next_actions`.
- `scripts/funding-release-report-validate.sh` проверяет schema `funding_data_quality_runway_v0`, включая enum статусов, соответствие gate ids/statuses и subset для blocking gate ids.
- Локальный CI-like temp evidence bundle прошёл с `ALLOW_UNAVAILABLE=1`, `RUN_FRONTEND_CHECK=0` и отдельной artifact directory; blocked runway без локальных rows считается валидным release blocker, а не ошибкой tooling.
- Следующая итерация: `v1.5.0` RC/version bump и финальные проверки; preview/prod rollout, backup, Browser QA и tag остаются отдельным release gate после review/merge.
- Граница сохранена: backend API, БД, provider calls, торговые/routing outputs и численные route/carry outputs не включались.

## Обновление 2026-06-20 — v1.5.0 Funding/Data QA product batch

- Итерация 2 закрыта одним безопасным batch: `Funding Data Quality Runway` добавлен в live Funding data, frontend QA view, preview fixture и funding QA smoke contract.
- Панель сводит `Data Health`, funding rows, source coverage, freshness/coverage/sync, history preview и `v1.5.0` preview gate как release QA evidence.
- Smoke marker `funding_data_quality_runway` и panel id добавлены в `scripts/funding-qa-smoke.sh`, чтобы frontend marker check видел новый read-only слой.
- Проверки: `npm run build` во `frontend` прошёл; `bash -n scripts/funding-qa-smoke.sh` прошёл.
- Следующая итерация: собрать release evidence bundle и preview/prod validation, не меняя production runtime.
- Граница сохранена: backend API, БД, provider calls, торговые/routing outputs и численные route/carry outputs не включались.

## Обновление 2026-06-20 — v1.5.0 release/planning/runway batch

- Рабочее дерево на старте чистое, текущая ветка — `codex/v1.4.1-funding-release-tooling`, `HEAD=1f84fab`.
- До `v1.5.0` запланированы 4 крупные итерации: 1) release/planning/runway; 2) один read-only Funding/Data QA product batch; 3) release evidence и preview/prod validation; 4) `v1.5.0` RC, production backup/deploy, smoke, Browser QA и tag.
- `v1.5.0` зависит от решения по `v1.4.1`: перед финальным RC нужно либо смержить/выпустить `v1.4.1`, либо явно включить его release tooling scope в `v1.5.0`.
- Итерация 1 фиксирует safe-start основу: scope, milestone, non-goals, release path, evidence gates, docs ownership и запрет на runtime changes.
- Следующий product batch должен использовать существующие `/data/funding` и `/data/health` либо уже имеющиеся smoke/evidence scripts; новые backend endpoints, provider calls, миграции и торговые/routing signals требуют отдельного решения.
- Проверка этой итерации: docs diff, `git diff --check` и docs-only release preflight `RELEASE_TARGET=1.5.0 RELEASE_CHECK_DOCS=1 ALLOW_DIRTY=1`.

## Обновление 2026-06-20 — v1.4.1 local intermediate

- Локально подготовлена промежуточная версия `v1.4.1`: обновлены `VERSION`, `frontend/package.json`, root version в `frontend/package-lock.json` и текущая версия в `README.md`.
- `v1.4.1` является patch/tooling релизом вокруг Funding release evidence, CI wrapper/runbook hardening и release docs.
- Production baseline пока остаётся `v1.4.0` на `main@3936c83`/tag `v1.4.0` до отдельного commit/tag/deploy решения.
- Следующий шаг после локальных проверок: при необходимости commit/push/tag/deploy `v1.4.1`, затем прогнать Funding release report на preview/prod URL как release evidence.
- Граница сохранена: backend API, БД, provider calls, frontend product flow, trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — v1.4.1 release candidate docs/runbook

- `v1.4.1` выбран как промежуточный patch/tooling target для накопленного Funding release evidence блока после production `v1.4.0`.
- `scripts/release-preflight.sh` получил optional guard `RELEASE_CHECK_DOCS=1`: он проверяет, что `v<RELEASE_TARGET>` уже упомянут в release docs из `RELEASE_DOCS_FILES`.
- Default preflight не изменён: без `RELEASE_CHECK_DOCS=1` скрипт по-прежнему проверяет версии, ветку и dirty tree.
- Release docs/runbook обновляются до version bump; сам `VERSION`, frontend package metadata и lockfile будут подняты в отдельной следующей итерации.
- Граница сохранена: backend API, БД, provider calls, frontend product flow, trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release CI Final Status Batch v0

- Одним batch закрыт scope из 10 задач: status artifact env, write guard, финальная запись после archive, `final_status`, `final_exit_code`, `final_stage`, stage exit codes, краткий artifact-status rollup, GitHub step summary readout и synthetic failure-mode checks.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-ci-status.json` рядом с evidence bundle.
- `funding-release-ci-status.json` фиксирует итоговый wrapper status (`passed`, `blocked`, `failed`), первую non-zero стадию и exit codes report/validation/bundle/review/summary/handoff/audit/index/verify/notes/archive.
- GitHub workflow `Funding Release Report` добавляет секцию `CI Final Status` в `$GITHUB_STEP_SUMMARY` и загружает status JSON в тот же artifact.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Archive Batch v0

- Одним batch закрыт scope из 10 задач: standalone archive CLI, Markdown output, JSON output, text output, required artifact inventory, optional compare artifact inventory, SHA-256/size/JSON-validity checks, verify/notes readiness consistency, CI wrapper archive artifacts и GitHub summary archive readout.
- Добавлен `scripts/funding-release-evidence-archive.sh`: он читает только локальные artifact-файлы из `artifacts/funding-release`, не запуская smoke заново.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-archive.json` и `funding-release-archive.md` после evidence notes.
- GitHub workflow добавляет `funding-release-archive.md` в `$GITHUB_STEP_SUMMARY` после notes; fallback parser умеет читать `funding-release-archive.json`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Compare Batch v0

- Одним batch закрыт scope из 10 задач: standalone compare CLI, Markdown output, JSON output, text output, required verify artifacts for two dirs, optional notes/index/audit/review/manifest/report reads, status/readiness diff, blocker diff, artifact presence diff и strict aligned gate.
- Добавлен `scripts/funding-release-evidence-compare.sh`: он сравнивает два локальных evidence bundle без повторного smoke.
- Compare показывает `compare_status=aligned|drift_detected|failed`, `comparison_mode`, `diff_count`, `blocking_diff_count` и `recommended_next_action`.
- По умолчанию drift остаётся runbook signal с exit `0`; `FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED=1` возвращает exit `2`, если найден drift.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Notes Batch v0

- Одним batch закрыт scope из 10 задач: standalone notes CLI, Markdown output, JSON output, text output, verify artifact dependency, optional index/audit/review/manifest/report consistency checks, release notes snippet, debug review snippet, CI wrapper notes artifacts и GitHub summary notes readout.
- Добавлен `scripts/funding-release-evidence-notes.sh`: он читает только локальные artifact-файлы из `artifacts/funding-release`, не запуская smoke заново.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-notes.json` и `funding-release-notes.md` после evidence verify.
- GitHub workflow добавляет `funding-release-notes.md` в `$GITHUB_STEP_SUMMARY` после verify; fallback parser умеет читать `funding-release-notes.json`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Verify Batch v0

- Одним batch закрыт scope из 10 задач: standalone verify CLI, text output, JSON output, Markdown output, index/audit consistency checks, optional review/manifest/report consistency checks, optional release-notes/debug gates, CI wrapper verify artifacts, GitHub summary verify readout и docs/checks.
- Добавлен `scripts/funding-release-evidence-verify.sh`: он читает только локальные artifact-файлы из `artifacts/funding-release`, не запуская smoke заново.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-verify.json` и `funding-release-verify.md` после evidence index.
- GitHub workflow добавляет `funding-release-verify.md` в `$GITHUB_STEP_SUMMARY` после index; fallback parser умеет читать `funding-release-verify.json`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Index Batch v0

- Одним batch закрыт scope из 10 задач: standalone index CLI, Markdown output, JSON output, text output, ordered artifact map, status rollup, local review commands, CI wrapper index artifacts, GitHub summary index entrypoint и docs/checks.
- Добавлен `scripts/funding-release-evidence-index.sh`: он читает только локальные artifact-файлы из `artifacts/funding-release`, не запуская smoke заново.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-index.md` и `funding-release-index.json` после audit.
- GitHub workflow сначала добавляет `funding-release-index.md` в `$GITHUB_STEP_SUMMARY`; summary/audit parser остаётся fallback.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Audit Summary CI Batch v0

- Одним batch закрыт scope из 10 задач: audit Markdown artifact, CI wrapper env, bool/path guards, JSON audit output, Markdown audit output, GitHub workflow env, GitHub step summary append, fallback audit JSON readout, docs/runbook updates и local failure-mode checks.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-audit.md` рядом с `funding-release-audit.json`.
- GitHub workflow добавляет `funding-release-audit.md` в `$GITHUB_STEP_SUMMARY` после `funding-release-summary.md`; fallback parser читает `funding-release-audit.json`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Audit Batch v0

- Одним batch закрыт scope из 10 задач: standalone audit CLI, text output, JSON output, Markdown output, expected file set, JSON-validity checks, status consistency checks, summary/handoff marker checks, CI wrapper audit artifact и workflow bundle upload.
- Добавлен `scripts/funding-release-evidence-audit.sh`: он проверяет директорию `artifacts/funding-release`, не читая full smoke payload и не запуская smoke заново.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-audit.json` после evidence handoff.
- GitHub workflow загружает audit в том же `artifacts/funding-release` bundle.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Evidence Handoff Batch v0

- Одним batch закрыт scope из 10 задач: standalone handoff CLI, Markdown output, text output, JSON output, `evidence_status`, artifact checklist, required/optional blockers, first actions, run context, CI wrapper handoff artifact и workflow bundle upload.
- Добавлен `scripts/funding-release-evidence-handoff.sh`: он читает `funding-release-review.json`, optional summary, manifest и bundle validation, не читая full smoke payload.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-handoff.md` после review summary.
- GitHub workflow загружает handoff в том же `artifacts/funding-release` bundle.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Review Summary Artifact Batch v0

- Одним batch закрыт scope из 10 задач: standalone summary CLI, Markdown output, text output, JSON output, `runbook_status`, blockers sections, first actions, run context, file integrity table, CI wrapper summary artifact и workflow summary через markdown.
- Добавлен `scripts/funding-release-review-summary.sh`: он читает `funding-release-review.json` и формирует GitHub-ready summary без чтения full smoke payload.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-summary.md` после review artifact.
- GitHub workflow summary сначала добавляет `funding-release-summary.md` в `$GITHUB_STEP_SUMMARY`, а старый parser остаётся fallback.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-20 — Funding Release Bundle Review Batch v0

- Одним batch закрыт scope из 10 задач: standalone review CLI, text output, JSON review artifact, bundle/report/validation exit summary, validation statuses, required/optional blockers, first actions, file integrity summary, CI wrapper review artifact и workflow summary через review.
- Добавлен `scripts/funding-release-bundle-review.sh`: он читает `funding-release-manifest.json` и optional `funding-release-bundle-validation.json`, не читая full smoke payload.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию пишет `funding-release-review.json` после manifest/bundle validation.
- GitHub workflow summary сначала читает review artifact и показывает `review_status`, `recommended_next_action`, blockers и checksum.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Bundle Manifest Validation Batch v0

- Одним batch закрыт scope из 10 задач: standalone bundle validator, schema/version validation, exit-code semantics, report/validation file presence, sha256/size/json-valid checks, required/optional blockers, JSON/text output, CI wrapper gate, workflow summary marker и synthetic/tamper checks.
- Добавлен `scripts/funding-release-bundle-validate.sh`: он проверяет `funding-release-manifest.json` как индекс evidence bundle без чтения full smoke payload.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию запускает bundle validation после записи manifest и сохраняет `funding-release-bundle-validation.json`.
- GitHub workflow summary показывает `bundle_validation_status`, чтобы runbook сразу отличал корректный blocked report от поломки bundle tooling.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Evidence Bundle Batch v0

- Одним batch закрыт scope из 10 задач: validation JSON artifact, manifest JSON artifact, bundle/report/validation exit codes, report summary, blocker action, file checksums/sizes, blocked-exit preservation, workflow manifest summary, docs и synthetic bundle checks.
- `scripts/funding-release-ci-report.sh` теперь создаёт `funding-release-validation.json` и `funding-release-manifest.json` рядом с compact report.
- Manifest содержит `manifest_version=funding_release_ci_bundle_v0`, `bundle_exit_code`, `report_exit_code`, `validation_exit_code`, release/validation statuses, required/optional blockers, report summary, `run_context` и sha256/size для report/stdout/validation files.
- GitHub workflow summary сначала читает manifest и показывает bundle status, validation status, blockers, first action и report checksum.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Artifact Validation Batch v0

- Одним batch закрыт scope из 10 задач: validator script, required field validation, status enum validation, summary/check consistency, safety invariants, CI context validation, CI wrapper integration, blocked-exit preservation, workflow env и docs/checks.
- Добавлен `scripts/funding-release-report-validate.sh`: он проверяет compact JSON artifact без чтения full smoke payload.
- `scripts/funding-release-ci-report.sh` теперь по умолчанию запускает validation после report; если report заблокирован readiness/compare gate, валидатор проверяет форму artifact и возвращается исходный report exit code.
- Manual workflow `Funding Release Report` явно включает artifact validation перед upload/final failure.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report CI Integration Batch v0

- Одним batch закрыт scope из 10 задач: CI wrapper, artifact dir/name defaults, stdout JSON file, report env validation, artifact path validation, CI/GitHub context, manual GitHub workflow, artifact upload before final failure, docs/runbook и local failure-mode checks.
- Добавлен `scripts/funding-release-ci-report.sh`: он запускает `scripts/funding-release-report.sh` с CI defaults (`FUNDING_RELEASE_REPORT_PROFILE=ci`, JSON output, artifact file) и создаёт `artifacts/funding-release`.
- Compact report теперь содержит `run_context.ci` с local/generic/GitHub context, а report preflight заранее ловит неверные bool/int env и плохие output paths.
- Добавлен manual workflow `.github/workflows/funding-release-report.yml`: он читает заданные URLs, сохраняет compact report/stdout artifact и только после upload фейлит job, если report заблокирован или упал.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Artifact Output Batch v0

- Одним batch закрыт scope из 8 задач: `FUNDING_RELEASE_REPORT_OUTPUT`, output path в `run_context`, JSON file writer, write-failure exit `4`, text output line, JSON stdout preservation, docs и проверки.
- `scripts/funding-release-report.sh` теперь может писать compact JSON artifact в файл, не меняя stdout формат: human text остаётся на экране, а JSON сохраняется отдельно.
- `FUNDING_RELEASE_REPORT_JSON` остаётся внутренним temp-файлом для raw smoke JSON; для итогового compact artifact нужно использовать `FUNDING_RELEASE_REPORT_OUTPUT`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Gate Actions Batch v0

- Одним крупным batch закрыт scope из 9 задач: check categories, `required_blocking_ids`, `optional_blocking_ids`, `blocker_groups`, `first_blocking_action`, `next_actions_by_check`, text summary, JSON artifact и docs.
- `release_gate_checks[*]` теперь содержит `category`, чтобы blockers группировались как `smoke`, `readiness`, `compare`, `data`, `frontend`, `safety` или `run_context`.
- `release_gate_summary` теперь показывает, какой action выполнить первым, какие blockers обязательные, какие optional и какие next actions привязаны к конкретным checks.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Gate Checklist Batch v0

- Одним крупным batch закрыт scope из 9 задач: `release_gate_checks`, `release_gate_summary`, normalized check ids, required/blocking counts, `required_ids`, `blocking_ids`, status counts, text summary и docs.
- `scripts/funding-release-report.sh` теперь отдаёт compact checklist для release artifact: `smoke_contract`, `release_readiness`, `compare_alignment`, `data_health`, `funding_rows`, `source_coverage`, `frontend_markers`, `safety_boundary`, `report_profile`.
- `release_gate_summary` помогает CI/dashboard быстро понять, сколько required checks есть, какие checks реально блокируют release-readiness и какие статусы повторяются.
- Soft/manual report может завершиться `passed`, но checklist всё равно показывает release blockers; это ожидаемо и полезно для локального dev режима.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Gate Status v0

- Одной итерацией закрыт scope из 7 задач: `release_gate_status`, mapping `passed|blocked|failed`, сохранение smoke-only `gate_status`, JSON field, text field, docs и проверки.
- `scripts/funding-release-report.sh` теперь отдельно показывает итоговый release/report status: `passed` для exit `0`, `blocked` для report-level readiness/compare gates и `failed` для underlying smoke failure.
- Это уменьшает путаницу между `gate_status` исходного smoke и итоговым статусом release artifact.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Exit Reason v0

- Одной итерацией закрыт scope из 7 задач: `report_exit_code`, `exit_reason`, единая exit-логика, JSON field, text field, smoke exit preservation и docs.
- `scripts/funding-release-report.sh` теперь показывает, почему artifact завершился с конкретным кодом: `passed`, `smoke_failed`, `readiness_not_ready` или `compare_not_aligned`.
- `report_exit_code` совпадает с фактическим итоговым exit code report, поэтому CI может читать причину без разбора stdout/stderr.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report CI Profile v0

- Одной итерацией закрыт scope из 7 задач: report profile env, manual default preservation, CI preset, env override priority, `run_context.report_profile`, text output profile и docs.
- `scripts/funding-release-report.sh` теперь поддерживает `FUNDING_RELEASE_REPORT_PROFILE=ci`: по умолчанию это JSON report + `FUNDING_RELEASE_REPORT_REQUIRE_READY=1` + `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE=1`.
- `FUNDING_RELEASE_REPORT_PROFILE=manual` остаётся default и сохраняет прежнее поведение для локальных ручных запусков.
- Явные `FUNDING_RELEASE_REPORT_FORMAT`, `FUNDING_RELEASE_REPORT_REQUIRE_READY` и `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE` могут переопределить defaults профиля.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Report Require Compare Gate v0

- Одной итерацией закрыт scope из 7 задач: report-level compare flag, default preservation, `compare_gate_status`, non-zero on missing/non-aligned compare, smoke failure preservation, text/JSON support и docs.
- `scripts/funding-release-report.sh` теперь поддерживает `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE=1`.
- Флаг полезен для preview/prod: report может падать, если `COMPARE_BASE_URL` не задан или compare status не `aligned`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Report Require Ready Gate v0

- Одной итерацией закрыт scope из 7 задач: report-level require-ready flag, default soft preservation, readiness non-zero, smoke failure preservation, run context flag, text/JSON support и docs.
- `scripts/funding-release-report.sh` теперь поддерживает `FUNDING_RELEASE_REPORT_REQUIRE_READY=1`.
- Флаг полезен для CI: report может падать при `readiness_gate_status=not_ready`, даже если underlying soft smoke вернул `gate_status=passed`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Readiness Gate Report v0

- Одной итерацией закрыт scope из 7 задач: `readiness_gate_status`, `blocking_reasons`, deduped `next_actions`, soft-smoke distinction, text blockers/actions, JSON blockers/actions и docs.
- `scripts/funding-release-report.sh` теперь отдельно показывает `gate_status` по exit code smoke и `readiness_gate_status` по `contract.release_readiness.status`.
- На локальной пустой funding БД soft report может иметь `gate_status=passed`, но `readiness_gate_status=not_ready`; это ожидаемое и более честное поведение.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Evidence v0

- Одной итерацией закрыт scope из 7 задач: `readiness_checks`, `sources_with_rows`, `source_pair_statuses`, `compare_diff_fields`, text evidence rows, JSON evidence fields и docs.
- `scripts/funding-release-report.sh` теперь объясняет, почему release gate готов или заблокирован: видны статусы data health, rows, source coverage, frontend markers, compare support и safety boundary.
- JSON artifact стал полезнее для CI dashboards: можно смотреть diff fields и source-pair statuses без full smoke payload.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report Context v0

- Одной итерацией закрыт scope из 7 задач: `report_version`, `gate_status`, URL context, strict context, effective fail flags, text context lines и JSON context fields.
- `scripts/funding-release-report.sh` теперь показывает не только результат, но и режим запуска: base/frontend/compare URL, strict mode и hard-gate flags.
- Compact JSON report стал удобнее для CI artifacts: по `gate_status` и `run_context` можно понять, почему gate прошёл или упал.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report JSON v0

- Одной итерацией закрыт scope из 7 задач: report format env, text/json support, сохранение text default, compact JSON fields, strict non-zero preservation, docs/runbook и неизменный `funding_qa_v0`.
- `scripts/funding-release-report.sh` теперь поддерживает `FUNDING_RELEASE_REPORT_FORMAT=json`.
- Compact JSON report содержит smoke exit, readiness status/action, funding rows, frontend marker gaps, compare status/diff count и safety status.
- Изменение не меняет frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Report v0

- Одной итерацией закрыт scope из 7 задач: report script, JSON-only wrapper run, contract parse, compact readiness/rows/frontend/compare/safety summary, exit-code preservation, strict failure visibility и docs.
- Добавлен `scripts/funding-release-report.sh`: краткий release artifact поверх `scripts/funding-release-smoke.sh`.
- Report сохраняет exit code smoke, поэтому его можно использовать и как human summary, и как CI gate.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Smoke JSON Output v0

- Одной итерацией закрыт scope из 7 задач: `OUTPUT_JSON_ONLY`, JSON-only output в QA smoke, passthrough в release wrapper, сохранение human default, неизменные strict/soft presets, CI/report пригодность и docs.
- `scripts/funding-qa-smoke.sh` теперь может печатать чистый JSON contract без строк `Funding QA smoke ...` и `Funding QA smoke passed`.
- `scripts/funding-release-smoke.sh` уважает тот же режим и не печатает свой context line при `OUTPUT_JSON_ONLY=1`.
- Изменение не меняет `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Smoke Wrapper v0

- Одной итерацией закрыт scope из 7 задач: wrapper script, soft default, strict preset, compare preset, frontend marker default, docs/runbook и smoke-проверки.
- Добавлен `scripts/funding-release-smoke.sh`: тонкий runner вокруг `scripts/funding-qa-smoke.sh` для повторяемого funding release smoke на preview/prod.
- По умолчанию wrapper сохраняет мягкий режим; `FUNDING_RELEASE_STRICT=1` включает `FAIL_ON_DIFF=1` и `FAIL_ON_RELEASE_NOT_READY=1`, если они не заданы явно.
- Wrapper не меняет contract `funding_qa_v0`, frontend product flow, backend endpoints, provider calls или БД.
- Граница сохранена: trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Readiness Hard Gate v0

- Одной итерацией закрыт scope из 7 задач: env `FAIL_ON_RELEASE_NOT_READY`, Python plumbing, release status gate, soft default, compare summary flag, expected-failure test и docs.
- `scripts/funding-qa-smoke.sh` теперь может падать по `contract.release_readiness.status`, если явно задан `FAIL_ON_RELEASE_NOT_READY=1`.
- По умолчанию hard gate выключен, поэтому локальный dev с `MIN_TOTAL_ROWS=0` не ломается случайно.
- Negative test на пустой локальной funding БД ожидаемо завершился failure с `release_readiness: needs_funding_rows`.
- Изменение не трогает frontend product flow, backend endpoints, provider calls или БД; trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.

## Обновление 2026-06-19 — Funding Release Readiness Smoke Summary v0

- Одной итерацией закрыт scope из 8 задач: compact `release_readiness`, общий release status, checks по health/rows/source/frontend/compare/safety, missing frontend markers, sources with rows, compare participation и docs.
- `scripts/funding-qa-smoke.sh` теперь выводит `contract.release_readiness`, чтобы release-prep был machine-readable без чтения full payload.
- Локальная проверка с пустыми funding rows ожидаемо вернула `release_readiness.status=needs_funding_rows`; это корректный guard для dev без накопленных rows.
- Изменение не трогает frontend product flow, backend endpoints, provider calls или БД; trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.
- Проверка: `sh -n scripts/funding-qa-smoke.sh`, `git diff --check` и same-base smoke `MIN_TOTAL_ROWS=0 RUN_FRONTEND_CHECK=0 COMPARE_BASE_URL=http://127.0.0.1:8000 FAIL_ON_DIFF=1` прошли.

## Обновление 2026-06-19 — Funding Release Checklist v0

- Одной крупной, но локальной итерацией закрыт scope из 9 задач: typed rows, live release builder, data health check, funding rows guard, OKX/CoinGlass source coverage, history workflow readiness, UI panel, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding Release Checklist` в `Overview`/`QA`: checklist показывает release-readiness по existing `/data/funding` и `/data/health`, а также подсказывает next action для funding QA smoke и preview/prod compare.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_release_checklist` в frontend markers и `panel_ids`.
- Изменение не добавляет backend endpoints, provider calls, БД-изменения или production signals; trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.

## Обновление 2026-06-19 — Funding QA Compare Summary v0

- Одной итерацией закрыт scope из 9 задач: compare path review, compact status, diff count, diff fields, ignored volatile fields, fail-on-diff flag, base/compare row totals, base/compare panel ids и safety flag alignment.
- `scripts/funding-qa-smoke.sh` теперь выводит `compare.summary` для `COMPARE_BASE_URL`, чтобы preview/prod drift был виден компактно и без full payload.
- Старый compact compare `contract` оставлен в output для обратной совместимости; новый summary помогает быстро понять `aligned`/`diff_detected`/`compare_failures`.
- Изменение не трогает frontend product flow, backend endpoints, provider calls или БД; trading, execution, route ranking, route selection, numeric route cost bps и diagnostic carry bps не включались.
- Проверка: `sh -n scripts/funding-qa-smoke.sh`, `git diff --check` и same-base smoke `MIN_TOTAL_ROWS=0 RUN_FRONTEND_CHECK=0 COMPARE_BASE_URL=http://127.0.0.1:8000 FAIL_ON_DIFF=1` прошли.

## Обновление 2026-06-19 — Funding History Readiness v0

- Одной итерацией закрыт scope из 9 задач: typed readiness rows, persisted rows check, selected asset coverage, selected source coverage, chart points readiness, numeric rate parsing readiness, source-aware chart empty-state, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding History Readiness`: read-only панель в `Overview`/`History`, которая объясняет, почему выбранная funding history series пустая, тонкая или готова для QA.
- Empty-state графика теперь показывает конкретный status/evidence/next action для выбранных `asset`/`source`, а не общий текст.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_history_readiness` в `panel_ids` и frontend marker checks.
- Изменение использует существующие `/data/funding` и `/data/health`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.

## Обновление 2026-06-19 — Funding History Controls v0

- Одной итерацией закрыт scope из 9 задач: URL `asset`/`source`, typed rows, source-aware history selection, asset/source controls, rows/window/interval/range hints, chart readiness, next action, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding History Controls`: read-only панель в `Overview`/`History` для выбора asset/source и понимания готовности выбранной funding history series.
- Панель использует существующие persisted rows из `/data/funding` и `/data/health`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_history_controls` в `panel_ids` и frontend marker checks.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.

## Обновление 2026-06-19 — Funding History Diagnostics v0

- Одной итерацией закрыт scope из 9 задач: UI history diagnostics, typed rows, observations/window/latest/interval, average/range, freshness status, next action, `Overview`/`History` placement, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding History Diagnostics`: compact QA таблицу по history window для `BTC/ETH/SOL × OKX/CoinGlass`.
- Панель показывается в `Overview` и `History`, не является strategy signal и не меняет funding calculations.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_history_diagnostics` в `panel_ids` и frontend marker checks.
- Изменение использует существующие `/data/funding` и `/data/health`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` прошли.

## Обновление 2026-06-19 — Funding QA View Grouping v0

- Одной итерацией закрыт scope из 9 задач: `QA` view, `showQaPanels`, compact grouping, overview compatibility, `/funding?view=qa`, скрытие QA block из остальных views, smoke check QA route, `funding_qa_view` marker и docs/backlog.
- `Funding` теперь имеет отдельную вкладку `QA`; QA panels остаются в `Overview`, но не перегружают `History`, `Arbitrage`, `Matrix`, `Predicted` и `Legs`.
- `scripts/funding-qa-smoke.sh` при frontend check проверяет и `/funding`, и `/funding?view=qa`.
- Изменение не трогает backend/data formulas; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` прошли.

## Обновление 2026-06-19 — Funding Anomaly Detail v0

- Одной итерацией закрыт scope из 9 задач: UI anomaly detail, typed rows, samples/latest/baseline/range/z-score, QA-only status, next review, fixed order, fixture fallback, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding Anomaly Detail`: baseline statistics по persisted funding rows для `BTC/ETH/SOL` по OKX/CoinGlass.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_anomaly_detail` в `panel_ids` и frontend marker checks.
- Изменение использует существующие `/data/funding`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` прошли.

## Обновление 2026-06-19 — Funding QA Drilldown v0

- Одной итерацией закрыт scope из 9 задач: UI drilldown, typed rows, freshness reason mapping, coverage reason mapping, sync health, next actions, fixed order without ranking, smoke marker/panel id и docs/backlog.
- `Funding` получил `Funding QA Drilldown`: per-symbol/source таблицу для `BTC/ETH/SOL` по OKX/CoinGlass с loaded rows, latest row age, freshness reason, coverage reason, sync status и next action.
- `scripts/funding-qa-smoke.sh` теперь включает `funding_qa_drilldown` в `panel_ids` и frontend marker checks.
- Изменение использует существующие `/data/funding` и `/data/health`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` прошли.

## Обновление 2026-06-19 — Funding QA smoke contract v0

- Одной итерацией закрыт scope из 9 задач: script, backend funding/health checks, compact contract, frontend marker checks, safety flags, no-full-payload output, env-настройки, preview/prod compare и docs/backlog.
- Добавлен `scripts/funding-qa-smoke.sh`: release-safety/data-QA guard для новых Funding panels.
- Скрипт проверяет `/api/v1/data/health` и `/api/v1/data/funding` по `BTC/ETH/SOL` для `okx` и `coinglass`, формирует `funding_qa_v0` contract и опционально проверяет `/funding` frontend markers.
- Для preview/prod diff поддержаны `COMPARE_BASE_URL` и `FAIL_ON_DIFF`; full payload и secrets не печатаются.
- Локальная проверка: `bash -n scripts/funding-qa-smoke.sh` прошёл; `RUN_FRONTEND_CHECK=0 MIN_TOTAL_ROWS=0` smoke прошёл. Дефолтный `MIN_TOTAL_ROWS=1` на локальном backend падает ожидаемо, потому что текущие локальные funding rows равны `0`.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## Обновление 2026-06-19 — Funding Source Comparison v0

- `Funding` получил третий read-only слой после source status и freshness/anomaly: `Funding Source Comparison`.
- Панель сравнивает последние OKX и CoinGlass funding rates для `BTC/ETH/SOL`, показывает source delta, latest pair, data note и source-alignment status.
- Comparison является только provider/data QA: строки не сортируются по выгоде, не создают opportunities и не используются как production trading signal.
- Изменение использует существующие `/data/funding`; новых API endpoints, provider calls, БД-изменений, carry bps, route ranking, route selection и execution не добавлено.
- Проверка: `frontend` `npm run build` и `git diff --check` прошли.

## Обновление 2026-06-19 — Funding Freshness & Anomaly v0

- `Funding` получил второй read-only слой после source status: `Funding Freshness & Anomaly`.
- Панель показывает для `BTC/ETH/SOL` по OKX и CoinGlass rows, latest age, latest rate, last change, data status и statistical anomaly status.
- Anomaly status является только data-quality/statistical QA по persisted funding rows и не является trading, carry, route ranking, route selection или execution signal.
- Изменение использует существующие `/data/funding` и `/data/health`; новых API endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build` и `git diff --check` прошли.

## Обновление 2026-06-19 — Funding Source Status v0

- После `v1.4.0` начата безопасная post-release итерация в сторону funding analytics без изменения backend contracts.
- `Funding` теперь показывает `Funding Source Status`: OKX funding history и CoinGlass funding snapshots сведены в read-only rows со статусом loaded rows, latest age, freshness, coverage, sync и boundary.
- Источники берутся из существующих `/data/funding` и `/data/health`; новых provider calls, БД-изменений, API endpoints и production trading signals не добавлено.
- `TerminalTable` получил contained horizontal scroll, чтобы широкие status/diagnostic таблицы не создавали page-level horizontal overflow на мобильных экранах.
- Проверка: `frontend` `npm run build` прошёл; Browser mobile smoke для `/funding` подтвердил наличие панели и отсутствие page-level horizontal overflow. Desktop smoke на старом локальном dev server ограничен локальным `next dev`/`.next` chunk mismatch после build.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## Обновление 2026-06-18 — v1.4.0 production release завершён

- Свежий production PostgreSQL backup создан перед rollout: `/opt/deltagrid/backups/deltagrid-v140-production_20260618T210020Z.sql.gz`, размер `4422613` bytes, `gzip -t` прошёл внутри `scripts/backup-postgres.sh`.
- `preview` смержен в `main` merge commit `3936c83` (`Merge preview for v1.4.0`); `RELEASE_BRANCH=main sh scripts/release-preflight.sh 1.4.0`, backend compileall, targeted backend pytest, frontend build и `npm audit --audit-level=high` прошли.
- GitHub CI для `main@3936c83` прошёл (`27789130591`), `Deploy Production` run `27789183806` завершился safe-skip/success, потому что `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR` всё ещё отсутствуют.
- Production deploy выполнен вручную тем же `scripts/deploy-compose-stack.sh` через SSH после backup; `/opt/deltagrid` обновлён до `3936c83`, `VERSION=1.4.0`, backend/frontend/postgres healthy.
- Production smoke прошёл: `scripts/release-smoke.sh`, `https://deltagrid.pro/version`, `/api/v1/health`, `/api/v1/health/readiness`.
- Browser QA production desktop/mobile прошёл для `/version`, `/perp-dex?view=venues`, `/charts?symbol=BTC&interval=1m&range=24h`, `/data-health`, `/market-matrix`, `/arbitrage-scanner`: runtime/console errors и page-level horizontal overflow не найдены.
- Annotated tag `v1.4.0` создан на `main@3936c83` и запушен в GitHub.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## Обновление 2026-06-18 — v1.4.0 release candidate подготовка

- GitHub CI для RC commit `e32922a` прошёл (`27784328974`), но `Deploy Preview` run `27784385918` упал на GitHub runner SSH reachability: порт/app-dir prechecks не дошли до remote deploy script; локальный SSH к VPS был здоров.
- Follow-up retry commit `647f7f3` также получил зелёный CI (`27785222823`), но `Deploy Preview` run `27785273679` снова упал на GitHub runner SSH reachability до remote deploy script.
- Ручной SSH deploy тем же `scripts/deploy-compose-stack.sh` обновил `/opt/deltagrid-preview` до `647f7f3`, `VERSION=1.4.0`; backend/frontend containers healthy, server smoke и `scripts/release-smoke.sh` прошли.
- Добавляется hardening: frontend `/version` отдаёт read-only package version, а GitHub `Deploy Preview` после SSH deploy failure сможет проверить публичный preview HTTP `/version` и `/api/v1/health` через `Host: preview.deltagrid.pro`; fallback проходит только если публичный preview уже показывает ожидаемую версию из `VERSION`.
- Ops-only workflow commit `main@3a8a497` нужен, потому что `workflow_run` берёт `deploy-preview.yml` с default branch; GitHub CI `27787523085` прошёл, `Deploy Production` `27787569689` завершился safe-skip/success, production runtime остался `0716f6a`/`VERSION=1.3.1`.
- Final preview retry `preview@e1be7a3` прошёл GitHub CI `27787569356` и `Deploy Preview` `27787622699`; `/opt/deltagrid-preview` обновлён до `e1be7a3`, `VERSION=1.4.0`, containers healthy, public `/version` возвращает `1.4.0`, финальный `scripts/release-smoke.sh` прошёл.
- Версия поднята до `1.4.0` в `VERSION`, `frontend/package.json` и root entry `frontend/package-lock.json`.
- `CHANGELOG.md` получил release block для `v1.4.0`: release runway, Perp DEX read-only cockpit, preview deploy baseline, production blockers и known limitations.
- `README.md` обновлён на текущую версию `v1.4.0`.
- Preview baseline перед RC зафиксирован как `preview@104b487`: CI `27782417781` и `Deploy Preview` `27782466540` зелёные, remote release smoke на `8011/3012` прошёл.
- Проверка перед RC commit/push: `RELEASE_BRANCH=preview RELEASE_TARGET=1.4.0-rc.1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh 1.4.0`, backend `compileall app`, targeted backend pytest, frontend `npm run build`, `npm audit --audit-level=high`, remote preview `scripts/release-smoke.sh` и Browser QA через SSH tunnel прошли.
- После RC commit `scripts/release-preflight.sh 1.4.0` повторён без `ALLOW_DIRTY` через Git Bash и прошёл на чистом `preview`.
- Browser QA preview проверил desktop/mobile `/perp-dex?view=venues`, `/charts?symbol=BTC&interval=1m&range=24h`, `/data-health`, `/market-matrix`, `/arbitrage-scanner`, `/assets?symbol=ETH`: runtime/console errors и page-level horizontal overflow не найдены.
- Следующий шаг: готовить promotion `preview -> main` только после подтверждения свежего production backup и production rollout checklist.
- Граница сохраняется: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## Обновление 2026-06-18 — Perp DEX provider state empty/error states v0

- Frontend `Perp DEX` теперь показывает compact state rows перед `Direct Perp DEX Market Snapshots`, `Depth Diagnostics` и `CoinGlass Perp DEX Enrichment`.
- Direct venue rows используют `availability_summary`: статус provider, rows, matched/missing symbols, market/depth status counts, provider issue и read-only boundary видны даже при пустых detail rows.
- Depth summary отдельно показывает freshness/statuses/required inputs и сохраняет явную блокировку slippage bps/numeric route cost.
- CoinGlass summary использует `coverage_summary` и graceful unavailable/empty state: coverage hints остаются research-only и не становятся ranking/execution signal.
- Проверка: targeted backend tests `test_perp_dex_policy.py` и `test_perp_dex_direct_availability.py`, frontend `npm run build`, `npm audit --audit-level=high`, policy/direct smoke, local graceful-unavailable CoinGlass smoke и Browser QA desktop/mobile для `/perp-dex?view=venues` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## Обновление 2026-06-18 — Perp DEX Lighter/Aster fee schedule evidence v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `fee_schedule_evidence_summary`: compact summary по Lighter/Aster fee evidence, source fields, required inputs/policy inputs, manual approvals и blocked outputs.
- Backend `diagnostic_cost_estimate_v0.summary` получил `fee_schedule_evidence_checklist` с rows `lighter_fee_schedule_evidence` и `aster_fee_schedule_evidence`.
- Frontend `Perp DEX` получил панели `Route Diagnostic Fee Schedule Evidence` и `Route Diagnostic Fee Schedule Checklist`.
- Policy smoke compact contract расширен полями `fee_schedule_evidence_*`; backend regression tests закрепляют account tier/order intent/manual approval gates.
- Граница не изменилась: fee bps total, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-18 — Perp DEX Source Status compare contract v0

- Добавлен `scripts/perp-dex-source-status-smoke.sh`: reusable compact smoke для `Perp DEX Source Status`, который собирает direct venues, GMX raw, CoinGlass enrichment, route policy/model и release-smoke checklist в один source-status contract.
- Скрипт поддерживает `COMPARE_BASE_URL` и `FAIL_ON_DIFF=1`, чтобы preview/prod drift был виден по ids/statuses/flags/counts без полного payload.
- Contract включает direct venue ids/statuses/rows/depth freshness/provider error classes, CoinGlass matched exchanges/candidate hints/route-input statuses, route policy/model blocker ids и safety flags.
- Raw provider payload, secrets, route ranking, route selection, numeric route cost bps, diagnostic carry bps и execution не включались.

## Обновление 2026-06-18 — Perp DEX GMX helper/source follow-up rows v0

- Backend `gmx_rate_mapping_review_v0` получил `helper_source_follow_up_summary`: compact summary по missing helper source inputs, связанным input/review ids, fixture/decision gates и manual approvals, которые блокируют GMX carry conversion.
- Backend `gmx_rate_mapping_review_v0` получил `helper_source_follow_up_checklist` с rows `source_helper_inputs_missing`, `live_nonzero_mapping_approval`, `side_direction_approval` и `carry_runtime_policy_approvals`.
- Frontend `Perp DEX` получил панель `GMX Rate Helper Source Follow-up`, где отдельно видны missing inputs и blocking manual approvals.
- Policy smoke compact contract расширен полями `gmx_rate_helper_follow_up_*`; backend regression tests закрепляют новый summary/checklist и неизменные safety flags.
- Граница не изменилась: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-18 — preview deploy follow-up после depth freshness

- Product commit `4433f0b` (`feat: add perp dex depth freshness evidence`) прошёл GitHub CI run `27761405255` со статусом `success`.
- GitHub `Deploy Preview` run `27761467202` для этого CI завершился `failure`: secrets/fingerprint/value checks, SSH port, SSH login и app-dir check прошли, но step `Deploy preview` упал после долгих retry; public logs endpoint вернул `403`, поэтому детальный stdout deploy step недоступен через API.
- Preview server вручную обновлён тем же `scripts/deploy-compose-stack.sh`: `/opt/deltagrid-preview` находится на `4433f0b`, backend/frontend containers healthy.
- Полный preview release smoke на `BASE_URL=http://127.0.0.1:8011` и `FRONTEND_URL=http://127.0.0.1:3012` прошёл: `server-smoke`, Perp DEX policy smoke, direct venues smoke и CoinGlass Perp DEX coverage smoke зелёные.
- Классификация остаётся ops/transport: manual deploy тем же script и release smoke прошли, значит depth freshness product/API change не блокирует runtime; нужен маленький docs-only follow-up, чтобы заново получить GitHub `Deploy Preview` gate.
- `main`, production deploy и tags не трогались.

## Обновление 2026-06-18 — Perp DEX depth freshness evidence v0

- `availability_summary.depth_diagnostics` для direct venue endpoints получил `freshness`: snapshot timestamp, observed timestamp, `age_ms`, display `max_age_ms`, status, required policy inputs и stale-depth action.
- Freshness evidence применяется к Lighter/Aster depth diagnostics как read-only readiness layer; для venues без depth diagnostics статус остаётся `not_applicable`.
- Smoke `scripts/perp-dex-direct-smoke.sh` теперь проверяет наличие depth freshness evidence и инварианты `may_emit_slippage_bps=false`, `numeric_total_status=blocked`.
- Проверка: targeted backend tests по direct availability/depth freshness, Lighter/Aster clients и Perp DEX policy contract прошли; `compileall` и `bash -n` для direct smoke прошли.
- Граница сохранена: freshness evidence не считает slippage bps, route cost bps, не сортирует venues и не включает route selection/execution.

## Обновление 2026-06-18 — Perp DEX direct availability summary v0

- Backend direct venue endpoints Hyperliquid, dYdX, Lighter, Aster и GMX получили `availability_summary`: rows, requested/matched/missing symbols, market/provider status counts, depth diagnostics availability, read-only/execution/ranking/production-signal flags и `safe_use`.
- Provider failures теперь классифицируются в machine-readable `provider_error_class`: `timeout`, `rate_limit`, `empty_response`, `schema_drift`, `unavailable_endpoint`, `provider_unavailable`, `provider_http_error`. Error path остаётся HTTP `502`, но `detail` содержит compact summary без raw payload.
- `scripts/perp-dex-direct-smoke.sh` читает backend `availability_summary`, печатает compact summary, считает provider error classes и проверяет, что direct snapshots остаются read-only без ranking/production signal/execution.
- Проверка: `backend` targeted pytest по Perp DEX direct availability, provider clients и policy contract прошёл; `compileall` для изменённых backend файлов прошёл.
- Граница сохранена: summary и taxonomy являются observability layer, а не route ranking, route selection, numeric route cost bps, diagnostic carry bps или execution.

## Обновление 2026-06-18 — Perp DEX Source Status rollup v0

- Frontend `Perp DEX` получил панель `Perp DEX Source Status` в `overview` и `venues`: direct venues, GMX raw, CoinGlass enrichment, route policy/model contract и last release smoke сведены в compact read-only таблицу.
- Панель строится из уже загруженных `getLive*` snapshots и `route-constraints`/`route-model`; новых provider calls, backend endpoints, БД-изменений и production signals не добавлено.
- Boundary сохранён: строки показывают rows/evidence/boundary/status, но не сортируют venues, не ранжируют маршруты, не считают numeric route cost bps и не включают execution.
- Проверка: `npm run build` в `frontend` прошёл; Browser QA на локальном `/perp-dex` с preview backend через SSH tunnel прошёл на desktop и mobile без runtime errors, console errors и page-level horizontal overflow.

## Обновление 2026-06-18 — v1.4.0 release runway и deploy diagnostics

- Docs follow-up по `v1.3.2` сохранён коммитом `60a7f0c`: зафиксированы `preview@d3de35e`, зелёный CI run `27744113125`, failed `Deploy Preview` run `27744161749` и успешный ручной preview deploy.
- GitHub `Deploy Preview` failure разобран через GitHub API/job page: обязательные `PREVIEW_*` secrets и fingerprint checks были настроены, но SSH port/login/app-dir/deploy attempts из GitHub runner были нестабильны. Ручной SSH deploy после run прошёл, поэтому причина классифицирована как transient SSH reachability, а не ошибка app deploy script.
- Deploy diagnostics усилены: deploy script печатает stage markers и failure snapshot, а GitHub preview/production workflows после failed deploy attempt пытаются собрать remote git/compose/logs snapshot или явно показывают SSH transport failure.
- Follow-up commit `b257cc8` прошёл GitHub CI run `27746664616` и `Deploy Preview` run `27746714283`; `/opt/deltagrid-preview` обновлён до `b257cc8`, `VERSION=1.3.2`.
- Добавлен `scripts/release-smoke.sh` для preview/prod release smoke: health/readiness/data-health/frontend, Perp DEX policy, direct venues и CoinGlass coverage.
- `scripts/release-preflight.sh` получил `RELEASE_TARGET`; проверка `RELEASE_BRANCH=preview RELEASE_TARGET=1.4.0-rc.1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh` проходит на текущей версии `1.3.2`.
- Production backup выполнен без изменения production checkout: script запущен из `/opt/deltagrid-preview` против production Compose project `deltagrid`, backup создан в `/opt/deltagrid/backups/deltagrid-v140-runway_20260618T081912Z.sql.gz`.
- Preview VPS release smoke прошёл на `BASE_URL=http://127.0.0.1:8011` и `FRONTEND_URL=http://127.0.0.1:3012`: `server-smoke`, `perp-dex-policy-smoke`, `perp-dex-direct-smoke`, `coinglass-perp-dex-coverage-smoke`.
- Browser QA через SSH tunnel прошёл для `/perp-dex?view=opportunities`, `/charts?symbol=BTC&interval=1m&range=24h`, `/data-health`, `/market-matrix`, `/arbitrage-scanner`, `/assets`; runtime errors и console errors не найдены. Публичный `preview.deltagrid.pro` всё ещё не резолвится, поэтому QA выполнен через tunnel.
- `PROD_*` GitHub secrets остаются ручным внешним blocker’ом для реального `Deploy Production`; checklist обновлён в `deploy/github-actions-secrets.md`.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps и numeric route cost bps не включались.

## Обновление 2026-06-18 — Perp DEX GMX live helper source review v0

- Backend `gmx_rate_mapping_review_v0` получил `live_helper_source_summary`: compact summary по live GMX `/markets/info` rate output fields, missing helper inputs, fixture cases, expectation ids и manual approval ids.
- Backend `gmx_rate_mapping_review_v0` получил `live_helper_source_checklist` для live rate output fields, nonzero-borrowing relation evidence, helper source fields presence, side-direction helper fields и manual review gate.
- Frontend `Perp DEX` получил панель `GMX Rate Live Helper Source Review`.
- Policy smoke compact contract получил `gmx_rate_live_helper_review_status`, `gmx_rate_live_helper_review_ids`, `gmx_rate_live_helper_review_statuses`, `gmx_rate_live_helper_missing_source_inputs` и `gmx_rate_live_helper_manual_approval_ids`.
- Граница не изменилась: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-18 — Perp DEX GMX carry-source evidence gate v0

- Backend `gmx_rate_mapping_review_v0` получил `carry_source_evidence_summary`: compact summary по evidence ids/types, related inputs, source inputs, fixture cases, decision checks и manual approval ids.
- Backend `gmx_rate_mapping_review_v0` получил `carry_source_evidence_checklist` для runtime inputs, side-aware fixture evidence, source helper field evidence, display-unit policy evidence и manual approval evidence.
- Frontend `Perp DEX` получил таблицы `GMX Rate Carry Evidence Summary` и `GMX Rate Carry Evidence Checklist`.
- Policy smoke compact contract получил `gmx_rate_carry_evidence_status`, `gmx_rate_carry_evidence_ids`, `gmx_rate_carry_evidence_statuses`, `gmx_rate_carry_evidence_types` и `gmx_rate_carry_evidence_manual_approval_ids`.
- Граница не изменилась: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-18 — Perp DEX GMX carry-readiness audit v0

- Backend `gmx_rate_mapping_review_v0` получил `carry_readiness_summary`: compact summary по carry inputs, required fixtures, decision checks и manual approval ids перед любым diagnostic carry bps.
- Backend `gmx_rate_mapping_review_v0` получил `carry_input_checklist` для `holding_period_hours`, `position_notional_usd`, `rate_sign_convention`, `source_helper_inputs` и `display_unit_decision`.
- Frontend `Perp DEX` получил таблицы `GMX Rate Carry Readiness Summary` и `GMX Rate Carry Input Checklist`.
- Policy smoke compact contract получил `gmx_rate_mapping_decision_manual_approval_ids`, `gmx_rate_carry_readiness_status`, `gmx_rate_carry_input_ids`, `gmx_rate_carry_input_statuses` и `gmx_rate_carry_manual_approval_ids`.
- Граница не изменилась: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-18 — Perp DEX GMX fixture/source hardening v0

- Backend `gmx_rate_mapping_review_v0` получил `side_aware_fixture_expectations` для `longsPayShorts`: long/short paying/receiving cases теперь перечислены явно до любого carry bps.
- Backend `gmx_rate_mapping_review_v0` получил `mapping_decision_checklist` с source helper inputs, fixture cases, expectation ids, review ids и manual approval ids перед первым diagnostic carry bps.
- Frontend `Perp DEX` получил таблицы `GMX Rate Side-aware Fixtures` и `GMX Rate Mapping Decision Checklist`; `GMX Rate Fixture Readiness` показывает expectation notes для `longsPayShorts`.
- Policy smoke compact contract получил `gmx_rate_fixture_statuses`, `gmx_rate_side_expectation_ids`, `gmx_rate_mapping_decision_check_ids` и `gmx_rate_mapping_decision_statuses`.
- Граница не изменилась: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-17 — Perp DEX GMX mapping evidence hardening v0

- Backend `gmx_rate_mapping_review_v0` получил `blocker_breakdown`, который группирует repeated blockers между source relation guardrail, live nonzero-borrowing mapping, source helper inputs и carry conversion boundary.
- Backend `gmx_rate_mapping_review_v0` получил `fixture_readiness_matrix` для GMX side-aware cases: source relation raw fields, nonzero borrowing, zero borrowing ambiguity, `longsPayShorts` direction и missing helper inputs.
- Frontend `Perp DEX` получил таблицы `GMX Rate Mapping Blockers` и `GMX Rate Fixture Readiness`.
- Policy smoke compact contract получил `gmx_rate_mapping_status`, `gmx_rate_mapping_blocker_ids` и `gmx_rate_fixture_case_ids`; backend regression tests проверяют новые rows.
- Граница не изменилась: carry conversion, numeric route cost bps, route ranking, route selection и execution не включались.

## Обновление 2026-06-17 — Perp DEX venue evidence and GMX mapping review v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `venue_evidence_status` для Lighter/Aster/GMX/cross-venue evidence gaps без route scoring.
- Backend route model получил `gmx_rate_mapping_review_v0`: отдельный read-only review поверх `rate_relation_summary`/`rate_source_fields_summary` без carry conversion.
- Frontend `Perp DEX` получил таблицы `Route Diagnostic Venue Evidence Status` и `GMX Rate Mapping Review`.
- Policy smoke и backend regression tests проверяют новые ids: `venue_evidence_status_ids` и `gmx_rate_mapping_review_ids`.
- README/ARCHITECTURE получили decision note: numeric route-cost model возможен только после source-backed fee/depth/carry/risk evidence, side-aware fixtures и отдельного решения; route ranking/execution не включались.

## Обновление 2026-06-17 — Perp DEX route-ready evidence checklist v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `route_ready_evidence_checklist`, который группирует pre-route-scoring evidence gates по fees, order intent, depth freshness, depth aggregation, carry semantics и risk limits.
- Frontend `Perp DEX` получил таблицу `Route Diagnostic Evidence Checklist` с fallback из source fields и depth policy checklist.
- Policy smoke и backend regression tests проверяют, что evidence checklist согласован с components/source fields/depth policy и сохраняет `may_estimate_cost_bps=false`, `may_rank_routes=false`, `may_submit_orders=false`.
- Compact smoke contract получил `route_ready_evidence_gate_ids` для preview/prod diff route-model observability.
- Граница не изменилась: evidence checklist не включает route cost bps, route ranking, route selection или execution.

## Обновление 2026-06-17 — Perp DEX diagnostic source input actions coverage v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `source_input_action_coverage`, который связывает sourced display fields с required route inputs и mapped next actions.
- Frontend `Perp DEX` получил таблицу `Route Diagnostic Source Input Actions` с fallback из `source_field_breakdown` и `next_action_breakdown`.
- Policy smoke и backend regression tests проверяют, что `source_input_action_coverage` согласован с source fields, required inputs и next actions.
- Compact smoke contract получил `source_input_action_fields`, а README фиксирует preview/prod compare пример с `depth_policy_ids` и `next_action_ids`.
- Граница не изменилась: source-input-action coverage не включает route cost bps, route ranking, route selection или execution.

## Обновление 2026-06-17 — Perp DEX diagnostic policy input breakdown v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `required_policy_input_breakdown`, который агрегирует required policy inputs из depth/staleness checklist по policy rows, components, venues, source endpoints и blockers.
- Frontend `Perp DEX` получил таблицу `Route Diagnostic Policy Inputs` с fallback из depth policy checklist, если backend summary недоступен.
- Policy smoke и backend regression tests проверяют, что `required_policy_input_breakdown` согласован с `depth_staleness_policy_checklist` и сохраняет `may_emit_slippage_bps=false`.
- Compact smoke contract получил `required_policy_input_ids` для preview/prod diff.
- Граница не изменилась: policy inputs не включают route cost bps, route ranking, route selection или execution.

## Обновление 2026-06-17 — Perp DEX diagnostic next actions breakdown v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `next_action_breakdown`, который группирует planning actions из required-input breakdown, readiness rollup и depth/staleness policy checklist.
- Frontend `Perp DEX` получил таблицу `Route Diagnostic Next Actions` с source count/types, required inputs, policy inputs, component ids, venues и safe-use boundary.
- Policy smoke и backend regression tests проверяют, что `next_action_breakdown` согласован с уже существующими summary layers и сохраняет `numeric_total_status=blocked`.
- Compact smoke contract получил `next_action_ids` для preview/prod diff.
- Граница не изменилась: planning actions не включают route cost bps, route ranking, route selection или execution.

## Обновление 2026-06-17 — Perp DEX diagnostic depth policy and smoke compare v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `depth_staleness_policy_checklist` для Lighter `orderBookOrders`, Aster `ticker/bookTicker` и Aster `fapi/v3/depth`.
- Checklist фиксирует required policy inputs: `depth_snapshot_timestamp`, `max_depth_age_ms`, `stale_depth_action`, `order_size_usd`, `side`, `depth_aggregation_policy`, `liquidity_cap`.
- Frontend `Perp DEX` получил таблицу `Route Diagnostic Depth/Staleness Policy` с fallback из `components`, если backend summary недоступен.
- Policy smoke теперь проверяет depth/staleness checklist и печатает compact `contract`; `COMPARE_BASE_URL` добавляет preview/prod diff summary, `FAIL_ON_DIFF=1` делает diff фейлом.
- Граница не изменилась: `may_emit_slippage_bps=false`, `numeric_total_status=blocked`, route cost bps, ranking, route selection и execution не включались.
- Проверка: `tests/test_perp_dex_policy.py`, `compileall app`, `bash -n scripts/perp-dex-policy-smoke.sh`, HTTP policy smoke, frontend `npm run build`, `npm audit --audit-level=high` и Browser QA проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic observability rollups v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `source_field_breakdown`: source fields агрегируются по components, venues, required inputs, display ids и blocked numeric ids.
- Backend `diagnostic_cost_estimate_v0.summary` получил `safe_use_breakdown`: safe-use boundaries сгруппированы по components, чтобы UI явно отделял display diagnostics от route signals.
- Backend `diagnostic_cost_estimate_v0.summary` получил `readiness_rollup`: compact fee/depth/carry/risk readiness показывает status, sourced counts, display ids, blocked numeric ids и next action.
- Frontend `Perp DEX` получил таблицы `Route Diagnostic Source Fields Breakdown`, `Route Diagnostic Safe Use Breakdown` и `Route Diagnostic Readiness Rollup` с fallback-группировкой из `components`.
- Policy smoke и backend regression tests проверяют consistency новых breakdown/rollup слоёв с component list.
- Граница не изменилась: rollups показывают observability/readiness, но не включают total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic required input breakdown v0

- Backend `diagnostic_cost_estimate_v0.components` получил `required_input_ids`, чтобы diagnostic components были связаны с обязательными входами route model.
- Backend `diagnostic_cost_estimate_v0.summary` получил `required_input_breakdown`: по каждому required input агрегируются component ids, venue ids, display ids, blocked numeric ids, sourced ids и next action.
- Frontend `Perp DEX` получил `Route Diagnostic Required Input Breakdown` с fallback-группировкой из `required_inputs` и `components`, если backend summary недоступен.
- Policy smoke и backend regression tests проверяют, что `required_input_breakdown` согласован с `components[*].required_input_ids`.
- Граница не изменилась: breakdown показывает coverage обязательных inputs, но не включает total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py`, `compileall app`, frontend `npm run build` и `npm audit --audit-level=high` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic blocker breakdown v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `blocker_breakdown`: каждый blocker из `components[*].blocked_by` агрегируется по component ids, venue ids, display ids и blocked numeric ids.
- Frontend `Perp DEX` получил `Route Diagnostic Blocker Breakdown` с fallback-группировкой из `components`, если backend summary недоступен.
- Policy smoke и backend regression tests проверяют, что `blocker_breakdown` согласован с component list и не теряет blockers.
- Граница не изменилась: breakdown показывает повторяющиеся причины блокировки, но не включает total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic venue breakdown v0

- Backend `diagnostic_cost_estimate_v0.summary` получил `venue_breakdown`: Lighter, Aster и cross-venue components теперь имеют отдельные counts/id-списки по display-only, blocked numeric и sourced fields.
- Frontend `Perp DEX` получил `Route Diagnostic Venue Breakdown` с fallback-группировкой из `components`, если backend summary недоступен.
- Policy smoke и backend regression tests проверяют, что `venue_breakdown` согласован с component list и не теряет blocked numeric ids.
- Граница не изменилась: breakdown показывает readiness по venue, но не включает total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic component summary contract v0

- `route-model.diagnostic_cost_estimate_v0` получил backend `summary`: количество компонентов, display-only ids, blocked numeric ids, sourced ids, `numeric_total_status=blocked` и boundary `component_readiness_only`.
- Frontend `Route Diagnostic Components Summary` теперь использует backend summary как основной контракт и сохраняет fallback на расчёт из `components`.
- Policy smoke и backend regression tests проверяют, что `summary` полностью согласован с `components` по counts и id-спискам.
- Граница не изменилась: summary остаётся observability/read-only контрактом; total route cost bps, ranking, route selection и execution не включались.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostic components summary v0

- Frontend `Perp DEX` получил `Route Diagnostic Components Summary`: summary по component count, display-only outputs, blocked numeric components, sourced fields и статусу total bps перед детальной таблицей `Route Cost Diagnostics v0`.
- `scripts/perp-dex-policy-smoke.sh` теперь проверяет `diagnostic_cost_estimate_v0.components`, включая обязательные ids, status, source fields, blocked-by причины и safe-use формулировки.
- Backend regression tests закрепляют структуру diagnostic components, чтобы future route-model правки не включили numeric total bps или не потеряли component-level blockers.
- Граница не изменилась: это observability layer поверх read-only route model; total route cost bps, ranking, route selection и execution не включались.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX route safety guardrails v0

- Frontend `Perp DEX` получил таблицу `Route Safety Guardrails`: она показывает верхнеуровневые safety-флаги expected vs actual перед любым route scoring.
- `scripts/perp-dex-policy-smoke.sh` теперь проверяет не только policy/model flags и blockers, но и структуру `required_inputs` плюс обязательные ключи `formula_skeleton`.
- Backend regression tests закрепляют полный набор formula skeleton keys и непустые formula strings.
- Граница не изменилась: route model остаётся read-only checklist/diagnostics, numeric cost bps, ranking, route selection и execution не включались.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX required inputs and direct smoke guardrails v0

- `scripts/perp-dex-direct-smoke.sh` теперь проверяет не только успешность direct venue endpoints и `execution_enabled=false`, но и `read_only=true`, а также отсутствие включённых `ranking_enabled` / `production_signal_enabled`, если эти flags присутствуют в response.
- Frontend `Perp DEX` получил таблицу `Route Required Inputs`, где обязательные route-model inputs вынесены отдельно от component readiness и blockers.
- Backend regression tests теперь проверяют, что каждый элемент `route-model.required_inputs` имеет `id`, `label` и `reason`.
- Граница не изменилась: required inputs остаются research checklist; route-level total cost bps, ranking, route selection и execution не включались.
- Проверка: `bash -n scripts/perp-dex-direct-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX policy smoke and output policy v0

- Добавлен reusable `scripts/perp-dex-policy-smoke.sh` для проверки `GET /api/v1/perp-dex/route-constraints` и `GET /api/v1/perp-dex/route-model` на preview/prod.
- Smoke закрепляет safety-инварианты: `read_only=true`, `execution_enabled=false`, route/model ranking выключен, `may_estimate_cost_bps=false`, `may_emit_numeric_total_bps=false`, `may_submit_orders=false`.
- Frontend `Perp DEX` получил `Route Output Policy`, где display-only outputs отделены от заблокированных production outputs.
- Frontend `Perp DEX` получил `Route Model Blockers`: model-level blockers теперь видны отдельной таблицей рядом с route-cost model и route policy.
- Backend regression tests теперь проверяют, что все route policy/model blockers структурированы через `missing_inputs`, `blocked_by` и `safe_use`.
- Граница не изменилась: численный route cost, route ranking, route selection и execution не включались.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## Обновление 2026-06-17 — Perp DEX diagnostics hardening v0

- Добавлен reusable `scripts/perp-dex-direct-smoke.sh` для проверки direct Perp DEX endpoints по Hyperliquid, dYdX, Lighter, Aster и GMX без raw payload и секретов.
- Frontend `Perp DEX` получил таблицу `Depth Diagnostics`: она показывает только display-only orderbook/depth diagnostics, включая best bid/ask, spread и top-depth summaries.
- Backend policy/model blockers расширены структурированными полями `missing_inputs`, `blocked_by` и `safe_use`, чтобы route-cost blockers были машинно-читаемыми и понятными в UI.
- Frontend `Perp DEX` получил `Route Blockers Matrix`, где явно видны scope, missing inputs, blocked-by причины, safe use и next action по route/ranking/execution blockers.
- Граница итерации не изменилась: route-level total cost bps, liquidity ranking, route selection и execution остаются выключены до account fee tier, order intent, order size/side, sourced depth aggregation, liquidity caps, stale-depth policy, carry horizon и risk checks.
- Проверка: `test_perp_dex_policy.py`, provider regression tests, `compileall app`, frontend `npm run build`, `npm audit --audit-level=high` и `bash -n scripts/perp-dex-direct-smoke.sh` проходят.

## Обновление 2026-06-17 — Aster depth ladder diagnostics v0

- Aster direct snapshot расширен public `GET /fapi/v3/depth` с `limit=20` для каждого выбранного USDT perpetual market.
- Нормализация отдаёт display-only depth ladder: best bid/ask, `top_of_book_spread_bps`, количество bid/ask levels и top-level depth summaries в base/USD.
- В `route-model` добавлен diagnostic component `aster_depth_ladder`, а Aster depth readiness стал `partial_ready_depth_ladder_display_only`.
- Граница не изменилась: slippage, route-cost total bps, liquidity ranking и execution остаются выключены до order size, side, aggregation policy, liquidity caps, stale-depth handling и risk boundary.

## Обновление 2026-06-17 — Lighter orderBookOrders depth diagnostics v0

- Lighter direct snapshot расширен public `orderBookOrders` endpoint с `limit=25` для каждого выбранного market.
- Нормализация отдаёт display-only top resting orders: best bid/ask, `top_of_book_spread_bps`, количество bid/ask orders и top-order depth summaries в base/USD.
- В `route-model` добавлен diagnostic component `lighter_top_order_depth`, а Lighter depth readiness стал `partial_ready_top_orders_only`.
- Граница не изменилась: slippage, route-cost total bps, liquidity ranking и execution остаются выключены до order size, side, aggregation policy, liquidity caps и risk boundary.

## Обновление 2026-06-17 — Diagnostic route-cost components v0

- `route-model` получил `diagnostic_cost_estimate_v0`: read-only список компонентной готовности по Lighter/Aster fees, Aster top-of-book spread, slippage/depth и carry.
- Aster теперь отдаёт `top_of_book_spread_bps` как display-only spread из `bid_price`/`ask_price`; это не depth curve, не price-impact model и не executable liquidity.
- Aster fee schedule добавлен только как published USDT-perp metadata: maker `0.0` bps, taker `4.0` bps; account tier, discounts, maker/taker side и order intent всё ещё обязательны перед numeric route cost.
- Lighter `maker_fee`/`taker_fee` остаются raw public fields с неподтверждёнными units для route-cost math.
- Frontend `Perp DEX` показывает `Route Cost Diagnostics v0`, но total cost bps, route ranking, carry conversion и execution остаются выключены.

## Обновление 2026-06-17 — Lighter/Aster cost semantics metadata v0

- Route policy/model расширены diagnostic-only metadata для Lighter и Aster перед любыми numeric route-cost estimates.
- Lighter: `maker_fee`/`taker_fee` признаны sourced display fields, но не route-ready fee estimate без account fee tier, maker/taker side и order intent.
- Aster: top-of-book из `ticker/bookTicker` признан sourced display field, но не depth curve и не slippage model; fee schedule/tier ещё не подключены.
- `Perp DEX` UI показывает `Source Semantics` в таблице `Route Model Venue Inputs`, чтобы partial readiness не выглядела как production route input.
- Граница итерации: route ranking, numeric cost bps, carry conversion и execution остаются выключены.

## Обновление 2026-06-17 — Aster direct Perp DEX snapshot v0

- После live CoinGlass coverage hints `Lighter`/`Aster` выполнен следующий безопасный шаг: Aster official API review и минимальный direct adapter v0.
- Официальная документация Aster фиксирует Futures API и market-data endpoints; live проверка показала, что `fapi3.asterdex.com` сейчас отвечает `403` из текущей сети, а публичный `https://fapi.asterdex.com/fapi/v1` отдаёт `exchangeInfo`, `premiumIndex`, `ticker/24hr`, `openInterest` и `ticker/bookTicker` для `BTCUSDT/ETHUSDT/SOLUSDT`.
- Добавлен read-only endpoint `GET /api/v1/perp-dex/venues/aster/markets?symbols=BTC,ETH,SOL`.
- Aster rows нормализуются в общий Perp DEX market shape: mark/index/mid price, funding rate, OI USD estimate, 24h base/quote volume, trades, top-of-book, tick/step size, min notional и exchange metadata.
- Граница итерации: Aster не включён в route/liquidity ranking, fee tier assumptions не добавлены, depth/slippage/carry-cost semantics не используются для production signal, execution остаётся выключенным.

## Обновление 2026-06-17 — Lighter direct Perp DEX snapshot v0

- Live CoinGlass Perp DEX coverage smoke по `BTC,ETH,SOL` и `Aster,Lighter,EdgeX,Drift` вернул `6` rows, `2` venues with matches и candidate hints `Lighter`, `Aster`.
- По результату coverage выбран следующий direct adapter: `Lighter`, потому что публичные API `orderBooks`, `orderBookDetails` и `funding-rates` доступны без auth и дают market details/funding/OI/volume для core symbols.
- Добавлен read-only endpoint `GET /api/v1/perp-dex/venues/lighter/markets?symbols=BTC,ETH,SOL`.
- Lighter rows нормализуются в общий Perp DEX market shape: last trade price как display price, funding rate, open interest USD estimate, 24h base/quote volume, trades, maker/taker fee, margin fractions, tick/step size.
- Live smoke Lighter endpoint вернул `3` rows для `BTC/ETH/SOL`; у всех есть price/funding/OI/volume/fees, `execution_enabled=false`.
- Граница итерации: Lighter не включён в route/liquidity ranking, orderbook depth/slippage/carry-cost semantics не используются для production signal; Aster теперь подключён отдельной следующей итерацией как read-only direct snapshot v0.

## Обновление 2026-06-17 — CoinGlass Perp DEX coverage smoke script v0

- Добавлен reusable smoke-скрипт `scripts/coinglass-perp-dex-coverage-smoke.sh` для проверки `GET /api/v1/perp-dex/venues/coinglass/markets` на preview/prod окружении.
- Скрипт печатает только compact coverage summary: status, requested symbols/exchanges, total rows, matched exchanges, candidate hints, field totals и per-exchange coverage; raw payload и секреты не выводятся.
- По умолчанию проверяются `BTC,ETH,SOL` и `Aster,Lighter,EdgeX,Drift`; параметры можно переопределить через `BASE_URL`, `SYMBOLS`, `EXCHANGES`, `MIN_ROWS`, `MIN_MATCHED_EXCHANGES`, `ALLOW_UNAVAILABLE`, `PYTHON_BIN`.
- Query-параметры кодируются через Python, поэтому exchanges с пробелами вроде `ApeX Omni` можно проверять безопасно.
- Локально проверен синтаксис через `bash -n`; фактический live smoke нужно выполнить на preview/prod, где настроен CoinGlass API key.

## Обновление 2026-06-17 — CoinGlass Perp DEX coverage summary v0

- CoinGlass Perp DEX enrichment snapshot получил `coverage_summary`: requested symbols/exchanges, total rows, exchanges with matches, field totals и per-venue coverage.
- Per-venue coverage фиксирует `matched_rows`, `matched_symbols`, `missing_symbols`, `available_field_groups`, `field_coverage`, `route_input_status=not_route_input` и `next_action`.
- UI получил отдельную таблицу `CoinGlass Perp DEX Coverage`, чтобы видеть coverage hints для выбора следующего direct adapter без liquidity ranking.
- `coverage_summary.direct_adapter_candidate_hints` является только подсказкой по покрытию; production route scoring и execution остаются выключены.
- Локальный live smoke пропущен: `COINGLASS_API_KEY` / `COINGLASS_STANDARD_API_KEY` не настроен в текущей Windows env; секреты не выводились.

## Обновление 2026-06-17 — CoinGlass Perp DEX enrichment v0

- Добавлен read-only endpoint `GET /api/v1/perp-dex/venues/coinglass/markets` для CoinGlass futures `coins-markets` по DEX-like venues.
- Default research venues: `Aster`, `Lighter`, `EdgeX`, `Drift`; candidate list также фиксирует `Hyperliquid`, `dYdX`, `Paradex`, `Extended`, `ApeX Omni`.
- Endpoint возвращает third-party coin-level aggregate rows с `normalization_status=coinglass_coin_market_enrichment`, `ranking_enabled=false`, `production_signal_enabled=false`, `execution_enabled=false`.
- `Perp DEX` UI получил отдельную таблицу `CoinGlass Perp DEX Enrichment`; эти rows не смешиваются с direct venue snapshots и не считаются route/liquidity signal.
- `route-constraints` и `route-model` получили capability/blocker `coinglass_perp_dex_enrichment` / `coinglass_enrichment_not_route_input`.
- Граница итерации: это discovery/enrichment слой для выбора следующих direct adapters; historical persistence, route ranking, slippage/fee model и execution не включались.

## Обновление 2026-06-17 — GMX rate source fields guardrail v0

- `GmxClient` добавил diagnostic-only `rate_source_fields_status` и `rate_source_fields_summary`.
- Guardrail проверяет, есть ли в GMX `/markets/info` helper inputs для пересчёта official `MarketTicker` hourly rates: `fundingFactorPerSecond`, `borrowingFactorPerSecondForLongs`, `borrowingFactorPerSecondForShorts`, `longsPayShorts`.
- Live GMX `/markets/info` сейчас отдаёт ticker rate outputs, но не отдаёт эти helper inputs; статус `source_factor_fields_unavailable`.
- `route-model.gmx_rate_semantics.mapping_review` теперь явно фиксирует `source_inputs_required`, а `blocked_for_numeric_carry` включает blocker `live /markets/info source helper inputs unavailable`.
- Граница итерации: raw rates не конвертируются в percent, bps, annualized rate или carry cost; production route scoring, liquidity ranking и execution остаются выключены.

## Обновление 2026-06-17 — GMX rate relation summary v0

- `GmxClient` добавил snapshot-level `rate_relation_summary`: counts по side statuses, source relation matches, raw-sum relation matches, nonzero/zero borrowing sides и zero-borrowing ambiguity.
- GMX endpoint meta теперь возвращает `rate_relation_summary`, чтобы live-shape можно было проверять через API без ручного diagnostic script.
- Добавлен offline fixture `backend/tests/fixtures/gmx_rate_live_shape_fixture.json` для observed pattern: nonzero-borrowing side совпадает с `funding+borrowing`, zero-borrowing side остаётся ambiguous.
- `route-model.gmx_rate_semantics` получил `mapping_review` со статусом `source_vs_live_mapping_unresolved`; это фиксирует разрыв между official source relation и live `/markets/info` observation.
- Граница итерации: carry conversion, bps/percent/annualized display, route scoring, liquidity ranking и execution не включались.

## Обновление 2026-06-17 — GMX rate relation guardrail v2

- `GmxClient` уточнил diagnostic-only классификацию GMX raw rate relation: если `borrowingRate=0`, side помечается как `net_equals_funding_with_zero_borrowing`, потому `funding-borrowing` и `funding+borrowing` дают одинаковый `netRate`.
- Side diagnostics теперь явно возвращает `source_relation_matches`, `raw_sum_relation_matches`, `borrowing_is_zero` и `zero_borrowing_relation_ambiguous`.
- Live GMX smoke по `BTC/ETH/SOL` вернул `9` rows и `rate_semantics_status=raw_rate_relation_plus_with_zero_borrowing`: `9` nonzero-borrowing sides совпали с `netRate=fundingRate+borrowingRate`, `9` zero-borrowing sides остались ambiguous.
- `route-model.gmx_rate_semantics` и `route-constraints` обновлены так, чтобы blocker был про live `/markets/info` nonzero-borrowing mapping review, а не про готовую альтернативную формулу.
- Граница итерации не изменилась: raw rates не конвертируются в percent, bps, annualized rate или carry cost; production route scoring, liquidity ranking и execution остаются выключены.

## Обновление 2026-06-16 — GMX rate relation guardrail v1

- `GmxClient` теперь диагностически проверяет GMX raw rate relation через exact integer arithmetic, чтобы не получать ложные deltas от `Decimal` context precision.
- GMX rows и endpoint meta получили `rate_semantics_status`; успешная relation-проверка помечается как `hourly_rate_relation_confirmed`.
- Добавлен offline fixture `backend/tests/fixtures/gmx_rate_fixture.json`, который работает как guardrail для ожидаемой source relation без live HTTP-вызова к GMX.
- `route-constraints` получил capability `gmx_rate_relation_fixtures=partial_ready`, а `route-model.gmx_rate_semantics` теперь `guardrail_metadata_only`.
- Предыдущий live GMX smoke по `BTC/ETH/SOL` вернул `9` rows и `rate_semantics_status=raw_rate_relation_mixed`; обновление v2 выше уточняет, что zero-borrowing sides были ambiguous, а nonzero-borrowing sides совпали с `netRate=fundingRate+borrowingRate`.
- Граница итерации: raw rates всё ещё не конвертируются в percent, bps, annualized rate или carry cost; нужны live mixed relation review, side-aware funding sign fixtures, `holding_period_hours`, `position_notional_usd` и sourced fee/depth/carry inputs.

## Обновление 2026-06-16 — GMX rate semantics metadata v0

- `GET /api/v1/perp-dex/route-model` получил блок `gmx_rate_semantics` со source-backed metadata по GMX `fundingRate*`, `borrowingRate*` и `netRate*`.
- По `gmx-interface` подтверждено: `MarketTicker` содержит rate fields, `getMarketTicker` считает их за период `1h`, а `netRateLong/Short = fundingRateLong/Short - borrowingRateLong/Short`.
- По `gmx-interface`/`gmx-synthetics` зафиксировано, что funding sign зависит от paying/receiving side через `longsPayShorts`, а borrowing fee требует side-specific factor, period и `sizeInUsd`.
- Это metadata-only слой: raw GMX rate fields не конвертируются в percent, bps или carry cost; нужны offline fixtures, side-aware sign tests, `holding_period_hours` и `position_notional_usd`.
- `route-constraints` получил capability `gmx_rate_semantics_metadata=partial_ready`; production route scoring остаётся заблокирован.

## Обновление 2026-06-16 — Perp DEX route model v0

- Добавлен `GET /api/v1/perp-dex/route-model`: статический read-only контракт для route-level fees/slippage/routing без внешних provider calls, без записи в PostgreSQL и без execution path.
- Model v0 фиксирует обязательные входы перед любым численным routing: fee schedule/tier, order side/size/notional, depth или price-impact model, carry horizon, sign convention, risk limits и execution boundary.
- Frontend `Perp DEX` показывает `Route Cost Model v0` и `Route Model Venue Inputs` как checklist/formula skeleton; numeric cost estimates, ranking и order submission остаются выключены.
- `route-constraints` получил capability `route_cost_model_v0=partial_ready`, но `route_level_pricing`, `multi_venue_liquidity_ranking` и `execution` остаются `blocked`.
- Граница итерации: GMX funding/borrowing/net rate semantics пока не нормализованы в carry cost, а venue fee/depth inputs не sourced; production routing signal не включался.

## Обновление 2026-06-16 — GMX OI/liquidity USD diagnostics v0

- `GmxClient` теперь масштабирует `openInterestLong/Short` и `availableLiquidityLong/Short` из GMX `/markets/info` в diagnostic-only строковые поля `open_interest_*_usd_diagnostic` и `available_liquidity_*_usd_diagnostic`.
- Масштабирование использует `1e30` USD decimals из official GMX interface/integration API semantics; значения не записываются в `open_interest_usd` и не участвуют в ranking.
- GMX snapshot и endpoint meta получили `diagnostic_usd_scale_status`.
- Route policy расширена capability `gmx_oi_liquidity_usd_diagnostics=partial_ready`; `multi_venue_liquidity_ranking`, route-level pricing и execution остаются заблокированы.
- Граница итерации: funding/borrowing/net rates пока остаются raw strings, потому route model должен отдельно описать период, знак и применение rates к размеру позиции.

## Обновление 2026-06-16 — GMX fixed-point source validation metadata v0

- `GET /api/v1/perp-dex/route-constraints` получил блок `gmx_formula_validation` с официальными source URLs, diagnostic-only scale notes и явным списком GMX fields, которые нельзя использовать как production liquidity/OI signal.
- Подтверждено и зафиксировано в policy: `poolAmountLong/Short` остаются token-unit diagnostics через decimals из `/tokens`, `Precision` factors используют `1e30`, а `openInterest` и `openInterestInTokens` в контрактах идут отдельными paths.
- `openInterest*`, `availableLiquidity*`, funding/borrowing/net rates всё ещё не конвертируются и не участвуют в ranking, пока `/markets/info` fields не будут сопоставлены с точными reader outputs и Decimal fixtures.
- Проверка: route constraints regression test обновлён для `gmx_formula_validation`.

## Обновление 2026-06-16 — GMX pool token amount diagnostics v0

- `GmxClient` теперь масштабирует GMX `poolAmountLong` и `poolAmountShort` в `pool_amount_long_token` / `pool_amount_short_token` через `Decimal` и decimals из GMX `/tokens`.
- GMX rows и snapshot получили `token_amount_scale_status`; endpoint meta также возвращает этот статус для быстрой диагностики.
- `Perp DEX` frontend показывает GMX mode как `Raw + Pool Units`, когда pool token amounts успешно масштабированы.
- Route policy расширена capability `gmx_pool_token_amount_diagnostics=partial_ready`.
- Граница итерации: `openInterest*`, `availableLiquidity*`, funding/borrowing/net rates и USD liquidity/OI всё ещё не конвертируются, пока GMX fixed-point formulas не подтверждены.
- Проверка: targeted GMX/policy tests `3 passed`; `compileall app` проходит.

## Обновление 2026-06-16 — Perp DEX route constraints policy v0

- Добавлен endpoint `GET /api/v1/perp-dex/route-constraints`, который возвращает read-only policy для текущей Perp DEX границы без внешних provider calls.
- Policy фиксирует статус `research_only`: direct market rows можно показывать, но liquidity ranking, route-level pricing и execution остаются заблокированы.
- В policy явно разделены normalized snapshots (`hyperliquid`, `dydx`) и raw snapshots (`gmx`), а blockers включают `gmx_scale_validation_required`, `fees_slippage_model_missing` и `execution_boundary`.
- `Perp DEX` frontend теперь показывает таблицу `Route & Execution Policy` поверх backend policy, чтобы route/execution blockers были видны в продукте.
- Проверка: route constraints test `1 passed`; полная targeted Perp DEX/data проверка должна включать `test_perp_dex_policy.py`.

## Обновление 2026-06-16 — GMX token decimals diagnostics v0

- `GmxClient` теперь читает GMX `/tokens` вместе с `/markets/info` и резолвит token metadata для `indexToken`, `longToken`, `shortToken`.
- GMX rows получили поля `index_token_symbol/decimals`, `long_token_symbol/decimals`, `short_token_symbol/decimals`, `scale_validation_status`, `scale_validation_reason`.
- Если decimals для index/long/short tokens найдены, row и snapshot получают `scale_validation_status=token_decimals_resolved`; до отдельного pool amount diagnostics GMX mode в UI отображался как `Raw + Decimals`.
- `open_interest_usd`, liquidity и GMX funding всё ещё не нормализуются: fixed-point formulas требуют отдельной валидации перед production liquidity/OI signal.
- Route policy обновлена: `gmx_token_decimals_diagnostics` теперь `partial_ready`, а blocker остаётся на raw fixed-point formula validation.
- Проверка: GMX/policy targeted tests `3 passed`, live smoke GMX вернул `9` rows для `BTC/ETH/SOL` со `scale_validation_status=token_decimals_resolved`.

## Обновление 2026-06-16 — GMX Perp DEX raw market snapshot v0

- Добавлен read-only `GmxClient` для GMX public REST `GET /markets/info` на Arbitrum.
- Открыт endpoint `GET /api/v1/perp-dex/venues/gmx/markets?symbols=BTC,ETH,SOL`; он делает live external provider call, но не пишет в PostgreSQL и не включает execution.
- Endpoint возвращает GMX market rows со статусом `partial` и `normalization_status=raw_fixed_point`; raw `openInterest*`, `availableLiquidity*`, `poolAmount*`, `fundingRate*`, `borrowingRate*`, `netRate*` сохраняются как strings без пересчёта в USD/percent.
- `Perp DEX` frontend теперь показывает GMX rows как `Raw` рядом с normalized Hyperliquid/dYdX snapshots; KPI считает normalized live venues отдельно, чтобы raw GMX не выглядел как production liquidity signal.
- Граница итерации: route-level fees/slippage/routing, execution, историзация DEX snapshots и нормализация GMX fixed-point/token-unit полей не подключались.
- Проверка: GMX targeted tests `2 passed`, live smoke GMX вернул `9` raw rows для `BTC/ETH/SOL`.

## Обновление 2026-06-16 — Hyperliquid Perp DEX live snapshot v0

- Добавлен read-only `HyperliquidClient` для public `POST /info` с `type=metaAndAssetCtxs`.
- Открыт endpoint `GET /api/v1/perp-dex/venues/hyperliquid/markets?symbols=BTC,ETH,SOL`; он делает live external provider call, но не пишет в PostgreSQL и не включает execution.
- Endpoint возвращает mark/mid/oracle price, funding, open interest, 24h volume, premium, impact prices, leverage metadata и флаги `read_only=true`, `execution_enabled=false`.
- `Perp DEX` frontend теперь показывает Hyperliquid live snapshot при доступности backend/provider; dYdX/GMX остаются pending.
- Граница итерации: fees/slippage/routing, multi-DEX liquidity model, execution и историзация Hyperliquid snapshots не подключались.
- Проверка: backend targeted tests `23 passed`, `compileall app` проходит, frontend `npm run build` проходит.

## Обновление 2026-06-16 — dYdX Perp DEX live snapshot v0

- Добавлен read-only `DydxClient` для dYdX v4 Indexer `GET /perpetualMarkets`.
- Открыт endpoint `GET /api/v1/perp-dex/venues/dydx/markets?symbols=BTC,ETH,SOL`; он делает live external provider call, но не пишет в PostgreSQL и не включает execution.
- Endpoint возвращает oracle price как mark proxy, 24h price change, funding, open interest, 24h volume, trades, margin fractions, tick/step size, leverage estimate и флаги `read_only=true`, `execution_enabled=false`.
- `Perp DEX` frontend теперь объединяет Hyperliquid и dYdX read-only live snapshots в одной таблице direct Perp DEX venues; GMX остаётся pending.
- Граница итерации: fees/slippage/routing, execution и историзация dYdX snapshots не подключались.
- Проверка: backend targeted tests `25 passed`, `compileall app` проходит, frontend `npm run build` проходит, live smoke dYdX вернул `BTC/ETH/SOL`.

## Обновление 2026-06-16 — Data promotion blocker resolution

- `GET /api/v1/data/provider-inventory` расширен resolution-полями для blocker rows: `resolution_strategy`, `historical_backfill_supported`, `minimum_collection_window_hours`, `resolution_action`, `resolution_reason`.
- В summary добавлены `coverage_blockers_by_resolution_strategy`, `freshness_blockers_by_resolution_strategy`, `promotion_blockers_by_resolution_strategy`.
- Для текущего MVP ingestion path `open_interest`, `basis_premium` и `spot_perp_price` классифицируются как `snapshot_accumulation_required`: эти потоки пишутся как snapshots, поэтому один запуск `--lookback-hours 168` не создаёт честную 7d историю.
- `ohlcv`, `funding_rates`, `long_short_ratio` остаются `history_backfill_supported`; `liquidations` закрываются через `provider_sync_required`, потому sparse coverage может подтверждаться свежим успешным sync-run.
- Regression tests обновлены: chart-ready candidate с partial `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot` проверяет `snapshot_accumulation_required`.
- Вывод для pipeline: `HYPE/XRP/DOGE/ADA/LINK` остаются в chart/asset режиме до 7d накопления snapshot-стримов или до подключения отдельного historical source для OI/basis/spot-perp.

## Обновление 2026-06-16 — Production auto-deploy preflight

- Проверены ветки и релиз: `origin/main` находится на `0716f6a`, `origin/preview` на `bc342ae`, деревья `main` и `preview` совпадают, annotated tag `v1.3.1` указывает на commit `0716f6a`.
- `Deploy Production` hardening присутствует в `main`: workflow проверяет наличие `PROD_*`, fingerprint deploy key, ожидаемые значения `2.25.143.143`, `root`, `/opt/deltagrid`, SSH login, app dir и затем запускает `scripts/deploy-compose-stack.sh`.
- GitHub Actions run `27619159104` для `main@0716f6a` завершился `success`, но это был safe-skip: шаги `Production secret ... missing` прошли для `SSH_HOST`, `SSH_USER`, `SSH_KEY`, `APP_DIR`, а `Deploy production` был skipped.
- Локальный deploy key `outputs/deploy-keys/github-actions-deltagrid-deploy` существует, игнорируется через `outputs/`, fingerprint совпадает с workflow: `SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg`.
- Read-only SSH preflight к `root@2.25.143.143` прошёл: `/opt/deltagrid` на `main@0716f6a`, backend/frontend/PostgreSQL healthy, `BASE_URL=http://127.0.0.1:8000 FRONTEND_URL=http://127.0.0.1:3001 sh scripts/server-smoke.sh` прошёл.
- На сервере есть untracked backup `.env.production.bak.20260605_020340`; он не влияет на deploy contract и не трогался.
- В текущей среде нет `gh` CLI и `GH_*/GITHUB_*` токена, поэтому repository secrets нельзя безопасно записать автоматически из терминала.
- В `Deploy Production` добавлен безопасный ручной запуск `workflow_dispatch` только для ветки `main`, чтобы после настройки `PROD_*` проверить deploy без пустого push.
- Подготовлен `Production Healthcheck` workflow: scheduled/manual GitHub Actions проверяет public `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend.
- Добавлен reusable `scripts/backup-postgres.sh` для PostgreSQL `pg_dump` через Docker Compose; production default читает `.env.production` и пишет compressed dump в `backups/`.
- Первый production backup текущей PostgreSQL БД выполнен вручную на сервере: `/opt/deltagrid/backups/deltagrid_20260616T132922Z.sql.gz`, `gzip -t` прошёл.
- `scripts/deploy-compose-stack.sh` теперь по умолчанию делает backup перед `BRANCH=main` deploy в `backups/deploy/`; для preview backup включается только явно через `BACKUP_BEFORE_DEPLOY=1`.
- Следующий безопасный шаг: вручную добавить GitHub repository secrets `PROD_SSH_HOST=2.25.143.143`, `PROD_SSH_USER=root`, `PROD_APP_DIR=/opt/deltagrid`, `PROD_SSH_KEY=<private deploy key>`, затем запустить `Actions -> Deploy Production -> Run workflow -> Branch: main` и проверить, что `Deploy production` больше не skipped. После доставки backup-скрипта на сервер следующий backup нужно выполнить уже через `scripts/backup-postgres.sh`.

## Обновление 2026-06-16 — Policy gate для chart-ready candidates

- Добавлен `scripts/release-preflight.sh` для подготовки `v1.3.1`: проверяет `VERSION`, frontend package version, lockfile root version, ожидаемую ветку и чистоту git-дерева.
- Версия поднята до `1.3.1` в `VERSION`, `frontend/package.json` и `frontend/package-lock.json`.
- В provider inventory добавлена summary-разбивка blocker'ов по stream: `coverage_blockers_by_stream`, `freshness_blockers_by_stream`, `promotion_blockers_by_stream`.
- Для текущего candidate gate это позволяет сразу увидеть, что full promotion блокируют partial `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot`, без ручного разбора всех per-symbol rows.
- В provider inventory зафиксировано разделение двух gate: `chart_ready_candidates` подходят только для preview `/charts` и `/assets`, а `promotion_candidates` относятся к full analytics universe.
- `promotion_candidate` теперь требует `complete_history`; статус `core_perp_ready` больше не считается full promotion, если `open_interest`, `basis_premium` или `spot_perp_price` остаются partial.
- В `policy.gates` добавлено машинно-читаемое описание правил для `chart_ready` и `promotion_candidate`, чтобы API сам объяснял, почему symbol можно смотреть на графиках, но нельзя продвигать в полный analytics universe.
- Добавлен regression test для chart-ready candidate с полной 7d OHLCV/funding/long-short coverage и partial snapshot/enrichment streams.
- После push CI выявил свежий high advisory `form-data@4.0.5` во frontend lockfile; выполнен `npm audit fix` без `--force`, lockfile обновлён до `form-data@4.0.6`, `npm audit --audit-level=high` и `npm run build` локально проходят.
- Следующий безопасный шаг: отдельно решить, нужно ли добирать 7d snapshot/enrichment историю для full promotion или оставить candidates в chart/asset режиме до следующего набора data requirements.

## Обновление 2026-06-15 — OKX rate-limit retry для preview cron

- Первый реальный scheduled preview core cron после установки split cron подтвердил, что один split не полностью закрывает проблему: OKX `long_short_ratio` для `SOL` вернул HTTP `429`, sync завершился `errors=1`.
- Причина на уровне кода: `resp.raise_for_status()` поднимал `httpx.HTTPStatusError`, который не попадал в существующий `RetryPolicy`; поэтому transient `429` превращался в `partial` run без retry.
- `OkxAdapter` теперь переводит HTTP `429` и OKX rate-limit payload в `RateLimitExceeded`; этот тип уже поддержан общим retry/backoff.
- OKX default pacing в `GlobalRateLimiter` снижен до `capacity=5`, `refill_rate=2 req/sec`, чтобы cron-path меньше давил на публичные derived endpoints.
- Добавлен regression test на классификацию OKX HTTP `429`; локально из `backend` прошёл `backend\venv\Scripts\python.exe -m pytest tests\test_okx_adapter.py` (`6 passed`), также прошли `py_compile` и `git diff --check`.
- CI `27539771597` и `Deploy Preview` `27539817178` завершились успешно; `/opt/deltagrid-preview` обновился до `725387d`, контейнеры preview healthy.
- Контрольный scheduled core cron в `2026-06-15 10:30 UTC` подтвердил fix: OKX вернул `429` на `SOL long_short_ratio`, adapter сделал retry, повторный запрос вернул `200 OK`, итог cron-run `fetched=462`, `inserted=461`, `errors=0`.
- Финальный preview `/api/v1/data/health`: cron diagnostics `healthy`, latest `okx/long_short_ratio` `completed`, `recent_error_classes.rate_limit=2` остаётся только как 24h история старых partial-run до фикса.

## Обновление 2026-06-15 — Preview market sync cron path

- Причина stale/degraded freshness на preview: регулярный host cron был установлен только для production `/opt/deltagrid` и синкал `BTC/ETH/SOL`; отдельного `/etc/cron.d/deltagrid-preview-market-sync` не было.
- `scripts/install-market-sync-cron.sh` обновлён: cron-команда теперь может явно пробрасывать `ENV_FILE`, `COMPOSE_FILE` и `COMPOSE_PROJECT_NAME`.
- Для preview зафиксирован безопасный split contract: отдельный cron/log для core symbols и отдельный cron/log для candidates со сдвигом минут, чтобы снизить риск OKX `429` на derived streams.
- Production cron не менялся и не переустанавливался в рамках кодовой правки.
- На preview VPS установлены `/etc/cron.d/deltagrid-preview-market-sync-core` и `/etc/cron.d/deltagrid-preview-market-sync-candidates`; production `/etc/cron.d/deltagrid-market-sync` остался прежним.
- Ручной preview sync по split-path прошёл `errors=0` для core и `errors=0` для candidates. Provider inventory после проверки: `chart_ready_candidates=5`, `promotion_candidates=0`, `coverage_blockers=15`, `freshness_blockers=5`, `promotion_blockers=20`.
- Оставшийся freshness blocker у candidates — `funding_rates:8h:stale`; full promotion по-прежнему блокируют 15 coverage blockers по `open_interest`, `basis_premium`, `spot_perp_price`.

## Обновление 2026-06-15 — Promotion blocker diagnostics

- Provider inventory теперь возвращает явные blocker-поля для full analytics promotion: `coverage_blockers_7d`, `freshness_blockers` и объединённый `promotion_blockers` на уровне каждого symbol.
- В `summary` добавлены счётчики `coverage_blockers`, `freshness_blockers` и `promotion_blockers`, чтобы видеть масштаб причин блокировки без ручного разбора coverage/freshness rows.
- Диагностика использует только persisted data из уже рассчитанных coverage/freshness reports и не вызывает внешние provider API.
- Regression tests обновлены для symbol без coverage и fresh-but-partial candidate; локально через `backend/venv` пройдено `20 passed`.
- Статус full promotion не менялся: `HYPE/XRP/DOGE/ADA/LINK` остаются preview chart/asset candidates, а следующий продуктовый выбор — закрывать partial `open_interest`, `basis_premium`, `spot_perp_price` или формально утвердить разделение `chart_ready` и full analytics universe.

## Обновление 2026-06-15 — Candidate gate diagnostics batch

- Provider inventory получил additive-поля `chart_ready_candidates` в `summary` и `policy`, чтобы не смешивать chart/asset readiness с full analytics promotion.
- `/charts` и `/assets` теперь показывают компактный scope выбранного актива: `Core` или `Preview Candidate`.
- Добавлен `scripts/preview-candidate-smoke.sh` для ручной проверки preview candidate paths и core-only границы.
- Скрипт проверен против текущего preview VPS: candidate charts/assets и 7d OHLCV windows прошли, `/market-matrix`, `/arbitrage-scanner`, `/perp-dex` остались core-only.
- Локально: `python -m compileall backend\app` и `npm run build` прошли; локальный `pytest` недоступен в Windows-сессии из-за отсутствующего пакета `pytest`, финальный backend test прогон должен пройти в GitHub CI.

## Обновление 2026-06-15 — Deploy SSH diagnostics follow-up

- Docs commit `e8ddb1f` прошёл CI, но `Deploy Preview` run `27533723576` упал на диагностическом шаге `Test preview SSH login`; deploy step не дошёл до выполнения.
- Preview VPS в этот момент оставался healthy, локальный SSH к `root@2.25.143.143` проходил, `/opt/deltagrid-preview` оставался на рабочем commit `57e743a`.
- `deploy-preview.yml` и `deploy-production.yml` обновлены: `Test SSH login` и `Check app directory` теперь warning-only diagnostics, а реальным gate остаётся deploy step.
- Deploy step теперь делает 3 попытки вместо 2 и использует нарастающую паузу между попытками.

## Обновление 2026-06-15 — Preview chart candidates scope

- В preview frontend разделены `CORE_SYMBOLS=BTC/ETH/SOL` и `CANDIDATE_SYMBOLS=HYPE/XRP/DOGE/ADA/LINK`.
- `/charts` и `/assets` теперь допускают candidate symbols, чтобы смотреть 7d OHLCV и asset deep dive на preview без изменения production.
- `Market Matrix`, `Arbitrage Scanner` и `Perp DEX` оставлены scoped к `BTC/ETH/SOL`, потому текущий strict gate для full promotion показывает `promotion_candidates=0`, `ready_for_ui_review=0`, `history_completion_required=5`.
- Причина блокировки full promotion: у всех 5 candidates есть `chart_ready=true`, но 7d history остаётся partial для snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- CI/CD проверен: commit `57e743a`, CI `success`, `Deploy Preview` run `27533404025` `success`, `/opt/deltagrid-preview` на `57e743a`, backend/frontend/PostgreSQL healthy.
- Smoke-check preview: `/charts?symbol=HYPE&interval=1m&range=7d`, `/assets?symbol=ADA`, `/market-matrix`, `/arbitrage-scanner`, `/perp-dex` возвращают HTTP `200`; candidates видны только в chart/asset paths.
- Следующий шаг: закрыть policy/history gap для `open_interest`, `basis_premium`, `spot_perp_price` или явно утвердить правило, что chart-ready candidates можно держать отдельно от full analytics universe.

## Обновление 2026-06-15 — Preview deploy SSH hardening

- Последний flaky `Deploy Preview` падал на шаге `Test preview SSH login`, хотя preview stack на VPS оставался healthy.
- В `deploy-preview.yml` и `deploy-production.yml` добавлены более строгие SSH options, явные `timeout` и controlled retries для login, app-dir check и deploy.
- GitHub Actions проверка: CI commit `4c3dec0` прошёл успешно, `Deploy Preview` run `27532247102` завершился `success`.
- `/opt/deltagrid-preview` автоматически обновился до `4c3dec0`; backend/frontend/PostgreSQL healthy.
- Следующий шаг по продукту закрыт частично и безопасно: `HYPE/XRP/DOGE/ADA/LINK` включены как preview chart/asset candidates, full analytics universe promotion ждёт закрытия history gate.

## Обновление 2026-06-15 — 72h/7d preview backfill первой группы

- 72h backfill `HYPE/XRP/DOGE/ADA/LINK` на preview завершён: `fetched=27065`, `inserted=26902`, `errors=0`.
- 7d backfill той же группы завершён: `fetched=63125`, `inserted=62858`, `errors=0`.
- OHLCV gaps по `1m/5m/1h` для всех 5 symbols равны `0`; chart window проверен: `HYPE 1m 7d = 10080` свечей, `LINK 5m 7d = 2016` свечей.
- 7d coverage: `covered=30`, `partial=15`, `missing=0`; partial остаётся только у snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Для chart path группа готова: OHLCV gaps `0`, `HYPE 1m 7d = 10080` свечей, `LINK 5m 7d = 2016` свечей.
- Full promotion gate при повторной проверке показывает `history_completion_required=5` из-за partial `open_interest`, `basis_premium`, `spot_perp_price`; поэтому candidates включены только в `/charts` и `/assets`.

## Обновление 2026-06-15 — Candidate freshness scope

- `/api/v1/data/provider-inventory` теперь считает freshness по запрошенным candidate symbols и явно возвращает `scope.freshness_scope=requested_symbols`.
- `/api/v1/data/health` не расширялся и остаётся production SLA snapshot для текущего UI universe `BTC/ETH/SOL`.
- Preview deploy проверен на `HYPE/XRP/DOGE/ADA/LINK`: `freshness_tracking_required=0`, все 5 symbols имеют `freshness.worst_status=fresh`.
- По readiness все 5 symbols пока остаются `history_completion_required`, потому 7d coverage ещё partial.
- Следующий шаг: выполнить 72h/7d preview backfill первой группы и проверить gaps/coverage перед UI universe expansion.

## Обновление 2026-06-15 — Alias expansion и 24h preview dry-run

- `SymbolMapper.seed_defaults()` стал идемпотентным и расширен aliases для `HYPE/XRP/DOGE/ADA/LINK`.
- Preview DB засеяна aliases; OKX/CoinGlass/CoinGecko mappings проверены внутри backend container.
- 24h sync dry-run `HYPE/XRP/DOGE/ADA/LINK` на preview завершён без расширения UI: `fetched=9035`, `inserted=8986`, `errors=0`.
- OHLCV gaps по `1m/5m/1h` для всех 5 symbols равны `0`.
- `/api/v1/data/coverage?symbols=HYPE,XRP,DOGE,ADA,LINK&exchange=okx&range=24h` показывает `covered=30`, `partial=15`, `missing=0`.
- До отдельного candidate freshness scope `/api/v1/data/provider-inventory` оставлял symbols вне promotion candidates с `next_action=freshness_tracking_required`, потому freshness SLA формально покрывал только `BTC/ETH/SOL`.
- Следующий шаг закрыт отдельной итерацией candidate freshness scope; далее нужен 72h/7d preview backfill и проверка gaps/coverage перед UI universe expansion.

## Обновление 2026-06-15 — Provider discovery v1

- Добавлен CLI `python -m app.adapters.data.discover_provider_universe` для read-only live discovery по OKX, CoinGlass, CoinGecko и legacy Binance.
- Preview/VPS discovery выполнен внутри `deltagrid-preview-backend`: OKX/CoinGlass/CoinGecko `healthy`, Binance legacy `blocked_http_451`.
- Все `20/20` candidate symbols получили `eligible_for_24h_sync_dry_run`.
- Discovery не пишет в PostgreSQL, не расширяет sync и не меняет UI.
- Следующий шаг: `SymbolMapper`/alias expansion plan для `HYPE/XRP/DOGE/ADA/LINK`, затем 24h sync dry-run на preview и проверка errors/gaps/coverage.

## Обновление 2026-06-15 — Provider inventory v0

- Добавлен `GET /api/v1/data/provider-inventory` для кандидатов на расширение universe за пределы `BTC/ETH/SOL`.
- Endpoint использует только persisted coverage/freshness и не вызывает OKX, CoinGlass, CoinGecko или legacy Binance.
- Default candidate set: `BTC/ETH/SOL/HYPE/XRP/DOGE/BNB/ADA/LINK/AVAX/SUI/TON/TRX/DOT/LTC/BCH/AAVE/UNI/APT/ARB`.
- Для каждого symbol возвращаются readiness status, `promotion_candidate`, `next_action`, coverage summaries и freshness tracking.
- Следующий шаг: внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper`, sync-конфига и UI selector'ов.

## Обновление 2026-06-14 — Release baseline и CI/CD

- Добавлены `VERSION=1.3.0` и `RELEASES.md`.
- Frontend package version поднят до `1.3.0`.
- Добавлены GitHub Actions workflows: `CI`, `Deploy Preview`, `Deploy Production`.
- Branch policy: `preview` — dev/staging, `main` — production.
- Deploy workflows используют SSH secrets и безопасно пропускают deploy, если secrets ещё не настроены.
- Production `/opt/deltagrid` переведён на clean `main`.
- Подготовлен preview stack contract: `/opt/deltagrid-preview`, `.env.preview`, Compose project `deltagrid-preview`, ports `8011/3012`.

## Обновление 2026-06-14 — Preview/dev stand

- На VPS поднят отдельный preview stack в `/opt/deltagrid-preview` из ветки `preview`.
- Preview использует отдельный `.env.preview`, Compose project `deltagrid-preview`, PostgreSQL volume `deltagrid-preview_postgres_data`, backend `127.0.0.1:8011`, frontend `127.0.0.1:3012`.
- Выполнен 7d OKX/CoinGlass/CoinGecko sync BTC/ETH/SOL в preview БД: `errors=0`, OHLCV gaps по логам `0`.
- Preview `/api/v1/data/health`: OKX/CoinGlass/CoinGecko `healthy`, freshness `24/0/24`, `core_perp_ready=3`, `chart_ready=3`.
- Preview пока не опубликован через DNS/Nginx; внешний доступ к `3012` не открыт.
- Подготовлены preview publication assets: `deploy/nginx/deltagrid-preview.conf.example`, `scripts/configure-preview-nginx-ssl.sh`, `deploy/dns/preview.deltagrid.pro.md`.
- Подготовлен чеклист GitHub Actions deploy secrets: `deploy/github-actions-secrets.md`; сами secrets ещё нужно добавить в GitHub.
- Dedicated SSH deploy key создан локально в `outputs/deploy-keys/github-actions-deltagrid-deploy`; public key добавлен на VPS, non-interactive login проверен.
- `main` и `preview` синхронизированы на ops commit `104502e`, чтобы default-branch GitHub Actions использовал актуальные deploy workflows. Production checkout `/opt/deltagrid` fast-forward обновлён без пересборки контейнеров; smoke-check прошёл.
- CI/CD probe `fdb08ec` подтвердил: preview CI проходит, `Deploy Preview` workflow запускается, но deploy делает safe-skip на шаге `Skip when preview secrets are not configured`. Значит GitHub secrets `PREVIEW_*` ещё отсутствуют или заполнены не полностью.
- Восстановлен отсутствующий `AGENTS.md` с проектными правилами для Codex/AI-агентов.

## Обновление 2026-06-14 — Production universe v1

- Добавлен `GET /api/v1/data/universe`: derived read-only policy view поверх coverage/freshness.
- `/api/v1/data/health` теперь возвращает блок `universe`, а `/data-health` показывает таблицу `Production Universe`.
- Статусы universe: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`.
- MVP1 policy: symbol попадает в primary UI universe только если chart-critical streams покрыты, freshness зелёный и нет missing tracked streams.
- Fix задеплоен на `deltagrid.pro`; production показывает `core_perp_ready=3`, `chart_ready=3`, `ui_universe=BTC/ETH/SOL`, `deferred_symbols=[]`.
- Partial enrichment streams для всех трёх symbols: `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot`; missing streams нет.
- Локальная проверка: backend `pytest` — `26 passed`; frontend `npm run build` проходит.

## Обновление 2026-06-14 — Coverage matrix

- Добавлен `GET /api/v1/data/coverage` для read-only инвентаризации покрытия истории по `symbol + exchange + stream + interval`.
- `/api/v1/data/health` теперь возвращает поле `coverage`, а `/data-health` показывает KPI `Coverage` и таблицу `Coverage Matrix`.
- Матрица считает OHLCV, funding, OI, long/short, liquidations, basis и `spot_perp_price`; для sparse `liquidations` учитывается свежий `coinglass/liquidations` sync-run.
- Fix задеплоен на `deltagrid.pro`; production `24h` coverage показывает `27/27`, `7d` coverage показывает `18 covered / 9 partial / 0 missing`.
- Partial `7d` coverage сейчас у `open_interest` и `basis/spot_perp_price`, поэтому production universe v1 нужно формировать с явным разделением complete-history и partial-history активов/потоков.
- Локальная проверка: backend `pytest` — `25 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## Обновление 2026-06-14 — Sparse liquidation freshness

- После ночи production health показал `freshness.summary={fresh:23, stale:1, degraded:0}`; stale был только `SOL / okx / liquidations / 1h`.
- Диагностика показала, что `coinglass/liquidations` sync свежий и `healthy`, а stale возник из-за отсутствия свежих SOL liquidation events, то есть это sparse event stream, а не сбой ingestion.
- Локально реализована правка: `liquidations` freshness учитывает свежесть последнего `coinglass/liquidations` sync-run; `/data-health` показывает `event age / sync age`.
- Fix задеплоен на `deltagrid.pro`; production `/api/v1/data/health` снова даёт `fresh=24/stale=0/degraded=0`, если sync свежий.

## Обновление 2026-06-14 — OHLCV window endpoint

- Добавлен и задеплоен `GET /api/v1/data/ohlcv/window` для Charts v0: один backend-запрос возвращает окно `2h/8h/24h/7d` по `1m/5m/1h`, anchored от последней доступной свечи.
- `/charts` переключён на новый endpoint, а старая постраничная сборка через `/data/ohlcv` оставлена fallback path.
- Production проверка: `/api/v1/data/ohlcv/window?...range=7d` отдаёт `10080/10080` строк, `/charts?symbol=BTC&interval=1m&range=7d` рендерит canvas и показывает `10,080` свечей.

## Обновление 2026-06-13 — Interactive Charts v0

- Локально реализован первый слой `/charts` на `lightweight-charts`: свечи OKX USDT Swap, volume histogram, crosshair OHLC/volume панель, pan/zoom/scroll, выбор символа, интервала и диапазона.
- Для `7d`/`1m` окно собирается постранично через существующий `/api/v1/data/ohlcv` без изменения backend API. Окно строится от последней доступной свечи в PostgreSQL.
- Browser QA через SSH tunnel к production backend подтвердил desktop `BTC 1m 7d` (`10,080` свечей) и mobile `ETH 5m 24h` (`288` свечей); мобильная ширина исправлена скрытием sidebar на малых viewport.
- Charts v0 задеплоен на `deltagrid.pro`; domain smoke и Browser QA прошли для desktop `BTC 1m 7d` и mobile `ETH 5m 24h`.
- Следующий безопасный шаг: решить, нужен ли отдельный backend window endpoint для более чистой пагинации, и отдельно спланировать upgrade `next` до patched версии.

## Обзор 2026-06-13

- Public smoke-check зелёный: `https://deltagrid.pro`, `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend отвечают.
- Серверные контейнеры healthy: backend, frontend и PostgreSQL работают через production compose stack.
- Host-level cron активен: `/etc/cron.d/deltagrid-market-sync` запускает `scripts/sync-market-data.sh` каждые 15 минут с `--lookback-hours 2`.
- Data-layer rows на момент аудита: `ohlcv=41000`, `funding_rates=2340`, `open_interest=4260`, `liquidations=1193`, `long_short_ratio=564`, `basis_premium=2271`, `provider_sync_runs=5260`.
- Свежие потоки: CoinGlass snapshots и CoinGecko basis обновлялись примерно за 12 минут до аудита; CoinGlass liquidations — примерно за 1 час.
- Stale потоки: Binance OHLCV/funding/OI/L/S по BTC/ETH/SOL застряли примерно на `2026-06-11 16:00–21:14 UTC`.
- Причина по логам cron: `https://fapi.binance.com` возвращает HTTP `451`, после чего circuit breaker открывается и остальные Binance-запросы завершаются partial.
- Локальная проверка текущего дерева: backend tests `19 passed`, `compileall app` проходит, frontend `npm run build` проходит с `BACKEND_INTERNAL_URL=https://deltagrid.pro`.
- Принятое решение: не ставить VPN/proxy на сервер; использовать OKX как primary CEX perp provider, CoinGlass/CoinGecko оставить enrichment/cross-check слоями, Binance оставить legacy/diagnostic.
- Реализация OKX primary локально: backend tests `19 passed`, frontend build проходит, local OKX sync smoke записал BTC 1m candles/OI/L/S без ошибок.
- Production deploy OKX primary выполнен: backend/frontend пересобраны на `deltagrid.pro`, контейнеры healthy, backup изменяемых файлов сохранён на сервере в `/tmp/deltagrid-okx-predeploy-20260612_233017.tgz`.
- Ручной OKX sync `BTC,ETH,SOL` за 24 часа завершился `fetched=5421`, `inserted=5439`, `errors=0`; cron-path без явного provider flag тоже завершился `errors=0` и пишет OKX endpoints, CoinGlass liquidations `OKX` и CoinGlass snapshots `OKX` в `/var/log/deltagrid-market-sync.log`.
- `/api/v1/data/health` после деплоя показывает `okx healthy`; production row counts: `ohlcv=46277`, `funding_rates=2373`, `open_interest=4299`, `liquidations=1288`, `long_short_ratio=636`, `basis_premium=2295`, `provider_sync_runs=5316`.
- `/api/v1/data/health` расширен полями `freshness`, `sync_health_by_type` и `sync_diagnostics`; `/data-health` показывает freshness SLA, cron-path и error classes без изменения старых полей ответа.
- Production deploy data quality gate выполнен на `deltagrid.pro`; backend/frontend пересобраны, контейнеры healthy, локальный и доменный `server-smoke.sh` проходят.
- Production `/api/v1/data/health` после backfill показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, cron-path `healthy`, OKX/CoinGlass/CoinGecko `healthy`, Binance `degraded` только как legacy/diagnostic из-за HTTP `451`.
- Первый host-level cron после деплоя и 7d backfill сработал в `2026-06-13 00:15 UTC` и завершился `fetched=465`, `inserted=460`, `errors=0`; финальный health после cron показывает `row_counts.ohlcv=77819` и `provider_sync_runs=5351`.
- 72h backfill BTC/ETH/SOL через OKX завершён `fetched=16239`, `inserted=16308`, `errors=0`; независимая SQL-проверка показала `4320/864/72` строк по `1m/5m/1h` на каждый символ и `gaps=0`.
- 7d backfill BTC/ETH/SOL через OKX завершён `fetched=37875`, `inserted=38103`, `errors=0`; независимая SQL-проверка показала `10080/2016/168` строк по `1m/5m/1h` на каждый символ и `gaps=0`.

## MVP1 — ближайший рабочий план

- [x] P0: решить production path для CEX candles/funding/OI/L/S после Binance `451`: выбран OKX primary.
- [x] P0: добавить `OkxAdapter` и переключить sync/frontend defaults на `okx`.
- [x] P0: задеплоить OKX primary flow на `deltagrid.pro` и выполнить ручной sync `BTC,ETH,SOL`.
- [x] P0: выполнить контрольный 24h backfill BTC/ETH/SOL по `1m/5m/1h` через OKX и проверить `gaps=0` в sync-логах.
- [x] P0: добавить freshness SLA в `/api/v1/data/health` по потокам, символам и интервалам.
- [x] P0: разделить provider health по `sync_type`, чтобы отдельно видеть OHLCV, funding, OI, long/short, liquidations и basis.
- [x] P0: добавить cron/data-sync diagnostics в backend/API и `/data-health`.
- [x] P0: задеплоить data quality gate на production и проверить `/api/v1/data/health` через `deltagrid.pro`.
- [x] P1: расширить backfill до 72h/7d и проверить gaps перед interactive charts.
- [x] P1: после data quality gate перейти к `lightweight-charts` и собрать локальный Charts v0.
- [x] P1: задеплоить Charts v0 на production и проверить `/charts` через домен.
- [x] P1: оценить backend OHLCV window endpoint вместо клиентской постраничной сборки 7d/1m.
- [x] P1: задеплоить sparse liquidation freshness fix и проверить `/data-health`.
- [x] P1: задеплоить OHLCV window endpoint и переключение `/charts`.
- [x] P1: добавить coverage matrix для BTC/ETH/SOL по OHLCV/funding/OI/long-short/liquidations/basis/spot-perp.
- [x] P1: сформировать production universe v1 на основе coverage matrix.
- [x] P1: провести provider inventory v0 для расширения universe за пределы BTC/ETH/SOL через read-only persisted-data endpoint.
- [x] P1: провести внешний provider discovery по OKX/CoinGlass/CoinGecko/legacy Binance перед расширением `SymbolMapper` и sync universe.
- [x] P1: подготовить `SymbolMapper`/alias expansion plan для первой малой группы `HYPE/XRP/DOGE/ADA/LINK`.
- [x] P1: выполнить 24h sync dry-run первой малой группы на preview без расширения UI.
- [x] P1: расширить freshness SLA scope для первой малой группы или явно отделить candidate freshness от current UI universe freshness.
- [x] P1: выполнить 72h/7d preview backfill первой малой группы и проверить gaps/coverage перед UI universe expansion.
- [x] OPS/P1: стабилизировать preview deploy SSH retry path и подтвердить успешный `Deploy Preview` после CI.
- [x] P1: включить первую малую группу как preview chart/asset candidates и проверить HTTP smoke `/charts`/`/assets` на preview.
- [x] P1: закрыть `history_completion_required=5` для `HYPE/XRP/DOGE/ADA/LINK` или явно зафиксировать policy-разделение `chart_ready` и full analytics universe promotion.
- [ ] P1: отдельно оценить backfill/ingestion для 7d `open_interest`, `basis_premium`, `spot_perp_price`, если решим продвигать candidates в full analytics universe.
- [ ] P2: backtest engine и scheduler делать только после стабилизации исторических рядов.

## PostgreSQL MVP Summary — 2026-06-05

- [x] PostgreSQL стал основным runtime persistence для backend.
- [x] Добавлен sync driver `psycopg[binary]`; async слой использует `asyncpg`.
- [x] Нормализованы DB URL для sync engine, async engine и Alembic.
- [x] `Base.metadata.create_all()` ограничен SQLite fallback для isolated tests.
- [x] Добавлена Alembic migration `3f0c2e5a7b91` для `backfill_jobs`.
- [x] Добавлена Alembic migration `7c1f2a8d9e34` для `BigInteger` timestamp-полей в data-layer/backtest.
- [x] `DataWriter` и `SymbolMapper` больше не создают production-схему вручную.
- [x] Docker Compose поднимает PostgreSQL 16 и запускает `alembic upgrade head` перед backend.
- [x] Обновлены инструкции запуска и архитектурная документация.
- [x] `DEBUG=false` блокирует слабые/dev secrets, пустой `VAULT_MASTER_KEY`, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS`.
- [x] `GET /api/v1/health/readiness` проверяет DB connectivity и соответствие Alembic revision source head.
- [x] Добавлены `.env.production.example`, `docker-compose.prod.yml` и `DEPLOYMENT.md`.
- [x] Frontend runtime proxy подготовлен к Docker deployment через `BACKEND_INTERNAL_URL`; WebSocket URL больше не привязан только к `127.0.0.1:8000`.
- [x] Docker build contexts очищены через `backend/.dockerignore` и `frontend/.dockerignore`.
- [x] Добавлены `deploy/nginx/deltagrid.conf.example` и `scripts/server-smoke.sh`.
- [x] Добавлены `scripts/server-preflight.sh` и `scripts/generate-production-env.sh`.
- [x] Deploy-шаблоны и документация привязаны к домену `deltagrid.pro`.
- [x] DNS Cloudflare активен: `deltagrid.pro` и `www.deltagrid.pro` проходят через Cloudflare edge к серверу `2.25.143.143`.
- [x] Серверный IP получен: `2.25.143.143`; SSH `22` открыт, HTTP `80` и HTTPS `443` пока закрыты.
- [x] Добавлены `scripts/bootstrap-ubuntu.sh`, `scripts/deploy-production.sh` и `deploy/dns/deltagrid.pro.md`.
- [x] Добавлен `scripts/configure-nginx-ssl.sh` для включения Nginx site и выпуска Let's Encrypt SSL.
- [x] SSH-доступ `root@2.25.143.143` по ключу подтверждён; production frontend port перенесён на `3001`, чтобы не трогать служебный процесс на `3000`.
- [x] DNS Cloudflare активирован: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`.
- [x] Реальный серверный rollout выполнен: `/opt/deltagrid`, `.env.production`, PostgreSQL, backend, frontend и Nginx.
- [x] HTTPS включён через Let's Encrypt; `https://deltagrid.pro` и `https://www.deltagrid.pro` отвечают.
- [x] Server smoke-check через HTTPS прошёл; основные frontend pages и API routes возвращают `200`.
- [x] Cloudflare proxy + SSL mode `Full (strict)` включены и проверены; WebSocket route проходит через Cloudflare.
- [x] Добавлена команда `python -m app.adapters.data.sync_market_data` и wrapper `scripts/sync-market-data.sh` для первичного заполнения data-layer.
- [x] Первый production sync Binance market data выполнен: `6837` rows inserted, `/api/v1/data/health` через домен показывает `binance healthy`.
- [x] Provider API keys добавлены в server `.env.production`; CoinGlass v4 health/funding endpoints работают через production-домен.
- [x] Sync-команда расширена до CoinGlass funding/OI snapshots и CoinGecko-derived `basis_premium`.
- [x] Sync-команда расширена до CoinGlass aggregated liquidation history с записью в таблицу `liquidations`.
- [x] Host-level cron `/etc/cron.d/deltagrid-market-sync` установлен; cron service активен.
- [x] `/api/v1/data/health` показывает `binance`, `coinglass` и `coingecko` healthy.
- [x] `Funding` читает persisted PostgreSQL funding rows и data health вместо mock fixture.
- [x] `/data-health` заменён с placeholder на live frontend screen.
- [x] Nested tabs в `Funding` и `Perp DEX` кликабельны через `view` query-param.
- [x] `Market Overview` читает live CoinGecko/CoinGlass/alternative.me backend endpoints вместо mock fixture.
- [x] `Assets` читает live SOL spot/funding/OHLCV и показывает pending-состояния вместо fake order book/liquidations.
- [x] Backend открыл read-only endpoints для `open_interest`, `long_short_ratio`, `basis_premium` и `liquidations`.
- [x] `/data/liquidations` теперь получает реальные агрегированные CoinGlass rows после production sync.
- [x] Production smoke после деплоя: `/api/v1/data/health` показывает `row_counts.liquidations=144`, `/api/v1/data/liquidations` отдаёт BTC long/short `value_usd`.
- [x] `Charts`, `Market Matrix` и `Arbitrage Scanner` читают live persisted data streams вместо mock fixture.
- [x] `Strategy Lab` больше не показывает fake PnL/trades; экран показывает readiness live inputs до реального backtest engine.

## Следующая итерация

- [x] Прогнать `alembic upgrade head` на PostgreSQL БД в Docker.
- [x] Сделать smoke-check backend routes: `/health`, `/data/health`, `/data/ohlcv`, `/market/trending`.
- [x] Проверить frontend against backend после запуска PostgreSQL окружения.
- [x] Добавить production readiness gate для env/DB/migrations.
- [x] Подготовить server deployment checklist: migrations, readiness, reverse proxy, SSL, backups.
- [x] Получить SSH-команду и учётные данные для `2.25.143.143`.
- [x] Перенастроить DNS `deltagrid.pro` на `2.25.143.143`.
- [x] На реальном сервере создать staging/prod `.env.production` с production secrets (`SECRET_KEY`, `VAULT_MASTER_KEY`) для `deltagrid.pro`.
- [x] Прогнать server preflight на сервере.
- [x] Настроить Nginx/SSL на сервере после DNS cutover.
- [x] Проверить reverse proxy/SSL на `deltagrid.pro` по `DEPLOYMENT.md`.
- [x] Прогнать smoke-check на сервере локально и через домен.
- [x] Проверить Cloudflare proxy, `Full (strict)` и WebSocket после включения оранжевого облака.
- [x] Выполнить `sh scripts/sync-market-data.sh --symbols BTC,ETH,SOL --lookback-hours 24 --ohlcv-intervals 1m,5m,1h` на сервере.
- [x] Проверить, что `/api/v1/data/health` показывает `row_counts.ohlcv > 0` и последний Binance sync.
- [x] Установить `scripts/install-market-sync-cron.sh` на сервере.
- [ ] Проверить первый cron-triggered market data sync по `/var/log/deltagrid-market-sync.log`.
- [x] Задеплоить live data streams fix на сервер и проверить `https://deltagrid.pro/charts`, `/market-matrix`, `/arbitrage-scanner`, `/strategy-lab`.
- [ ] Добавить email к Let's Encrypt account для уведомлений о продлении сертификата.
- [ ] После согласования времени выполнить reboot сервера из-за pending kernel upgrade.

## Frontend MVP Summary — 2026-06-04

- [x] App shell: left sidebar + top workspace tabs.
- [x] Sidebar MVP: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
- [x] Nested nav для Perp DEX и Funding.
- [x] Typed mock data adapter под будущие CoinGecko/CoinGlass integrations.
- [x] Market Overview / Command Center без funding-heavy блоков.
- [x] Perp DEX Intelligence без полноценного Funding dashboard.
- [x] Funding Overview как first-class module.
- [x] Market Overview/Assets/Funding/Charts/Market Matrix/Arbitrage Scanner/Data Health подключены к backend data-layer.
- [x] Perp DEX не показывает mock DEX volume/OI/liquidity как production-данные до live DEX adapter.
- [x] Asset Deep Dive SOL.
- [x] Market Matrix без funding metric / Funding Matrix.
- [x] Strategy Lab / Backtest.
- [x] Charts placeholder без новых зависимостей.
- [x] Frontend build: `npm run build` проходит.

## Следующая frontend-итерация

- [x] Подключить `lightweight-charts` и реализовать первый production-oriented Charts v0.
- [x] Задеплоить Charts v0 на `deltagrid.pro` и пройти visual/smoke QA.
- [x] Подключить Funding/Data Health к backend/data-layer endpoint'ам.
- [x] Подключить Market Matrix, Arbitrage Scanner, Charts и Strategy Lab к backend/data-layer endpoint'ам или честным pending/readiness states.
- [x] Реализовать live Perp DEX venue adapters v0: Hyperliquid, dYdX и GMX raw snapshot без execution path.
- [x] Описать route/execution constraints через backend policy endpoint и Perp DEX UI-таблицу.
- [x] Добавить GMX pool token amount diagnostics для `poolAmountLong/Short` без конвертации USD liquidity/OI.
- [x] Добавить route-level model v0 как read-only checklist/formula skeleton без numeric cost estimates, ranking и execution.
- [x] Описать GMX funding/borrowing/net rate semantics как source-backed metadata без carry conversion.
- [x] Добавить offline GMX rate relation guardrail без carry conversion.
- [ ] Разобрать live GMX `/markets/info` nonzero-borrowing rate mapping, затем добавить side-aware GMX rate fixtures и sourced fee/depth/carry inputs перед численной route-level model.
- [ ] Добавить ручной visual QA checklist по 6 MVP-экранам.

## План новой версии `v1.3.2`: 2 итерации по 10 задач

Цель новой версии — довести Perp DEX / route-model observability до следующего безопасного уровня и запушить результат в GitHub без включения trading, execution, route ranking, route selection, route cost bps или diagnostic carry bps.

### Итерация 1 — Perp DEX GMX live helper source review v0

- [x] Изучить текущий GMX provider/client, normalizer, route-model builder, fixtures и tests, не меняя public API.
- [x] Найти, какие live `/markets/info` поля уже доступны в GMX rows: `fundingRate*`, `borrowingRate*`, `netRate*`, helper source fields и side-direction hints.
- [x] Добавить read-only backend review для live helper/source fields внутри `gmx_rate_mapping_review_v0` без carry conversion.
- [x] Зафиксировать nonzero-borrowing relation evidence как status/checklist rows, не переводя raw rates в percent/bps/carry.
- [x] Расширить side-aware fixture artifacts только для evidence/status: `longsPayShorts`, long/short paying/receiving cases и missing helper inputs.
- [x] Добавить compact smoke keys для live helper/source review ids, statuses и missing helper fields без вывода raw payload.
- [x] Добавить backend regression tests на consistency summary/checklist и неизменные safety flags.
- [x] Протянуть frontend types и небольшую observability-панель `GMX Rate Live Helper Source Review`.
- [x] Обновить русскую документацию: `CHANGELOG.md`, `CURRENT_TASK.md`, `BACKLOG.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `README.md`.
- [x] Прогнать проверки: backend compileall, `pytest backend/tests/test_perp_dex_policy.py`, `bash -n scripts/perp-dex-policy-smoke.sh`, HTTP policy smoke, frontend build/audit и Browser QA `/perp-dex?view=opportunities`.

### Итерация 2 — release stabilization, version bump и GitHub push

- [x] Выполнить full regression pass по Perp DEX direct/policy smoke и core backend tests, не расширяя scope.
- [x] Проверить, что `may_emit_carry_bps`, `may_estimate_cost_bps`, `may_rank_routes`, `may_submit_orders`, route selection и execution остаются выключены.
- [x] Осмотреть `git diff` и исключить raw provider payloads, secrets, accidental large files и unrelated rewrites.
- [x] Обновить `VERSION`, frontend package version и lockfile root version до `v1.3.2`, если release-preflight требует синхронизации.
- [x] Обновить финальные release notes в `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и при необходимости `README.md`/`ARCHITECTURE.md`.
- [x] Запустить `scripts/release-preflight.sh` и исправить только релизные несоответствия.
- [x] Прогнать frontend `npm run build` и `npm audit --audit-level=high`.
- [x] Закоммитить scoped changes в текущей ветке без отката чужих изменений: `d3de35e chore: release v1.3.2 perp dex observability`.
- [x] Push в GitHub на рабочую ветку `preview` и проверить GitHub CI: CI run `27744113125` прошёл `success`.
- [x] Получить зелёный GitHub `Deploy Preview` run для follow-up commit: run `27744161749` для `d3de35e` упал на шаге `Deploy preview`, но `b257cc8` прошёл CI `27746664616` и `Deploy Preview` `27746714283`; `/opt/deltagrid-preview` обновлён до `b257cc8`, `VERSION=1.3.2`.
- [x] После зелёного preview deploy включить promotion/tag `v1.3.2` не отдельным patch rollout, а в финальный `v1.4.0` release path; production deploy останется зависимым от настроенных `PROD_*` secrets.

## Follow-up по `v1.3.2` — 2026-06-18

- `preview` запушен на commit `d3de35e`; локальное дерево чистое.
- GitHub CI для `preview@d3de35e` зелёный.
- GitHub `Deploy Preview` для этого push завершился `failure` на шаге `Deploy preview`; без GitHub job logs через API причина не видна, потому что logs endpoint вернул `403`.
- Read-only SSH показал, что после failed run preview server оставался на `bc342ae`, но ручной запуск того же deploy script на сервере прошёл: `git pull` fast-forward до `d3de35e`, Docker build успешен, containers healthy, `scripts/server-smoke.sh` прошёл.
- Follow-up `preview@b257cc8` прошёл GitHub CI `27746664616` и `Deploy Preview` `27746714283`; server release smoke на preview-портах `8011/3012` прошёл.
- Production `main` и tag `v1.3.2` пока не трогались. Следующая версия должна идти как `v1.4.0` после отдельного preview-green и production rollout gate.
- Важный blocker для production auto-deploy остаётся прежним: GitHub repository secrets `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR` ещё нужно завести вручную.

## План новой версии `v1.4.0`: 3 итерации, 36 задач

Цель `v1.4.0` — выпустить production-ready minor release на `deltagrid.pro`: стабилизировать release/deploy pipeline, довести Perp DEX research cockpit до более полезного read-only уровня и провести preview -> main -> production rollout без включения trading, execution, route ranking, route selection или numeric route cost bps.

### Итерация 1 — Release runway и deploy hardening

- [x] Разобрать причину красного GitHub `Deploy Preview` run `27744161749`: GitHub API/job page показали transient SSH reachability из runner; ручной SSH deploy тем же script прошёл.
- [x] Сделать GitHub `Deploy Preview` зелёным для маленького follow-up commit без продуктового scope: `b257cc8`, CI `27746664616`, Deploy Preview `27746714283`.
- [x] Зафиксировать в docs фактическое состояние `v1.3.2`: CI зелёный, manual preview deploy зелёный, follow-up Deploy Preview зелёный.
- [x] Обновить release/deploy scripts так, чтобы transient SSH/deploy failure давал более короткий diagnostic output и не скрывал причину в GitHub UI.
- [x] Добавить preview/prod release smoke checklist для `perp-dex-direct`, `perp-dex-policy`, `coinglass-perp-dex-coverage`, `/api/v1/health`, `/api/v1/data/health` и frontend.
- [x] Подготовить и выполнить безопасный production backup run через новый `scripts/backup-postgres.sh` из preview checkout против production Compose project, не пачкая production git checkout untracked script-файлом.
- [x] Подготовить инструкцию и checklist для ручного добавления `PROD_*` secrets в GitHub без вывода private key в repo/logs.
- [ ] Проверить `Deploy Production` manual workflow после добавления `PROD_*`: сначала secret readiness/fingerprint/app dir, затем deploy step.
- [x] Добавить release preflight target для `1.4.0-rc.1` на `preview` без преждевременного production bump.
- [x] Провести Browser QA smoke для preview `/perp-dex`, `/charts`, `/data-health`, `/market-matrix`, `/arbitrage-scanner`, `/assets`.
- [x] Обновить `CURRENT_TASK.md`, `BACKLOG.md`, `PROJECT_PLAN.md`, `README.md` и `DEPLOYMENT.md` по результатам deploy hardening.
- [x] Не включать новые trading/execution/ranking/cost-bps capabilities в этой итерации; итог итерации — зелёный release runway.

### Итерация 2 — Perp DEX research cockpit v1.4 read-only

- [x] Добавить compact Perp DEX source status rollup: direct venues, CoinGlass enrichment, GMX raw, policy/model contract, last successful smoke.
- [x] Добавить backend summary по direct venue availability: rows, partial/live status, read-only flags, depth diagnostics availability, provider error class.
- [x] Добавить UI-панель `Perp DEX Source Status` без сортировки venues и без production signal.
- [x] Расширить provider error taxonomy для direct venues: timeout, rate limit, empty response, schema drift, unavailable endpoint.
- [x] Добавить smoke/test coverage на provider error taxonomy без live secrets и без raw payload dumps.
- [x] Добавить GMX helper/source follow-up rows: какие source helper inputs всё ещё отсутствуют, какие manual approvals блокируют carry conversion.
- [x] Добавить Lighter/Aster depth freshness evidence layer: timestamp/source-age policy как readiness, без slippage bps.
- [x] Добавить fee schedule evidence layer для Lighter/Aster: account tier/order intent/manual approval gates, без fee bps total.
- [x] Добавить compact compare contract для `Perp DEX Source Status`, чтобы preview/prod drift был виден без полного payload.
- [x] Улучшить пустые/error states в Perp DEX UI для provider unavailable и partial data states.
- [x] Прогнать backend tests, direct/policy/coinglass smoke, frontend build/audit и Browser QA desktop/mobile.
- [x] Обновить русскую документацию по всем новым read-only panels, API fields и safety gates.

### Итерация 3 — `v1.4.0` release candidate и production rollout

- [x] Поднять версию до `1.4.0` в `VERSION`, `frontend/package.json`, `frontend/package-lock.json`.
- [x] Подготовить `CHANGELOG.md` release block для `v1.4.0`: release runway, Perp DEX source status, deploy/backup, known limitations.
- [x] Пройти `scripts/release-preflight.sh 1.4.0` на `preview` с `ALLOW_DIRTY=1` перед RC commit.
- [x] Выполнить full local regression: backend compileall, targeted backend tests, frontend build, `npm audit --audit-level=high`.
- [x] Выполнить HTTP smoke на preview backend: direct venues, policy/model, CoinGlass coverage, health/readiness/data-health.
- [x] Выполнить Browser QA preview desktop/mobile для `/perp-dex`, `/charts`, `/data-health` и ключевых terminal screens.
- [x] Закоммитить `v1.4.0` release candidate в `preview` и push в GitHub.
- [x] Повторить `scripts/release-preflight.sh 1.4.0` на чистом `preview` без `ALLOW_DIRTY` после RC commit.
- [x] После повторного SSH runner failure вручную обновить preview до `647f7f3` и пройти полный `scripts/release-smoke.sh`.
- [x] Добавить `/version` и GitHub `Deploy Preview` public HTTP fallback для уже доставленного preview.
- [x] Дождаться зелёного GitHub CI и зелёного GitHub `Deploy Preview`.
- [x] Выполнить финальный preview smoke после deploy: backend/frontend health, Perp DEX policy/direct smoke, data-health.
- [x] Merge/push `preview` в `main` только после зелёного preview gate.
- [x] Запустить production deploy для `main` через GitHub Actions или согласованный ручной SSH fallback; перед deploy обязательно сделать PostgreSQL backup.
- [x] После production deploy проверить `https://deltagrid.pro`: health/readiness/data-health, frontend, `/perp-dex`, route safety flags, затем создать annotated tag `v1.4.0` и обновить docs итоговым production follow-up.

## Phase 6 Summary (ARCHITECTURE HARDENING)

Phase 6 is split into incremental sub-phases:

### Phase 6.0 — Foundation & Boundaries ✅ COMPLETED
- [x] Alembic migration `b19c6344f081` — `plan_capabilities`, `feature_flags` tables + `users` alterations
- [x] `CapabilityService` — plan-based feature gating with user-level overrides
- [x] `RequestIDMiddleware` — `X-Request-ID` tracing on all requests
- [x] Global exception handler — `DeltaGridException` hierarchy wired into FastAPI
- [x] CORS hardening — env-aware method/header restrictions + `expose_headers`
- [x] Health endpoint enhanced with `api_version`, `api_tier`
- [x] Billing `/plans` now returns capabilities per plan
- [x] Auth response includes `feature_flags` for authenticated users
- [x] Frontend: `useFeatureFlag` hook, `hasFeature` in authStore, `X-API-Version` header
- [x] API boundary markers — `@internal` / `@public_ready` docstrings on endpoints

### Phase 6.1 — B2B API Foundation 📋 DEFERRED
- [ ] API key generation and storage
- [ ] API key auth middleware
- [ ] Rate limiting by tier
- [ ] B2B router prefix `/api/b2b/v1/`
- [ ] Webhook subscription system

### Phase 6.2 — Multi-Tenancy 📋 DEFERRED
- [ ] `organizations` and `organization_members` tables
- [ ] Tenant-scoped query filter
- [ ] Org admin endpoints

### Phase 6.3 — White-Label 📋 DEFERRED
- [ ] `BrandConfig` abstraction
- [ ] Config-driven sidebar theming
- [ ] Custom domain support

### Phase 6.4 — Enterprise Admin Suite 📋 DEFERRED
- [ ] Admin dashboard
- [ ] Usage analytics and quotas

## Phase 6 Database Schema (2 New Tables + 1 Altered)
- `plan_capabilities` — Plan → feature mapping (41 seeded rows: free/pro/enterprise)
- `feature_flags` — User-level feature overrides with expiration
- `users` — altered: `feature_flags_json`, `plan_started_at`, `plan_expires_at`

## Regression Test Results
- [x] Scanner: GET /api/v1/scanner — operational
- [x] Market Dashboard: all endpoints respond
- [x] Auth: register, login, refresh, me — all pass (feature_flags included)
- [x] Execution: exchange accounts, risk rules, order intents — preserved
- [x] Stream: config, WebSocket, SSE — operational
- [x] Alerts: rules CRUD, events list — operational
- [x] Notifications: preferences CRUD — operational
- [x] RWA: GET /rwa/assets, categories, compare — operational
- [x] Treasury: GET /treasury/entities, btc-holdings, platforms — operational
- [x] Billing: GET /billing/plans — now includes capabilities
- [x] Health: GET /health — returns api_version, api_tier, X-Request-ID header
- [x] Frontend Build: `npm run build` — 0 TS errors
- [x] Backend Startup: `uvicorn app.main:app` — clean start
- [x] Alembic: all 9 migrations applied successfully

## URL разработки
- Frontend: http://127.0.0.1:3000
- Backend API: http://127.0.0.1:8000
- Readiness: http://127.0.0.1:8000/api/v1/health/readiness
- Scanner: http://127.0.0.1:3000/
- Market Dashboard: http://127.0.0.1:3000/market
- Exchange Accounts: http://127.0.0.1:3000/exchange-accounts
- Execution: http://127.0.0.1:3000/execution
- Risk Rules: http://127.0.0.1:3000/risk-rules
- Alerts: http://127.0.0.1:3000/alerts
- Notifications: http://127.0.0.1:3000/notifications
- RWA: http://127.0.0.1:3000/rwa
- Treasury: http://127.0.0.1:3000/treasury
