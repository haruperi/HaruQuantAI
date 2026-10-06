# Walkthrough: TickDownloader frontend alignment

Approved plan/version: implementation-plan.md version 1; owner APPROVED: EXECUTE reply on 2026-10-06.
Status: bounded frontend structural cohort completed and verified; Light-skin visual qualification remains limited.
Source HEAD: 30128b58bbc7ac495f33a860ba7d31d603eecec5. Working-tree baseline clean following SQData commit. No cohort commit made.

## Outcome and changes

Confirmed outer mapping: SQX_REFERENCE_ROOT/internal/plugins/DataSourceTD -> HARUQUANTAI_ROOT/ui/app/plugins/data_source/TickDownloader. Preserved donor-relative filenames/casing beneath that root, with HTML -> TSX, JS -> TS and CSS -> CSS.

Before inventory (3 files): TickDownloaderImportDialog.tsx, tickDownloader.css, tickDownloader.ts. After inventory (9 files): DataSourceTDService.ts, module.ts, styles.css, import/DataSourceTDImportCtrl.ts, import/importPopup.tsx, import/module.ts, tickDownloader.ts, README.md, source-map.json. Complete before application hashes and after scoped hashes are recorded in baseline.json and after-inventory.json.

Counts: 7 donor artifacts; 6 mapped counterparts and 1 excluded backend JAR. Target has 6 counterparts and 3 explicit exceptions. No flattening, helper folders or empty counterparts. Shared Common/dataManagerStore.ts is an unchanged external capability dependency, outside scoped target inventory.

View/controller responsibilities now match mapped files: controller owns manifest/postfix/selection/errors, picker processing, indeterminate checkbox, focus effects and submission. View retains JSX and Escape/Tab trap. Service attaches metadata discovery, import start and existing pause/resume/stop API to target rules/shared store. Modules own the existing provider/command. Common ribbon and Data Manager imports updated together. Existing state subscription, persistence keys, cross-provider guards, error text, mock progress and callback order remain preserved. Relocated stylesheet is byte-identical.

README registers FEAT-UI-TD-TRACEABILITY, DEC-UI-TD-TRACEABILITY and FR-UI-TD-source-mapping/workflow-preservation/clean-room. Manifest includes exact logical source locators, catalog references, line locations, access date, SHA-256 fingerprints, source commit/review reference, limitations and clean-room flags. No donor code copied or parity claimed.

## Verification

Execution date: 2026-10-06, Africa/Cairo. Focused tests began 13:53:08; full unit tests began 13:53:35. Machine inventory/hash validation timestamp is recorded in mapping-verification.json. Commands run from HARUQUANTAI_ROOT; donor CLI argument below is represented by its logical root.

| Exact command | Exit/result | Evidence |
| --- | --- | --- |
| npm --prefix ui run test -- tests/unit/plugins/data_source/TickDownloader | 0; 2 files, 9 tests passed | scoped rules/mapping tests; observed output |
| npm --prefix ui run typecheck | 0 | observed compiler output |
| npm --prefix ui run test | 0; 76 files, 340 tests passed | observed summary |
| npm --prefix ui run build | 0; 2075 modules, built in 5.63 s | observed Vite output; existing large-chunk warning |
| npm --prefix ui run test:ui -- tests/e2e/data-manager-tickdownloader.spec.ts --workers=1 | 0; initial 2 tests passed, final 3 tests passed in 20.2 s | observed Playwright output; screenshots |
| npm --prefix ui run test:ui -- tests/e2e/data-manager-tickdownloader.spec.ts --workers=1 --grep 'initial focus' | 0; 1 test passed | observed Playwright summary; subsequent search returned 1 for no matches in combined shell invocation |
| Get-Content .agents/logs/20261006_135038_data-source-td-alignment/verify.py.txt -Raw \| python -X utf8 - SQX_REFERENCE_ROOT/internal/plugins/DataSourceTD | 0; inventory, fingerprints, ownership and protected application checks passed | mapping-verification.json; archived verification script |
| git diff --check | 0 | observed output |
| rg -n 'TickDownloader/TickDownloaderImportDialog|tickDownloader.css' ui/app ui/tests | 1; no matches, obsolete imports absent | observed output |

