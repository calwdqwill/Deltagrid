# Changelog — DeltaGrid

## [2026-06-20] - [CI] - v1.5.0 branch CI success
- Скоуп батча закрыт как CI evidence update: 1) branch push на `codex/v1.4.1-funding-release-tooling` запустил GitHub `CI`; 2) commit `9bc6dd7` проверен; 3) run id `27863265157`; 4) run завершился `success`; 5) handoff обновлён ссылкой на run; 6) `CURRENT_TASK.md` обновлён; 7) `BACKLOG.md` обновлён; 8) `PROJECT_PLAN.md` обновлён; 9) `CHANGELOG.md` обновлён; 10) merge/deploy/tag не выполнялись.
- Branch CI является предварительным evidence для feature branch, но не заменяет PR review, preview evidence, production backup/deploy, smoke, Browser QA и annotated tag.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [CI] - v1.5.0 branch CI readiness
- Скоуп батча закрыт как CI-only release readiness: 1) `.github/workflows/ci.yml` теперь запускается на push в `codex/**`; 2) `preview` и `main` push triggers сохранены; 3) pull request triggers сохранены; 4) deploy workflows не менялись; 5) branch CI можно использовать как предварительное evidence до ручного PR; 6) PR review не заменяется branch CI; 7) production deploy gate не менялся; 8) handoff обновлён; 9) release docs обновлены; 10) runtime не трогался.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [QA] - v1.5.0 pre-merge validation
- Скоуп батча закрыт как pre-merge validation: 1) worktree чистый; 2) `merge-base` совпадает с `origin/main=2b6c830`; 3) `git merge-tree origin/main HEAD` проходит без conflict output; 4) `git diff --check origin/main...HEAD` чистый; 5) backend files в PR diff отсутствуют; 6) generated artifact paths в PR diff отсутствуют; 7) secret-like additions не найдены; 8) targeted forbidden capability enable scan пустой; 9) `deploy/v1.5.0-release-handoff.md` обновлён; 10) merge/deploy/tag не выполнялись.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [QA] - v1.5.0 full local regression pass
- Скоуп батча закрыт как локальный release QA pass: 1) `scripts/release-preflight.sh 1.5.0` проходит; 2) docs-check preflight для `v1.5.0` проходит; 3) backend compileall через project venv проходит; 4) backend pytest через project venv проходит (`59 passed`); 5) frontend `npm run build` проходит; 6) frontend `npm audit --audit-level=high` не находит high/critical blocker; 7) Funding release scripts проходят `bash -n`; 8) CI-like Funding evidence bundle проходит; 9) `deploy/v1.5.0-release-handoff.md` обновлён фактическими checks; 10) production runtime/tag/deploy не трогались.
- Локальный системный Python 3.12 не содержит `pytest`; backend regression в этом workspace нужно запускать через `backend\\venv\\Scripts\\python.exe`.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [RELEASE] - v1.5.0 PR/release handoff readiness
- Скоуп батча закрыт как docs-only release handoff: 1) проверены remote refs `origin/main=2b6c830`, `origin/preview=5f8ad89`, branch `0a43813`; 2) подтверждено отсутствие tags `v1.4.1`/`v1.5.0`; 3) подтверждено отсутствие открытого PR; 4) зафиксировано отсутствие `gh` CLI и локального GitHub token; 5) проверено, что CI не запускается на `codex/*` push; 6) добавлен `deploy/v1.5.0-release-handoff.md`; 7) handoff содержит PR URL/body; 8) handoff содержит checks и preview evidence path; 9) handoff фиксирует production release gate; 10) merge/deploy/tag не выполнялись.
- Уточнена формулировка baseline: `3936c83` является release/runtime commit для `v1.4.0`, а текущий `origin/main` находится на docs-only follow-up `2b6c830`.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [RELEASE] - v1.5.0 local RC/version bump
- Скоуп батча закрыт как локальный release candidate: 1) `VERSION` поднят до `1.5.0`; 2) `frontend/package.json` поднят до `1.5.0`; 3) root version в `frontend/package-lock.json` поднят до `1.5.0`; 4) README показывает текущую версию `v1.5.0`; 5) release docs обновлены; 6) `scripts/release-preflight.sh 1.5.0` проходит с `ALLOW_DIRTY=1`; 7) frontend `npm run build` проходит; 8) `npm audit --audit-level=high` не находит high/critical blocker; 9) funding compact report + validator проходят на temp artifact; 10) production runtime, tag и deploy не трогались.
- `v1.5.0` включает накопленный `v1.4.1` Funding release tooling scope, read-only `Funding Data Quality Runway` и `data_quality_runway` release evidence contract; отдельный patch release `v1.4.1` больше не обязателен для локального RC, если этот branch идёт как minor PR.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [OPS] - v1.5.0 Funding runway evidence contract batch
- Скоуп батча закрыт одним release-evidence блоком: 1) `scripts/funding-qa-smoke.sh` добавляет contract field `data_quality_runway`; 2) summary фиксирует runway version, gate ids, gate statuses, blocking gate ids, missing sources, history preview rows и next action; 3) summary остаётся backend-only и не зависит от frontend marker check; 4) `scripts/funding-release-report.sh` выводит `data_quality_runway` в compact report; 5) release gate checks получили `data_quality_runway`; 6) `blocking_reasons` и `next_actions` учитывают runway blockers; 7) `scripts/funding-release-report-validate.sh` проверяет schema нового summary; 8) CI-like temp evidence bundle проходит; 9) docs/runbook обновлены; 10) production runtime не трогался.
- Локальный evidence run с `ALLOW_UNAVAILABLE=1`, `RUN_FRONTEND_CHECK=0` и temp artifact dir подтвердил форму `funding-release-report.json`, validation, manifest, bundle validation, review, summary, handoff, audit, index, verify, notes, archive и CI final status.
- Граница сохранена: backend API, БД, provider calls, trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT] - v1.5.0 Funding Data Quality Runway batch
- Скоуп батча закрыт одним read-only блоком: 1) добавлен тип `FundingDataQualityRunwayRow`; 2) live Funding builder собирает `dataQualityRunway` из уже загруженных `/data/funding` и `/data/health`; 3) `/funding` получил панель `Funding Data Quality Runway` в `Overview` и `QA`; 4) fixture path обновлён как preview-only; 5) funding QA smoke получил marker `funding_data_quality_runway`; 6) `panel_ids` smoke-контракта расширен новым panel id; 7) backend API не менялся; 8) БД и provider calls не менялись; 9) frontend build проходит; 10) docs обновлены под Итерацию 2.
- Новый runway-блок сводит health, funding rows, source coverage, freshness/coverage/sync, history preview и `v1.5.0` preview gate в одну таблицу для релизного QA.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PLANNING] - v1.5.0 release runway batch
- Скоуп батча закрыт одним блоком: 1) проверена чистая ветка `codex/v1.4.1-funding-release-tooling`; 2) зафиксирован production baseline `v1.4.0` на `main@3936c83`; 3) зафиксирована зависимость от unsmerged `v1.4.1` commit `1f84fab`; 4) определён target `v1.5.0`; 5) scope ограничен Funding/Data QA и release evidence; 6) non-goals явно исключают backend API, БД, provider calls и frontend product flow в runway; 7) путь до релиза разбит на 4 крупные итерации; 8) release path описан через preview evidence, main, production backup/deploy, smoke, Browser QA и tag; 9) docs-only preflight для `v1.5.0` добавлен в release policy; 10) runtime-код и версии не менялись.
- `v1.5.0` стартует как minor release runway после production `v1.4.0`; финальный RC зависит от решения по `v1.4.1`: отдельный patch release или перенос tooling scope в `v1.5.0`.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [RELEASE] - v1.4.1 local intermediate
- Скоуп батча закрыт одним блоком: 1) `VERSION` поднят до `1.4.1`; 2) `frontend/package.json` поднят до `1.4.1`; 3) root version в `frontend/package-lock.json` поднят до `1.4.1`; 4) README показывает текущую версию `v1.4.1`; 5) release docs фиксируют локальный intermediate статус; 6) `RELEASE_CHECK_DOCS=1` включён в финальный preflight; 7) funding CI status artifact остаётся частью evidence bundle; 8) ожидаемый локальный blocker `needs_funding_rows` не считается tooling bug; 9) production baseline `v1.4.0` не объявлялся обновлённым; 10) commit/tag/deploy не выполнялись.
- `v1.4.1` подготовлен как локальная промежуточная patch/tooling версия для Funding release evidence и CI/runbook hardening.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [RELEASE] - v1.4.1 release candidate docs/runbook
- Скоуп батча закрыт одним блоком: 1) `v1.4.1` зафиксирован как промежуточный patch/tooling target; 2) `scripts/release-preflight.sh` получил optional `RELEASE_CHECK_DOCS=1`; 3) добавлен `RELEASE_DOCS_FILES`; 4) docs check требует `RELEASE_TARGET` или expected version; 5) docs check проверяет упоминание `v<target>` в release docs; 6) default preflight behavior сохранён; 7) `RELEASES.md` получил runbook для docs-check; 8) `PROJECT_PLAN.md` обновил следующий шаг; 9) `BACKLOG.md` получил release-candidate checklist; 10) локальный docs-check preflight подготовлен для `v1.4.1`.
- `v1.4.1` остаётся patch/tooling release candidate вокруг Funding release evidence: без backend API, БД, provider calls, frontend product flow и production trading signals.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release CI Final Status Batch v0
- Скоуп батча закрыт одним блоком: 1) `scripts/funding-release-ci-report.sh` получил `FUNDING_RELEASE_CI_STATUS_FILE`; 2) добавлен guard `FUNDING_RELEASE_CI_WRITE_STATUS`; 3) wrapper пишет `funding-release-ci-status.json` после archive; 4) status фиксирует `final_status`; 5) status фиксирует `final_exit_code`; 6) status фиксирует `final_stage`; 7) status сохраняет exit codes всех evidence-стадий; 8) status подтягивает краткие report/verify/notes/archive поля; 9) GitHub workflow добавляет `CI Final Status` в step summary; 10) synthetic checks покрывают passed/blocked/env paths.
- CI final status является runbook/readout слоем поверх уже созданного evidence bundle: он не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Archive Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-archive.sh`; 2) поддержан Markdown output; 3) поддержан JSON output; 4) поддержан text output; 5) archive проверяет required artifact inventory; 6) optional учитывает compare artifacts; 7) считает `size_bytes`, `sha256` и `json_valid`; 8) сверяет verify/notes readiness consistency; 9) `scripts/funding-release-ci-report.sh` пишет `funding-release-archive.json`/`.md`; 10) GitHub workflow добавляет archive readout в step summary.
- Evidence archive является финальным offline checksum/readout слоем для уже созданного evidence bundle: он не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Compare Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-compare.sh`; 2) поддержан Markdown output; 3) поддержан JSON output; 4) поддержан text output; 5) compare требует `funding-release-verify.json` в двух директориях; 6) optional читает notes/index/audit/review/manifest/report artifacts; 7) сравнивает status/readiness drift; 8) сравнивает required/optional blocker drift; 9) сравнивает artifact presence drift; 10) добавлен strict gate `FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED=1`.
- Evidence compare является offline readout слоем для двух уже созданных evidence bundles: он не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Notes Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-notes.sh`; 2) поддержан Markdown output; 3) поддержан JSON output; 4) поддержан text output; 5) notes требует `funding-release-verify.json`; 6) notes сверяет optional index/audit/review/manifest/report artifacts при наличии; 7) добавлен release notes snippet; 8) добавлен debug review snippet для blocked valid evidence; 9) `scripts/funding-release-ci-report.sh` пишет `funding-release-notes.json`/`.md`; 10) GitHub workflow добавляет notes readout в step summary после verify.
- Evidence notes является paste-ready readout слоем для уже созданного evidence bundle: он не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Verify Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-verify.sh`; 2) поддержан text output; 3) поддержан JSON output; 4) поддержан Markdown output; 5) verify проверяет `funding-release-index.json` и `funding-release-audit.json`; 6) verify сверяет review/manifest/report statuses при наличии; 7) добавлены optional gates `FUNDING_RELEASE_VERIFY_REQUIRE_RELEASE_NOTES_READY` и `FUNDING_RELEASE_VERIFY_REQUIRE_DEBUG_READY`; 8) `scripts/funding-release-ci-report.sh` пишет `funding-release-verify.json`/`.md`; 9) GitHub workflow добавляет verify readout в step summary; 10) docs/runbook и failure-mode checks обновлены.
- Evidence verify является финальным локальным readout слоем для уже созданного evidence bundle: он не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Index Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-index.sh`; 2) поддержан Markdown output; 3) поддержан JSON output; 4) поддержан text output; 5) index показывает ordered artifact map; 6) index показывает status rollup по review/audit/manifest; 7) index показывает required/optional blockers; 8) index показывает local review commands; 9) `scripts/funding-release-ci-report.sh` пишет `funding-release-index.md`/`.json`; 10) GitHub workflow сначала показывает index в step summary.
- Evidence index является entrypoint/readout слоем поверх уже созданного evidence bundle, не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Audit Summary CI Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен artifact `funding-release-audit.md`; 2) добавлен env `FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE`; 3) добавлен guard `FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN`; 4) wrapper пишет JSON audit; 5) wrapper пишет Markdown audit; 6) GitHub workflow задаёт audit Markdown env; 7) GitHub step summary добавляет audit Markdown после release summary; 8) fallback summary читает `funding-release-audit.json`; 9) docs/runbook обновлены; 10) synthetic checks покрывают passed/blocked/tamper/env paths.
- Audit summary CI layer использует уже существующий `scripts/funding-release-evidence-audit.sh`, не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Audit Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-audit.sh`; 2) поддержан text output; 3) поддержан JSON output; 4) поддержан Markdown output; 5) audit проверяет expected files; 6) audit проверяет JSON-validity; 7) audit проверяет status consistency между report/validation/manifest/bundle validation/review; 8) audit проверяет summary/handoff markers; 9) `scripts/funding-release-ci-report.sh` пишет `funding-release-audit.json`; 10) GitHub workflow загружает audit в evidence bundle.
- Evidence audit является directory-level проверкой скачанного `artifacts/funding-release`, не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Evidence Handoff Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-evidence-handoff.sh`; 2) поддержан Markdown output; 3) поддержан text output; 4) поддержан JSON output; 5) handoff показывает `evidence_status`; 6) handoff показывает artifact checklist; 7) handoff показывает required/optional blockers; 8) handoff показывает first actions и run context; 9) `scripts/funding-release-ci-report.sh` пишет `funding-release-handoff.md`; 10) GitHub workflow загружает handoff в evidence bundle.
- Evidence handoff является release/runbook слоем поверх `funding-release-review.json`, summary, manifest и bundle validation, не запускает smoke заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Review Summary Artifact Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-review-summary.sh`; 2) поддержан Markdown output; 3) поддержан text output; 4) поддержан JSON output; 5) summary показывает `runbook_status`; 6) summary показывает required/optional blocker sections; 7) summary показывает first actions; 8) summary показывает run context; 9) summary показывает file integrity table; 10) `scripts/funding-release-ci-report.sh` и GitHub workflow используют `funding-release-summary.md`.
- Review summary является presentation/readout слоем поверх `funding-release-review.json`, не валидирует bundle заново, не читает full smoke payload и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-20] - [PRODUCT/OPS] - Funding Release Bundle Review Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-bundle-review.sh`; 2) поддержан text output; 3) поддержан JSON review artifact; 4) review показывает bundle/report/validation exit codes; 5) review показывает validation statuses; 6) review показывает required/optional blockers и first actions; 7) review показывает file integrity summary без raw payload; 8) `scripts/funding-release-ci-report.sh` пишет `funding-release-review.json`; 9) GitHub summary сначала читает review artifact; 10) synthetic checks подтверждают passed/blocked/corrupt review paths.
- Bundle review является runbook/readout слоем поверх manifest и validation artifacts, не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Bundle Manifest Validation Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-bundle-validate.sh`; 2) validator проверяет `manifest_version`; 3) проверяются bundle/report/validation exit-code semantics; 4) проверяются release/validation statuses; 5) проверяются required/optional blockers; 6) проверяются file presence, `size_bytes`, `sha256` и `json_valid`; 7) поддержаны text/json outputs; 8) `scripts/funding-release-ci-report.sh` пишет `funding-release-bundle-validation.json`; 9) GitHub summary показывает `bundle_validation_status`; 10) synthetic/tamper checks подтверждают pass/blocked/failure modes.
- Bundle validation является CI/runbook проверкой evidence bundle поверх manifest, не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Evidence Bundle Batch v0
- Скоуп батча закрыт одним блоком: 1) `scripts/funding-release-ci-report.sh` пишет `funding-release-validation.json`; 2) добавлен `funding-release-manifest.json`; 3) manifest содержит bundle/report/validation exit codes; 4) manifest разделяет required/optional blockers и first blocking/optional action; 5) manifest содержит file sizes и sha256 для report/stdout/validation; 6) blocked report сохраняет исходный exit code после успешной validation/manifest; 7) GitHub summary читает manifest; 8) workflow artifact upload включает bundle; 9) runbook обновлён; 10) synthetic checks подтверждают passed/blocked bundle paths.
- Evidence bundle является CI/runbook индексом поверх compact report и validation result, не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Artifact Validation Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-report-validate.sh`; 2) validator проверяет обязательные поля compact report; 3) проверяются enum-статусы `gate_status`/`release_gate_status`/`exit_reason`; 4) проверяется consistency `release_gate_summary` с `release_gate_checks`; 5) проверяются safety invariants по `safety_status`/`unsafe_flags`; 6) проверяется `run_context.ci`; 7) `scripts/funding-release-ci-report.sh` запускает validation после report; 8) blocked report сохраняет свой exit code после успешной validation; 9) GitHub workflow включает artifact validation; 10) runbook обновлён.
- Validation batch проверяет форму и инварианты compact artifact, но не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report CI Integration Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `scripts/funding-release-ci-report.sh`; 2) wrapper задаёт CI defaults и artifact directory; 3) добавлен optional stdout JSON file; 4) `scripts/funding-release-report.sh` получил preflight validation для bool/int env и artifact paths; 5) compact report получил `run_context.ci`; 6) добавлен manual GitHub Actions workflow `Funding Release Report`; 7) workflow сохраняет artifact до финального failure; 8) runbook обновлён; 9) локальные failure-mode checks добавлены в проверку.
- CI integration остаётся report-level tooling поверх `funding_qa_v0`: backend API, provider calls, БД и frontend product flow не менялись.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Artifact Output Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `FUNDING_RELEASE_REPORT_OUTPUT`; 2) text stdout может одновременно писать compact JSON artifact в файл; 3) JSON stdout также может дублироваться в artifact file; 4) `run_context` фиксирует output path и enabled flag; 5) write failure возвращает exit `4`; 6) default без env не изменён; 7) `FUNDING_RELEASE_REPORT_JSON` остаётся внутренним temp-файлом smoke JSON; 8) runbook обновлён.
- Artifact output является optional report-level side effect для CI и не меняет `funding_qa_v0`, backend endpoints, provider calls, БД или frontend product flow.
- Проверка: `sh -n` для funding smoke/report scripts, text+artifact write, JSON+artifact write, artifact write failure и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Gate Actions Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлена `category` для каждого `release_gate_checks` row; 2) добавлены `required_blocking_ids`; 3) добавлены `optional_blocking_ids`; 4) добавлены `blocker_groups` по категориям; 5) добавлен `first_blocking_action`; 6) добавлен `next_actions_by_check`; 7) text report печатает blocker groups и first action; 8) JSON artifact остаётся report-level summary; 9) документация обновлена.
- Actions batch делает release artifact более применимым для CI/runbook, но остаётся производным слоем поверх `funding_qa_v0` без backend/API/provider/БД изменений.
- Проверка: `sh -n` для funding smoke/report scripts, manual actions, CI readiness actions, CI compare actions, strict smoke actions и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Gate Checklist Batch v0
- Скоуп батча закрыт одним блоком: 1) добавлен `release_gate_checks`; 2) добавлен `release_gate_summary`; 3) checks нормализованы по `smoke_contract`, `release_readiness`, `compare_alignment`, `data_health`, `funding_rows`, `source_coverage`, `frontend_markers`, `safety_boundary` и `report_profile`; 4) summary показывает total/required/blocking counts; 5) summary показывает `required_ids` и `blocking_ids`; 6) status counts добавлены для dashboard; 7) text report печатает compact gate checks; 8) JSON artifact остаётся коротким; 9) документация обновлена.
- Checklist является report-level observability поверх `funding_qa_v0`: он не меняет smoke contract, backend endpoints, provider calls, БД или frontend product flow.
- Проверка: `sh -n scripts/funding-release-report.sh`, manual checklist, CI readiness checklist, CI compare checklist, strict smoke checklist и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Gate Status v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `release_gate_status`; 2) статус принимает `passed`, `blocked` или `failed`; 3) `gate_status` оставлен как smoke-only поле; 4) readiness/compare report gates мапятся в `blocked`; 5) underlying smoke failure мапится в `failed`; 6) text/JSON report печатают новый статус; 7) документация обновлена.
- Это верхнеуровневый report artifact status для CI/dashboard, а не изменение `funding_qa_v0`, provider flow, backend API или БД.
- Проверка: `sh -n scripts/funding-release-report.sh`, manual passed, CI readiness blocked, CI compare blocked, strict smoke failed и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Exit Reason v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `report_exit_code`; 2) добавлен `exit_reason`; 3) причины разделяют `passed`, `smoke_failed`, `readiness_not_ready` и `compare_not_aligned`; 4) JSON report возвращает тот же итоговый код, который записан в artifact; 5) text report печатает exit context; 6) smoke exit preservation сохранён; 7) документация обновлена.
- Это observability metadata для release report, а не изменение `funding_qa_v0`, provider flow, backend API или БД.
- Проверка: `sh -n scripts/funding-release-report.sh`, manual default report, CI readiness expected failure, CI compare expected failure, strict smoke expected failure и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report CI Profile v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `FUNDING_RELEASE_REPORT_PROFILE`; 2) профиль `manual` сохраняет текущие defaults; 3) профиль `ci` по умолчанию включает JSON report, require-ready и require-compare; 4) явные env overrides сохраняют приоритет; 5) `run_context.report_profile` фиксирует режим запуска; 6) text report печатает profile; 7) документация обновлена.
- Это preset для CI/release artifacts поверх `scripts/funding-release-report.sh`, а не изменение `funding_qa_v0`, backend endpoints, provider flow или БД.
- Проверка: `sh -n scripts/funding-release-report.sh`, manual default report, `ci` expected readiness failure, `ci` with ready override and compare aligned, require-compare expected failure и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Report Require Compare Gate v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `FUNDING_RELEASE_REPORT_REQUIRE_COMPARE`; 2) default `0` сохранён; 3) report получил `compare_gate_status`; 4) при `1` report возвращает non-zero, если compare не запускался или не `aligned`; 5) smoke failure exit code сохраняется; 6) text/JSON report показывают compare gate context; 7) документация обновлена.
- Это report-level CI gate для preview/prod drift checks, а не изменение `funding_qa_v0`, provider flow или backend API.
- Проверка: `sh -n scripts/funding-release-report.sh`, default report, require-compare aligned report, require-compare expected failure без `COMPARE_BASE_URL` и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Report Require Ready Gate v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `FUNDING_RELEASE_REPORT_REQUIRE_READY`; 2) default `0` сохранён; 3) при `1` report возвращает non-zero, если `readiness_gate_status != ready` и underlying smoke сам прошёл; 4) smoke failure exit code сохраняется; 5) `run_context` показывает `report_require_ready`; 6) text/JSON report поддерживают флаг; 7) документация обновлена.
- Это report-level CI gate поверх compact summary, а не изменение `funding_qa_v0` или release smoke contract.
- Проверка: `sh -n scripts/funding-release-report.sh`, default soft report, require-ready expected failure, strict expected failure и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Readiness Gate Report v0
- Скоуп итерации закрыт одним блоком: 1) compact report получил `readiness_gate_status`; 2) добавлены `blocking_reasons`; 3) добавлены deduped `next_actions`; 4) soft smoke теперь явно отличает passed smoke от not-ready release readiness; 5) text report печатает blockers/actions; 6) JSON report сохраняет те же поля; 7) документация обновлена.
- Report остаётся thin summary поверх `funding_qa_v0`: он не меняет smoke contract, backend endpoints, provider calls или БД.
- Проверка: `sh -n scripts/funding-release-report.sh`, text report, JSON report parse, expected-failure strict JSON report и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Evidence v0
- Скоуп итерации закрыт одним блоком: 1) compact report получил `readiness_checks`; 2) добавлен `sources_with_rows`; 3) добавлены `source_pair_statuses`; 4) добавлены `compare_diff_fields`; 5) text report печатает эти evidence строки; 6) JSON report сохраняет те же поля; 7) документация обновлена.
- Evidence fields объясняют причину `ready`/`blocked` без чтения полного `funding_qa_v0` payload и не меняют сам smoke contract.
- Проверка: `sh -n scripts/funding-release-report.sh`, text report, JSON report parse, expected-failure strict JSON report и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report Context v0
- Скоуп итерации закрыт одним блоком: 1) compact report получил `report_version`; 2) добавлен `gate_status`; 3) добавлен `run_context` с base/frontend/compare URL; 4) добавлен strict-mode context; 5) добавлены effective `fail_on_diff` и `fail_on_release_not_ready`; 6) text report показывает ключевой context; 7) JSON report сохраняет те же поля для CI.
- Это metadata вокруг release report, а не изменение `funding_qa_v0` или backend/data-layer contract.
- Проверка: `sh -n scripts/funding-release-report.sh`, text report, JSON report parse, expected-failure strict JSON report и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report JSON v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `FUNDING_RELEASE_REPORT_FORMAT`; 2) `scripts/funding-release-report.sh` поддерживает `text` и `json`; 3) default `text` сохранён; 4) compact JSON report содержит smoke exit, readiness, rows, frontend markers, compare и safety; 5) strict failure сохраняет non-zero exit code; 6) docs/runbook обновлены; 7) формат не меняет `funding_qa_v0`.
- JSON report нужен для коротких CI artifacts и dashboards поверх уже существующего smoke output.
- Проверка: `sh -n scripts/funding-release-report.sh`, soft text report, soft JSON report parse, expected-failure strict JSON report и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Report v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `scripts/funding-release-report.sh`; 2) report запускает release wrapper в `OUTPUT_JSON_ONLY=1`; 3) JSON contract парсится без raw payload; 4) печатается compact summary по readiness, rows, frontend markers, compare и safety; 5) exit code исходного smoke сохраняется; 6) strict failure остаётся видимым в report; 7) документация обновлена.
- Report является удобным release artifact поверх `funding_qa_v0`, а не новым data/API contract.
- Проверка: `sh -n` для funding smoke/report scripts, soft report smoke, expected-failure strict report smoke и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Smoke JSON Output v0
- Скоуп итерации закрыт одним блоком: 1) добавлен env `OUTPUT_JSON_ONLY`; 2) `scripts/funding-qa-smoke.sh` умеет печатать чистый JSON без human prefix/suffix; 3) `scripts/funding-release-smoke.sh` прокидывает этот режим и тоже убирает context line; 4) дефолтный human-readable output сохранён; 5) strict/soft presets не изменены; 6) JSON-only output пригоден для CI/report artifacts; 7) документация обновлена.
- Это output-format режим поверх существующего `funding_qa_v0`, а не новый data/API contract.
- Проверка: `sh -n` для обоих funding smoke scripts, JSON-only parse через Python, soft wrapper smoke, expected-failure strict wrapper smoke и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Smoke Wrapper v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `scripts/funding-release-smoke.sh`; 2) wrapper запускает существующий `scripts/funding-qa-smoke.sh` без дублирования Python-логики; 3) сохранён soft mode по умолчанию; 4) добавлен strict preset через `FUNDING_RELEASE_STRICT=1`; 5) strict preset включает `FAIL_ON_DIFF=1` и `FAIL_ON_RELEASE_NOT_READY=1`, если они не заданы явно; 6) wrapper печатает compact run context; 7) документация и release runbook обновлены.
- Wrapper нужен для воспроизводимого preview/prod funding release smoke: он не меняет contract `funding_qa_v0`, не добавляет provider calls и не пишет в БД.
- Проверка: `sh -n scripts/funding-release-smoke.sh`, `sh -n scripts/funding-qa-smoke.sh`, `git diff --check`, soft wrapper smoke и expected-failure strict wrapper smoke прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Readiness Hard Gate v0
- Скоуп итерации закрыт одним блоком: 1) добавлен env `FAIL_ON_RELEASE_NOT_READY`; 2) флаг прокинут в Python smoke; 3) smoke падает, если `contract.release_readiness.status` не `ready_for_preview_smoke`; 4) soft mode по умолчанию сохранён; 5) compare summary показывает `fail_on_release_not_ready`; 6) negative test на пустых локальных funding rows подтвердил controlled failure; 7) документация обновлена.
- Это release hard gate только по явному флагу; локальный dev flow с `MIN_TOTAL_ROWS=0` остаётся мягким, если `FAIL_ON_RELEASE_NOT_READY=1` не задан.
- Проверка: `sh -n scripts/funding-qa-smoke.sh`, `git diff --check`, soft same-base smoke и expected-failure smoke с `FAIL_ON_RELEASE_NOT_READY=1` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Readiness Smoke Summary v0
- Скоуп итерации закрыт одним блоком: 1) добавлен compact `release_readiness` в `funding_qa_v0`; 2) добавлен общий release status; 3) добавлены checks `data_health`, `funding_rows`, `source_coverage`, `frontend_markers`, `compare_support`, `safety_boundary`; 4) добавлены `missing_frontend_markers`; 5) добавлены `sources_with_rows`; 6) `release_readiness` участвует в compare diff; 7) same-base compare smoke проверен; 8) документация обновлена.
- Summary не печатает raw payload и нужен для release/readiness диагностики: локально при пустых funding rows он честно возвращает `needs_funding_rows`, а не маскирует отсутствие данных.
- Проверка: `sh -n scripts/funding-qa-smoke.sh`, `git diff --check` и same-base smoke `MIN_TOTAL_ROWS=0 RUN_FRONTEND_CHECK=0 COMPARE_BASE_URL=http://127.0.0.1:8000 FAIL_ON_DIFF=1` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding Release Checklist v0
- Скоуп итерации закрыт одним большим блоком: 1) добавлен typed contract `FundingReleaseChecklistRow`; 2) добавлен live builder release-readiness; 3) проверяются data health и funding rows; 4) проверяется source coverage OKX/CoinGlass; 5) проверяется selected history workflow; 6) добавлена UI-панель `Funding Release Checklist`; 7) fixture fallback обновлён; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids`; 9) документация и backlog обновлены.
- Checklist является release/readiness слоем для `Overview`/`QA`: он помогает понять, можно ли запускать funding QA smoke и preview/prod compare, но не является market signal, strategy signal или routing gate.
- Изменение использует существующие `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding QA Compare Summary v0
- Скоуп итерации закрыт одним блоком: 1) уточнён compare path в `scripts/funding-qa-smoke.sh`; 2) добавлен compact `compare.summary.status`; 3) добавлены `diff_count` и `diff_fields`; 4) явно перечислены ignored volatile fields; 5) добавлен `fail_on_diff`; 6) добавлены base/compare total rows; 7) добавлены base/compare panel ids; 8) добавлен `safety_flags_aligned`; 9) документация и backlog обновлены.
- `COMPARE_BASE_URL` теперь даёт короткий release/readiness summary для preview/prod drift, сохраняя старый compact `contract` в output для обратной совместимости.
- Проверка: `sh -n scripts/funding-qa-smoke.sh`, `git diff --check` и same-base smoke `MIN_TOTAL_ROWS=0 RUN_FRONTEND_CHECK=0 COMPARE_BASE_URL=http://127.0.0.1:8000 FAIL_ON_DIFF=1` прошли.
- Граница сохранена: compare summary не является trading/routing gate и не включает execution, route ranking, route selection, diagnostic carry bps, fee bps total или numeric route cost bps.

