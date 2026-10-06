# Implementation plan: SQData equity and futures frontend alignment

Version: 1. Status: APPROVED.
Date: 2026-10-06, Africa/Cairo. Source HEAD: 7866f254378fac3b478537d3e59ba01c9976821b.
Working-tree baseline: clean after owner-authorized MetaTrader commit.
Owner approval reference: explicit APPROVED: EXECUTE user reply on 2026-10-06 for version 1. Commit/start-next authorizes the previous commit and this audit/plan only.

## Objective and acceptance boundary

Align one bounded target folder, HARUQUANTAI_ROOT/ui/app/plugins/data_source/SQData, with its two confirmed donor roots. Explicit mapping: SQX_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData -> SQData/Equity; SQX_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData -> SQData/Futures. These deliberately distinct outer folders prevent collisions between separately named donor counterparts. Preserve frontend mock catalogues, stores, simulated lookup/add/update operations, validation, focus, Escape, selection, subscriptions, persistence and progress. No backend, network integration, database change or SQX parity claim.

## Research and authority

Audited donor recursive inventories, root services/modules, add templates/controllers/modules/conditions, update modules/controllers/templates and styles. Audited current SQDataAddDialog.tsx, sqData.ts, sqDataStore.ts, sqData.css, Data Manager integration, ribbon contribution, unit and browser tests, sibling store reservations and shared dependencies. Read root AGENTS.md and canonical plan/walkthrough templates; completed Dukascopy and subsequent cohorts establish the standard. Audit commands: git status --short, git rev-parse HEAD, Get-ChildItem, Get-Item, Get-Content, rg and rg --files. Canonical reimplementation.json and reimplementation.schema.json remain absent; no behavioral ledger edits or validation claim authorized.

Current target has four files. Shared dialog owns both provider presentations, search delay and cleanup, eligibility/selection, conditions/focus return and add orchestration. Rules/store own mock catalogues, subscription profiles, validation, reservations, progress and browser persistence. DataManager.tsx owns existing generic simulated equity/futures update actions. Other providers consume shared SQData rules/store; keep those paths and APIs unchanged. Common ribbon owns provider commands. No separate provider route files were found.

Each donor has 11 artifacts: 3 HTML, 6 JS, 1 CSS and 1 JAR. Each update/updatePopup.html is verified zero bytes. Exclude those empty templates with their byte-size/fingerprint evidence; do not invent update UI or create empty placeholders. Exclude both backend JARs. Each provider therefore has 9 mapped counterparts and 2 justified exclusions; combined counts: 18 counterparts, 4 exclusions.

## Decisions and public contracts

Propose root SQData/README.md ownership registration for FEAT-UI-SQEQUITY-TRACEABILITY and FEAT-UI-SQFUTURES-TRACEABILITY, corresponding DEC-UI-SQEQUITY-TRACEABILITY and DEC-UI-SQFUTURES-TRACEABILITY, and each provider's FR-UI-SQEQUITY/FR-UI-SQFUTURES-source-mapping, -workflow-preservation and -clean-room requirements. IDs become repository truth only after approved registration. Root README owns implementation status.

For each provider, preserve these donor-relative paths beneath the explicitly mapped Equity or Futures root:

| Donor | Counterpart |
| --- | --- |
| module.js | module.ts |
| SQEquityDataService.js / SQFuturesDataService.js | SQEquityDataService.ts / SQFuturesDataService.ts |
| styles.css | styles.css |
| add/addPopup.html | add/addPopup.tsx |
| add/dataUsageConditionsPopup.html | add/dataUsageConditionsPopup.tsx |
| add/module.js | add/module.ts |
| add/SQEquityDataAddCtrl.js / add/SQFuturesDataAddCtrl.js | add/SQEquityDataAddCtrl.ts / add/SQFuturesDataAddCtrl.ts |
| update/module.js | update/module.ts |
| update/SQEquityDataUpdateCtrl.js / update/SQFuturesDataUpdateCtrl.js | update/SQEquityDataUpdateCtrl.ts / update/SQFuturesDataUpdateCtrl.ts |

Distinct provider files remain distinct. Equity mapped view/controller may export shared typed composition reused by Futures mapped view/controller; each provider binds its own identity/service/conditions counterpart. Keep small helpers in owning mapped files. Services attach to existing target rules/store and host simulation callbacks. Update controllers dispatch the existing host simulation labels and guards, without creating dataset update semantics. Root/child modules own existing contributions and exports. Equity styles own relocated shared CSS; Futures styles explicitly import/reuse the mapped shared stylesheet, without new visual behavior.

Each child receives source-map.json covering its 11 donor artifacts and 10 target files (9 counterparts plus manifest exception). Root source-map.json accounts for retained shared sqData.ts, sqDataStore.ts, README.md and itself, and delegates to the two child manifests. Expected total: 24 target files = 18 counterparts + 6 declared exceptions. Parent/child counts distinguish delegated files and avoid counting them twice. Source references use exact logical locators, inspection dates, SHA-256 fingerprints, catalog IDs, narrow locations and relation; review/source HEAD and clean-room flags follow the pilot. Structural manifests do not replace a behavioral ledger.

## Ordered implementation

