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

Для промежуточного patch/tooling target или docs-only runway target вроде `v1.7.0` можно сначала проверить, что release docs уже упоминают target, не меняя текущий `VERSION`:

```bash
RELEASE_TARGET=1.7.0 RELEASE_CHECK_DOCS=1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh
```

Для стартовой runway-проверки `v1.7.0`:

```bash
RELEASE_TARGET=1.7.0 RELEASE_CHECK_DOCS=1 ALLOW_DIRTY=1 sh scripts/release-preflight.sh
```

`RELEASE_CHECK_DOCS=1` требует `RELEASE_TARGET` или expected version и проверяет наличие `v<target>` в файлах из `RELEASE_DOCS_FILES`. По умолчанию проверяются `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и `RELEASES.md`; `README.md` лучше добавлять в этот список только после фактического version bump.

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

Для compact Funding QA guard после funding-related UI/data changes можно отдельно выполнить:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-qa-smoke.sh
```

Для preview/prod backend diff без frontend marker check:

```bash
BASE_URL=http://127.0.0.1:8011 COMPARE_BASE_URL=http://127.0.0.1:8000 RUN_FRONTEND_CHECK=0 sh scripts/funding-qa-smoke.sh
```

Для воспроизводимого Funding release-prep запуска можно использовать wrapper:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-release-smoke.sh
```

Для strict release gate:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 FUNDING_RELEASE_STRICT=1 sh scripts/funding-release-smoke.sh
```

Funding compare output должен содержать compact `compare.summary` со статусом `aligned`/`diff_detected`/`compare_failures`, `diff_count`, `diff_fields`, ignored volatile fields, `fail_on_diff`, base/compare row totals, base/compare `panel_ids` и `safety_flags_aligned`. `contract.release_readiness` должен показывать общий release-prep status, checks по health/rows/source/frontend/compare/safety, missing frontend markers и sources with rows. Для hard gate разрешено добавить `FAIL_ON_DIFF=1` и `FAIL_ON_RELEASE_NOT_READY=1` или запустить wrapper с `FUNDING_RELEASE_STRICT=1`; это release/readiness check, а не product trading gate.

Если результат нужно сохранить как machine-readable artifact, добавьте `OUTPUT_JSON_ONLY=1`; тогда smoke печатает только JSON contract без human prefix/suffix:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 OUTPUT_JSON_ONLY=1 sh scripts/funding-release-smoke.sh > funding-release-smoke.json
```

Для короткого release report можно запустить:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/funding-release-report.sh
```

Report должен показывать `readiness_status`, `funding_total_rows`, `funding_rows_by_source`, `compare_status`, `safety_status` и `data_quality_runway_status`; exit code должен совпадать с underlying smoke.

Для compact JSON report:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 FUNDING_RELEASE_REPORT_FORMAT=json sh scripts/funding-release-report.sh > funding-release-report.json
```

Если human-readable stdout должен остаться в логе, а compact JSON нужен отдельным artifact-файлом:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 FUNDING_RELEASE_REPORT_OUTPUT=funding-release-report.json sh scripts/funding-release-report.sh
```