## [2026-06-19] - [PRODUCT/UI] - Funding History Readiness v0
- Скоуп итерации закрыт одним блоком: 1) добавлен typed row contract `FundingHistoryReadinessRow`; 2) readiness считает persisted rows; 3) отдельно объясняет selected asset coverage; 4) отдельно объясняет selected source coverage; 5) показывает chart points readiness; 6) показывает numeric rate parsing readiness; 7) chart empty-state получил source-aware status/evidence/next action; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids`; 9) документация и backlog обновлены.
- Панель `Funding History Readiness` является read-only empty-state/QA слоем для выбранной funding history series; она объясняет, почему график пустой или тонкий, но не является strategy signal, provider ranking или route input.
- Изменение использует существующие `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding History Controls v0
- Скоуп итерации закрыт одним блоком: 1) добавлены URL-параметры `asset`/`source` для `Funding History`; 2) введён typed row contract `FundingHistoryControlRow`; 3) history chart выбирает source-aware series; 4) добавлены asset/source segmented controls; 5) показываются rows/window/interval/range hints; 6) отображается chart readiness; 7) добавлен `Next Action`; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids`; 9) документация и backlog обновлены.
- Панель `Funding History Controls` является read-only UX/QA слоем поверх persisted funding rows; она помогает выбрать историю для просмотра, но не является strategy signal, provider ranking или route input.
- Изменение использует существующие `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check`, `sh -n scripts/funding-qa-smoke.sh` и funding QA smoke с локальным frontend прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding History Diagnostics v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `Funding History Diagnostics`; 2) введён typed row contract; 3) считаются observations/window/latest/interval; 4) считаются average rate и observed range; 5) status связан с freshness health; 6) добавлен `Next Action`; 7) панель показывается в `Overview` и `History`; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids`; 9) документация и backlog обновлены.
- Панель является history-window QA поверх persisted funding rows и помогает понять, хватает ли истории для графика/анализа; это не strategy signal и не route input.
- Изменение использует существующие `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` через Git Bash прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding QA View Grouping v0
- Скоуп итерации закрыт одним блоком: 1) добавлен отдельный `QA` view в `Funding`; 2) введён `showQaPanels`; 3) пять Funding QA panels сгруппированы в один compact block; 4) default `Overview` сохранил QA panels; 5) `/funding?view=qa` показывает QA-only workflow; 6) остальные Funding views больше не тянут весь QA block сверху; 7) `scripts/funding-qa-smoke.sh` проверяет `/funding?view=qa`; 8) добавлен frontend marker `funding_qa_view`; 9) документация и backlog обновлены.
- Изменение улучшает UX/readability Funding screen без backend changes, новых provider calls, БД-изменений и production signals.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` через Git Bash прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding Anomaly Detail v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `Funding Anomaly Detail`; 2) введён typed row contract; 3) считаются samples/latest/baseline average/range/z-score; 4) anomaly status оставлен только как QA label; 5) добавлен `Next Review`; 6) порядок `BTC/ETH/SOL × OKX/CoinGlass` остаётся фиксированным без ranking; 7) добавлен fixture fallback; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids`; 9) документация и backlog обновлены.
- `Funding Anomaly Detail` показывает baseline statistics по persisted funding rows и объясняет, есть ли достаточно истории для оценки; это не strategy signal и не route input.
- Панель строится поверх существующих `/data/funding`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` через Git Bash прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding QA Drilldown v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `Funding QA Drilldown`; 2) введён typed row contract; 3) funding rows связаны с `/data/health` freshness; 4) добавлена связь с coverage reasons; 5) добавлен sync health status; 6) выводится per-row `Next Action`; 7) порядок `BTC/ETH/SOL × OKX/CoinGlass` остаётся фиксированным без ranking; 8) `scripts/funding-qa-smoke.sh` расширен marker/`panel_ids` для drilldown; 9) документация и backlog обновлены.
- Drilldown показывает loaded rows, latest row age, freshness reason, coverage reason, sync status и next action как data-QA подсказки, а не как trade/setup сигнал.
- Панель строится поверх существующих `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build`, `git diff --check` и `sh -n scripts/funding-qa-smoke.sh` через Git Bash прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/OPS] - Funding QA smoke contract v0
- Скоуп итерации закрыт одним блоком: 1) добавлен `scripts/funding-qa-smoke.sh`; 2) проверяются `/data/health` и `/data/funding` для `BTC/ETH/SOL` по OKX/CoinGlass; 3) формируется compact `funding_qa_v0` contract; 4) проверяются панели `Funding Source Status`, `Funding Freshness & Anomaly`, `Funding Source Comparison`; 5) добавлены safety flags против trading/routing outputs; 6) raw payload не печатается; 7) поддержаны `BASE_URL`, `FRONTEND_URL`, `SYMBOLS`, `EXCHANGES`, `MIN_TOTAL_ROWS`, `RUN_FRONTEND_CHECK`; 8) поддержаны `COMPARE_BASE_URL` и `FAIL_ON_DIFF`; 9) документация и backlog обновлены.
- Скрипт является release-safety/data-QA guard для funding analytics и использует только существующие read-only endpoints; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Локальная проверка: `bash -n scripts/funding-qa-smoke.sh` прошёл через Git Bash; backend-only smoke с `RUN_FRONTEND_CHECK=0 MIN_TOTAL_ROWS=0` прошёл. Дефолтный `MIN_TOTAL_ROWS=1` честно падает на текущем локальном backend, где funding rows равны `0`.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding Source Comparison v0
- `Funding` получил read-only панель `Funding Source Comparison`: для `BTC/ETH/SOL` сравниваются последние OKX и CoinGlass funding rates, source delta, latest pair, data note и source-alignment status.
- Source comparison является provider/data QA: строки идут в фиксированном порядке symbols, не сортируются по выгоде и не создают opportunities, route ranking, route selection или production trading signal.
- Панель строится поверх существующих `/data/funding`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build` и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding Freshness & Anomaly v0
- `Funding` получил read-only панель `Funding Freshness & Anomaly`: для `BTC/ETH/SOL` по OKX и CoinGlass показываются rows, latest age, latest rate, last change, data status и statistical anomaly status.
- Anomaly status считается только как data-quality/statistical QA по уже загруженным funding rows: `Need more history`, `Stable baseline`, `Normal`, `Elevated` или `Stat outlier`; это не торговый сигнал и не route input.
- Панель строится поверх существующих `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build` и `git diff --check` прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-19] - [PRODUCT/UI] - Funding Source Status v0
- `Funding` получил read-only панель `Funding Source Status`: OKX funding history и CoinGlass funding snapshots показывают loaded rows, latest age, freshness, coverage, sync и boundary.
- Панель строится из уже загруженных `/data/funding` и `/data/health`; новых backend endpoints, provider calls, БД-изменений и production signals не добавлено.
- `TerminalTable` получил гарантированный contained horizontal scroll для мобильных таблиц, чтобы широкие status/diagnostic rows не расширяли страницу.
- Проверка: `frontend` `npm run build` прошёл; Browser mobile smoke для `/funding` подтвердил наличие панели и отсутствие page-level horizontal overflow. Desktop Browser smoke на старом локальном dev server был ограничен локальным `next dev`/`.next` chunk mismatch после build, а не product regression.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-18] - [RELEASE] - v1.4.0 production
- `preview` смержен в `main` merge commit `3936c83`, `VERSION=1.4.0`; annotated tag `v1.4.0` создан и запушен.
- Перед rollout создан свежий PostgreSQL backup `/opt/deltagrid/backups/deltagrid-v140-production_20260618T210020Z.sql.gz` (`4422613` bytes, gzip integrity check прошёл).
- GitHub CI для `main@3936c83` прошёл (`27789130591`); `Deploy Production` run `27789183806` сделал safe-skip/success из-за отсутствующих `PROD_*`, поэтому production deploy выполнен вручную тем же `scripts/deploy-compose-stack.sh`.
- `/opt/deltagrid` обновлён до `3936c83`, `VERSION=1.4.0`; backend/frontend/postgres healthy, `scripts/release-smoke.sh`, public `/version`, `/api/v1/health`, `/api/v1/health/readiness` и Browser QA desktop/mobile прошли.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-18] - [RELEASE] - v1.4.0 release candidate
- Версия поднята до `1.4.0` в `VERSION`, `frontend/package.json` и root package entry в `frontend/package-lock.json`.
- Release scope: release/deploy runway v1.4, зелёный preview deploy path, reusable release smoke, production backup tooling, Perp DEX Source Status rollup/compare contract, direct venue `availability_summary`, provider error taxonomy, depth freshness evidence, Lighter/Aster fee schedule evidence и provider state empty/error states.
- Preview baseline перед RC: `preview@104b487` прошёл GitHub CI `27782417781`, `Deploy Preview` `27782466540`, `/opt/deltagrid-preview` был обновлён и remote `scripts/release-smoke.sh` на `8011/3012` прошёл.
- Проверка перед RC commit/push: release preflight для `1.4.0-rc.1`, backend compileall, targeted backend pytest, frontend build, `npm audit --audit-level=high`, preview HTTP release smoke, Browser QA desktop/mobile через SSH tunnel и post-commit preflight без `ALLOW_DIRTY` прошли.
- GitHub CI для `e32922a` (`27784328974`) и retry `647f7f3` (`27785222823`) прошли, но `Deploy Preview` runs `27784385918` и `27785273679` упали на GitHub runner SSH reachability до remote deploy script; ручной deploy тем же `scripts/deploy-compose-stack.sh` обновил preview до `647f7f3`/`1.4.0`, полный `scripts/release-smoke.sh` прошёл.
- Preview deploy hardening: добавлен frontend `/version` endpoint и public HTTP fallback в GitHub `Deploy Preview`, который после SSH deploy failure проверяет ожидаемую версию из `VERSION` и backend health через `Host: preview.deltagrid.pro`.
- Final preview gate: ops-only `main@3a8a497` доставил fallback workflow на default branch без production runtime deploy; `preview@e1be7a3` прошёл CI `27787569356` и `Deploy Preview` `27787622699`, `/opt/deltagrid-preview` обновлён до `e1be7a3`/`1.4.0`, public `/version` возвращает `1.4.0`, финальный `scripts/release-smoke.sh` прошёл.
- Known limitations: public `preview.deltagrid.pro` всё ещё ждёт DNS/SSL, production auto-deploy зависит от ручного добавления GitHub secrets `PROD_*`, GMX carry conversion и numeric route-cost model остаются decision-gated.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps, fee bps total и numeric route cost bps не включались.