1. Record baseline/donor inventories and hashes; verify approved scope and source identities.
2. Relocate SQDataAddDialog.tsx to Equity/add/addPopup.tsx and extract existing state, timers and actions into Equity/add/SQEquityDataAddCtrl.ts. Export shared typed composition as needed. Add meaningful Futures mapped view/controller bindings and both separately named conditions components, retaining target-authored conditions text.
3. Add provider service adapters and add/root/update modules; move existing direct-update dispatch responsibility into named update controllers through host callbacks. Preserve command IDs, labels, ordering and guard/progress behavior.
4. Relocate sqData.css to Equity/styles.css and add Futures/styles.css shared-style reuse. Update Data Manager imports/rendering/dispatch and Common ribbon contributions together.
5. Register root ownership README and root/child manifests. Record empty-template and binary exclusions, independent target implementation and unverified donor behaviors explicitly.
6. Add scoped mapping/boundary qualification tests; adjust scoped browser launcher/profile fixtures only where current harness requires it. Run checks and create walkthrough before requesting commit authorization.

## ALLOWED_WRITE_PATHS

All paths below are HARUQUANTAI_ROOT-relative.

Moves/removals:
- ui/app/plugins/data_source/SQData/SQDataAddDialog.tsx -> ui/app/plugins/data_source/SQData/Equity/add/addPopup.tsx
- ui/app/plugins/data_source/SQData/sqData.css -> ui/app/plugins/data_source/SQData/Equity/styles.css

New files (exact paths):
- ui/app/plugins/data_source/SQData/README.md
- ui/app/plugins/data_source/SQData/source-map.json
- ui/app/plugins/data_source/SQData/Equity/source-map.json
- ui/app/plugins/data_source/SQData/Equity/module.ts
- ui/app/plugins/data_source/SQData/Equity/SQEquityDataService.ts
- ui/app/plugins/data_source/SQData/Equity/add/dataUsageConditionsPopup.tsx
- ui/app/plugins/data_source/SQData/Equity/add/module.ts
- ui/app/plugins/data_source/SQData/Equity/add/SQEquityDataAddCtrl.ts
- ui/app/plugins/data_source/SQData/Equity/update/module.ts
- ui/app/plugins/data_source/SQData/Equity/update/SQEquityDataUpdateCtrl.ts
- ui/app/plugins/data_source/SQData/Futures/source-map.json
- ui/app/plugins/data_source/SQData/Futures/module.ts
- ui/app/plugins/data_source/SQData/Futures/SQFuturesDataService.ts
- ui/app/plugins/data_source/SQData/Futures/styles.css
- ui/app/plugins/data_source/SQData/Futures/add/addPopup.tsx
- ui/app/plugins/data_source/SQData/Futures/add/dataUsageConditionsPopup.tsx
- ui/app/plugins/data_source/SQData/Futures/add/module.ts
- ui/app/plugins/data_source/SQData/Futures/add/SQFuturesDataAddCtrl.ts
- ui/app/plugins/data_source/SQData/Futures/update/module.ts
- ui/app/plugins/data_source/SQData/Futures/update/SQFuturesDataUpdateCtrl.ts

Integration/tests:
- ui/app/workspace/DataManager/DataManager.tsx (SQData imports, rendering and existing update dispatch only)
- ui/app/plugins/data_source/Common/dataSourceRibbon.ts (equity/futures contributions only)
- ui/tests/unit/plugins/data_source/SQData/sourceMapping.test.ts
- ui/tests/unit/plugins/data_source/SQData/sourceMappingValidation.ts
- ui/tests/e2e/data-manager-sq-data.spec.ts (scoped workflows/qualification and isolated fixtures)

Evidence: bounded .agents/logs/20261006_133334_data-source-sqdata-alignment/ subtree for plan, inventories/hashes, verification scripts/results and walkthrough. No absolute machine paths or donor source text in evidence.

Protected: sqData.ts, sqDataStore.ts and existing sqData.test.ts; siblings/shared utilities, dependencies/config, backend, donor installation, data/, .vscode/ and live databases. Only two named obsolete frontend files may be removed following relocation. No junction change, schema action or Git mutation under execution approval.

## Verification and release conditions

Record timestamps, exit codes and actual results:
- npm --prefix ui run test -- tests/unit/plugins/data_source/SQData
- npm --prefix ui run typecheck
- npm --prefix ui run test
- npm --prefix ui run build
- npm --prefix ui run test:ui -- tests/e2e/data-manager-sq-data.spec.ts --workers=1
- git diff --check
- rg -n 'SQData/SQDataAddDialog|sqData.css' ui/app ui/tests (obsolete imports absent)

Validate full 22-artifact donor inventory/fingerprints, 18 mappings/4 exclusions, exact case/extensions, zero collisions, all 24 target files classified, root delegation, provenance/catalog/ownership/review references and clean-room fields. Negative cases cover omitted/mis-cased/unclassified/duplicate files, incorrect extensions/hashes and invalid references. Verify protected file and sibling hashes, component/controller responsibilities and write-path compliance. Browser qualification covers both provider searches, eligibility, sorting/selection, conditions/focus/Escape, validation, timezone metadata, duplicate/active-job guards, add/pause/reload/resume/stop, offline behavior, light/narrow layout and existing direct-update simulation. Report any unexercised limits explicitly. No ledger validation while canonical files are absent.

## Risks and deviations

Dual donor roots require explicit child mapping rather than collapsing same-named files. Shared hook/view relocation must preserve timers, cancellation and profile changes. Empty donor update templates support exclusion, not a parity claim. Shared target conditions/CSS composition is declared reuse, while separate counterparts retain provider responsibility. No new legal donor prose, subscriptions, remote datasets or update semantics. Material added paths, behavior/contracts/dependencies/destructive targets require recorded iteration and renewed approval.

## Walkthrough and owner gates

Create walkthrough.md using the canonical template: actual commands/results, before/after inventories and separate counts, deviations, residual gaps, Git status and proposed subject `refactor(ui): align SQData equity and futures donor structure`.

Stop for APPROVED: EXECUTE on version 1 before source edits or ownership registration. Separate owner authorization is required to commit after walkthrough review.