Для CI-профиля release report:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 FUNDING_RELEASE_REPORT_PROFILE=ci sh scripts/funding-release-report.sh > funding-release-report.json
```

Для CI-like локального запуска с предсказуемым artifact path:

```bash
BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 COMPARE_BASE_URL=http://127.0.0.1:8000 sh scripts/funding-release-ci-report.sh
```

Wrapper пишет evidence bundle в `artifacts/funding-release`: index `funding-release-index.md`/`funding-release-index.json`, verify `funding-release-verify.md`/`funding-release-verify.json`, notes `funding-release-notes.md`/`funding-release-notes.json`, archive `funding-release-archive.md`/`funding-release-archive.json`, CI final status `funding-release-ci-status.json`, compact report `funding-release-report.json`, optional stdout JSON, validation result `funding-release-validation.json`, manifest `funding-release-manifest.json`, bundle validation result `funding-release-bundle-validation.json`, runbook review `funding-release-review.json`, Markdown summary `funding-release-summary.md`, evidence handoff `funding-release-handoff.md`, audit result `funding-release-audit.json` и audit Markdown `funding-release-audit.md`. Он создаёт artifact directory, задаёт `FUNDING_RELEASE_REPORT_PROFILE=ci` и сохраняет stdout JSON в `FUNDING_RELEASE_CI_STDOUT_FILE`, если этот env задан. Для GitHub доступен manual workflow `Funding Release Report`: он принимает `base_url`, `frontend_url`, optional `compare_base_url`, загружает `artifacts/funding-release` через `actions/upload-artifact` и только потом фейлит job при blocked/failed report.

CI final status для wrapper-а:

```bash
cat artifacts/funding-release/funding-release-ci-status.json
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-ci-status.json`, если `FUNDING_RELEASE_CI_WRITE_STATUS=1` (default). Имя файла можно переопределить через `FUNDING_RELEASE_CI_STATUS_FILE`. Status artifact создаётся после archive и фиксирует `ci_status_version=funding_release_ci_status_v0`, `final_status=passed|blocked|failed`, `final_exit_code`, `final_stage`, `stage_exit_codes`, краткий rollup report/verify/notes/archive и `run_context`. Если report заблокирован readiness вроде локального `needs_funding_rows`, но validation/index/verify/archive прошли, это должно читаться как release blocker, а не как поломка evidence tooling. GitHub workflow добавляет секцию `CI Final Status` в `$GITHUB_STEP_SUMMARY`.

Перед прикладыванием artifact к release evidence можно отдельно проверить его форму:

```bash
sh scripts/funding-release-report-validate.sh artifacts/funding-release/funding-release-report.json
```

`scripts/funding-release-ci-report.sh` запускает эту validation автоматически, если `FUNDING_RELEASE_CI_VALIDATE_ARTIFACT=1` (default). Validator проверяет required fields, status enum'ы, consistency `release_gate_summary`/`release_gate_checks`, safety invariants, `data_quality_runway` schema и `run_context.ci`; blocked report считается валидным artifact, если его форма корректна. Для отдельного hard-check на зелёный artifact используйте `FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_PASSED=1`.

Manifest/checksum validation запускается отдельно:

```bash
sh scripts/funding-release-bundle-validate.sh artifacts/funding-release/funding-release-manifest.json
```

`scripts/funding-release-ci-report.sh` запускает bundle validation автоматически, если `FUNDING_RELEASE_CI_VALIDATE_BUNDLE=1` (default), и пишет `funding-release-bundle-validation.json`. Validator проверяет `manifest_version`, bundle/report/validation exit codes, status semantics, required/optional blockers и checksum/size/json-valid consistency для report/stdout/validation files.

Runbook review запускается отдельно:

```bash
sh scripts/funding-release-bundle-review.sh artifacts/funding-release/funding-release-manifest.json
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-review.json`, если `FUNDING_RELEASE_CI_WRITE_REVIEW=1` (default). Review не валидирует заново bundle и не читает full smoke payload; он собирает `review_status`, `recommended_next_action`, exit codes, validation statuses, blockers, first actions, run context и file integrity summary для быстрого release/evidence review.

Markdown summary для GitHub step summary или release notes:

```bash
sh scripts/funding-release-review-summary.sh artifacts/funding-release/funding-release-review.json
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-summary.md`, если `FUNDING_RELEASE_CI_WRITE_SUMMARY=1` (default). Summary читает только `funding-release-review.json`, поддерживает `markdown`, `text` и `json`, показывает `runbook_status`, next action, required/optional blockers, first actions, run context и file integrity table. GitHub workflow сначала добавляет этот markdown в `$GITHUB_STEP_SUMMARY`, а старый review/manifest/report parser остаётся fallback.

Release handoff для передачи bundle в release notes/runbook:

```bash
sh scripts/funding-release-evidence-handoff.sh artifacts/funding-release/funding-release-review.json
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-handoff.md`, если `FUNDING_RELEASE_CI_WRITE_HANDOFF=1` (default). Handoff читает review, optional summary, manifest и bundle validation, поддерживает `markdown`, `text` и `json`, показывает `evidence_status`, `release_evidence_ready`, `debug_evidence_ready`, blockers, first actions, run context, artifact checklist и локальные follow-up команды. Это handoff поверх уже созданного evidence bundle; он не запускает smoke заново и не меняет `funding_qa_v0`.

Directory-level audit скачанного evidence bundle:

```bash
sh scripts/funding-release-evidence-audit.sh artifacts/funding-release
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-audit.json`, если `FUNDING_RELEASE_CI_WRITE_AUDIT=1` (default), и `funding-release-audit.md`, если `FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN=1` (default). Audit проверяет expected files, JSON-валидность, status consistency report/validation/manifest/bundle validation/review и markdown markers summary/handoff. Он нужен для проверки скачанного artifact из GitHub; blocked report считается валидным evidence, если bundle целостный. GitHub workflow добавляет audit Markdown в `$GITHUB_STEP_SUMMARY` после release summary, а fallback summary читает `funding-release-audit.json`.

Evidence index запускается отдельно:

```bash
sh scripts/funding-release-evidence-index.sh artifacts/funding-release
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-index.json`, если `FUNDING_RELEASE_CI_WRITE_INDEX=1` (default), и `funding-release-index.md`, если `FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN=1` (default). Index является первым файлом для reviewer: он показывает ordered artifact map, status rollup, blockers и локальные команды проверки поверх уже созданных report/review/handoff/audit artifacts. GitHub workflow сначала добавляет `funding-release-index.md` в `$GITHUB_STEP_SUMMARY`, а summary/audit parser остаётся fallback.

Evidence verify запускается отдельно:

```bash
sh scripts/funding-release-evidence-verify.sh artifacts/funding-release
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-verify.json`, если `FUNDING_RELEASE_CI_WRITE_VERIFY=1` (default), и `funding-release-verify.md`, если `FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN=1` (default). Verify является финальным local verdict для reviewer: он сверяет index/audit, optional review/manifest/report statuses, показывает `verification_status`, `blocking_mode`, `release_notes_ready`, `debug_review_ready` и `recommended_next_action`. По умолчанию blocked readiness evidence остаётся валидным bundle, если index/audit прошли; для strict release-notes handoff можно задать `FUNDING_RELEASE_VERIFY_REQUIRE_RELEASE_NOTES_READY=1`, а для debug-review handoff — `FUNDING_RELEASE_VERIFY_REQUIRE_DEBUG_READY=1`. GitHub workflow добавляет `funding-release-verify.md` в `$GITHUB_STEP_SUMMARY` сразу после index.

Evidence notes запускается отдельно:

```bash
sh scripts/funding-release-evidence-notes.sh artifacts/funding-release
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-notes.json`, если `FUNDING_RELEASE_CI_WRITE_NOTES=1` (default), и `funding-release-notes.md`, если `FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN=1` (default). Notes является paste-ready слоем поверх verify: он читает `funding-release-verify.json`, optional index/audit/review/manifest/report artifacts, показывает `notes_status`, `notes_mode`, release/debug readiness, blockers, artifact checklist и готовый snippet для release notes или debug review. По умолчанию blocked readiness evidence пишет debug snippet и остаётся валидным tooling output; для strict release-notes handoff можно задать `FUNDING_RELEASE_NOTES_REQUIRE_READY=1`. GitHub workflow добавляет `funding-release-notes.md` в `$GITHUB_STEP_SUMMARY` после verify.

Evidence archive запускается отдельно:

```bash
sh scripts/funding-release-evidence-archive.sh artifacts/funding-release
```

`scripts/funding-release-ci-report.sh` пишет `funding-release-archive.json`, если `FUNDING_RELEASE_CI_WRITE_ARCHIVE=1` (default), и `funding-release-archive.md`, если `FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN=1` (default). Archive является финальным offline checksum/readout слоем поверх downloaded bundle: он читает локальные report/validation/manifest/review/summary/handoff/audit/index/verify/notes artifacts, считает `size_bytes`, `sha256`, `json_valid`, сверяет verify/notes readiness и показывает `archive_status`, `archive_mode`, missing required files, blockers и recommended next action. По умолчанию blocked evidence остаётся валидным archive output для debug review; для strict release-ready handoff используйте `FUNDING_RELEASE_ARCHIVE_REQUIRE_RELEASE_READY=1`, тогда not-ready bundle вернёт exit `2`. Archive не запускает smoke заново, не вызывает backend/provider API и не меняет `funding_qa_v0`.

Offline compare двух evidence bundles:

```bash
sh scripts/funding-release-evidence-compare.sh artifacts/funding-release-base artifacts/funding-release
```

`scripts/funding-release-evidence-compare.sh` сравнивает два уже скачанных/созданных bundle без повторного smoke: обязательный `funding-release-verify.json`, optional notes/index/audit/review/manifest/report artifacts, readiness/status fields, blockers и artifact presence. Output поддерживает `markdown`, `text` и `json`; верхний статус `compare_status` принимает `aligned`, `drift_detected` или `failed`, а `comparison_mode` отделяет blocking drift от non-blocking drift. По умолчанию drift нужен для runbook review и возвращает exit `0`; для strict handoff используйте `FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED=1`, тогда drift вернёт exit `2`. Это offline evidence check, а не новый release smoke, provider call или изменение `funding_qa_v0`.

`funding-release-manifest.json` должен быть первым файлом для runbook/evidence review: он содержит `bundle_exit_code`, `report_exit_code`, `validation_exit_code`, release/validation statuses, required/optional blockers, `first_blocking_action`, `first_optional_action`, `run_context` и checksum/size для report/stdout/validation files. Если `validation_exit_code=0`, но `bundle_exit_code` non-zero, это означает корректный artifact с реальным release blocker, а не поломку tooling.

`FUNDING_RELEASE_REPORT_PROFILE=ci` по умолчанию включает JSON report, `FUNDING_RELEASE_REPORT_REQUIRE_READY=1` и `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE=1`; явные env overrides сохраняют приоритет для локальных исключений. Compact report должен включать `report_version=funding_release_report_v0`, `gate_status`, `release_gate_status`, `report_exit_code`, `exit_reason`, `release_gate_summary`, `release_gate_checks`, `readiness_gate_status`, `blocking_reasons`, `next_actions`, `run_context`, `readiness_checks`, `source_pair_statuses`, `compare_diff_fields` и `data_quality_runway`, чтобы release artifact фиксировал режим запуска smoke, output path, CI/GitHub context, итоговый artifact status, итоговый exit, normalized release-check blockers, blocker groups, Funding runway gates и first blocking action.

Для report-level readiness gate можно добавить `FUNDING_RELEASE_REPORT_REQUIRE_READY=1`; это не меняет smoke contract, а только делает report non-zero, если `readiness_gate_status=not_ready` при успешном underlying smoke.

Для report-level compare gate можно добавить `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE=1`; это полезно для preview/prod, где отсутствие `COMPARE_BASE_URL` должно считаться неготовым release artifact.

Funding QA contract должен включать panel id `funding_data_quality_runway`, `funding_release_checklist`, `funding_anomaly_detail`, `funding_history_diagnostics`, `funding_history_controls`, `funding_history_readiness` и `funding_qa_drilldown` вместе с `funding_source_status`, `funding_freshness_anomaly` и `funding_source_comparison`; frontend marker check должен также видеть `funding_qa_view` через `/funding?view=qa`. Это release-safety/data-QA contract, а не trading/routing gate.

Для `v1.5.0` Funding smoke contract также должен включать backend-only `contract.data_quality_runway` с `runway_version=funding_data_quality_runway_v0`, `status=ready|needs_review|blocked`, `gate_ids`, `gate_statuses`, `blocking_gate_ids`, `missing_sources`, `history_preview_rows`, `next_action` и `safe_boundary`. Этот summary нужен для release evidence и не зависит от frontend marker check; report-level gate `data_quality_runway` может быть blocked при пустых локальных rows, но это валидный release blocker, если validator проходит.

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

`v1.5.0` — текущий production minor release на `deltagrid.pro`: `origin/main=3f6f3f7`, tag `v1.5.0` указывает на release `3f6f3f7`, production `/version` возвращает `1.5.0`.

Production evidence для `v1.5.0`:

- production smoke прошёл;
- Funding release report на VPS прошёл с `release_gate_status=passed`;
- `funding_total_rows=3126`, `coinglass=3000`, `okx=126`;
- `missing_frontend_markers=0`;
- backup перед deploy: `/opt/deltagrid/backups/deploy/deltagrid-main_20260620T075400Z.sql.gz`.

Локальный RC `v1.6.0` подготовлен в ветке `codex/v1.6.0-production-ops-data-reliability` на commit `e0bcbc6`: ветка содержит 5 commits поверх `origin/main`, версии в этой ветке подняты до `1.6.0`, локальные release/backend/frontend/funding checks были подготовлены, а GitHub CI run `27872800819` завершился `success`. Это не production release: PR к `main` не найден, tag `v1.6.0` отсутствует, production backup/deploy/smoke/tag `v1.6.0` не выполнялись.

Следующий рабочий target: `v1.7.0` — Data Quality Observability & Funding Reliability release в ветке `codex/v1.7.0-data-quality-observability` от `origin/main=3f6f3f7`. Так как ветка стартует от production `main`, изменения локального RC `v1.6.0` не входят в неё автоматически; переносить их можно только осознанно и с повторными проверками.

Safe release path для `v1.7.0`:

1. Работать в feature branch `codex/v1.7.0-data-quality-observability`.
2. Сначала закрыть docs-only baseline/planning audit и зафиксировать, что `v1.6.0` не был production release.
3. Усиливать Funding/Data evidence и UX маленькими проверяемыми batch без изменения backend API, БД и provider calls, если отдельное решение не принято.
4. Перед RC поднять `VERSION`, frontend package metadata и lockfile root version до `1.7.0`.
5. Пройти `scripts/release-preflight.sh 1.7.0`, backend compile/tests, frontend build/audit и funding/data release evidence.
6. Открыть PR к `main` и дождаться PR CI.
7. До production deploy создать свежий PostgreSQL backup.
8. Выполнить production deploy только после отдельного подтверждения владельца; evidence должно явно показать real deploy, `/version`, smoke и Funding release report.
9. Создать annotated tag `v1.7.0` только после успешного production evidence.

До отдельного продуктового решения запрещено включать trading, execution, route ranking, route selection, route cost bps и diagnostic carry bps. `v1.7.0` не должен менять backend API, БД-схему и provider calls в planning/evidence итерациях без отдельного обоснования.