## [2026-06-18] - [PRODUCT/UI] - Perp DEX provider state empty/error states v0
- `Perp DEX` получил compact state rows перед таблицами `Direct Perp DEX Market Snapshots`, `Depth Diagnostics` и `CoinGlass Perp DEX Enrichment`: venue/source status, rows, matched/missing symbols, provider issue, depth freshness и read-only boundary теперь видны даже при пустых detail rows.
- UI использует уже загруженные `availability_summary` direct venues и `coverage_summary` CoinGlass, а для старого snapshot shape имеет frontend fallback; новых backend endpoints, provider calls, БД-записей и production signals не добавлено.
- Empty/error states теперь явно разделяют provider unavailable, request failed/empty response, partial data, missing symbols и отсутствие depth diagnostics, не превращая coverage hints в ranking.
- Проверка: targeted backend tests `test_perp_dex_policy.py` и `test_perp_dex_direct_availability.py` прошли; `npm run build`, `npm audit --audit-level=high`, policy smoke, direct venues smoke и Browser QA `/perp-dex?view=venues` desktop/mobile прошли. Локальный CoinGlass no-secret smoke проверен в graceful-unavailable режиме с `ALLOW_UNAVAILABLE=1 MIN_ROWS=0 MIN_MATCHED_EXCHANGES=0`.
- Граница сохранена: slippage bps, fee bps total, diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## [2026-06-18] - [PRODUCT/OPS] - Perp DEX Source Status compare contract v0
- Добавлен `scripts/perp-dex-source-status-smoke.sh`: compact smoke для `Perp DEX Source Status`, который собирает direct venues, GMX raw, CoinGlass enrichment, route policy/model и release-smoke checklist в один machine-readable contract.
- Скрипт поддерживает `COMPARE_BASE_URL` и `FAIL_ON_DIFF=1`, чтобы сравнивать preview/prod source-status drift без полного payload и без вывода raw provider data или secrets.
- Contract фиксирует ids/statuses/flags/counts: direct venue rows/statuses/depth freshness, provider error classes, CoinGlass matched exchanges/candidate hints, route policy/model blockers и safety flags.
- Граница сохранена: source-status compare не является route ranking, route selection, numeric route cost bps, diagnostic carry bps или execution signal.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX Lighter/Aster fee schedule evidence v0
- `diagnostic_cost_estimate_v0.summary` получил `fee_schedule_evidence_summary`: compact status по Lighter/Aster fee evidence, source fields, required route inputs, required policy inputs, manual approvals и blocked outputs.
- `diagnostic_cost_estimate_v0.summary` получил `fee_schedule_evidence_checklist`: отдельные read-only rows для Lighter public maker/taker fee fields и Aster published USDT perpetual fee defaults.
- `Perp DEX` UI получил панели `Route Diagnostic Fee Schedule Evidence` и `Route Diagnostic Fee Schedule Checklist` рядом с readiness/depth policy слоями.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `fee_schedule_evidence_*`; backend regression tests закрепляют manual approval gates и safety flags.
- Граница сохранена: fee bps total, numeric route cost bps, route ranking, route selection и execution не включались.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX GMX helper/source follow-up rows v0
- `gmx_rate_mapping_review_v0` получил `helper_source_follow_up_summary`: compact worklist по отсутствующим GMX helper source inputs, связанным review/input ids, fixture/decision gates и manual approval ids, которые всё ещё блокируют carry conversion.
- `gmx_rate_mapping_review_v0` получил `helper_source_follow_up_checklist`: отдельные rows для missing helper inputs, live nonzero mapping approval, side-direction approval и carry runtime/display approvals.
- `Perp DEX` UI получил панель `GMX Rate Helper Source Follow-up` рядом с текущими GMX live helper/carry evidence panels.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_helper_follow_up_status`, ids/statuses, missing source inputs и blocking manual approval ids; backend regression tests закрепляют новый summary/checklist и safety flags.
- Граница сохранена: diagnostic carry bps, numeric route cost bps, route ranking, route selection и execution не включались.

## [2026-06-18] - [OPS] - Preview deploy follow-up после depth freshness
- Product commit `4433f0b` прошёл GitHub CI `27761405255`, но GitHub `Deploy Preview` `27761467202` снова завершился `failure` на шаге `Deploy preview` после успешных secrets/fingerprint/value checks, SSH port/login и app-dir check.
- Public logs endpoint для failed run вернул `403`, поэтому причина внутри stdout deploy step недоступна через API; по step timing это выглядит как повторный transient SSH/deploy transport failure из GitHub runner.
- Ручной SSH deploy тем же `scripts/deploy-compose-stack.sh` успешно обновил `/opt/deltagrid-preview` до `4433f0b`; backend/frontend containers healthy.
- Полный preview release smoke на `8011/3012` прошёл: health/readiness/data/frontend, Perp DEX policy, direct venues и CoinGlass coverage зелёные.
- `main`, production deploy и tags не трогались; trading, execution, route ranking, route selection, diagnostic carry bps и numeric route cost bps не включались.

## [2026-06-18] - [PRODUCT/API] - Perp DEX depth freshness evidence v0
- `availability_summary.depth_diagnostics` получил `freshness`: snapshot timestamp, observed timestamp, `age_ms`, display `max_age_ms`, status, required policy inputs и stale-depth action.
- Direct smoke проверяет freshness evidence и закрепляет `may_emit_slippage_bps=false`, `numeric_total_status=blocked`.
- Добавлены targeted backend tests для fresh/stale/missing/not-applicable depth freshness statuses.
- Граница сохранена: Lighter/Aster depth freshness является readiness/evidence layer, а не slippage bps, route cost, route ranking, route selection или execution.

## [2026-06-18] - [PRODUCT/API] - Perp DEX direct availability summary v0
- Direct venue endpoints Hyperliquid, dYdX, Lighter, Aster и GMX получили `availability_summary`: rows, requested/matched/missing symbols, market/provider status counts, depth diagnostics availability, read-only flags и `safe_use`.
- Provider failures получили compact taxonomy `provider_error_class`: `timeout`, `rate_limit`, `empty_response`, `schema_drift`, `unavailable_endpoint`, `provider_unavailable`, `provider_http_error`.
- `scripts/perp-dex-direct-smoke.sh` теперь читает backend summary, считает provider error classes и проверяет, что direct venues остаются read-only без ranking, production signal и execution.
- Добавлены targeted backend tests для success summary, schema-drift snapshot и error taxonomy; raw payload/secrets в smoke не выводятся.
- Граница сохранена: availability summary не включает route ranking, route selection, numeric route cost bps, diagnostic carry bps или execution.

## [2026-06-18] - [PRODUCT/UI] - Perp DEX Source Status rollup v0
- `Perp DEX` получил панель `Perp DEX Source Status` для compact read-only обзора direct venues, GMX raw, CoinGlass enrichment, route policy/model contract и last release smoke.
- Панель строится из уже загруженных frontend snapshots и backend policy/model responses; новых provider calls, backend endpoints, БД-изменений и production signals не добавлено.
- Проверка: `frontend` `npm run build` прошёл; Browser QA локального `/perp-dex` с preview backend через SSH tunnel прошёл на desktop и mobile без runtime errors, console errors и page-level horizontal overflow.
- Граница сохранена: venue sorting, route ranking, route selection, numeric route cost bps, diagnostic carry bps и execution не включались.

## [2026-06-18] - [OPS] - v1.4.0 release runway и deploy diagnostics
- `v1.3.2` follow-up сохранён отдельным docs-коммитом: зафиксированы зелёный CI, ручной preview deploy и красный GitHub `Deploy Preview` run `27744161749`.
- Причина красного `Deploy Preview` классифицирована как transient SSH reachability из GitHub runner: secrets/fingerprint/value checks были настроены, но SSH port/login/app-dir/deploy attempts были нестабильны; ручной SSH deploy тем же script прошёл.
- `.github/workflows/deploy-preview.yml`, `.github/workflows/deploy-production.yml` и `scripts/deploy-compose-stack.sh` получили stage-aware diagnostics и remote diagnostic snapshot для failed deploy attempts.
- Follow-up `preview@b257cc8` прошёл GitHub CI `27746664616` и `Deploy Preview` `27746714283`; `/opt/deltagrid-preview` обновлён до `b257cc8`, `VERSION=1.3.2`.
- Добавлен `scripts/release-smoke.sh`: общий preview/prod smoke для health/readiness/data-health/frontend, Perp DEX policy, direct venues и CoinGlass coverage.
- `scripts/release-preflight.sh` получил `RELEASE_TARGET`, чтобы проверять `1.4.0-rc.1` как preview target без преждевременного production bump.
- Production backup подготовлен и выполнен безопасно через новый script из preview checkout против production Compose project: `/opt/deltagrid/backups/deltagrid-v140-runway_20260618T081912Z.sql.gz`, gzip integrity check прошёл внутри script.
- Preview release smoke на VPS прошёл на `8011/3012`: server smoke, Perp DEX policy smoke, direct venue smoke и CoinGlass coverage smoke зелёные; Browser QA через SSH tunnel прошёл для `/perp-dex`, `/charts`, `/data-health`, `/market-matrix`, `/arbitrage-scanner`, `/assets` без runtime errors.
- Граница сохранена: trading, execution, route ranking, route selection, diagnostic carry bps и numeric route cost bps не включались.

## [2026-06-18] - [RELEASE] - v1.3.2 release stabilization
- Версия поднята до `1.3.2` в `VERSION`, `frontend/package.json` и root package entry в `frontend/package-lock.json`.
- Release scope: Perp DEX route-model observability, GMX carry/source evidence gates, GMX live helper source review, production deploy hardening, production healthcheck и PostgreSQL backup tooling.
- Safety boundary сохранена: diagnostic carry bps, route cost bps, route ranking, route selection и execution не включались.
- Проверка: release preflight `1.3.2`, backend compileall, targeted backend regression tests, HTTP Perp DEX policy smoke, HTTP Perp DEX direct smoke, frontend build и `npm audit --audit-level=high` проходят.
- Production deploy для `main` остаётся зависимым от настроенных GitHub secrets `PROD_*`; preview push должен пройти через GitHub CI и `Deploy Preview`.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX GMX live helper source review v0
- `gmx_rate_mapping_review_v0` получил `live_helper_source_summary`: compact summary по live GMX `/markets/info` rate output fields, missing helper source inputs, fixture cases, side-aware expectations и manual approval ids.
- `gmx_rate_mapping_review_v0` получил `live_helper_source_checklist`: live rate output fields, nonzero-borrowing relation evidence, helper source fields presence, side-direction helper fields и manual review gate теперь видны как отдельные read-only review rows.
- `Perp DEX` UI получил панель `GMX Rate Live Helper Source Review` рядом с текущими GMX carry evidence panels.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_live_helper_review_status`, `gmx_rate_live_helper_review_ids`, `gmx_rate_live_helper_review_statuses`, `gmx_rate_live_helper_missing_source_inputs` и `gmx_rate_live_helper_manual_approval_ids`; backend regression tests закрепляют новый summary/checklist и flags.
- Граница не изменилась: diagnostic carry bps, route cost bps, route ranking, route selection и execution не включались.
- Проверка: backend compileall, `pytest backend/tests/test_perp_dex_policy.py`, `bash -n scripts/perp-dex-policy-smoke.sh`, HTTP policy smoke, frontend build/audit и Browser QA desktop/mobile для `/perp-dex?view=opportunities` проходят.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX GMX carry-source evidence gate v0
- `gmx_rate_mapping_review_v0` получил `carry_source_evidence_summary`: compact summary по GMX carry evidence ids, evidence types, related inputs, source fields, fixture cases, decision checks и manual approval ids.
- `gmx_rate_mapping_review_v0` получил `carry_source_evidence_checklist`: runtime inputs, side-aware fixture evidence, source helper field evidence, display-unit policy evidence и manual approval evidence теперь видны как read-only gates перед любым diagnostic carry bps.
- `Perp DEX` UI получил таблицы `GMX Rate Carry Evidence Summary` и `GMX Rate Carry Evidence Checklist` рядом с текущими carry readiness panels.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_carry_evidence_status`, `gmx_rate_carry_evidence_ids`, `gmx_rate_carry_evidence_statuses`, `gmx_rate_carry_evidence_types` и `gmx_rate_carry_evidence_manual_approval_ids`; backend regression tests закрепляют новые rows и flags.
- Граница не изменилась: diagnostic carry bps, route cost bps, route ranking, route selection и execution не включались.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX GMX carry-readiness audit v0
- `gmx_rate_mapping_review_v0` получил `carry_readiness_summary`: compact summary по GMX carry inputs, required fixtures, decision checks и manual approval ids перед любым diagnostic carry bps.
- `gmx_rate_mapping_review_v0` получил `carry_input_checklist`: `holding_period_hours`, `position_notional_usd`, `rate_sign_convention`, `source_helper_inputs` и `display_unit_decision` теперь видны как read-only gates без расчёта carry bps.
- `Perp DEX` UI получил таблицы `GMX Rate Carry Readiness Summary` и `GMX Rate Carry Input Checklist` рядом с текущими GMX mapping/fixture panels.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_mapping_decision_manual_approval_ids`, `gmx_rate_carry_readiness_status`, `gmx_rate_carry_input_ids`, `gmx_rate_carry_input_statuses` и `gmx_rate_carry_manual_approval_ids`; backend regression tests закрепляют новые rows и flags.
- Граница не изменилась: diagnostic carry bps, route cost bps, route ranking, route selection и execution не включались.

## [2026-06-18] - [PRODUCT/DATA] - Perp DEX GMX fixture/source hardening v0
- `gmx_rate_mapping_review_v0` получил `side_aware_fixture_expectations`: для `longsPayShorts` явно перечислены long/short paying/receiving cases, которые должны быть покрыты fixtures до любого carry bps.
- `gmx_rate_mapping_review_v0` получил `mapping_decision_checklist`: source helper inputs, live nonzero-borrowing mapping, side-aware fixtures, carry horizon/notional и display-unit decision теперь видны как read-only checklist с manual approval ids.
- `Perp DEX` UI получил таблицы `GMX Rate Side-aware Fixtures` и `GMX Rate Mapping Decision Checklist`; `GMX Rate Fixture Readiness` показывает expectation notes для `longsPayShorts`.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_fixture_statuses`, `gmx_rate_side_expectation_ids`, `gmx_rate_mapping_decision_check_ids` и `gmx_rate_mapping_decision_statuses`; backend regression tests проверяют новые rows и сохраняют `carry/cost/rank/exec=false`.
- Граница не изменилась: diagnostic carry bps, route cost bps, route ranking, route selection и execution не включались.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX GMX mapping evidence hardening v0
- `gmx_rate_mapping_review_v0` получил `blocker_breakdown`: blockers GMX source helper inputs, live mapping, fixture coverage, side-aware sign tests, holding period/notional и display decision теперь агрегируются по review rows.
- `gmx_rate_mapping_review_v0` получил `fixture_readiness_matrix`: nonzero borrowing, zero borrowing ambiguity, `longsPayShorts` direction и missing helper inputs видны как отдельные readiness cases без carry conversion.
- `Perp DEX` UI получил таблицы `GMX Rate Mapping Blockers` и `GMX Rate Fixture Readiness` рядом с текущим `GMX Rate Mapping Review`.
- `scripts/perp-dex-policy-smoke.sh` compact contract теперь включает `gmx_rate_mapping_status`, `gmx_rate_mapping_blocker_ids` и `gmx_rate_fixture_case_ids`; backend regression tests проверяют новые rows и сохраняют `carry/cost/rank/exec=false`.
- Граница не изменилась: numeric carry bps, route cost bps, route ranking, route selection и execution не включались.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX venue evidence and GMX mapping review v0
- `diagnostic_cost_estimate_v0.summary` получил `venue_evidence_status`: Lighter, Aster, GMX и cross-venue gates теперь разделены по venue-specific evidence, cross-venue blockers и явным `cost/rank/exec=false`.
- `GET /api/v1/perp-dex/route-model` получил read-only `gmx_rate_mapping_review_v0`, который выносит GMX `rate_relation_summary`/`rate_source_fields_summary` в отдельный mapping review без percent, bps, annualized или carry conversion.
- `Perp DEX` UI получил таблицы `Route Diagnostic Venue Evidence Status` и `GMX Rate Mapping Review` с fallback из уже существующих route-model слоёв.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют `venue_evidence_status`, `gmx_rate_mapping_review_v0`, compact `venue_evidence_status_ids` и `gmx_rate_mapping_review_ids`.
- В README/ARCHITECTURE добавлен decision note: до первой numeric route-cost formula нужны source-backed fee tiers, order intent, depth/staleness policy, GMX mapping fixtures, carry horizon/notional, risk gates и отдельное явное решение; route ranking/execution не включались.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX route-ready evidence checklist v0
- `diagnostic_cost_estimate_v0.summary` получил `route_ready_evidence_checklist`: fee schedule, order intent, depth freshness, depth aggregation, carry semantics и risk limits теперь видны как отдельные evidence-gates перед route-ready use.
- `Perp DEX` UI получил таблицу `Route Diagnostic Evidence Checklist`, где каждый gate показывает required inputs, policy inputs, sourced evidence fields, blocked outputs и явные блокировки cost/rank/exec.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `route_ready_evidence_checklist` с components/source fields/depth policy и закрепляют `may_estimate_cost_bps=false`, `may_rank_routes=false`, `may_submit_orders=false`.
- Compact smoke contract теперь включает `route_ready_evidence_gate_ids`, чтобы preview/prod diff ловил исчезновение или перестановку evidence gates.
- Граница не изменилась: checklist является pre-route-scoring observability/readiness layer, а не route cost bps, route ranking, route selection или execution.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic source input actions coverage v0
- `diagnostic_cost_estimate_v0.summary` получил `source_input_action_coverage`: sourced display fields теперь связаны с required route inputs и mapped next actions.
- `Perp DEX` UI получил таблицу `Route Diagnostic Source Input Actions`, где видно, какие display fields уже есть, какие inputs они частично покрывают и какие actions всё ещё блокируют route-ready use.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `source_input_action_coverage` с `source_field_breakdown` и `next_action_breakdown`.
- Compact smoke contract теперь включает `source_input_action_fields`; README фиксирует preview/prod compare пример с `depth_policy_ids` и `next_action_ids`.
- Граница не изменилась: coverage является observability/readiness layer, а не route cost, route ranking, route selection или execution.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic policy input breakdown v0
- `diagnostic_cost_estimate_v0.summary` получил `required_policy_input_breakdown`: required policy inputs из depth/staleness checklist теперь агрегируются по policy rows, components, venues, source endpoints и blockers.
- `Perp DEX` UI получил таблицу `Route Diagnostic Policy Inputs`, где видно, какие policy inputs блокируют Lighter/Aster depth freshness и stale-depth gates перед любым slippage bps.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `required_policy_input_breakdown` с `depth_staleness_policy_checklist` и сохраняют `may_emit_slippage_bps=false`.
- Compact smoke contract теперь включает `required_policy_input_ids`, чтобы preview/prod diff ловил исчезновение или перестановку required policy inputs.
- Граница не изменилась: policy input breakdown является readiness/observability layer, а не route cost, route ranking, route selection или execution.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic next actions breakdown v0
- `diagnostic_cost_estimate_v0.summary` получил `next_action_breakdown`: required-input, readiness rollup и depth/staleness policy actions теперь агрегируются в machine-readable planning layer.
- `Perp DEX` UI получил таблицу `Route Diagnostic Next Actions`, где видно action, source count/types, required inputs, policy inputs, components, venues и boundary для numeric total.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `next_action_breakdown` с `required_input_breakdown`, `readiness_rollup` и `depth_staleness_policy_checklist`.
- Compact smoke contract теперь включает `next_action_ids`, чтобы preview/prod diff ловил исчезновение или перестановку planning actions.
- Граница не изменилась: next-action breakdown является planning/observability layer, а не route cost, route ranking, route selection или execution.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic depth policy and smoke compare v0
- `diagnostic_cost_estimate_v0.summary` получил `depth_staleness_policy_checklist`: Lighter `orderBookOrders`, Aster `ticker/bookTicker` и Aster `fapi/v3/depth` теперь явно требуют timestamp freshness, `max_depth_age_ms`, stale-depth action, order size, side, aggregation policy и liquidity cap перед любым slippage bps.
- `Perp DEX` UI получил таблицу `Route Diagnostic Depth/Staleness Policy` с venue, depth scope, endpoint, source fields, required policy inputs, blockers, slippage boundary и next action.
- `scripts/perp-dex-policy-smoke.sh` теперь проверяет depth/staleness checklist и печатает compact `contract` для route policy/model observability. Через `COMPARE_BASE_URL` можно добавить preview/prod diff summary, а `FAIL_ON_DIFF=1` делает расхождения фейлом.
- Backend regression tests закрепляют, что depth checklist согласован с `diagnostic_cost_estimate_v0.components`, а `may_emit_slippage_bps=false` и `numeric_total_status=blocked` остаются неизменными.
- Граница не изменилась: depth/staleness checklist является observability/policy layer, а не расчётом slippage, total route cost bps, route ranking, route selection или execution.
- Проверка: `tests/test_perp_dex_policy.py`, `compileall app`, `bash -n scripts/perp-dex-policy-smoke.sh`, HTTP `scripts/perp-dex-policy-smoke.sh`, frontend `npm run build`, `npm audit --audit-level=high` и Browser QA проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic observability rollups v0
- `diagnostic_cost_estimate_v0.summary` получил `source_field_breakdown`: sourced display fields теперь агрегируются по component ids, venue ids, required input ids и blocked numeric ids.
- `diagnostic_cost_estimate_v0.summary` получил `safe_use_breakdown`: safe-use boundaries теперь сгруппированы по components, чтобы display diagnostics не выглядели как route signal.
- `diagnostic_cost_estimate_v0.summary` получил `readiness_rollup`: compact fee/depth/carry/risk readiness показывает status, sourced counts, display ids, blocked numeric ids и next action без numeric total bps.
- `Perp DEX` UI получил таблицы `Route Diagnostic Source Fields Breakdown`, `Route Diagnostic Safe Use Breakdown` и `Route Diagnostic Readiness Rollup` с fallback-группировкой из `components`.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency новых breakdown/rollup слоёв с `diagnostic_cost_estimate_v0.components`.
- Граница не изменилась: новые rollups являются observability layer, а не route cost, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic required input breakdown v0
- `diagnostic_cost_estimate_v0.components` получили `required_input_ids`, чтобы component-level diagnostics были связаны с обязательными входами route model.
- `diagnostic_cost_estimate_v0.summary` получил `required_input_breakdown`: по каждому required input теперь видны component ids, venue ids, display ids, blocked numeric ids, sourced ids и next action.
- `Perp DEX` UI получил таблицу `Route Diagnostic Required Input Breakdown` с fallback-группировкой из `required_inputs` и `components`, если backend summary недоступен.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `required_input_breakdown` с `components[*].required_input_ids`.
- Граница не изменилась: breakdown показывает coverage обязательных inputs, но не включает total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py`, `compileall app`, frontend `npm run build` и `npm audit --audit-level=high` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic blocker breakdown v0
- `diagnostic_cost_estimate_v0.summary` получил `blocker_breakdown`: повторяющиеся `blocked_by` причины теперь агрегируются по component ids, venue ids, display component ids и blocked numeric component ids.
- `Perp DEX` UI получил таблицу `Route Diagnostic Blocker Breakdown`, чтобы видеть, какие blockers мешают route-ready cost inputs чаще всего.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `blocker_breakdown` с `diagnostic_cost_estimate_v0.components[*].blocked_by`.
- Граница не изменилась: blocker breakdown является observability layer, а не route cost, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic venue breakdown v0
- `diagnostic_cost_estimate_v0.summary` получил `venue_breakdown`: component counts, display-only ids, blocked numeric ids и sourced ids теперь доступны по Lighter, Aster и cross-venue components.
- `Perp DEX` UI получил таблицу `Route Diagnostic Venue Breakdown`, чтобы видеть venue-level component readiness отдельно от общей summary и детального component list.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency `venue_breakdown` с `diagnostic_cost_estimate_v0.components`.
- Граница не изменилась: venue breakdown является observability layer, а не route cost, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic component summary contract v0
- `GET /api/v1/perp-dex/route-model` получил machine-readable `diagnostic_cost_estimate_v0.summary`: component counts, display-only ids, blocked numeric ids, sourced ids, `numeric_total_status=blocked` и boundary `component_readiness_only`.
- `Perp DEX` UI теперь читает `Route Diagnostic Components Summary` из backend summary, но сохраняет fallback-расчёт из `components` для совместимости со старым response.
- `scripts/perp-dex-policy-smoke.sh` и backend regression tests проверяют consistency между `summary` и `components`, чтобы component diagnostics не расходились с отображаемым summary.
- Граница не изменилась: summary является контрактом наблюдаемости, а не включением total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostic components summary v0
- `Perp DEX` UI получил таблицу `Route Diagnostic Components Summary`: количество diagnostic components, display-only outputs, blocked numeric components, sourced component fields и статус numeric total bps теперь видны отдельным summary-layer перед `Route Cost Diagnostics v0`.
- `scripts/perp-dex-policy-smoke.sh` теперь проверяет структуру `diagnostic_cost_estimate_v0.components`: обязательные component ids, `status`, `source_fields`, `blocked_by`, `safe_use` и запрет total numeric bps.
- Backend regression tests закрепляют полный набор diagnostic component ids и machine-readable поля каждого component.
- Граница не изменилась: summary показывает готовность компонент, но не включает total route cost bps, route ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX route safety guardrails v0
- `Perp DEX` UI получил таблицу `Route Safety Guardrails`: top-level expected vs actual по `research_only`, execution, liquidity ranking, order submission, model read-only, production signal и numeric total bps.
- `scripts/perp-dex-policy-smoke.sh` теперь дополнительно проверяет `route-model.required_inputs` и `formula_skeleton`, включая обязательные ключи `gross_edge_bps`, `estimated_cost_bps`, `net_edge_bps` и `route_allowed`.
- Backend regression tests закрепляют полный набор ключей `formula_skeleton` и непустые formula strings.
- Граница не изменилась: guardrails являются observability/checklist layer, а не включением numeric route cost, ranking, route selection или execution.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX required inputs and direct smoke guardrails v0
- `scripts/perp-dex-direct-smoke.sh` усилен safety-инвариантами по direct venue snapshots: `read_only` должен оставаться `true`, `execution_enabled` должен оставаться `false`, а optional `ranking_enabled` / `production_signal_enabled` не могут стать `true`.
- `Perp DEX` UI получил таблицу `Route Required Inputs`, которая отдельно показывает обязательные входы route model: fee schedule, order intent, depth/impact model, carry horizon и risk limits.
- Regression tests закрепляют структуру `route-model.required_inputs`: у каждого input должны быть `id`, `label` и `reason`.
- Граница не изменилась: таблица required inputs является checklist для следующего research шага, а не разрешением на numeric route cost, ranking или execution.
- Проверка: `bash -n scripts/perp-dex-direct-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX policy smoke and output policy v0
- Добавлен `scripts/perp-dex-policy-smoke.sh` для компактной preview/prod проверки `route-constraints` и `route-model`: read-only режим, выключенные ranking/execution, запрет numeric total bps и структурированные blockers.
- `Perp DEX` UI получил таблицу `Route Output Policy`, где явно видно, какие route-model outputs можно показывать как diagnostics, а какие остаются заблокированы для production scoring.
- `Perp DEX` UI получил таблицу `Route Model Blockers` поверх `route-model.blockers`: missing inputs, blocked-by причины и safe-use формулировки теперь видны отдельно от route-constraints blockers.
- Regression tests усилены общим инвариантом: все route policy/model blockers должны иметь `id`, `severity=blocker`, `reason`, `missing_inputs`, `blocked_by` и `safe_use`; policy blockers дополнительно требуют `scope`.
- Граница не изменилась: numeric route cost bps, route ranking, route selection и order submission остаются выключены до sourced fee/depth/carry inputs, order intent, risk gates и execution boundary.
- Проверка: `bash -n scripts/perp-dex-policy-smoke.sh`, `tests/test_perp_dex_policy.py` и frontend `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Perp DEX diagnostics hardening v0
- Добавлен `scripts/perp-dex-direct-smoke.sh` для компактной server-side проверки direct Perp DEX venue endpoints на preview/prod без вывода raw payload и секретов.
- `Perp DEX` UI получил таблицу `Depth Diagnostics`: display-only best bid/ask, spread и top-depth summaries по direct venues, где источник отдаёт публичную depth/orderbook диагностику.
- `route-constraints` и `route-model` получили структурированные blockers: `missing_inputs`, `blocked_by` и `safe_use`, чтобы явно видеть, что именно мешает numeric route cost, ranking и execution.
- `Perp DEX` UI получил `Route Blockers Matrix` поверх backend policy, чтобы route/execution ограничения были видны рядом с route-cost diagnostics.
- Граница не изменилась: total cost bps, liquidity ranking, route selection и order submission не включались; Lighter/Aster depth остаются display-only diagnostics до order size, side, aggregation policy, liquidity caps, stale-depth policy и risk boundary.
- Проверка: backend Perp DEX regression tests, `compileall app`, frontend `npm run build`, `npm audit --audit-level=high` и `bash -n scripts/perp-dex-direct-smoke.sh` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Aster depth ladder diagnostics v0
- Aster direct snapshot теперь дополнительно читает public `GET /fapi/v3/depth?symbol=...&limit=20` для каждого выбранного USDT perpetual market.
- `AsterClient` нормализует display-only depth ladder: best bid/ask, `top_of_book_spread_bps`, количество bid/ask levels и top-level depth summaries в base/USD.
- `route-constraints` и `route-model` получили capability/component `aster_depth_ladder_diagnostics` / `aster_depth_ladder`.
- Aster depth status повышен до `partial_ready_depth_ladder_display_only`, но slippage bps, order-size aggregation, liquidity caps, stale-depth policy, ranking и execution остаются заблокированы.
- `Perp DEX` UI автоматически показывает новый Aster component в `Route Cost Diagnostics v0`; total cost bps и route ranking не включались.