Mapping tests reject missing/mis-cased/unclassified files, collisions, wrong extensions, unsafe paths, unresolved owners/catalog IDs and invalid fingerprints; command identity and component/controller boundaries checked. Filesystem verification compares actual donor inventory/hash, all target classification, byte-identical rules/CSS and every baseline application file outside approved paths. Shared Common store and sibling application files remain unchanged. JSON manifest parsed and owner IDs resolve against README; no behavioral ledger validation asserted.

Browser coverage: required-folder/no-selection/duplicate validation, metadata picker, individual/select-all selection, postfix, pause/reload/resume/completion, persisted row status, retained-folder reselection, unchanged mock fixture content, offline routing, empty folder, cancellation, quota error, initial focus, both Tab boundaries and Escape closure. Initial focus and closure directly verified; prior focus restoration effect is preserved but successful restoration to a possibly removed menu item is not independently established.

Reviewed normal and 740x650 screenshots directly: dialog and footer controls fit, grid/selection visible, no layout overlap. Light-skin selection action succeeds, but its captured image remains dark; Light-skin visual appearance is unverified. Existing stylesheet/host behavior preserved; no unrelated theme fix. Screenshot paths: HARUQUANTAI_ROOT/ui/test-results/data-manager-tickdownloade-f2deb-d-persisted-trailing-status/tickdownloader-dark.png and HARUQUANTAI_ROOT/ui/test-results/data-manager-tickdownloade-17ff3-ellation-and-failed-storage/tickdownloader-light.png. Generated artifacts remain ignored.

## Deviations and residual risks

No material scope expansion. Scoped browser launcher disambiguation follows prior cohorts. Added keyboard qualification within approved test path. Service action adapter exposes existing shared-store actions; host lifecycle continues using its original store API.

Canonical reimplementation.json and reimplementation.schema.json remain absent. No behavioral records, decrypted-source algorithms, runtime defaults or parity assertions. Backend JAR inspected by inventory/hash only. Protected tickDownloader.ts retains a pre-existing SQX-attributing discovery comment with no ledger support; this is an unresolved research gap, not a verified finding. Real TickDownloader import/parsing remains outside frontend scope.

No shared junction, data/.vscode file, live database/schema, donor installation, dependency, backend or Git history change. One-off verification script is archived as text evidence, rather than retained application Python.

## Working tree and commit proposal

Observed git status --short:

```text
 M ui/app/plugins/data_source/Common/dataSourceRibbon.ts
 D ui/app/plugins/data_source/TickDownloader/TickDownloaderImportDialog.tsx
 D ui/app/plugins/data_source/TickDownloader/tickDownloader.css
 M ui/app/workspace/DataManager/DataManager.tsx
 M ui/tests/e2e/data-manager-tickdownloader.spec.ts
?? ui/app/plugins/data_source/TickDownloader/DataSourceTDService.ts
?? ui/app/plugins/data_source/TickDownloader/README.md
?? ui/app/plugins/data_source/TickDownloader/import/
?? ui/app/plugins/data_source/TickDownloader/module.ts
?? ui/app/plugins/data_source/TickDownloader/source-map.json
?? ui/app/plugins/data_source/TickDownloader/styles.css
?? ui/tests/unit/plugins/data_source/TickDownloader/sourceMapping.test.ts
?? ui/tests/unit/plugins/data_source/TickDownloader/sourceMappingValidation.ts
```

No unrelated changes observed. Audit evidence remains in this bounded ignored log subtree until authorized commit preparation.
Proposed commit message: refactor(ui): align TickDownloader UI with DataSourceTD structure
No commit/merge/push/history mutation without separate owner authorization.

## Next gate

Owner walkthrough review and separate commit authorization. DataSourceYahoo is the remaining donor cohort; audit and present its next bounded plan after owner instruction.