## [2026-06-17] - [PRODUCT/DATA] - Lighter orderBookOrders depth diagnostics v0
- Lighter direct snapshot теперь дополнительно читает public `GET /api/v1/orderBookOrders?market_id=...&limit=25`.
- `LighterClient` нормализует display-only top resting orders: best bid/ask, `top_of_book_spread_bps`, count bids/asks и top-order depth summaries в base/USD.
- `route-constraints` и `route-model` получили capability/component `lighter_orderbook_orders_depth_diagnostics` / `lighter_top_order_depth`.
- Lighter depth status повышен до `partial_ready_top_orders_only`, но slippage bps, depth aggregation policy, liquidity caps, order size/side и execution остаются обязательными blockers.
- `Perp DEX` UI автоматически показывает новый Lighter component в `Route Cost Diagnostics v0`; route ranking, total cost bps и execution не включались.

## [2026-06-17] - [PRODUCT/DATA] - Diagnostic route-cost components v0
- `GET /api/v1/perp-dex/route-model` получил read-only блок `diagnostic_cost_estimate_v0`: компонентные diagnostics по fees/spread/slippage/carry без суммарного route-cost bps.
- Aster normalizer теперь считает `top_of_book_spread_bps` из `bid_price`/`ask_price` как display-only spread; это не depth curve, не slippage model и не executable liquidity.
- Aster policy получила published USDT-perp fee metadata: maker `0.0` bps и taker `4.0` bps по публичному fee schedule; это default reference metadata, а не account-level fee tier.
- Lighter fee fields остаются `source_fields_available_unit_unconfirmed`: `maker_fee`/`taker_fee` можно показывать как raw public fields, но нельзя включать в numeric route cost без подтверждения units, account tier и order intent.
- `Perp DEX` UI получил таблицу `Route Cost Diagnostics v0`, чтобы показывать компонентную готовность без route ranking, execution и total cost estimate.
- `output_policy.may_show_diagnostic_cost_components=true`, но `may_estimate_cost_bps=false`, `may_rank_routes=false` и execution остаётся выключенным.

## [2026-06-17] - [PRODUCT/DATA] - Lighter/Aster cost semantics metadata v0
- `GET /api/v1/perp-dex/route-constraints` расширен diagnostic-only блоками `cost_input_semantics` для Lighter и Aster.
- Для Lighter явно зафиксировано: `maker_fee`/`taker_fee` являются sourced display fields, но route-level fee estimate всё ещё требует account fee tier, maker/taker side и order intent.
- Для Aster явно зафиксировано: `ticker/bookTicker` даёт top-of-book display fields, но это не depth curve и не slippage model; fee schedule/tier ещё не подключены.
- `GET /api/v1/perp-dex/route-model` теперь показывает source semantics и `cost_input_status` по Lighter/Aster в venue readiness.
- `Perp DEX` UI показывает колонку `Source Semantics` в `Route Model Venue Inputs`, чтобы partial readiness не выглядела как готовый route-cost input.
- Route ranking, numeric cost bps, carry conversion и execution не включались.

## [2026-06-17] - [PRODUCT/DATA] - Aster direct Perp DEX snapshot v0
- Проведён Aster official API review для следующего direct Perp DEX candidate после Lighter.
- Добавлен read-only `AsterClient` поверх публичных Aster Futures endpoints `exchangeInfo`, `premiumIndex`, `ticker/24hr`, `openInterest` и `ticker/bookTicker`.
- Открыт endpoint `GET /api/v1/perp-dex/venues/aster/markets?symbols=BTC,ETH,SOL`; он делает live provider calls, не пишет в PostgreSQL и возвращает `execution_enabled=false`.
- Aster normalizer возвращает direct market rows: mark/index/mid price, funding, OI USD estimate, 24h volume, trades, top-of-book, tick/step size, min notional и `normalization_status=aster_public_futures_market_data`.
- `Perp DEX` UI теперь читает Aster рядом с Hyperliquid/dYdX/Lighter как четвёртый normalized direct venue; GMX остаётся raw diagnostics, CoinGlass остаётся research enrichment.
- Route policy/model обновлены: `aster` добавлен в direct snapshot venues, но fee tier assumptions, depth/slippage model, carry-cost conversion, route ranking и execution остаются заблокированы.
- Проверка: `tests/test_aster_client.py`, `tests/test_lighter_client.py`, `tests/test_perp_dex_policy.py` и `compileall app` проходят.

## [2026-06-17] - [PRODUCT/DATA] - Lighter direct Perp DEX snapshot v0
- По live CoinGlass Perp DEX coverage smoke выбран следующий direct adapter candidate: `Lighter` (`Lighter`, `Aster` получили full `BTC/ETH/SOL` matches; `EdgeX`/`Drift` не вернули rows в текущем smoke).
- Добавлен read-only `LighterClient` поверх публичных Lighter endpoints `orderBooks`, `orderBookDetails` и `funding-rates`.
- Открыт endpoint `GET /api/v1/perp-dex/venues/lighter/markets?symbols=BTC,ETH,SOL`; он делает live provider calls, не пишет в PostgreSQL и возвращает `execution_enabled=false`.
- Lighter normalizer возвращает direct market rows: display price из `last_trade_price`, funding, OI USD estimate, 24h volume, trades, maker/taker fee, margin fractions, tick/step size и `normalization_status=lighter_public_market_details`.
- `Perp DEX` UI теперь читает Lighter рядом с Hyperliquid/dYdX как третий normalized direct venue; GMX остаётся raw diagnostics, CoinGlass остаётся research enrichment.
- Route policy/model обновлены: `lighter` добавлен в direct snapshot venues, но route-level liquidity ranking, slippage/depth model, carry-cost conversion и execution остаются заблокированы.
- Live smoke Lighter endpoint вернул `3` rows для `BTC/ETH/SOL`; у всех rows есть price/funding/OI/volume/fees, execution выключен.
- Проверка: `tests/test_lighter_client.py`, `tests/test_perp_dex_policy.py`, targeted Perp DEX tests, `compileall app` и frontend `npm run build` проходят.

## [2026-06-17] - [OPS/DATA] - CoinGlass Perp DEX coverage smoke script v0
- Добавлен `scripts/coinglass-perp-dex-coverage-smoke.sh` для повторяемой проверки CoinGlass Perp DEX coverage endpoint на preview/prod backend.
- Скрипт вызывает `GET /api/v1/perp-dex/venues/coinglass/markets`, проверяет минимальные thresholds по rows/matched exchanges и печатает compact summary без raw payload и без секретов.
- Параметры `BASE_URL`, `SYMBOLS`, `EXCHANGES`, `MIN_ROWS`, `MIN_MATCHED_EXCHANGES`, `ALLOW_UNAVAILABLE`, `PYTHON_BIN` позволяют запускать один и тот же smoke на `/opt/deltagrid-preview` и `/opt/deltagrid`.
- Query-параметры URL-encoded, поэтому venues с пробелами вроде `ApeX Omni` не ломают запрос.
- Проверка: `bash -n scripts/coinglass-perp-dex-coverage-smoke.sh` проходит; live smoke отложен до запуска на окружении с CoinGlass API key.

## [2026-06-17] - [PRODUCT/DATA] - CoinGlass Perp DEX coverage summary v0
- CoinGlass Perp DEX enrichment snapshot теперь возвращает `coverage_summary` поверх normalized third-party rows.
- Summary включает `total_rows`, `exchanges_with_matches`, `field_totals`, `direct_adapter_candidate_hints` и per-venue `by_exchange`.
- Для каждого venue фиксируются `matched_rows`, `matched_symbols`, `missing_symbols`, `available_field_groups`, `field_coverage`, `route_input_status=not_route_input` и `next_action`.
- `Perp DEX` UI получил отдельную таблицу `CoinGlass Perp DEX Coverage`; это coverage hints для выбора следующего direct adapter, а не liquidity ranking.
- Локальный live smoke пропущен из-за отсутствующего CoinGlass API key в текущей Windows env; проверка не выводила секреты.
- Проверка: `tests/test_coinglass_perp_dex_client.py` и `tests/test_perp_dex_policy.py` проходят, frontend `npm run build` проходит.

## [2026-06-17] - [PRODUCT/DATA] - CoinGlass Perp DEX enrichment v0
- `CoinGlassClient` получил read-only Perp DEX enrichment path поверх CoinGlass futures `coins-markets`.
- Добавлен endpoint `GET /api/v1/perp-dex/venues/coinglass/markets`: по умолчанию проверяются `Aster`, `Lighter`, `EdgeX`, `Drift`, а policy фиксирует candidate venues `Hyperliquid`, `dYdX`, `Aster`, `Lighter`, `EdgeX`, `Drift`, `Paradex`, `Extended`, `ApeX Omni`.
- Endpoint возвращает third-party aggregate rows с `normalization_status=coinglass_coin_market_enrichment`, `execution_enabled=false`, `ranking_enabled=false`, `production_signal_enabled=false`; это не direct venue adapter и не route-level liquidity signal.
- `Perp DEX` UI получил отдельную таблицу `CoinGlass Perp DEX Enrichment`; CoinGlass rows не смешиваются с direct Hyperliquid/dYdX/GMX snapshots.
- `route-constraints` и `route-model` получили capability/blocker для CoinGlass Perp DEX enrichment, чтобы route scoring и execution оставались явно заблокированы.
- Проверка: `tests/test_coinglass_perp_dex_client.py` и `tests/test_perp_dex_policy.py` закрепляют normalizer, endpoint meta и read-only policy; `compileall app` и `npm run build` проходят.

## [2026-06-17] - [PRODUCT/DATA] - GMX rate source fields guardrail v0
- `GmxClient` добавил diagnostic-only `rate_source_fields_status` и `rate_source_fields_summary` для проверки, есть ли в GMX `/markets/info` helper inputs, нужные для пересчёта official `MarketTicker` hourly rates.
- Проверяемые helper inputs: `fundingFactorPerSecond`, `borrowingFactorPerSecondForLongs`, `borrowingFactorPerSecondForShorts`, `longsPayShorts`.
- Live GMX `/markets/info` по текущему payload не отдаёт эти поля: статус `source_factor_fields_unavailable`; endpoint показывает только ticker rate outputs (`fundingRate*`, `borrowingRate*`, `netRate*`).
- `route-model.gmx_rate_semantics.mapping_review` расширен `source_inputs_required`, а `blocked_for_numeric_carry` получил blocker `live /markets/info source helper inputs unavailable`.
- Production carry conversion, route scoring, liquidity ranking и execution не включались.
- Проверка: `tests/test_gmx_client.py` и `tests/test_perp_dex_policy.py` закрепляют source-fields diagnostics и route-model blocker.

## [2026-06-17] - [PRODUCT/DATA] - GMX rate relation summary v0
- `GmxClient` добавил snapshot-level `rate_relation_summary`: counts по side statuses, source relation matches, raw-sum relation matches, nonzero/zero borrowing sides и zero-borrowing ambiguity.
- GMX endpoint meta теперь отдаёт `rate_relation_summary`, чтобы UI/API diagnostics могли видеть live-shape без ручного скрипта.
- Добавлен offline fixture `backend/tests/fixtures/gmx_rate_live_shape_fixture.json`: он закрепляет observed pattern, где одна nonzero-borrowing side совпадает с `funding+borrowing`, а zero-borrowing side остаётся ambiguous.
- `route-model.gmx_rate_semantics` получил `mapping_review` со статусом `source_vs_live_mapping_unresolved` и явным списком diagnostic fields: `rate_semantics_status`, `rate_relation_diagnostics`, `rate_relation_summary`.
- Production carry conversion, route scoring, liquidity ranking и execution не включались.
- Проверка: `tests/test_gmx_client.py` и `tests/test_perp_dex_policy.py` закрепляют summary contract, fixture coverage и read-only policy.

## [2026-06-17] - [PRODUCT/DATA] - GMX rate relation guardrail v2
- `GmxClient` уточнил side-level диагностику GMX raw rate relation: zero-borrowing sides больше не считаются подтверждением `netRate=fundingRate-borrowingRate`, потому при `borrowingRate=0` relation `funding-borrowing` и `funding+borrowing` недискриминируемы.
- Side diagnostics теперь возвращает `source_relation_matches`, `raw_sum_relation_matches`, `borrowing_is_zero` и `zero_borrowing_relation_ambiguous`.
- Live GMX smoke по `BTC/ETH/SOL` вернул `9` rows и `rate_semantics_status=raw_rate_relation_plus_with_zero_borrowing`: `9` nonzero-borrowing sides совпали с `netRate=fundingRate+borrowingRate`, `9` zero-borrowing sides помечены как ambiguous.
- `route-model.gmx_rate_semantics` и `route-constraints` обновлены: blocker теперь сформулирован как live `/markets/info` nonzero-borrowing mapping review, а не как готовая альтернативная формула.
- Production route scoring, carry conversion, liquidity ranking и execution не включались: GMX raw rates остаются metadata/diagnostics до source-level mapping, side-aware fixtures, `holding_period_hours`, `position_notional_usd` и sourced fee/depth/carry inputs.
- Проверка: `tests/test_gmx_client.py` и `tests/test_perp_dex_policy.py` закрепляют zero-borrowing ambiguity и live nonzero-borrowing blocker.

## [2026-06-16] - [PRODUCT/DATA] - GMX rate relation guardrail v0
- `GmxClient` добавил diagnostic-only проверку GMX raw rate fields через exact integer arithmetic без пересчёта в percent, bps или carry cost.
- GMX market rows и endpoint meta теперь возвращают `rate_semantics_status`; при успешной проверке статус равен `hourly_rate_relation_confirmed`.
- Добавлен offline fixture `backend/tests/fixtures/gmx_rate_fixture.json`, который работает как guardrail для ожидаемой source relation без live HTTP-вызова к GMX.
- `GET /api/v1/perp-dex/route-constraints` получил capability `gmx_rate_relation_fixtures=partial_ready`, а `gmx_rate_semantics` в route model переведён в `guardrail_metadata_only`.
- Live GMX smoke по `BTC/ETH/SOL` вернул `9` rows и `rate_semantics_status=raw_rate_relation_mixed`: часть side diagnostics совпадает с `netRate=fundingRate-borrowingRate`, часть — с `netRate=fundingRate+borrowingRate`.
- Production route scoring, carry conversion, liquidity ranking и execution не включались: нужны side-aware funding sign fixtures, `holding_period_hours`, `position_notional_usd` и sourced fee/depth/carry inputs.
- Проверка: `tests/test_gmx_client.py` и `tests/test_perp_dex_policy.py` закрепляют relation fixture, API meta и сохранение блокеров.

## [2026-06-16] - [PRODUCT/DATA] - GMX rate semantics metadata v0
- `GET /api/v1/perp-dex/route-model` расширен блоком `gmx_rate_semantics`: source-backed metadata по `fundingRateLong/Short`, `borrowingRateLong/Short` и `netRateLong/Short`.
- По official `gmx-interface` зафиксировано: `MarketTicker` содержит rate fields, `getMarketTicker` считает их за период `1h`, а `netRateLong/Short = fundingRateLong/Short - borrowingRateLong/Short`.
- По `gmx-interface`/`gmx-synthetics` зафиксировано, что funding sign зависит от paying/receiving side через `longsPayShorts`, а borrowing fee требует side-specific factor, period и `sizeInUsd`.
- `GET /api/v1/perp-dex/route-constraints` получил capability `gmx_rate_semantics_metadata=partial_ready`, но raw GMX rates не конвертируются в percent/bps/carry cost.
- Проверка: `test_perp_dex_policy.py` закрепляет metadata-only статус, official source URLs и blockers `holding_period_hours input` / `position_notional_usd input`.

## [2026-06-16] - [PRODUCT/DATA] - Perp DEX route model v0
- Добавлен read-only endpoint `GET /api/v1/perp-dex/route-model`: он возвращает checklist входов и formula skeleton для route-level fees/slippage/routing без внешних provider calls, без записи в БД и без execution path.
- Route model v0 явно требует sourced inputs перед численными оценками: venue fee schedule/tier, order side/size/notional, depth или price-impact model, carry horizon, rate sign convention и risk limits.
- `GET /api/v1/perp-dex/route-constraints` получил capability `route_cost_model_v0=partial_ready`, но `route_level_pricing`, `multi_venue_liquidity_ranking` и `execution` остаются `blocked`.
- Perp DEX UI показывает `Route Cost Model v0` и `Route Model Venue Inputs` как diagnostic checklist; numeric cost estimates, route ranking и order submission не включены.
- Проверка: `test_perp_dex_policy.py` расширен regression test'ом для `/route-model`, который закрепляет `execution_enabled=false`, `ranking_enabled=false`, blockers по fee/slippage/GMX rates и запрет `may_rank_routes`.

## [2026-06-16] - [PRODUCT/DATA] - GMX OI/liquidity USD diagnostics v0
- `GmxClient` добавил diagnostic-only масштабирование GMX `openInterestLong/Short` и `availableLiquidityLong/Short` из `1e30` USD decimals в строковые поля `*_usd_diagnostic`.
- `open_interest_usd` и production liquidity/ranking поля не заполняются: GMX остаётся raw/partial venue, а новые значения предназначены только для диагностики и ручной сверки.
- `GET /api/v1/perp-dex/route-constraints` получил capability `gmx_oi_liquidity_usd_diagnostics=partial_ready`; `multi_venue_liquidity_ranking` остаётся `blocked`.
- Endpoint meta для GMX возвращает `diagnostic_usd_scale_status`, чтобы быстро видеть, удалось ли масштабировать OI/liquidity diagnostics.
- Проверка: GMX/policy regression tests обновлены для diagnostic USD fields и сохранения route blocker.

## [2026-06-16] - [PRODUCT/DATA] - GMX fixed-point source validation metadata v0
- `GET /api/v1/perp-dex/route-constraints` расширен блоком `gmx_formula_validation` с официальными source URLs, подтверждёнными diagnostic-only scale notes и явным списком GMX fields, заблокированных для production liquidity/OI signal.
- Зафиксировано безопасное разделение: `poolAmountLong/Short` можно показывать только как token-unit diagnostics через decimals из `/tokens`, `Precision` factors используют `1e30`, а `openInterest` и `openInterestInTokens` остаются разными contract paths до маппинга `/markets/info` fields на точные reader outputs.
- `openInterest*`, `availableLiquidity*`, funding/borrowing/net rates не конвертируются и не участвуют в multi-venue liquidity ranking.
- Проверка: route constraints regression test обновлён для `gmx_formula_validation`.

## [2026-06-16] - [PRODUCT/DATA] - GMX pool token amount diagnostics v0
- `GmxClient` теперь масштабирует GMX `poolAmountLong` и `poolAmountShort` в token-unit поля `pool_amount_long_token` и `pool_amount_short_token` через `Decimal` и decimals из GMX `/tokens`.
- GMX market rows получили `token_amount_scale_status` и `token_amount_scale_reason`; snapshot и endpoint meta возвращают snapshot-level `token_amount_scale_status`.
- Perp DEX UI показывает GMX mode как `Raw + Pool Units`, когда token pool amounts успешно масштабированы; GMX остаётся raw/partial venue, а не normalized liquidity source.
- Route policy расширена capability `gmx_pool_token_amount_diagnostics=partial_ready`; blocker для multi-venue liquidity ranking остаётся активным, потому `openInterest*`, `availableLiquidity*`, funding/borrowing/net rates и USD liquidity/OI formulas ещё не валидированы.
- Проверка: targeted GMX/policy tests `3 passed`; `compileall app` проходит.

## [v1.3.1] - 2026-06-16 - Patch release
- Уточнён MVP1 provider inventory gate: `promotion_candidate` для full analytics universe теперь требует `complete_history`, а `chart_ready_candidates` остаются только для preview `/charts` и `/assets`.
- Добавлена summary-разбивка blocker'ов по stream для `/api/v1/data/provider-inventory`, чтобы быстро видеть, какие persisted streams блокируют full promotion.
- Закрыт свежий frontend high advisory `form-data@4.0.5` через lockfile update до `form-data@4.0.6`; `npm audit --audit-level=high` снова проходит.
- Добавлен `scripts/release-preflight.sh` и обновлён release flow для проверки согласованности `VERSION`, frontend package version и lockfile root version.
- Версия проекта поднята до `1.3.1` в `VERSION`, `frontend/package.json` и `frontend/package-lock.json`.

## [2026-06-16] - [PRODUCT/DATA] - Perp DEX route constraints policy v0
- Добавлен read-only endpoint `GET /api/v1/perp-dex/route-constraints`, который возвращает машинно-читаемую policy-границу для Perp DEX без внешних provider calls.
- Policy фиксирует текущий статус `research_only`: market rows можно показывать, но liquidity ranking, route-level pricing и execution заблокированы.
- В policy явно разделены normalized venue snapshots (`hyperliquid`, `dydx`) и raw venue snapshots (`gmx`), а также blockers `gmx_scale_validation_required`, `fees_slippage_model_missing` и `execution_boundary`.
- Perp DEX screen теперь читает route policy и показывает таблицу `Route & Execution Policy`, чтобы блокеры были видны в UI, а не только в документации.
- Добавлен regression test для route constraints endpoint: проверяется `execution_enabled=false`, `production_liquidity_signal=false` и запрет `may_rank_by_liquidity`.

## [2026-06-16] - [PRODUCT/DATA] - GMX token decimals diagnostics v0
- `GmxClient` теперь вместе с `/markets/info` читает GMX Oracle API `/tokens` и резолвит `index/long/short` token metadata для raw market rows.
- В GMX market rows добавлены `index_token_symbol/decimals`, `long_token_symbol/decimals`, `short_token_symbol/decimals`, `scale_validation_status` и `scale_validation_reason`.
- Snapshot-level поле `scale_validation_status` показывает `token_decimals_resolved`, если для всех выбранных GMX rows найдены decimals index/long/short tokens.
- UI Perp DEX теперь показывает GMX mode как `Raw + Decimals`, когда token decimals resolved; `open_interest_usd`, liquidity и funding по GMX остаются `No data`, пока raw fixed-point formulas не валидированы.
- Route policy обновлена: GMX token decimals diagnostics помечены как `partial_ready`, а blocker теперь относится к fixed-point formula validation.
- Проверка: targeted GMX/policy tests `3 passed`; live smoke GMX вернул `9` rows для `BTC/ETH/SOL` со `scale_validation_status=token_decimals_resolved`.

## [2026-06-16] - [PRODUCT/DATA] - GMX Perp DEX raw market snapshot v0
- Добавлен read-only `GmxClient` для GMX public REST `GET /markets/info` через `https://arbitrum-api.gmxinfra.io`.
- Открыт backend endpoint `GET /api/v1/perp-dex/venues/gmx/markets?symbols=BTC,ETH,SOL`, который делает live external provider call, но не пишет в БД и возвращает `execution_enabled=false`.
- GMX поля `openInterest*`, `availableLiquidity*`, `poolAmount*`, `fundingRate*`, `borrowingRate*` и `netRate*` сохраняются как raw fixed-point/token-unit strings; USD/OI/liquidity/funding не нормализуются до отдельной проверки scales и token decimals.
- Perp DEX screen теперь показывает GMX rows как `Raw`/`Partial` рядом с normalized Hyperliquid и dYdX snapshots; KPI считает normalized live venues отдельно, чтобы GMX raw data не выглядел как production liquidity signal.
- Добавлены regression tests для GMX payload normalization и endpoint dependency override без реального HTTP-вызова.
- Проверка: backend GMX test `2 passed`; live smoke GMX вернул `9` raw rows для `BTC/ETH/SOL` со статусом `partial` и `normalization_status=raw_fixed_point`.

## [2026-06-16] - [PRODUCT/DATA] - Hyperliquid Perp DEX live snapshot v0
- Добавлен read-only `HyperliquidClient` для public `POST /info` с `type=metaAndAssetCtxs`: нормализуются mark/mid/oracle price, funding, open interest, 24h volume, premium, impact prices и leverage metadata.
- Открыт backend endpoint `GET /api/v1/perp-dex/venues/hyperliquid/markets?symbols=BTC,ETH,SOL`, который делает live external provider call, но не пишет в БД и не включает execution.
- Perp DEX screen теперь показывает Hyperliquid как live venue, если backend вернул market snapshot; dYdX/GMX остаются pending, а direct execution/fees/slippage/routing не заявляются как подключённые.
- Добавлены regression tests для Hyperliquid payload normalization и endpoint dependency override без реального HTTP-вызова.
- Проверка: backend targeted tests `23 passed`, `compileall app` проходит, frontend `npm run build` проходит.

## [2026-06-16] - [PRODUCT/DATA] - dYdX Perp DEX live snapshot v0
- Добавлен read-only `DydxClient` для dYdX v4 Indexer `GET /perpetualMarkets`: нормализуются oracle price как mark proxy, 24h price change, funding, open interest, 24h volume, trades, margin fractions, tick/step size и leverage estimate.
- Открыт backend endpoint `GET /api/v1/perp-dex/venues/dydx/markets?symbols=BTC,ETH,SOL`, который делает live external provider call, но не пишет в БД и возвращает `execution_enabled=false`.
- Perp DEX screen теперь объединяет Hyperliquid и dYdX live snapshots в одной read-only таблице direct Perp DEX venues; GMX, fees/slippage/routing и execution остаются pending.
- Добавлены regression tests для dYdX payload normalization и endpoint dependency override без реального HTTP-вызова.
- Проверка: backend targeted tests `25 passed`, `compileall app` проходит, frontend `npm run build` проходит; live smoke dYdX вернул `BTC/ETH/SOL`.

## [2026-06-16] - [DATA] - Resolution strategy для promotion blockers
- `GET /api/v1/data/provider-inventory` расширен additive-полями в blocker rows: `resolution_strategy`, `historical_backfill_supported`, `minimum_collection_window_hours`, `resolution_action`, `resolution_reason`.
- В `summary` добавлены разбивки `coverage_blockers_by_resolution_strategy`, `freshness_blockers_by_resolution_strategy`, `promotion_blockers_by_resolution_strategy`.
- Для текущего OKX/CoinGlass/CoinGecko ingestion path `open_interest`, `basis_premium` и `spot_perp_price` классифицируются как `snapshot_accumulation_required`: один запуск с `--lookback-hours 168` не создаёт честную 7d историю для этих потоков.
- `ohlcv`, `funding_rates` и `long_short_ratio` остаются `history_backfill_supported`; `liquidations` классифицируется через `provider_sync_required`, потому sparse coverage может подтверждаться свежим успешным sync-run.
- Regression tests обновлены для chart-ready candidate: partial `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot` теперь явно проверяются как snapshot accumulation blockers.
- Практический вывод для `HYPE/XRP/DOGE/ADA/LINK`: candidates остаются в chart/asset режиме до 7d накопления snapshot-стримов или подключения отдельного historical source для OI/basis/spot-perp.

## [2026-06-16] - [OPS] - Production deploy secrets preflight
- Проверено состояние релиза после `v1.3.1`: `origin/main` находится на `0716f6a`, `origin/preview` на `bc342ae`, деревья веток совпадают, annotated tag `v1.3.1` указывает на commit `0716f6a`.
- Подтверждено, что `Deploy Production` hardening уже находится в `main`: workflow проверяет обязательные `PROD_*`, fingerprint deploy key, ожидаемые значения VPS/user/app dir и только затем запускает `scripts/deploy-compose-stack.sh`.
- GitHub Actions run `27619159104` для `main@0716f6a` завершился success как safe-skip: отсутствуют `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_KEY`, `PROD_APP_DIR`, поэтому `Deploy production` был skipped.
- Локальный deploy key существует в ignored `outputs/deploy-keys`, fingerprint совпадает с workflow: `SHA256:TYYi5IayfvNvxRGC3K/J637w8rkUw/+5QtyvtUFJGsg`.
- Read-only SSH preflight к `root@2.25.143.143` прошёл: `/opt/deltagrid` на `main@0716f6a`, production containers healthy, `scripts/server-smoke.sh` зелёный.
- `Deploy Production` получил ручной `workflow_dispatch` с ограничением на ветку `main`, чтобы после добавления `PROD_*` выполнить контрольный deploy без пустого push.
- Добавлен `Production Healthcheck` GitHub Actions workflow: scheduled/manual проверка public production endpoints `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend.
- Добавлен `scripts/backup-postgres.sh`: reusable PostgreSQL backup через Docker Compose с чтением `POSTGRES_USER`/`POSTGRES_DB` из env-файла и compressed dump в `backups/`.
- Первый production backup текущей PostgreSQL БД выполнен вручную на сервере: `/opt/deltagrid/backups/deltagrid_20260616T132922Z.sql.gz`, gzip integrity check прошёл.
- `scripts/deploy-compose-stack.sh` теперь запускает backup перед production deploy (`BRANCH=main`) по умолчанию; для preview backup остаётся opt-in через `BACKUP_BEFORE_DEPLOY=1`.
- В `BACKLOG.md` зафиксирован рабочий pipeline: CI/CD safety, production ops-наблюдаемость, preview publication, data promotion gate, product data adapters, backtest engine.
- В текущей среде нет `gh` CLI и `GH_*/GITHUB_*` токена; repository secrets нужно добавить вручную в GitHub UI или через авторизованный `gh secret set`, не коммитя private key.

## [2026-06-16] - [RELEASE] - Release preflight для patch-релизов
- Добавлен `scripts/release-preflight.sh` для проверки согласованности `VERSION`, `frontend/package.json` и root version в `frontend/package-lock.json`.
- Скрипт поддерживает ожидаемую версию аргументом или через `EXPECTED_VERSION`, проверку ветки через `RELEASE_BRANCH` и строгую проверку чистого git-дерева; для проверки во время незакоммиченного release bump можно использовать `ALLOW_DIRTY=1`.
- `RELEASES.md` и `README.md` обновлены: preflight добавлен в release flow перед bump/tag для `v1.3.1`.

## [2026-06-16] - [DATA] - Provider inventory blocker breakdown
- `GET /api/v1/data/provider-inventory` получил additive summary-поля `coverage_blockers_by_stream`, `freshness_blockers_by_stream` и `promotion_blockers_by_stream`.
- Разбивка считается из уже построенных persisted coverage/freshness blocker rows и не делает внешних API-вызовов к OKX, CoinGlass, CoinGecko или legacy Binance.
- Regression tests расширены: chart-ready candidate с partial `open_interest`, `basis_premium`, `spot_perp_price` теперь проверяет не только `promotion_candidate=false`, но и ожидаемую stream-разбивку blocker'ов.

## [2026-06-16] - [SECURITY] - Frontend audit repair for `form-data`
- После push commit `2b561bb` GitHub Actions показал `Frontend build` failure, при этом `Backend tests` прошли успешно.
- Причина failure воспроизведена локально: `npm audit --audit-level=high` нашёл новый high advisory для транзитивного `form-data@4.0.5` через `axios`.
- Выполнен production-safe `npm audit fix` без `--force`: `frontend/package-lock.json` обновлён до `form-data@4.0.6` и `hasown@2.0.4`.
- Повторная локальная проверка: `npm audit --audit-level=high` проходит; остаётся только известный moderate `postcss` внутри Next.js, который не блокирует текущий CI gate. `npm run build` проходит на Next.js `15.5.19`.

## [2026-06-16] - [DATA] - Provider inventory policy gate для chart-ready candidates
- `GET /api/v1/data/provider-inventory` теперь явно разделяет `chart_ready_candidates` и `promotion_candidates` через `policy.gates`.
- `promotion_candidate` для full analytics universe требует `complete_history`; статус `core_perp_ready` с partial snapshot/enrichment streams больше не считается full promotion.
- `chart_ready_candidates` остаются разрешением только для preview `/charts` и `/assets`, чтобы можно было смотреть 7d OHLCV candidates без продвижения их в `Market Matrix`, `Arbitrage Scanner` и `Perp DEX`.
- Добавлен regression test для symbol с полной chart-critical 7d coverage и partial `open_interest`, `basis_premium`, `spot_perp_price`: такой symbol получает `chart_ready=true`, но остаётся `promotion_candidate=false` и `next_action=history_completion_required`.
- Документация обновлена: `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md`, `ARCHITECTURE.md`, `README.md`.

## [2026-06-15] - [DATA/OPS] - OKX rate-limit retry for preview cron
- Реальный cron-triggered preview core sync подтвердил проблему: после установки split cron OKX `long_short_ratio` всё ещё мог вернуть HTTP `429` даже на `BTC/ETH/SOL`.
- `OkxAdapter` теперь классифицирует HTTP `429` и OKX rate-limit payload как `RateLimitExceeded`, чтобы существующий `RetryPolicy` выполнял backoff/retry вместо немедленного `partial` sync-run.
- Default pacing для OKX в `GlobalRateLimiter` снижен до более консервативного публичного режима `capacity=5`, `refill_rate=2 req/sec`.
- Добавлен regression test для классификации OKX HTTP `429` в `RateLimitExceeded`.
- Локально проверено: `backend\venv\Scripts\python.exe -m pytest tests\test_okx_adapter.py` из `backend` прошёл `6 passed`, также прошли `py_compile` и `git diff --check`.
- CI `27539771597` и `Deploy Preview` `27539817178` завершились успешно; `/opt/deltagrid-preview` обновился до `725387d`, backend/frontend/PostgreSQL healthy.
- Scheduled preview core cron в `2026-06-15 10:30 UTC` снова получил OKX HTTP `429` на `SOL long_short_ratio`, выполнил retry через `RateLimitExceeded`, повторный запрос вернул `200 OK`, итог sync-run: `fetched=462`, `inserted=461`, `errors=0`.
- Финальный `/api/v1/data/health` на preview: cron diagnostics `healthy`, latest `okx/long_short_ratio` `completed`, свежие `rate_limit=2` остаются только как 24h history от старых partial-run до фикса.

## [2026-06-15] - [OPS] - Preview market sync cron path
- `scripts/install-market-sync-cron.sh` теперь умеет записывать в cron переменные `ENV_FILE`, `COMPOSE_FILE` и `COMPOSE_PROJECT_NAME`, чтобы один installer можно было безопасно использовать для production и preview Compose projects.
- Для preview зафиксирован split cron contract: core symbols пишутся в `/etc/cron.d/deltagrid-preview-market-sync-core`, candidates — в `/etc/cron.d/deltagrid-preview-market-sync-candidates` со сдвигом минут, чтобы снизить OKX derived endpoint burst.
- Production cron по умолчанию не меняется: без `ENV_FILE` и `COMPOSE_PROJECT_NAME` installer сохраняет прежний production-safe path через `/opt/deltagrid`.
- На VPS preview установлены оба cron-файла; ручной core-only и candidate-only sync прошёл `errors=0`. Candidate freshness blockers снизились с `39` до `5`, остался stale funding `8h` по каждому candidate.

## [2026-06-15] - [DATA] - Promotion blocker diagnostics for provider inventory
- `GET /api/v1/data/provider-inventory` расширен additive-диагностикой `coverage_blockers_7d`, `freshness_blockers` и `promotion_blockers` на уровне каждого symbol.
- В `summary` добавлены счётчики `coverage_blockers`, `freshness_blockers` и `promotion_blockers`, чтобы быстро видеть масштаб причин, блокирующих full analytics promotion.
- Новые blocker-поля используют уже рассчитанные persisted coverage/freshness rows и не делают внешних вызовов к OKX, CoinGlass, CoinGecko или legacy Binance.
- Regression tests обновлены: проверяется symbol без coverage, fresh-but-partial candidate и наличие новых summary/symbol fields.
- Локально проверено: `backend\venv\Scripts\python.exe -m pytest tests\test_data_api.py -q` из `backend` прошёл `20 passed`; `python -m compileall backend\app` и `backend\venv\Scripts\python.exe -m compileall backend\app` прошли.

## [2026-06-15] - [DATA/OPS] - Candidate gate diagnostics batch
- `GET /api/v1/data/provider-inventory` расширен additive-полями `summary.chart_ready_candidates` и `policy.chart_ready_candidates`, чтобы явно отделять активы, готовые для `/charts`/`/assets`, от `promotion_candidates` для full analytics universe.
- Добавлен regression coverage для новых provider-inventory полей без изменения существующих `promotion_candidate` и `next_action`.
- Во frontend добавлен компактный scope label выбранного актива: `/charts` показывает `Core` или `Preview Candidate`, `/assets` показывает такой же status badge.
- Добавлен ручной smoke-скрипт `scripts/preview-candidate-smoke.sh`: проверяет candidate `/charts`, `/assets`, 7d OHLCV window rows и отсутствие candidate markers на core-only pages `/market-matrix`, `/arbitrage-scanner`, `/perp-dex`.
- Скрипт проверен против текущего preview VPS через SSH: `HYPE/XRP/DOGE/ADA/LINK` charts/assets и 7d windows прошли, core-only pages остались без candidate markers.

## [2026-06-15] - [OPS] - Deploy SSH diagnostics made non-blocking
- После успешного CI для docs commit `e8ddb1f` workflow `Deploy Preview` run `27533723576` упал на диагностическом шаге `Test preview SSH login`; deploy step не запускался, preview VPS при этом оставался healthy и локальный SSH к `root@2.25.143.143` работал.
- В `deploy-preview.yml` и `deploy-production.yml` шаги `Test SSH login` и `Check app directory` переведены в warning-only diagnostics: они больше не останавливают workflow сами по себе.
- Реальным gating шагом остаётся `Deploy preview` / `Deploy production`: если SSH deploy не сможет подключиться или выполнить `scripts/deploy-compose-stack.sh`, workflow по-прежнему завершится failure.
- Количество попыток deploy увеличено с 2 до 3, пауза между попытками стала нарастающей: `30/60/90` секунд.

## [2026-06-15] - [FRONTEND] - Preview chart candidates scope
- В preview frontend добавлено разделение universe: `CORE_SYMBOLS=BTC/ETH/SOL` остаётся для `Market Matrix`, `Arbitrage Scanner` и `Perp DEX`, а `CANDIDATE_SYMBOLS=HYPE/XRP/DOGE/ADA/LINK` доступны в `/charts` и `/assets` как preview chart/asset candidates.
- Устаревшие UI-подписи `Binance` в affected screens заменены на `OKX` там, где это только отображение текущего primary perp source и не меняет backend-логику.
- Повторная gate-проверка `/api/v1/data/provider-inventory?symbols=HYPE,XRP,DOGE,ADA,LINK&exchange=okx` перед UI promotion показала текущий строгий статус: `promotion_candidates=0`, `ready_for_ui_review=0`, `history_completion_required=5`; у всех 5 symbols `chart_ready=true`, но полный promotion блокируют partial snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Preview CI/CD подтверждён на итоговом commit `57e743a`: CI `success`, `Deploy Preview` run `27533404025` `success`, `/opt/deltagrid-preview` обновлён до `57e743a`, backend/frontend/PostgreSQL healthy.
- Smoke-check preview после deploy: `/charts?symbol=HYPE&interval=1m&range=7d` и `/assets?symbol=ADA` возвращают HTTP `200` и показывают candidate symbols + OKX; `/market-matrix`, `/arbitrage-scanner`, `/perp-dex` возвращают HTTP `200` и остаются scoped к `BTC/ETH/SOL`.
- API smoke для chart windows: `HYPE 1m 7d` отдаёт около `10080` timestamp rows, `LINK 5m 7d` отдаёт около `2016` timestamp rows.

## [2026-06-15] - [OPS] - Preview deploy SSH hardening
- Усилен `Deploy Preview` workflow после flaky failure на шаге `Test preview SSH login`: SSH теперь использует `IdentitiesOnly`, `PreferredAuthentications=publickey`, короткий `ConnectionAttempts=1`, явные `timeout` и controlled retries для login, app-dir check и deploy.
- Аналогичный SSH retry/timeout hardening применён к `Deploy Production`, чтобы production workflow имел тот же безопасный профиль перед отдельной проверкой `PROD_*`.
- Проверка GitHub Actions: CI для commit `4c3dec0` прошёл успешно, `Deploy Preview` run `27532247102` завершился `success`.
- Preview VPS `/opt/deltagrid-preview` автоматически обновился до `4c3dec0`; backend/frontend/PostgreSQL в Compose project `deltagrid-preview` находятся в состоянии `healthy`.

## [2026-06-15] - [DATA] - 72h/7d preview backfill первой expansion group
- На preview выполнен 72h backfill `HYPE/XRP/DOGE/ADA/LINK` через OKX primary path: `fetched=27065`, `inserted=26902`, `errors=0`, OHLCV gaps по `1m/5m/1h` равны `0`.
- На preview выполнен 7d backfill той же группы: `fetched=63125`, `inserted=62858`, `errors=0`, OHLCV jobs по всем symbols/intervals завершились с `gaps=0`.
- `/api/v1/data/coverage?symbols=HYPE,XRP,DOGE,ADA,LINK&exchange=okx&range=7d` показывает `covered=30`, `partial=15`, `missing=0`, `total=45`, `coverage_pct=66.67`.
- 7d coverage по streams: OHLCV `15/15 covered`, funding `5/5 covered`, long/short `5/5 covered`, liquidations `5/5 covered`; partial остаётся у snapshot/enrichment streams `open_interest`, `basis_premium`, `spot_perp_price`.
- Для chart path группа готова: `/api/v1/data/provider-inventory` показывает `backfill_required=0`, `freshness_tracking_required=0`, а у всех 5 symbols `chart_ready=true`; последующая строгая gate-проверка перед full UI promotion зафиксирована отдельной frontend-итерацией выше и требует закрыть `history_completion_required=5` по partial snapshot/enrichment streams.
- Проверен chart window endpoint на preview: `HYPE 1m 7d` отдаёт `10080` свечей, `LINK 5m 7d` отдаёт `2016` свечей.

## [2026-06-15] - [DATA] - Candidate freshness scope для provider inventory
- `/api/v1/data/provider-inventory` теперь строит freshness report по запрошенным candidate symbols, а не только по текущему watched universe `BTC/ETH/SOL`.
- `/api/v1/data/health` сохранён без расширения публичного health scope: основной production SLA по-прежнему относится к текущему UI universe `BTC/ETH/SOL`.
- В ответ `provider-inventory.scope` добавлено `freshness_scope=requested_symbols`, чтобы явно отделять candidate freshness от current UI universe freshness.
- Preview deploy проверен на `HYPE/XRP/DOGE/ADA/LINK`: `freshness_tracking_required=0`, все 5 symbols получили `freshness.worst_status=fresh`, но остаются `history_completion_required` до 72h/7d backfill.
- Добавлен regression test, который проверяет freshness scope для candidate symbol за пределами `BTC/ETH/SOL`.

## [2026-06-15] - [DATA] - Alias expansion и 24h preview sync dry-run
- `SymbolMapper.seed_defaults()` стал идемпотентным: повторный запуск больше не создаёт дубликаты `instruments`/`instrument_aliases` и безопасно обновляет существующие aliases.
- В default aliases добавлена первая малая группа expansion candidates: `HYPE`, `XRP`, `DOGE`, `ADA`, `LINK` для OKX, CoinGlass, CoinGecko и legacy Binance.
- Preview DB засеяна aliases через `SymbolMapper().seed_defaults()`; проверены OKX/CoinGlass/CoinGecko mappings для всех 5 symbols.
- На preview выполнен 24h sync dry-run `HYPE/XRP/DOGE/ADA/LINK` через OKX primary path без расширения UI: `fetched=9035`, `inserted=8986`, `errors=0`.
- OHLCV gaps по `1m/5m/1h` для всех 5 symbols равны `0`; `/data/coverage` за 24h показывает `missing=0`, `covered=30`, `partial=15`.
- До отдельного candidate freshness scope `/data/provider-inventory` оставлял symbols вне promotion candidates с `next_action=freshness_tracking_required`, потому freshness SLA формально покрывал только `BTC/ETH/SOL`.
- Добавлен regression test для idempotent `SymbolMapper` seeding и новых aliases.

## [2026-06-15] - [DATA] - Provider discovery v1 для expansion candidates
- Добавлен read-only CLI `python -m app.adapters.data.discover_provider_universe` для live discovery по OKX, CoinGlass, CoinGecko и legacy Binance без записи в PostgreSQL.
- CLI проверяет candidate symbols из MVP1 inventory: OKX USDT swap instrument/OHLCV/funding/OI/long-short, CoinGlass OKX snapshots/liquidations, CoinGecko spot price и Binance USD-M как legacy diagnostic.
- Добавлены retry/backoff и спокойный OKX pacing, чтобы discovery не ловил ложные `429` на long/short endpoint.
- Preview/VPS discovery выполнен внутри `deltagrid-preview-backend`: OKX/CoinGlass/CoinGecko `healthy`, Binance legacy `blocked_http_451`, все `20/20` symbols получили `eligible_for_24h_sync_dry_run`.
- Добавлены unit tests для parser/readiness/markdown report helpers.

## [2026-06-15] - [DATA] - Provider inventory v0 для расширения universe
- Добавлен read-only endpoint `GET /api/v1/data/provider-inventory`, который строит inventory кандидатов на расширение universe поверх уже сохранённых coverage/freshness сигналов.
- Default candidate set расширен за пределы `BTC/ETH/SOL`: `HYPE`, `XRP`, `DOGE`, `BNB`, `ADA`, `LINK`, `AVAX`, `SUI`, `TON`, `TRX`, `DOT`, `LTC`, `BCH`, `AAVE`, `UNI`, `APT`, `ARB`.
- Endpoint не вызывает OKX, CoinGlass, CoinGecko или legacy Binance: `inventory_mode=persisted_data_only`, `external_provider_calls=false`.
- Для каждого symbol возвращаются readiness status, 24h/7d coverage summary, freshness tracking, `promotion_candidate`, `next_action` и reason. Символы без persisted streams получают `backfill_required` и не попадают в promotion candidates.
- Добавлены regression tests для default candidate list и блокировки symbol без coverage.

## [2026-06-14] - [OPS] - Docker Compose deploy recreate стабилизирован
- `scripts/deploy-compose-stack.sh` больше не использует единый `docker compose up -d --build backend frontend`, который на preview дважды приводил к Docker Compose name-conflict при recreate backend.
- Новый порядок deploy: сначала `compose build backend frontend`, затем явный `compose rm -sf backend frontend`, затем `compose up -d --no-build backend frontend`.
- PostgreSQL container и volume не удаляются; изменение касается только пересоздания app containers `backend` и `frontend`.
- Добавлен `.gitattributes` с `*.sh text eol=lf`, чтобы shell-скрипты не получали CRLF/mixed line endings в Windows workspace.
- Проверка на `/opt/deltagrid-preview`: `sh -n scripts/deploy-compose-stack.sh` проходит, ручной preview deploy завершился без name-conflict, backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.

## [2026-06-14] - [CI/SECURITY] - Frontend audit gate для high/critical advisory
- Проверен Next.js 16 regression path: актуальный stable `next@16.2.9` требует Node `>=20.9.0`, но всё ещё содержит bundled `postcss 8.4.31`, поэтому не закрывает остаточный `moderate` advisory `postcss <8.5.10`.
- Fixed `postcss 8.5.10` найден только в `next@canary`; canary-версия не переводится в production/preview runtime без отдельного решения.
- В `CI` добавлен frontend-шаг `npm audit --audit-level=high`, который блокирует high/critical advisory и при этом не ломает pipeline из-за текущего известного moderate внутри Next.
- `README.md`, `PROJECT_PLAN.md` и `BACKLOG.md` обновлены под новый security baseline и оставшийся upstream follow-up.

## [2026-06-14] - [FRONTEND/SECURITY] - Next.js обновлён до 15.5.19
- Frontend dependency `next` обновлена с `14.1.0` до `15.5.19`, чтобы закрыть critical/high advisory из старой версии.
- App Router страницы `/assets`, `/charts`, `/funding` и `/perp-dex` мигрированы на async `searchParams`, который требуется Next.js 15 при production build.
- `scripts/server-smoke.sh` переключён с проверки корня frontend на `/market`, чтобы deploy smoke оставался строгим по HTTP `200` и не падал на ожидаемом redirect `/ -> /market`.
- `README.md` и `ARCHITECTURE.md` обновлены до актуального стека Next.js 15.
- Проверка локально: `npm run build` во `frontend` проходит на Next.js `15.5.19`.
- `npm audit --json` после апгрейда показывает `0 high`, `0 critical` и `2 moderate`; остаточный риск связан с bundled `postcss <8.5.10` внутри Next и вынесен в отдельный regression pass для Next.js 16.x или upstream patch.

## [2026-06-14] - [OPS] - Production deploy diagnostics подготовлены в preview
- В ветке `preview` подготовлен hardening для `Deploy Production`: явные `configured/missing` шаги для `PROD_*`, проверка fingerprint deploy key, expected values для `2.25.143.143/root//opt/deltagrid`, warning-only TCP port probe, SSH login retry и проверка production app dir перед deploy.
- Safe-skip семантика сохранена: если обязательный production secret отсутствует, workflow не должен падать на value-check шагах.
- Preview workflow также получил guard для value-check шагов, чтобы пустой secret не превращал safe-skip в failure.
- Изменение пока не активировано на `main`; production `/opt/deltagrid` не менялся и остаётся healthy.
- Проверка после preview auto-deploy: `/opt/deltagrid-preview` обновился до `9aab346`, backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.

## [2026-06-14] - [OPS] - Preview Nginx HTTP pre-stage
- На VPS заранее включён отдельный Nginx site `deltagrid-preview` для `preview.deltagrid.pro`: frontend проксируется на `127.0.0.1:3012`, backend/API/WebSocket — на `127.0.0.1:8011`.
- Production site `deltagrid` не изменялся; `nginx -t` прошёл успешно, Nginx reload выполнен.
- Проверка без публичного DNS через `Host: preview.deltagrid.pro` прошла: backend readiness возвращает `ready`, `/` и `/charts?symbol=BTC&interval=1m&range=7d` возвращают HTTP `200`.
- DNS `preview.deltagrid.pro` пока не резолвится, поэтому Let's Encrypt SSL ещё не выпускался. Следующий шаг: добавить DNS `A preview -> 2.25.143.143`, затем запустить `scripts/configure-preview-nginx-ssl.sh`.

## [2026-06-14] - [OPS] - Preview auto-deploy через GitHub Actions
- GitHub repository secrets `PREVIEW_SSH_HOST`, `PREVIEW_SSH_USER`, `PREVIEW_SSH_KEY` и `PREVIEW_APP_DIR` доведены до рабочего состояния для preview deploy.
- Workflow `Deploy Preview` прошёл end-to-end: readiness обязательных secrets, fingerprint deploy key, SSH port/login, проверка `/opt/deltagrid-preview` и сам deploy step.
- Preview VPS `/opt/deltagrid-preview` обновлён через GitHub Actions; контрольные probes `1e1371c` и `6e8edb2` подтвердили реальный deploy, backend/frontend/PostgreSQL в Compose project `deltagrid-preview` находятся в состоянии `healthy`.
- Preview workflow усилен после flaky GitHub runner: TCP port probe переведён в warning-only diagnostics, SSH login получил явные timeout/keepalive и retry.
- Проверка после auto-deploy: `BASE_URL=http://127.0.0.1:8011 FRONTEND_URL=http://127.0.0.1:3012 sh scripts/server-smoke.sh` прошёл.
- Production deploy в этой итерации не менялся; следующий ops-шаг — DNS/Nginx/SSL для `preview.deltagrid.pro` и отдельная проверка `PROD_*` secrets.

## [2026-06-14] - [RELEASE/OPS] - Preview domain и deploy runbooks
- Восстановлен `AGENTS.md` как проектный файл правил для Codex/AI-агентов; локально файла не было, хотя workflow проекта его требует.
- Добавлен preview Nginx template `deploy/nginx/deltagrid-preview.conf.example`: frontend `127.0.0.1:3012`, backend/API/WebSocket `127.0.0.1:8011`, домен `preview.deltagrid.pro`.
- Добавлен `scripts/configure-preview-nginx-ssl.sh` для безопасной публикации preview-домена: DNS-precheck, отдельный site `deltagrid-preview`, отдельный Let's Encrypt сертификат, без изменения production site `deltagrid`.
- Добавлен DNS-чеклист `deploy/dns/preview.deltagrid.pro.md` с Cloudflare/DNS записью, командами проверки и smoke-check после SSL.
- Добавлен чеклист `deploy/github-actions-secrets.md` для repository secrets `PREVIEW_*` и `PROD_*`, включая создание dedicated SSH key и проверку первого auto-deploy.
- Создан dedicated SSH deploy key `github-actions-deltagrid-deploy`; public key добавлен на VPS в `/root/.ssh/authorized_keys`, non-interactive login проверен. Private key сохранён локально в `outputs/deploy-keys/` и не коммитится.
- `main` fast-forward синхронизирован с `preview` на ops commit `104502e`, потому что `workflow_run` использует deploy workflows из default branch. Production checkout `/opt/deltagrid` также fast-forward обновлён без rebuild; local smoke-check прошёл.
- Preview deploy probe `fdb08ec` показал, что workflow запускается после preview CI, но deploy пока safe-skip из-за отсутствующих или неполных GitHub secrets `PREVIEW_*`.
- Deploy workflows получили безопасную диагностику readiness: логи показывают только `configured/missing` для обязательных SSH secrets, без вывода значений.
- Документация обновлена: `README.md`, `DEPLOYMENT.md`, `RELEASES.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md`, `BACKLOG.md`.
- Фактическая проверка перед правками: `preview.deltagrid.pro` ещё не резолвится; production и preview containers на VPS находятся в состоянии `healthy`.

## [2026-06-14] - [RELEASE/OPS] - Preview stack contract
- Добавлен `.env.preview.example` для отдельного dev/staging стенда: `preview.deltagrid.pro`, ports `8011/3012`, отдельные PostgreSQL credentials и runtime tuning.
- `.gitignore` дополнен `.env.preview`, чтобы реальные preview secrets не попадали в Git.
- Добавлен общий `scripts/deploy-compose-stack.sh`, который делает `git pull --ff-only`, запускает нужный Compose project и прогоняет smoke-check для выбранного стенда.
- `scripts/deploy-compose-stack.sh` ждёт healthcheck `postgres`, `backend` и `frontend` перед smoke-check, чтобы deploy не падал на race condition сразу после старта frontend.
- `scripts/sync-market-data.sh` теперь поддерживает `COMPOSE_PROJECT_NAME`, чтобы market sync можно было запускать против preview stack без риска затронуть production containers/volume.
- GitHub workflows `Deploy Preview` и `Deploy Production` переведены на общий deploy script и разные defaults: preview использует `.env.preview`/`deltagrid-preview`/`8011/3012`, production использует `.env.production`/`deltagrid`/`8000/3001`.
- Preview stack поднят на VPS в `/opt/deltagrid-preview`: backend `127.0.0.1:8011`, frontend `127.0.0.1:3012`, PostgreSQL volume `deltagrid-preview_postgres_data`.
- Preview 7d sync BTC/ETH/SOL завершён с `errors=0`; `/api/v1/data/health` показывает OKX/CoinGlass/CoinGecko `healthy`, freshness `24/0/24`, `core_perp_ready=3`, `chart_ready=3`.
- Production stack после preview rollout повторно проверен через local smoke; containers остаются healthy.
- Документация обновлена под dev/prod разделение: `README.md`, `DEPLOYMENT.md`, `RELEASES.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md`, `BACKLOG.md`.

## [2026-06-14] - [RELEASE/OPS] - Baseline `v1.3.0` и GitHub CI/CD
- Зафиксирована корневая версия `VERSION=1.3.0`; frontend package version поднят до `1.3.0`.
- Добавлен `RELEASES.md` с правилами SemVer, ветками `preview/main`, release flow и назначением файлов `CHANGELOG.md`, `CURRENT_TASK.md`, `PROJECT_PLAN.md`, `BACKLOG.md`, `ARCHITECTURE.md`.
- Добавлен GitHub Actions workflow `CI`: backend tests, `compileall app`, frontend `npm ci` и `npm run build`.
- `CI` устанавливает `pytest` отдельно от backend runtime dependencies, чтобы production `requirements.txt` не раздувался тестовыми пакетами.
- Backend CI запускает `pytest tests`, чтобы legacy smoke scripts `test_api.py` и `regression_test.py` не исполнялись как unit tests без поднятого сервера.
- Добавлены GitHub Actions workflows `Deploy Preview` и `Deploy Production`; они деплоят `preview` и `main` по SSH после успешного CI, если соответствующие secrets настроены.
- Deploy workflows дополнительно проверяют `workflow_run.head_branch`, чтобы preview deploy не запускался от `main` CI и production deploy не запускался от `preview` CI.
- Deploy workflows безопасно пропускают deploy, если SSH secrets ещё не заведены в GitHub.
- `.gitignore` дополнен `outputs/`, чтобы локальные логи и временные deploy-архивы не попадали в release commit.

## [2026-06-14] - [DATA/FRONTEND] - Production universe v1
- Добавлен read-only endpoint `GET /api/v1/data/universe`, который классифицирует symbols поверх coverage/freshness сигналов.
- Universe readiness статусы: `complete_history`, `core_perp_ready`, `partial_history`, `not_ready`.
- `/api/v1/data/health` теперь включает блок `universe` с `policy.ui_universe`, `deferred_symbols` и per-symbol summary.
- `/data-health` получил таблицу `Production Universe`: symbol, status, chart readiness, 24h/7d coverage, partial/missing streams и reason.
- Правило MVP1: показывать symbol в primary UI universe только если chart-critical streams покрыты, freshness зелёный и нет missing tracked streams.
- Добавлен regression test: symbol без persisted coverage классифицируется как `not_ready` и попадает в `deferred_symbols`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/universe?symbols=BTC,ETH,SOL&exchange=okx` показывает `core_perp_ready=3`, `chart_ready=3`, `not_ready=0`; `policy.ui_universe=["BTC","ETH","SOL"]`.
- Все три symbol имеют partial enrichment streams на `7d`: `open_interest:1h`, `basis_premium:snapshot`, `spot_perp_price:snapshot`; missing streams нет.
- SSR-проверка `/data-health` вернула `200` и подтвердила наличие блока `Production Universe`.
- Проверка локально: backend `pytest` — `26 passed`; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - Coverage matrix для data-layer
- Добавлен read-only endpoint `GET /api/v1/data/coverage` для инвентаризации покрытия истории по `symbol + exchange + stream + interval`.
- `/api/v1/data/health` расширен полем `coverage` без breaking changes: старые поля health, freshness и sync diagnostics сохранены.
- Coverage matrix считает регулярные потоки по ожидаемой cadence в окне `24h/7d`: OHLCV, funding, OI, long/short, basis и отдельный поток `spot_perp_price`.
- Для sparse stream `liquidations` coverage учитывает свежий успешный `coinglass/liquidations` sync-run, чтобы отсутствие событий не считалось отсутствием provider coverage.
- `/data-health` получил KPI `Coverage` и таблицу `Coverage Matrix` с rows/expected, coverage %, latest timestamp и reason.
- Добавлены regression tests для `/data/coverage`, unsupported range и включения `coverage` в `/data/health`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/coverage?symbols=BTC,ETH,SOL&exchange=okx&range=24h` показывает `covered=27/27`, `missing=0`.
- Production `7d` coverage показывает `covered=18`, `partial=9`, `missing=0`: partial сейчас у `open_interest` и `basis/spot_perp_price`, что даёт честный вход для production universe v1.
- SSR-проверка `/data-health` вернула `200` и подтвердила наличие блока `Coverage Matrix`.
- Проверка локально: backend `pytest` — `25 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - OHLCV window endpoint для charts
- Добавлен read-only endpoint `GET /api/v1/data/ohlcv/window` для interactive charts: он возвращает bounded OHLCV окно по `symbol`, `exchange`, `interval` и `range` без клиентской постраничной сборки через `/data/ohlcv`.
- Поддерживаемые интервалы: `1m`, `5m`, `1h`; диапазоны: `2h`, `8h`, `24h`, `7d`; максимальный размер окна ограничен `20000` строками.
- Если `end` не задан, endpoint сам использует последнюю доступную свечу в PostgreSQL как правый край окна, что сохраняет поведение Charts v0 при рассинхроне локального времени и production dataset.
- `/charts` переключён на `/data/ohlcv/window`; старая клиентская постраничная сборка оставлена fallback path, если endpoint временно недоступен.
- Добавлены regression tests для latest-anchored окна и unsupported interval.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/ohlcv/window?symbol=BTC&exchange=okx&interval=1m&range=7d` возвращает `count=10080`, `expected_rows=10080`, `limit=20000`, `window_source=latest_available`.
- Browser QA `/charts?symbol=BTC&interval=1m&range=7d` подтвердил chart container `935x520`, `7` canvas, `10,080` свечей и отсутствие `No candle data`.
- Проверка локально: backend `pytest` — `23 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-14] - [DATA/FRONTEND] - Sparse liquidation freshness
- Исправлена семантика freshness SLA для sparse event stream `liquidations`: старый timestamp последнего события больше не помечает поток как stale, если последний `coinglass/liquidations` sync-run свежий и завершён успешно.
- `/api/v1/data/health` теперь добавляет для sparse streams поля `freshness_mode`, `sync_provider`, `sync_type`, `latest_sync_status`, `latest_sync_at`, `latest_successful_sync_at`, `sync_age_minutes`, `sync_stale_after_minutes` и `sync_degraded_after_minutes`.
- `/data-health` показывает для sparse streams возраст как `event ... / sync ...`, чтобы было видно различие между отсутствием свежих ликвидационных событий и проблемой ingestion path.
- Добавлен regression test: старый `SOL/okx/liquidations/1h` event при свежем `coinglass/liquidations` sync остаётся `fresh` с reason `no recent liquidation events`.
- Fix задеплоен на `deltagrid.pro`; backend/frontend/PostgreSQL healthy, `scripts/server-smoke.sh` прошёл.
- Production `/api/v1/data/health` после deploy показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`; `SOL/okx/liquidations/1h` имеет `status=fresh`, `freshness_mode=sparse_event`, `sync_provider=coinglass`, `sync_type=liquidations`.
- Browser QA `/data-health` подтвердил `24/24`, колонку `Event / sync age` и reason `no recent liquidation events`.
- Проверка локально: backend `pytest` — `21 passed`; `compileall app` проходит; frontend `npm run build` проходит.

## [2026-06-13] - [DEPLOY/FRONTEND] - Production Interactive Charts v0
- Charts v0 задеплоен на `deltagrid.pro`: frontend image пересобран с `lightweight-charts`, stack поднят через `docker-compose.prod.yml`, backend/frontend/PostgreSQL находятся в состоянии `healthy`.
- Перед файловым deploy сохранён backup затрагиваемых серверных файлов в `/tmp/deltagrid-deploy-backups/charts-v0-predeploy-20260613_161655.tgz`.
- Локальный server smoke на VPS прошёл: backend health, readiness, data health и frontend вернули `ok`.
- Публичные smoke-checks прошли: `/api/v1/health/readiness`, `/api/v1/data/health`, `/charts?symbol=BTC&interval=1m&range=7d` и `/charts?symbol=ETH&interval=5m&range=24h` возвращают `200`.
- Browser QA на production подтвердил desktop `BTC 1m 7d`: chart container `935x520`, `10,080` свечей, canvas отрисован, `No candle data` отсутствует.
- Browser QA на production подтвердил mobile `ETH 5m 24h`: chart container `309x520`, `288` свечей, sidebar скрыт, горизонтального overflow нет.
- Production `/api/v1/data/health` после deploy показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, OKX/CoinGlass/CoinGecko `healthy`, Binance `degraded` как legacy/diagnostic provider.

## [2026-06-13] - [FRONTEND] - Interactive Charts v0 локально
- Добавлен первый production-oriented слой интерактивных графиков на `lightweight-charts`: OHLCV candles, volume histogram, crosshair OHLC/volume панель, pan/zoom/scroll и выбор `BTC/ETH/SOL`, интервала `1m/5m/1h`, диапазона `2h/8h/24h/7d`.
- `/charts` читает проверенную OKX USDT Swap историю через существующие read-only data-layer endpoints без изменения backend API-контракта. Для 7d `1m` режима frontend собирает окно постранично поверх текущего лимита `/data/ohlcv` в 1000 строк.
- Данные для окна строятся от последней доступной свечи в PostgreSQL, а не от локального `Date.now()`, чтобы интерфейс корректно работал при расхождении времени тестового окружения и production dataset.
- Исправлена мобильная ширина терминала: sidebar скрывается на малых viewport, поэтому chart canvas получает рабочую область вместо узкой колонки.
- Проверка: frontend `npm run build` проходит; Browser QA через SSH tunnel к production backend подтвердил `BTC 1m 7d` с `10,080` свечами на desktop и `ETH 5m 24h` с `288` свечами на mobile, без `No candle data`.
- Статус обновлён: production deploy выполнен отдельной итерацией выше.

## [2026-06-13] - [DEPLOY/DATA] - Production Data Quality Gate и 7d backfill
- Data Quality Gate diagnostics задеплоены на `deltagrid.pro`: `/api/v1/data/health` отдаёт `freshness`, `sync_health_by_type` и `sync_diagnostics`, а `/data-health` показывает `Freshness SLA`, `Sync Types`, `Cron Diagnostics` и `Recent Error Classes`.
- Production smoke-check прошёл локально на сервере и через домен: backend health, readiness, data health и frontend возвращают `ok`.
- После деплоя production health показывает `freshness.summary={fresh:24, stale:0, degraded:0, total:24}`, cron-path `healthy`, OKX/CoinGlass/CoinGecko `healthy`; Binance остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451`.
- Первый host-level cron после деплоя и 7d backfill сработал в `2026-06-13 00:15 UTC` и завершился `fetched=465`, `inserted=460`, `errors=0`; health после cron показывает `last_run_age_minutes≈1` и cron status `healthy`.
- 72h OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `fetched=16239`, `inserted=16308`, `errors=0`; SQL-проверка покрытия показала `4320/864/72` строк на каждый символ и `gaps=0`.
- 7d OKX backfill BTC/ETH/SOL по `1m/5m/1h` завершён `fetched=37875`, `inserted=38103`, `errors=0`; SQL-проверка покрытия показала `10080/2016/168` строк на каждый символ и `gaps=0`.
- Production row counts после 7d backfill и cron: `ohlcv=77819`, `funding_rates=2442`, `open_interest=4329`, `liquidations=1930`, `long_short_ratio=1068`, `basis_premium=2310`, `provider_sync_runs=5351`.

## [2026-06-13] - [DATA/FRONTEND] - Data Quality Gate diagnostics
- `/api/v1/data/health` расширен без breaking changes: старые поля `providers`, `last_sync`, `row_counts` и `data_quality` сохранены, добавлены `freshness`, `sync_health_by_type` и `sync_diagnostics`.
- `freshness` считает SLA по `BTC/ETH/SOL`, `exchange=okx`, streams `ohlcv`, `funding_rates`, `open_interest`, `long_short_ratio`, `liquidations`, `basis_premium` и интервалам `1m/5m/1h/8h/snapshot`.
- `sync_health_by_type` разделяет provider health по `provider_name + sync_type`, чтобы частичные ошибки одного потока не скрывали состояние остальных потоков.
- `sync_diagnostics` показывает cron-path состояние из `provider_sync_runs`: последний запуск, последний успешный запуск, records fetched/inserted и классы ошибок `http_451`, `rate_limit`, `circuit_breaker`, `empty_response`.
- `/data-health` получил таблицы `Freshness SLA`, `Sync Types`, `Cron Diagnostics` и `Recent Error Classes`.
- Проверка: backend `pytest` — `20 passed`; `compileall app` проходит; frontend `npm run build` проходит; локальный HTTP smoke `/data-health` через `next start` вернул `200`.

## [2026-06-13] - [DEPLOY/DATA] - OKX primary на production
- OKX primary flow задеплоен на `deltagrid.pro`: backend и frontend Docker images пересобраны, `deltagrid-backend-1`, `deltagrid-frontend-1` и `deltagrid-postgres-1` находятся в состоянии `healthy`.
- Перед распаковкой на сервере создан backup изменяемых файлов: `/tmp/deltagrid-okx-predeploy-20260612_233017.tgz`.
- Ручной production sync `BTC,ETH,SOL` за 24 часа с `--primary-perp-provider okx` завершился без ошибок: `fetched=5421`, `inserted=5439`, `errors=0`.
- Проверен cron-path без явного provider flag: `/etc/cron.d/deltagrid-market-sync` вызывает `scripts/sync-market-data.sh`, а новый default пишет OKX OHLCV/OI/long-short, CoinGlass liquidations и CoinGlass snapshots с `exchange_list=OKX`; контрольный прогон завершился `errors=0`.
- `/api/v1/data/health` теперь показывает `okx healthy`; последние OKX sync-runs завершены успешно, Binance остаётся `degraded` как legacy/diagnostic provider из-за HTTP `451` на текущем VPS.
- Production row counts после проверки: `ohlcv=46277`, `funding_rates=2373`, `open_interest=4299`, `liquidations=1288`, `long_short_ratio=636`, `basis_premium=2295`, `provider_sync_runs=5316`.
- Прямые API-проверки с `exchange=okx` возвращают данные для OHLCV, funding, open interest, long/short ratio, liquidations и basis; frontend routes `/market`, `/charts?symbol=BTC`, `/assets?symbol=BTC`, `/funding`, `/perp-dex`, `/data-health` отвечают `200`.

## [2026-06-13] - [DATA/FRONTEND] - OKX primary perp provider
- Добавлен `OkxAdapter` для public OKX USDT swap data: OHLCV candles, funding history, open interest snapshots и long/short account ratio.
- `sync_market_data` получил флаг `--primary-perp-provider` и по умолчанию использует `okx`; `binance` сохранён как legacy/diagnostic option.
- CoinGecko-derived `basis_premium` теперь может считаться от последнего primary perp close; для OKX это `CoinGecko spot vs OKX 1m perp close`.
- CoinGlass aggregated liquidations теперь получают exchange list по primary provider и могут записывать строки с `exchange=okx`.
- CoinGlass funding/OI snapshots теперь тоже принимают exchange list по primary provider, чтобы enrichment-слой не оставался скрыто привязанным к Binance.
- `/api/v1/data/health` начал отслеживать provider `okx` вместе с `binance`, `coinglass` и `coingecko`.
- Terminal frontend read-side переключён на `exchange=okx` для persisted OHLCV, funding, OI, long/short, basis и asset liquidations; UI captions больше не обещают Binance как primary source.
- Добавлены regression tests для OKX normalization: candle volume, funding realized rate, OI snapshot, long/short ratio conversion и interval mapping.
- Проверка: backend tests `19 passed`; `compileall app` проходит; frontend `npm run build` проходит. Local OKX sync smoke на in-memory SQLite записал 15 BTC 1m candles, 1 OI snapshot и 3 long/short points без ошибок.

## [2026-06-13] - [AUDIT/PLAN] - Production data health и старт MVP1
- Проведён обзор состояния после MVP0: public smoke-check `https://deltagrid.pro`, `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health` и frontend проходят.
- Проверено состояние сервера по SSH: `cron` активен, `deltagrid-backend-1`, `deltagrid-frontend-1` и `deltagrid-postgres-1` healthy, host-level cron установлен на запуск market data sync каждые 15 минут.
- Зафиксировано накопление PostgreSQL data-layer: `ohlcv=41000`, `funding_rates=2340`, `open_interest=4260`, `liquidations=1193`, `long_short_ratio=564`, `basis_premium=2271`, `provider_sync_runs=5260`.
- Обнаружен production-блокер свежести CEX-данных: Binance Futures API на сервере возвращает HTTP `451`, из-за чего Binance OHLCV/funding/OI/L/S стали stale, а `/data/health` показывает `binance degraded`.
- Подтверждено, что CoinGlass/CoinGecko ветка продолжает обновляться: snapshots, basis и aggregated liquidations пишутся в PostgreSQL; проблема локализована в direct Binance FAPI path.
- `PROJECT_PLAN.md` и `BACKLOG.md` обновлены под новую стадию MVP1: data freshness SLA, provider health по потокам, cron diagnostics, backfill после восстановления provider path и только затем interactive charts/backtest foundation.
- Проверка локального дерева: backend `pytest` — `14 passed`; `compileall app` проходит; frontend `npm run build` проходит с `BACKEND_INTERNAL_URL=https://deltagrid.pro`.

## [2026-06-05] - [FRONTEND] - Presentation safety sweep
- Заменены грубые demo-формулировки в UI: `No mock fallback` -> `Live data only`, `No fake PnL` -> `Real PnL only`, `no fake DEX volume/OI` -> `direct DEX volume/OI pending`.
- `/backtests` заменён с `Coming Soon` на честный `Backtest History / Engine pending` readiness-state со ссылкой в `Strategy Lab`.
- `Strategy Lab` и provider screens сохраняют честную границу: реальные inputs показываются, synthetic PnL/performance скрыты до production backtest engine.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, контейнеры healthy, `server-smoke.sh` зелёный. HTML sweep подтвердил `200` и отсутствие `Application error`/грубых demo-labels на маршрутах `/market`, `/charts?symbol=BTC`, `/assets?symbol=ETH`, `/funding`, `/perp-dex`, `/arbitrage-scanner`, `/market-matrix`, `/strategy-lab`, `/backtests`; Browser QA подтвердил `Live data only`, `Real PnL only`, `Backtest Output Boundary`, `Backtest History / Engine pending` и heatmap без `USDT/USDE/USDH`.

## [2026-06-05] - [FRONTEND] - Strategy Lab readiness polish
- `Strategy Lab` больше не показывает пустой chart placeholder в `Backtest Output`: вместо этого добавлена таблица `Backtest Output Boundary` с PnL/equity, drawdown/Sharpe, trade log и execution как pending/disabled до реального engine.
- Price/funding input charts получили форматирование осей и hover-title с ценой/фандингом.
- Верхняя workspace-вкладка `/strategy-lab` переименована из `Backtest #1` в `Strategy Lab / Readiness`, чтобы не обещать fake backtest run.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. `/strategy-lab` возвращает `200`, Browser QA подтвердил `Strategy Lab / Readiness`, `Backtest Output Boundary`, `No fake PnL` и отсутствие `Backtest #1`.

## [2026-06-05] - [FRONTEND] - Final demo polish: Funding, Arbitrage, Matrix
- `Funding` получил source-плашки по assets/providers/storage, историю с реальными time labels вместо индексов и hover-title на funding chart.
- Funding matrix теперь показывает пустые ячейки нейтрально, а не как отрицательный сигнал; captions явно указывают persisted Binance/CoinGlass rows from PostgreSQL.
- `Arbitrage Scanner` убрал dev-like opportunity id из первой колонки: теперь таблица показывает candidate, type, legs, basis edge, funding, OI, evidence и risk note.
- `Market Matrix` получила колонку `Coverage` и status в source table, чтобы partial/missing streams выглядели как состояние данных, а не визуальная ошибка.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. Финальный route pass подтвердил `/market`, `/charts?symbol=BTC`, `/assets?symbol=ETH`, `/funding`, `/perp-dex`, `/arbitrage-scanner`, `/market-matrix` без runtime error; Browser QA подтвердил новые панели Funding/Arbitrage/Matrix.

## [2026-06-05] - [FRONTEND] - Assets symbol polish перед демо
- `Assets` больше не показывает hardcoded `SOLUSDT` в блоке order book: заголовок и empty-state строятся от выбранного `BTC/ETH/SOL`.
- Liquidation progress bars в `Assets` теперь рассчитываются от реальных long/short totals, а не от фиксированных demo widths.
- Верхняя workspace-вкладка для `/assets` переименована из `SOL` в `Assets`, а `/charts` больше не помечается как `Placeholder`.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный. `/assets?symbol=BTC`, `/assets?symbol=ETH`, `/assets?symbol=SOL` возвращают правильные `BTCUSDT/ETHUSDT/SOLUSDT` labels без чужих pair labels; Browser QA подтвердил `Assets / Deep Dive` и `Charts / Live Streams`.

## [2026-06-05] - [FRONTEND] - Perp DEX live readiness screen
- `Perp DEX` больше не выглядит как пустой pending-экран: страница переиспользует live `Market Matrix`, `Arbitrage Scanner` и `Data Health` потоки без добавления fake DEX volume/OI.
- Добавлены KPI по live perp inputs, pending direct DEX adapters, largest OI, funding rows, liquidation rows и largest basis/funding edge.
- Добавлены таблицы `Perp Universe Readiness`, `Venue Adapter Status`, `Persisted Perp Data Coverage`, `Provider Health` и `Perp Research Candidates`.
- Direct Hyperliquid/dYdX/GMX adapters явно остаются `Pending`, а Binance/CoinGlass/CoinGecko показываются как live providers.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный, `/perp-dex` и `/perp-dex?view=opportunities` возвращают `200` без runtime error. Browser QA подтвердил новые панели и `Perp inputs live`.

## [2026-06-05] - [FRONTEND] - Быстрые hover-графики и stablecoin filter перед демо
- `Market Overview` теперь фильтрует stablecoin-like активы (`USDT`, `USDC`, `USDE`, `USDS`, `USDH`, `DAI`, `FDUSD`, `TUSD` и похожие USD-символы) до формирования heatmap, top gainers/losers и top assets.
- Heatmap берёт до 80 CoinGecko markets, после фильтрации оставляет top-30 и показывает первые 12 non-stable активов, чтобы вместо стоимости стейблов в демо были BTC/ETH/BNB/XRP/SOL/TRX/HYPE/DOGE и другие рыночные активы.
- `Charts` расширил видимый historical slice с 96 до 240 точек для line charts и до 120 точек для quote volume, а bar labels теперь разрежаются автоматически.
- `LineChart`, `BarChart` и свечной chart в `Assets` получили hover-title: время и значение по точке, для свечей - `Open/High/Low/Close/Volume`.
- `Assets` показывает до 240 1m свечей и использует `quote_volume` как основной volume для USD-контекста.
- В `BACKLOG.md` добавлена следующая крупная задача: полноценный слой historical charts на `lightweight-charts` с crosshair, pan/zoom/scroll, диапазонами и backend pagination/backfill.
- Проверка: `npm run build` во `frontend` проходит успешно; production Docker rebuild на `deltagrid.pro` прошёл, `server-smoke.sh` зелёный, `/market`, `/charts?symbol=BTC` и `/assets?symbol=ETH` возвращают `200` без runtime error. Browser QA подтвердил `display: grid` у heatmap, отсутствие стейблов и наличие SVG hover-title в Charts/Assets.

## [2026-06-05] - [FRONTEND] - Демо-доводка графиков и Market Overview
- Общие terminal-графики получили числовой контекст: `Last`, `Range`, Y-шкалу и X-подписи для line charts; bar charts теперь показывают максимум и диапазон.
- `Charts` показывает price, volume, OI, basis, funding и long/short с разными форматами осей: цена/доллары/проценты больше не выглядят как безымянные линии.
- `Assets` больше не захардкожен только на SOL: экран поддерживает переключение `BTC`, `ETH`, `SOL` через `?symbol=...`, показывает логотип CoinGecko и цену/диапазон на свечном графике.
- `Assets` ограничивает OHLCV-запрос последним рабочим окном через `start`, чтобы SSR не тянул тяжёлый 1000-row payload перед демо и не падал в пустой график при живых backend-данных.
- `Market Overview` теперь показывает цену в heatmap как основной сигнал, капитализацию как вторичный контекст, логотипы CoinGecko в top assets и реальные OHLCV sparkline для BTC/ETH/SOL, где история уже есть в PostgreSQL.
- В `BACKLOG.md` добавлена следующая data coverage итерация по perp/RWA universe: CoinGlass/CoinGecko/Binance coverage matrix, top-30 crypto и RWA-кандидаты.
- Проверка: `npm run build` проходит; локальный visual QA с `BACKEND_INTERNAL_URL=https://deltagrid.pro` подтвердил `/market`, `/charts?symbol=BTC`, `/assets?symbol=SOL`, `/assets?symbol=BTC` и `/perp-dex` без runtime error.
- Production deploy выполнен на `deltagrid.pro`: frontend image пересобран, stack healthy, `server-smoke.sh` через домен прошёл, `/market`, `/charts?symbol=BTC`, `/assets?symbol=SOL`, `/assets?symbol=BTC` и `/perp-dex` возвращают `200` без runtime error.

## [2026-06-05] - [DATA] - CoinGlass liquidation ingestion
- `CoinGlassClient` получил v4 endpoint `/api/futures/liquidation/aggregated-history` для агрегированной истории ликвидаций по монетам.
- `sync_market_data` теперь поддерживает `--include-liquidations` и пишет CoinGlass long/short liquidation history в таблицу `liquidations` с `exchange=binance`, чтобы существующие data endpoints и frontend-фильтры продолжали работать без изменения контракта.
- `scripts/sync-market-data.sh` по умолчанию включает загрузку ликвидаций вместе с OHLCV/funding/OI/L/S, CoinGlass snapshots и CoinGecko basis.
- Добавлены regression tests для нормализации CoinGlass liquidation payload: nested `Binance`/`all` поля, seconds/ms timestamps и пустые строки.
- Production deploy проверен: ручной sync на `deltagrid.pro` записал `144` строки в `liquidations`, публичный `/api/v1/data/health` показывает `row_counts.liquidations=144`, а `/api/v1/data/liquidations` отдаёт BTC long/short `value_usd`.
- Ограничение: поток хранит агрегированный `value_usd`; `quantity` и `price` остаются `0.0`, пока не подключён отдельный per-order liquidation tape.

## [2026-06-05] - [FIX/DATA] - Устойчивость live data SSR
- Backend SQLAlchemy pool стал управляемым через env: `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_TIMEOUT_SECONDS`.
- Frontend server-side API client получил таймаут `BACKEND_FETCH_TIMEOUT_MS`, чтобы live-страница не зависала бесконечно при проблемном backend-запросе.
- Live stream loader снизил параллельность запросов на один символ: `Charts`, `Market Matrix`, `Arbitrage Scanner` и `Strategy Lab` больше не открывают десятки DB-сессий одномоментно.
- Production-риск: таблица `liquidations` пока пустая, поэтому liquidation-блоки остаются в честном pending-состоянии до подключения ingestion.

## [2026-06-05] - [DATA/FRONTEND] - Live data streams для Charts, Matrix и Scanner
- Добавлены read-only backend endpoint'ы для уже сохраняемых PostgreSQL потоков: `GET /api/v1/data/open-interest`, `/data/long-short-ratio`, `/data/basis-premium` и `/data/liquidations`.
- Расширены regression tests `backend/tests/test_data_api.py`: новые data endpoints должны возвращать `200` даже при пустых таблицах.
- `Charts` заменён с placeholder на live stream workspace: price, volume, open interest, basis, funding и long/short читаются через backend data-layer.
- `Market Matrix` больше не использует `terminalDataAdapter`: BTC/ETH/SOL matrix строится из CoinGecko spot, Binance perp close, basis, funding, OI и long/short.
- `Arbitrage Scanner` больше не показывает mock opportunities: таблица строится из persisted `basis_premium` и `funding_rates` как read-only research candidates.
- `Strategy Lab` очищен от fake backtest PnL/trades: экран показывает readiness live inputs и блокирует backtest output до появления реального engine.
- `Assets` теперь читает `/data/liquidations`; пока строк нет, блок остаётся pending, но будущий ingestion автоматически появится в UI.
- Проверка: `venv\Scripts\python.exe -m pytest tests/test_data_api.py -q` — `10 passed`; `python -m compileall backend/app` и `npm run build` проходят успешно.

## [2026-06-05] - [FRONTEND] - Live Market Overview и Assets
- Добавлен backend endpoint `GET /api/v1/market/markets` для топовых spot markets из CoinGecko с `24h` и `7d` изменениями.
- `Market Overview` больше не читает `terminalDataAdapter`: global cap/volume, BTC/ETH dominance, heatmap, top assets, gainers/losers и `Fear & Greed Index` строятся из live backend API.
- `Assets` больше не использует mock SOL fixture: цена, market cap, volume, open interest, funding и OHLCV читаются через backend/data-layer.
- Fake order book, fake liquidations и fake venue breakdown убраны из production UI; вместо них показаны явные pending-состояния до подключения live endpoints.
- Общие terminal chart/table компоненты получили безопасные empty-state'ы для пустых ответов provider'ов.
- Проверка: `python -m compileall backend/app` и `npm run build` проходят успешно.

## [2026-06-05] - [FRONTEND] - Live Funding tabs и Data Health
- Исправлена вложенная навигация в `Funding` и `Perp DEX`: sidebar и верхние segmented tabs теперь используют стабильный `view` query-param, активное состояние больше не привязано к первому пункту.
- `SegmentedControl` получил поддержку ссылок без поломки старого режима с кнопками.
- `Funding` больше не читает mock fixture: KPI, matrix, history, arbitrage baseline, legs и predicted baseline строятся из persisted PostgreSQL rows через `GET /api/v1/data/funding` и `GET /api/v1/data/health`.
- `/data-health` заменён с placeholder на live-экран provider/storage health по `GET /api/v1/data/health`.
- `Perp DEX` больше не показывает mock DEX volumes/OI как реальные данные: экран помечает DEX venue data как pending и показывает реальные row counts/provider health из PostgreSQL.
- Проверка: `npm run build` во frontend проходит успешно.

## [2026-06-05] — [DATA] — Multi-provider ingestion и регулярный sync
- `sync_market_data` расширен до multi-provider flow: Binance USD-M продолжает писать OHLCV/funding/OI/L/S, CoinGlass v4 пишет funding/OI snapshots, CoinGecko даёт spot price для approximate `basis_premium`.
- `DataWriter` получил безопасную вставку `basis_premium` и чтение последнего Binance 1m close без изменения схемы БД.
- `GET /api/v1/data/health` теперь отслеживает provider `coingecko` вместе с `binance` и `coinglass`.
- `scripts/sync-market-data.sh` по умолчанию включает `--include-coinglass` и `--include-coingecko-basis`.
- Добавлен `scripts/install-market-sync-cron.sh`, который создаёт `/etc/cron.d/deltagrid-market-sync` для запуска sync каждые 15 минут.
- CoinGecko API key больше не передаётся в query params, чтобы HTTP logs не содержали секреты.
- Production deploy выполнен: cron service активен, `/api/v1/data/health` показывает `binance`, `coinglass` и `coingecko` healthy; row counts после ручной проверки: `ohlcv=5376`, `funding_rates=15`, `open_interest=1509`, `long_short_ratio=75`, `basis_premium=6`.
- `DEPLOYMENT.md`, `ARCHITECTURE.md`, `BACKLOG.md`, `PROJECT_PLAN.md` и `CURRENT_TASK.md` обновлены под регулярный multi-provider sync.

## [2026-06-05] — [DATA] — Provider API keys и CoinGlass v4
- Provider API keys добавлены в `/opt/deltagrid/.env.production` без вывода секретов; backend container перечитал env после recreate.
- `CoinGecko` ключ активен: `market/trending` и `market/global` отвечают через production-домен.
- `CoinGlassClient` переведён на v4 base URL `https://open-api-v4.coinglass.com`, header `CG-API-KEY` и endpoint `/api/futures/coins-markets`.
- `GET /api/v1/market/enrichments` теперь может проверять CoinGlass v4 health, а `GET /api/v1/market/funding-rates` нормализует live-поля `avg_funding_rate_by_oi`, `open_interest_usd` и `current_price`.

## [2026-06-05] — [DATA] — Ручной production sync market data
- Добавлена backend-команда `python -m app.adapters.data.sync_market_data` для загрузки свежих Binance USD-M данных в PostgreSQL без нового scheduler/cron.
- `BinanceAdapter` теперь реально загружает funding history, open interest history и global long/short account ratio; liquidations остаются отдельной задачей.
- Добавлен wrapper `scripts/sync-market-data.sh` для запуска синка внутри production Compose stack из `/opt/deltagrid`.
- Sync пишет OHLCV, funding, open interest, long/short ratio, `backfill_jobs` и `provider_sync_runs`, поэтому `/api/v1/data/health` может показывать актуальные `row_counts` и последний sync.
- Первый production sync выполнен на сервере `2.25.143.143`: загружено `6837` rows, `/api/v1/data/health` через `https://deltagrid.pro` показывает `binance healthy`, `ohlcv=5256`, `funding_rates=9`, `open_interest=1500`, `long_short_ratio=72`, `data_quality.score=100`.
- `DEPLOYMENT.md`, `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `BACKLOG.md` и `CURRENT_TASK.md` обновлены с инструкциями по заполнению market data и текущими ограничениями.

## [2026-06-05] — [DEPLOY] — Реальный запуск `deltagrid.pro` на сервере
- DNS Cloudflare активирован: `deltagrid.pro` и `www.deltagrid.pro` указывают на `2.25.143.143`, старая `AAAA`-запись для корня отсутствует.
- SSH-доступ `root@2.25.143.143` по ключу подтверждён; код развёрнут в `/opt/deltagrid` из ветки `preview`.
- На Ubuntu 22.04 установлен Nginx/Certbot, Docker Compose stack поднят с PostgreSQL, backend и frontend.
- `.env.production` создан на сервере с production secrets; файл не коммитится.
- Приложение работает через Nginx: `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- Let's Encrypt сертификат выпущен для `deltagrid.pro` и `www.deltagrid.pro`, срок действия до `2026-09-03`; `certbot renew --dry-run` прошёл успешно.
- Проверки: server smoke-check через HTTPS прошёл; страницы `/`, `/market`, `/data-health`, `/watchlist`, `/settings`, `/funding`, `/perp-dex`, `/assets`, `/charts`, `/strategy-lab` возвращают `200`; API `/api/v1/health`, `/api/v1/health/readiness`, `/api/v1/data/health`, `/api/v1/market/trending` возвращают `200`.
- Cloudflare proxy включён обратно, SSL mode `Full (strict)` проверен: edge отдаёт `Server: cloudflare`, frontend/API возвращают `200`, WebSocket `/api/v1/stream/ws` отдаёт `101 Switching Protocols`.
- `scripts/deploy-production.sh` теперь ждёт healthcheck сервисов перед smoke-check, чтобы убрать race condition первого запуска frontend.

## [2026-06-05] — [DEPLOY] — Привязка deployment flow к `deltagrid.pro`
- `.env.production.example` обновлён под `https://deltagrid.pro` и `https://www.deltagrid.pro`.
- `deploy/nginx/deltagrid.conf.example` теперь содержит `server_name deltagrid.pro www.deltagrid.pro`.
- `scripts/generate-production-env.sh` по умолчанию генерирует `.env.production` для `deltagrid.pro`.
- `DEPLOYMENT.md`, `README.md`, `PROJECT_PLAN.md` и `CURRENT_TASK.md` обновлены под реальный домен.
- DNS preflight: `deltagrid.pro` и `www.deltagrid.pro` сейчас резолвятся в `31.31.196.50` и `2a00:f940:2:2:1:1:0:266`; HTTP отдаёт parking page REG.RU, HTTPS требует настройки.
- Целевой сервер пользователя: `2.25.143.143`; SSH `22` открыт, HTTP `80` и HTTPS `443` пока закрыты.
- Добавлены `scripts/bootstrap-ubuntu.sh`, `scripts/deploy-production.sh` и `deploy/dns/deltagrid.pro.md` для Ubuntu/VPS rollout.
- Добавлен `scripts/configure-nginx-ssl.sh` для включения Nginx site и выпуска Let's Encrypt SSL после DNS cutover.
- Production frontend host port переключён на `127.0.0.1:3001`, чтобы не конфликтовать со служебным процессом хостинга на `3000`.

## [2026-06-05] — [DEPLOY] — Минимальный server deployment flow
- Добавлен `.env.production.example` с обязательными production-переменными: secrets, CORS, PostgreSQL credentials, provider keys и runtime tuning.
- `.env.production` добавлен в `.gitignore`, чтобы реальные секреты не попадали в репозиторий.
- Добавлены `backend/.dockerignore` и `frontend/.dockerignore`, чтобы production images не получали локальные env, SQLite DB, venv, `node_modules`, `.next` и cache artifacts.
- Добавлен `docker-compose.prod.yml`: PostgreSQL не публикуется наружу, backend/frontend слушают `127.0.0.1`, backend стартует через `alembic upgrade head`, backend/frontend имеют healthcheck.
- Добавлен `DEPLOYMENT.md` на русском языке: подготовка env, запуск, readiness checks, reverse proxy, SSL, backup PostgreSQL и rollback.
- Добавлен `deploy/nginx/deltagrid.conf.example` как переносимый Nginx-шаблон для домена и WebSocket upgrade.
- Добавлен `scripts/server-smoke.sh` для проверки backend health, readiness, data health и frontend локально или через домен.
- Добавлен `scripts/server-smoke.ps1` для локальной Windows-проверки.
- Добавлен `scripts/server-preflight.sh` для проверки server prerequisites, Docker daemon, compose config, DNS lookup и занятых портов.
- Добавлен `scripts/generate-production-env.sh` для безопасной генерации `.env.production` по домену без ручной сборки секретов.
- `frontend/next.config.js` больше не привязан к `http://127.0.0.1:8000`: rewrite использует `BACKEND_INTERNAL_URL` с локальным fallback, а Docker передаёт его на frontend build stage.
- `frontend/src/hooks/useRealtime.ts` больше не зашит только на `ws://127.0.0.1:8000`: локально остаётся прямое подключение к backend, а на домене используется same-origin WebSocket path или `NEXT_PUBLIC_WS_URL`.
- Проверка: `npm run build` проходит; Docker frontend пересобран; `http://127.0.0.1:3000/api/v1/health/readiness` через Next.js proxy возвращает `ready`.

## [2026-06-05] — [HARDENING] — Production readiness gate для env, DB и миграций
- Усилена startup validation при `DEBUG=false`: backend блокирует слабые/dev `SECRET_KEY`, короткий или пустой `VAULT_MASTER_KEY`, SQLite `DATABASE_URL` и wildcard `CORS_ORIGINS`.
- Добавлен `GET /api/v1/health/readiness`: endpoint проверяет локальное подключение к БД, читает `alembic_version` и сравнивает текущую revision с source head.
- В `Settings` добавлен `COINGLASS_STANDARD_API_KEY`, чтобы `.env.example` и runtime config не расходились.
- `docker-compose.yml` теперь прокидывает `COINGLASS_API_KEY` и `COINGLASS_STANDARD_API_KEY` в backend.
- Обновлены `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `CURRENT_TASK.md` и `BACKLOG.md` с readiness flow и staging/prod рисками.
- Проверка: `venv\Scripts\python.exe -m pytest tests -q` — 6 passed; `venv\Scripts\python.exe -m compileall app` — успешно.
- Проверка Docker: backend пересобран, PostgreSQL healthy, frontend отвечает на `http://127.0.0.1:3000`, `/api/v1/health`, `/api/v1/data/health` и `/api/v1/health/readiness` возвращают ожидаемый статус; readiness показывает head `7c1f2a8d9e34`.

## [2026-06-05] — [DB] — PostgreSQL runtime для production-ready MVP
- Backend persistence переведён на PostgreSQL как основной runtime через `DATABASE_URL`.
- Добавлен sync PostgreSQL driver `psycopg[binary]`; async layer продолжает использовать `asyncpg`.
- Добавлена нормализация DB URL для sync engine, async engine и Alembic: `postgres://`, `postgresql://`, `postgresql+psycopg://`, `postgresql+asyncpg://`.
- `Base.metadata.create_all()` больше не создаёт production-схему для PostgreSQL; схема управляется через Alembic.
- Добавлена миграция `3f0c2e5a7b91_postgresql_mvp_hardening` для таблицы `backfill_jobs`, которая раньше создавалась только ручным SQLite-DDL внутри `DataWriter`.
- Добавлена миграция `7c1f2a8d9e34_bigint_market_timestamps`: Unix timestamp в миллисекундах для market/backtest/data-layer хранится в `BigInteger`, а не в PostgreSQL `integer`.
- `DataWriter` и `SymbolMapper` используют PostgreSQL-safe engine settings; SQLite fallback оставлен только для isolated tests.
- Старые migration seed'и обновлены для PostgreSQL-safe boolean values (`true/false` вместо `1/0` в boolean-колонках).
- `docker-compose.yml` теперь поднимает PostgreSQL 16, ждёт healthcheck и запускает `alembic upgrade head` перед стартом backend.
- Обновлены `README.md`, `DATA_ARCHITECTURE.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md` и `BACKLOG.md` с инструкциями PostgreSQL-запуска и рисками.
- Проверено на живом Docker Compose окружении: PostgreSQL healthy, backend применяет Alembic migrations при старте, `/api/v1/health`, `/api/v1/data/health`, `/api/v1/data/ohlcv` и `/api/v1/market/trending` возвращают 200, frontend отвечает на `http://127.0.0.1:3000`.

## [2026-06-04] — [v1.2.0] — Frontend MVP terminal shell и 6 ключевых экранов
- Frontend package version обновлён до `1.2.0`.
- Основной frontend shell переведён на тёмный terminal layout: left sidebar, top workspace tabs, search и компактные controls.
- Sidebar обновлён под MVP-информационную архитектуру: Market Overview, Perp DEX, Assets, Funding, Arbitrage Scanner, Market Matrix, Charts, Strategy Lab.
- Perp DEX и Funding получили nested navigation с визуальной tree-line.
- Добавлен typed mock data adapter в `frontend/src/lib/terminal`, чтобы UI работал на fixtures сейчас и мог быть заменён на CoinGecko/CoinGlass-backed providers позже.
- Реализованы экраны: Market Overview / Command Center, Perp DEX Intelligence, Funding Overview, Asset Deep Dive SOL, Market Matrix, Strategy Lab / Backtest.
- Добавлены routes `/arbitrage-scanner` и `/charts`; Charts пока реализован как аккуратный placeholder без новых зависимостей.
- Market Overview, Perp DEX, Arbitrage Scanner и Market Matrix очищены от полноценного funding-дублирования; Funding Matrix, Funding Arbitrage и Long/Short legs живут только в Funding.
- Корневой route `/` теперь ведёт на `/market`, чтобы MVP не открывал старый scanner flow с right drawer.
- Проверка: `npm run build` во frontend проходит успешно.

## [2026-06-02] — [CRITICAL FIX] — Code Review v2: security, symbol contract, regression tests
- **Security**: Telegram/Web3 auth endpoint'ы (`/auth/telegram`, `/auth/web3/challenge`, `/auth/web3/verify`) теперь возвращают `501 Not Implemented` при `DEBUG=false`.
- **Security**: Добавлена fail-fast startup validation: в production-like режиме (`DEBUG=false`) приложение падает при старте, если `SECRET_KEY` оставлен дефолтным или `VAULT_MASTER_KEY` пустой.
- **Data layer symbol contract**: `BinanceAdapter.fetch_ohlcv` теперь принимает canonical symbol (например, `BTC`) и маппит в provider-native (`BTCUSDT`) внутри адаптера через `SymbolMapper`. Все записи в БД теперь используют canonical symbol.
- **Data layer**: Исправлен gap detection bug в `BackfillOrchestrator`: `expected` теперь считается до сдвига `current_start`.
- **Testing**: Добавлен `backend/tests/test_data_api.py` — regression tests на `TestClient` с in-memory SQLite, которые доказывают, что `/api/v1/data/ohlcv?symbol=BTC&exchange=binance` возвращает seeded данные.
- **Docs**: Обновлён `backend/.env.example` с секциями `Security` и комментариями о production secrets.

## [2026-06-02] — [UI] — Standalone HTML preview frontend
- Добавлен автономный preview-интерфейс в `frontend/preview/`, который открывается напрямую через `index.html` без Next.js, React, backend API и сборки.
- Реализованы страницы `index.html`, `asset.html`, `strategy-lab.html`, `data-health.html` и общий `styles.css` в тёмной dashboard-теме.
- Scanner содержит mock-данные по BTC, ETH, SOL и HYPE, фильтры по exchange/signal, кликабельные строки и переходы в asset/backtest flow.
- Asset preview поддерживает табы Overview/Funding/OI/Liquidations/Long/Short и переход в Strategy Lab с передачей `symbol` через query string.
- Strategy Lab показывает selector стратегий, параметры backtest и disabled-кнопку `Run Backtest` до появления engine.
- Data Health показывает mock-статусы CoinGlass, CoinGecko и Binance.

## [2026-06-02] — [UI] — MVP-навигация frontend
- Sidebar переведён на MVP-набор разделов: Market, Strategy Lab, Backtests, Data Health, Watchlist и Settings.
- Старые product-разделы скрыты только из навигации; route-файлы и существующая реализация не удалялись.
- Добавлены placeholder-страницы `/strategy-lab`, `/backtests`, `/data-health`.
- Добавлен route `/watchlist` как alias на текущий scanner/watchlist-интерфейс, чтобы новый пункт меню не вёл в 404.
- На `/market` добавлен mock-индикатор свежести данных `Updated 2 min ago`.

## [2026-06-02] — [API] — Read-only endpoint'ы проверки market data
- Добавлен роутер `backend/app/api/v1/data.py` с публичными read-only endpoint'ами `GET /api/v1/data/ohlcv`, `GET /api/v1/data/funding` и `GET /api/v1/data/health`.
- `ohlcv` и `funding` читают данные из SQLite через существующие SQLAlchemy-модели `DataOhlcv` и `DataFundingRate`, фильтруют по `symbol`, `exchange`, `start`, `end` и возвращают максимум 1000 строк.
- `data/health` возвращает статус `binance`/`coinglass`, последний sync по провайдерам, количество строк в data-layer таблицах и приближённый `data_quality.score` по логам качества данных за последние 24 часа.
- Роутер подключён в `app.main`; POST/DELETE операции не добавлялись.
- Проверка: `venv\Scripts\python.exe -m compileall app` и smoke-test через `TestClient` на in-memory SQLite для трёх новых endpoint'ов.

## [2026-05-20] — [AUDIT/FIX] — Техническое ревью Codex
- Проведён технический аудит структуры проекта, frontend build, backend import/compile, зависимостей, Alembic-состояния и базового health endpoint.
- Исправлено восстановление frontend auth-состояния после reload: валидный persisted JWT снова выставляет `isAuthenticated=true`.
- Исправлен auto-refresh JWT: ответ `/auth/refresh` теперь приводится к camelCase перед чтением `accessToken`.
- Исправлен импорт `async_database.py` на дефолтном SQLite URL через нормализацию async driver URL.
- Docker Compose теперь пишет SQLite базу в примонтированный volume `/app/data` и разрешает CORS для `localhost` и `127.0.0.1`.
- Убрано устаревшее поле `version` из `docker-compose.yml`.
- Добавлена пустая `frontend/public/.gitkeep`, чтобы production Dockerfile не падал на `COPY /app/public`.
- Исправлено двойное чтение HTTP error body в backend test helper scripts.
- Startup seeding и scanner warm-up теперь логируют warning при ошибке вместо полного silent failure.
- RWA/Treasury UI теперь безопаснее обрабатывает `null`/`undefined` в числовых snapshot-полях.
- Отложено: настройка ESLint, полноценные backend tests, проверка реальных API/рыночных данных, архитектурное разделение sync/async persistence перед PostgreSQL.

## [2026-05-13] — [ARCH] — Phase 1 MVP Scanner реализован
- Создана полная архитектура backend (FastAPI) + frontend (Next.js 14)
- Реализованы: Scanner, Detail View, Settings, KPI Cards, Search/Sort/Filter
- Добавлена RU/EN локализация через centralized dictionaries
- Настроены CoinGecko adapter + Perp DEX stubs (Hyperliquid, Aster, Lighter)
- Реализован SpreadCalculator + SignalClassifier (STRONG/BUY_SELL/MARGINAL/HOLD)
- Добавлен in-memory cache с TTL + stale/fallback logic
- SQLite persistence для favorites, pinned, preferences
- Созданы Docker + docker-compose конфигурации

## [2026-05-13] — [FIX] — Исправлена ошибка camelCase ↔ snake_case между backend/frontend
- Добавлены хелперы snakeToCamel / camelToSnake в frontend API client
- Исправлен Runtime Error в SettingsForm (undefined при toFixed)

## [2026-05-13] — [UI] — Первая сборка frontend
- Next.js build проходит без TypeScript ошибок
- Tailwind конфиг с кастомной дизайн-системой (light theme)
- Zustand stores + TanStack Query hooks

## [2026-05-13] — [API] — Backend endpoints активны
- GET /api/v1/scanner — список арбитражных возможностей (24 записи на mock)
- GET /api/v1/scanner/{id} — детальная карточка
- GET/POST /api/v1/preferences — настройки
- GET/POST /api/v1/preferences/favorites — избранное
- GET/POST /api/v1/preferences/pinned — закреплённые
- GET /api/v1/health + /status — health check + data source status

## [2026-05-13] — [ARCH] — Phase 2 Migration: Foundation + Auth + Paper Trading
- **Backend foundation**: PostgreSQL-ready async engine, Alembic migrations, Redis cache abstraction
- **Auth foundation**: JWT tokens, register/login endpoints, optional auth middleware, bcrypt password hashing
- **Paper Trading**: VirtualBalance, trade lifecycle (open/close), PnL calculation, portfolio state
- **Performance Tracking**: PnL, win rate, max drawdown, Sharpe-ready metrics structure
- **Billing/Referral hooks**: Plan definitions, subscription placeholders, referral code generation
- **Frontend**: authStore (Zustand + persist), LoginModal, UserMenu, PaperTrading page, Profile page
- **API Evolution**: 12 new endpoints under /api/v1/{auth,paper,performance,billing}
- **Compatibility**: All Phase 1 endpoints preserved, scanner/settings/favorites work for anonymous users
- **Regression**: Full test suite passes — Phase 1 baseline intact

## [2026-05-13] — [CRITICAL FIX] — Исправлены фатальные баги авторизации и scanner performance
- **FIX**: `LoginModal.tsx` передавал `user` и `token` в `authStore.login()` в обратном порядке → токен сохранялся как объект, API отправлял `Bearer [object Object]` → 401 → авто-логаут
- **FIX**: `LoginModal.tsx` искал `data.access_token`, но `api.ts` transformResponse превращает snake_case в camelCase → `data.accessToken` → токен был `undefined`
- **FIX**: `scanner.py` создавал новый `InMemoryCacheService` на каждый запрос → cache не работал → scanner endpoint занимал 12+ секунд (CoinGecko API каждый раз)
- **FIX**: `localhost` на Windows резолвится в IPv6 (`::1`), серверы слушали IPv4 → ~2 секунды таймаута на каждый запрос
  - Решение: Next.js dev server `-H 127.0.0.1`, rewrite proxy на `127.0.0.1:8000`
- **FIX**: Singleton cache/registry в scanner endpoint + warm-up при старте backend
- **FIX**: Увеличен cache TTL с 60 до 300 секунд
- **FIX**: `authStore` добавлен `onRehydrateStorage` валидатор JWT токена — очищает битые токены из localStorage
- **FIX**: Страницы `/paper-trading` и `/profile` защищены redirect'ом для анонимных пользователей
- **FIX**: `usePaperAccounts()` не делает запрос если пользователь не авторизован (`enabled: isAuthenticated`)
- **RESULT**: Scanner загружается за ~85ms, Paper Trading открывается без разлогина, auth работает стабильно

## [2026-05-14] — [ARCH] — Phase 3 Quick Wins: Market Dashboard (A+B+F+G)
- **Increment A — Market Overview Dashboard**: endpoints `/market/{trending,gainers,losers,global}`, CoinGeckoAdapter extensions, MarketService with caching, frontend page `/market` with 4 cards
- **Increment B — Fear & Greed Index**: endpoint `/market/fear-greed`, alternative.me API integration, `FearGreedCard` with 7-day history and color-coded indicator. Current value: 34 (Fear)
- **Increment F — New Listings**: endpoint `/market/new-listings`, filter from trending by market_cap_rank, `NewListingsCard` component
- **Increment G — Funding Rates (placeholder)**: endpoint `/market/funding-rates`, mock data for 8 perp pairs (BTC, ETH, SOL, XRP, DOGE, HYPE, LINK, SUI), `FundingRatesCard` with "Mock" badge
- **CoinGecko auth fix**: removed demo keys causing 401 on public API — free tier works without any key
- **Frontend**: `useMarketData` hook, `TrendingCard`, `GainersCard`, `LosersCard`, `GlobalStatsCard`, `FearGreedCard`, `NewListingsCard`, `FundingRatesCard`
- **i18n**: Added RU/EN translations for all market components (fearGreed, newListings, fundingRates, globalStats, etc.)
- **Sidebar**: Added "Market" navigation item with Activity icon
- **RESULT**: Full market dashboard at `/market` with real live data from CoinGecko + alternative.me

## [2026-05-15] — [ARCH] — Phase 3 Execution Foundation: Increments A+B+C+D+E COMPLETED
- **Increment A — Foundation & Security**:
  - Alembic initial migration for Phase 1/2 tables + Phase 3 migration (exchange_accounts, exchange_keys, connector_capabilities, real_orders, order_events, execution_runs, risk_rules, position_snapshots, live_trade_sessions, audit_logs)
  - `SecretsVaultService` (Fernet AES-256 encryption for API keys)
  - `ExchangeAccountService` with CRUD + encrypted key storage (backend-only, never exposed)
  - `GET/POST/DELETE /exchange-accounts`, `POST /exchange-accounts/{id}/keys`, `GET /connectors/capabilities`
  - Frontend: `/exchange-accounts` page, `AddExchangeModal`, `exchangeAccountStore`, sidebar navigation
  - Connector capabilities seeded for Binance, Bybit, OKX, Hyperliquid, Aster
- **Increment B — Order Intent Pipeline + Risk Manager**:
  - `RiskManager` service: rule CRUD, kill-switch, position sizing, max exposure, dry-run checks
  - `ExecutionService`: order intent lifecycle (intent -> risk_check -> pending_confirmation -> submitted/failed)
  - Safe default: `is_live=False` rejects orders with safe message
  - Endpoints: `/execution/intents`, `/execution/orders`, `/risk/rules`, `/risk/check`
  - Frontend: `/execution` dashboard, `/risk-rules` page, `OrderIntentModal` integrated into ScannerRow
  - Audit trail: `order_events` + `audit_logs` for every action
- **Increment C — Connector Foundation**:
  - `ExchangeConnector` ABC with `ConnectorCapabilities`, `OrderRequest`, `OrderResult`, `OrderStatus`
  - `ConnectorRegistry` for runtime connector discovery
  - `BinanceConnector` with REST spot API (account info, ticker, place order, status)
  - `OrderManager`: retry logic (3x exponential backoff), partial fill handling, status sync
  - ExecutionService delegates to OrderManager on `confirm_intent(is_live=True)`
- **Increment D — Additional CEX Connectors**:
  - `BybitConnector` (V5 unified API): ticker, account, place order, status
  - `OKXConnector`: ticker, account, place order, status (passphrase support)
- **Increment E — Perp DEX + Kill Switch + Sessions**:
  - `HyperliquidConnector` (direct REST): ticker via `allMids`, clearinghouse state, placeholder trading (needs wallet signing)
  - `AsterConnector` stub for future expansion
  - Kill switch: `POST /risk/rules/{id}/toggle` for quick activation
  - Execution sessions: `GET/POST /execution/sessions`, `POST /execution/sessions/{id}/stop`
  - Frontend: Session start/stop buttons on Execution dashboard
- **Compatibility**: All Phase 1/2 endpoints preserved. Scanner, auth, paper trading, settings, i18n, favorites/pins unchanged.
- **Security**: Encrypted API keys, no secret exposure in frontend, explicit opt-in for live trading, safe defaults.

## [2026-05-15] — [FIX] — Phase 3 Final Polish: Login Modal, Sidebar, Port Conflicts
- **FIX**: `LoginModal.tsx` использовал `data.access_token` вместо `data.accessToken` — `transformResponse` конвертирует snake_case → camelCase → токен был `undefined` → 401 → авто-логаут loop
- **FIX**: Страницы `/execution`, `/exchange-accounts`, `/risk-rules` не обёрнуты в `<Shell>` → sidebar отсутствовал, нет навигации
- **FIX**: Конфликты порта 8000 — multiple zombie python процессы удерживали порт → backend не стартовал
- **FIX**: Пустая initial Alembic migration (`pass` в upgrade/downgrade) — пофикшено через ручной seed `alembic_version` + правильная Phase 3 migration
- **Backend restart**: `deltagrid.db` на SQLite с полной схемой Phase 3, Alembic `9cc9da229c47` применена
- **RESULT**: Frontend http://127.0.0.1:3000 и Backend http://127.0.0.1:8000 работают стабильно. Phase 3 готова к тестированию.

## [2026-05-16] — [ARCH] — Phase 4 Scale + Live Features COMPLETED
- **Increment A — Tech Debt Remediation**:
  - Fix `httpx.AsyncClient` leaks: explicit `close()` in all 5 connectors + `OrderManager` try/finally
  - Cache upgrade: FIFO → LRU via `OrderedDict`, cache invalidation on preference changes
  - `PreferenceService`: explicit session lifecycle, no unmanaged `SessionLocal()`
  - Dual-token auth: access + refresh tokens, `/auth/refresh` endpoint, frontend auto-refresh on 401
- **Increment B — Provider Layer & Enrichments**:
  - `CoinGlassClient` + `GeckoTerminalClient` with rate-limit awareness and graceful fallback
  - `ProviderHealthMonitor` + `provider_health` table + `provider_sync_logs`
  - Hardcoded funding rates replaced with CoinGlass-backed data + fallback mock with `data_status: fallback`
  - New endpoints: `GET /market/enrichments`, `GET /health/providers`
- **Increment C — Realtime Streaming Foundation**:
  - `WebSocketManager`: Binance public ticker stream, reconnect/backoff, heartbeat
  - `NormalizedStreamEvent`: unified ticker DTO across exchanges
  - WebSocket endpoint `/api/v1/stream/ws` + SSE fallback `/api/v1/stream/sse`
  - Frontend: `useRealtime` hook, `streamStore` (isolated from polling), `RealtimeIndicator` component
  - Tables: `realtime_feed_sessions`, `stream_events`
- **Increment D — Alerting Engine**:
  - `AlertService`: rule CRUD, evaluation, deduplication (hash-based), cooldown
  - `NotificationService`: email/web-push/Telegram delivery stubs with logged fallback
  - New endpoints: `/alerts/rules`, `/alerts/events`, `/notifications/preferences`, `/notifications/web-push/*`
  - Frontend: `/alerts` page, `/notifications` page, `useAlerts` + `useNotifications` hooks
  - Tables: `alert_rules`, `alert_events`, `alert_deliveries`, `notification_preferences`
- **Increment E — Security Hardening & Auth Extensions**:
  - `User.session_version` for global logout capability
  - Telegram OAuth: `/auth/telegram` endpoint
  - Web3 login: `/auth/web3/challenge` + `/auth/web3/verify` endpoints
  - Frontend: Telegram + Web3 login buttons in `LoginModal` (Coming Soon stubs)
- **Compatibility**: All Phase 1/2/3 endpoints preserved. Scanner, auth, paper trading, execution, risk controls, settings, i18n unchanged.
- **Schema**: 4 Alembic migrations added (`69bd5d1e4711`, `2583b2f128b1`, `8d4a2b9ab83a`, `bd43594cd747`) → 29 total tables.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.

## [2026-05-16] — [FIX] — Phase 4 Final Polish: UI snakeToCamel, Alerts Form, Server Restarts
- **FIX**: `useNotifications.ts` не применял `snakeToCamel` к ответу API → `emailEnabled` был всегда `undefined` → toggle застревал в `true` (fallback `?? true`)
  - Backend возвращал `email_enabled`, frontend искал `emailEnabled` → mismatch
  - Экспортирован `snakeToCamel` из `api.ts`, применён в `useNotifications.ts` и `useAlerts.ts`
- **FIX**: `useAlerts.ts` — та же проблема с `snakeToCamel` для rules/events
- **FIX**: Alerts page (`/alerts`) — добавлена кнопка "Add Rule" и полноценная форма создания правила (name, ruleType, symbol, threshold, comparison, cooldown, severity)
- **FIX**: Frontend сервер не подхватывал изменения в `/alerts/page.tsx` без перезагрузки (Next.js dev cache)
- **RESULT**: Notifications toggles работают корректно, Alerts page позволяет создавать правила. Оба сервера перезапущены.

## [2026-05-16] — [ARCH] — Phase 5 RWA / Treasuries COMPLETED
- **Increment A — Foundation & Provider Wiring**:
  - Alembic migration `b6fa1801e11d_phase_5_rwa_treasuries`: 5 new tables (`rwa_assets`, `rwa_asset_snapshots`, `treasury_entities`, `treasury_snapshots`, `tokenization_platforms`)
  - Alembic migration `f99eef8f0f6c_add_rwa_alerts_enabled`: `rwa_alerts_enabled` on `notification_preferences`
  - `BaseRwaAdapter` ABC in `adapters/rwa/`
  - `RwaAssetService` + `TreasuryService` with async cache, CRUD, seeding
  - `CoinGeckoRwaAdapter` for XAUT/PAXG via `/coins/{id}`
  - Pydantic schemas: `RwaAssetSchema`, `RwaAssetSnapshotSchema`, `TreasuryEntitySchema`, `TreasurySnapshotSchema`, `TokenizationPlatformSchema`
- **Increment B — RWA Asset Data & Gold Tokens**:
  - `GET /rwa/assets` with category filter, `GET /rwa/assets/{id}`, `GET /rwa/categories`, `GET /rwa/compare`
  - Seeded: XAUT, PAXG, BUIDL, USDY, CFG
  - Frontend: `/rwa` page with category filters, asset table, source/freshness badges
- **Increment C — Treasury Entities & BTC Holdings**:
  - `GET /treasury/entities`, `GET /treasury/entities/{id}`, `GET /treasury/btc-holdings`, `GET /treasury/platforms`
  - Seeded: MicroStrategy, MARA, Tesla, Block
  - Frontend: `/treasury` page with Companies/Platforms tabs, BTC holdings summary cards
- **Increment D — Tokenization Platforms & Detail Views**:
  - Seeded: Centrifuge, Figure, Maple Finance
  - Detail pages: `/rwa/[id]`, `/treasury/[id]` with issuer, blockchain, contract, snapshots
- **Increment E — Alert Compatibility & Polish**:
  - `AlertService` supports `rwa_price_threshold`, `treasury_holdings_change` rule types
  - `rwa_alerts_enabled` toggle on `/notifications` page
  - Frontend i18n: RU/EN translations for RWA/Treasury domain
  - Header: route-aware title, scanner status badge scoped to scanner page only
- **Compatibility**: All Phase 1-4 endpoints preserved. Zero breaking changes.
- **Schema**: 2 Alembic migrations added → 31 total tables, 8 total migrations.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.

## [2026-05-16] — [ARCH] — Phase 6.0 Architecture Hardening COMPLETED
- **Architecture Audit & Risk Map**: Full codebase audit, bounded contexts identified, tight coupling documented, enterprise-readiness gaps catalogued
- **Alembic Migration `b19c6344f081_phase_6_capability_foundation`**:
  - New table `plan_capabilities` — 41 seeded rows mapping plans (free/pro/enterprise) to features with limits
  - New table `feature_flags` — user-level feature overrides with expiration support
  - Altered `users` — added `feature_flags_json`, `plan_started_at`, `plan_expires_at` (all nullable)
- **CapabilityService** (`app/services/capability_service.py`): Plan-based feature gating with user-level override support. `check()`, `get_limit()`, `list_capabilities()`
- **RequestIDMiddleware** (`app/core/middleware.py`): ASGI middleware injecting `X-Request-ID` into all requests/responses
- **Global Exception Handler**: `DeltaGridException` hierarchy wired into FastAPI. Consistent `{ error: { code, message, request_id } }` format
- **CORS Hardening**: Env-aware method/header restrictions. `expose_headers=["X-Request-ID"]`. Debug mode keeps permissive defaults
- **Health Endpoint**: Now returns `api_version: "v1"`, `api_tier: "internal"`
- **Billing Plans**: `/billing/plans` now includes `capabilities` array per plan
- **Auth Response**: `UserResponse` now includes `feature_flags` dictionary
- **Frontend**:
  - `authStore.ts` enhanced with `featureFlags` on `User` and `hasFeature(key)` method
  - New hook: `useFeatureFlag.ts`
  - `api.ts` sends `X-API-Version: v1` header on all requests
- **API Boundary Markers**: `@internal` and `@public_ready` docstrings added to endpoints
- **Deferred to Phase 6.1–6.4**: B2B API, multi-tenancy, white-label, enterprise admin suite (backlogged with prerequisites)
- **Compatibility**: All Phase 1-5 endpoints preserved. Zero breaking changes.
- **Schema**: 1 Alembic migration added → 33 total tables, 9 total migrations.
- **Build**: Frontend `npm run build` passes with 0 TS errors. Backend starts cleanly.
