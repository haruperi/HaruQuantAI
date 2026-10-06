# Walkthrough: Yahoo frontend alignment and donor-family structural completion

Approved plan/version: implementation-plan.md version 1; explicit owner APPROVED: EXECUTE reply on 2026-10-06.
Status: bounded Yahoo frontend cohort completed and verified; all installed DataSource donor folders structurally accounted for. Behavioral parity is unverified.
Source HEAD: 69c24c148be9693a2c300f88c179b3ef2e832ddc. Baseline clean after TickDownloader commit. No Yahoo cohort commit performed.

## Outcome and changes

Confirmed mapping: SQX_REFERENCE_ROOT/internal/plugins/DataSourceYahoo -> HARUQUANTAI_ROOT/ui/app/plugins/data_source/Yahoo. Preserve donor-relative names/casing, including singular style.css and exact add/addPopupCtrl.ts/download/downloadPopupCtrl.ts filenames.

Before target inventory (5): YahooAddDialog.tsx, YahooDownloadDialog.tsx, yahoo.css, yahoo.ts, yahooStore.ts. After (13): YahooService.ts, module.ts, style.css, add/addPopup.tsx, add/addPopupCtrl.ts, add/module.ts, download/downloadPopup.tsx, download/downloadPopupCtrl.ts, download/module.ts, yahoo.ts, yahooStore.ts, README.md, source-map.json. baseline.json/after-inventory.json record complete before application/after scoped SHA-256 inventories.

Counts: 10 donor artifacts, 9 counterparts, 1 backend-JAR exclusion; 13 target files, 9 counterparts and 4 declared exceptions. No flattening/helpers/placeholders. Rules/store remain unchanged. Stylesheet relocation is byte-identical. Controllers own existing form/date/preset/overwrite/error actions; views own presentation, shared YahooModal remains in mapped add view, reused by download. Service owns relocated reservation/context and attaches to existing mock startAdd/startDownload/action authority. Modules own existing command contributions; Common ribbon/Data Manager imports updated together. Preserved IDs, labels, icon, command order, selected-row eligibility, errors, callback order, mock data, persistence keys and host progress.

README registers FEAT-UI-YAHOO-TRACEABILITY, DEC-UI-YAHOO-TRACEABILITY and FR-UI-YAHOO-source-mapping/workflow-preservation/clean-room. Manifest resolves ownership/catalog/review references, exact logical artifact locators, line locations, inspection date, SHA-256, source commit and clean-room fields. No donor implementation copied or new remote functionality.

Final read-only donor-family inventory, recorded in donor-family-coverage.json:

| Donor | Target folder | Artifacts | Counterparts | Exclusions |
| --- | --- | ---: | ---: | ---: |
| DataSourceDukascopy | Dukascopy | 19 | 16 | 3 |
| DataSourceCrypto | Crypto | 10 | 9 | 1 |
| DataSourceDarwinex | Darwinex | 19 | 17 | 2 |
| DataSourceFiles | FileImport | 17 | 13 | 4 |
| DataSourceMt5Api | MetaTrader | 7 | 6 | 1 |
| DataSourceSQEquityData | SQData/Equity | 11 | 9 | 2 |
| DataSourceSQFuturesData | SQData/Futures | 11 | 9 | 2 |
| DataSourceTD | TickDownloader | 7 | 6 | 1 |
| DataSourceYahoo | Yahoo | 10 | 9 | 1 |
| Total | nine explicit donor roots | 111 | 94 | 17 |

All nine donor inventories/fingerprints and manifest target classifications verified; no missing/unexpected donors or reported structural issues. Including SQData parent shared exceptions, 129 scoped target files comprise 94 counterparts and 35 exceptions. This audit checks structural completion only, retains justified exclusions and does not requalify every earlier browser workflow. Common/Catalogs/Export/Indicators/Tools and other donor families are outside this request's DataSource* scope.

## Verification

Execution date: 2026-10-06, Africa/Cairo. Focused tests began 14:02:12, repeated with both controller/view boundaries at 14:03:40. Full unit run began 14:02:38. Timestamped inventory verification is recorded in mapping-verification.json and donor-family-coverage.json. Commands below run from HARUQUANTAI_ROOT; donor argument is represented by logical root.

| Exact command | Exit/result | Evidence |
| --- | --- | --- |
| npm --prefix ui run test -- tests/unit/plugins/data_source/Yahoo | 0; 2 files, 9 tests passed | scoped mapping/rules tests; observed output |
| npm --prefix ui run typecheck | 0; initial and final repeat passed | observed compiler output |
| npm --prefix ui run test | 0; 77 files, 345 tests passed | observed summary |
| npm --prefix ui run build | 0; 2081 modules, built in 5.78 s | observed output; existing large-chunk warning |
| npm --prefix ui run test:ui -- tests/e2e/data-manager-yahoo.spec.ts --workers=1 | 0; 3 tests passed in 33.8 s | observed Playwright summary/screenshots |
| Get-Content .agents/logs/20261006_135832_data-source-yahoo-alignment/execute.py.txt -Raw \| python -X utf8 - | 0 | archived independently written relocation script |
| Get-Content .agents/logs/20261006_135832_data-source-yahoo-alignment/verify.py.txt -Raw \| python -X utf8 - SQX_REFERENCE_ROOT/internal/plugins | 0 | mapping-verification.json; donor-family-coverage.json |
| git diff --check | 0 | observed output |
| rg -n 'Yahoo/YahooAddDialog|Yahoo/YahooDownloadDialog|yahoo.css' ui/app ui/tests | 1/no matches; obsolete imports absent | observed search output |

Negative structural tests cover omitted/mis-cased/unclassified targets, collisions, wrong extensions, unsafe paths, invalid hashes/catalogs and unresolved owners. Both add/download views/controllers callable; provider commands retained. File verification confirms protected rules/store and all baseline sibling application files outside approved paths are byte-identical. All manifests parse, donor sources/catalog IDs and owner/review references resolve, clean-room fields valid; SQData root delegation/exception classification resolves. Canonical behavioral ledger/schema absent, so no ledger validation claimed.

Browser workflows verify Yahoo label/icon, input separators/postfix/required validation, offline add, persistence, selected-row download eligibility including mixed-source selection, all date presets/custom invalid range, overwrite coverage metadata, paused restore/resume, narrow footer, Tab wrap, quota failure, Escape and focus return. Mock operations remain offline; no Yahoo requests observed. Existing unit tests also exercise corrupt storage, active-job guard, cloned targets, duplicate catalogue input and range merges.

Reviewed download and narrow add screenshots directly: labels, dates/radios and footer fit; narrow textarea/postfix/modal controls remain visible. Light-skin selection action succeeds but screenshot retains dark colors, so Light-skin visual appearance is not established. Existing target CSS/host behavior retained. Generated screenshot evidence lives under HARUQUANTAI_ROOT/ui/test-results/data-manager-yahoo-matches-b9bc9-esets-and-redownload-policy/yahoo-download-dark.png and HARUQUANTAI_ROOT/ui/test-results/data-manager-yahoo-support-5008d-s-focus-and-storage-failure/yahoo-light-narrow.png; these runtime artifacts remain ignored.

## Deviations and residual risks

No material scope expansion. Scoped launcher disambiguation follows prior cohorts. Initial inline relocation script had a syntax error and executed no writes; corrected archived script then completed successfully. The baseline-only four-test run immediately after that failed script was not implementation qualification; successful nine-test/full-suite runs above are the candidate evidence.

Canonical reimplementation ledger/schema remain absent; no behavioral entries, decrypted-source algorithms or independent runtime parity established. Donor backend JAR only inventoried/hashed. Existing target offline catalogue and date policies retained even where donor defaults differ. Final donor-family audit reports structural completeness, not parity or revalidation of earlier runtime workflows. Prior documented unsupported/remote/backend and visual-theme gaps remain unresolved.

Shared junctions/data/.vscode/live databases/schema/donor installation/dependencies/backend untouched. Service lifecycle adapter exposes existing store actions; host progress controls retain original store authority. One-off scripts archived as text evidence, not retained Python application modules.

## Working tree and commit proposal

Observed git status --short:

```text
 M ui/app/plugins/data_source/Common/dataSourceRibbon.ts
 D ui/app/plugins/data_source/Yahoo/YahooAddDialog.tsx
 D ui/app/plugins/data_source/Yahoo/YahooDownloadDialog.tsx
 D ui/app/plugins/data_source/Yahoo/yahoo.css
 M ui/app/workspace/DataManager/DataManager.tsx
 M ui/tests/e2e/data-manager-yahoo.spec.ts
?? ui/app/plugins/data_source/Yahoo/README.md
?? ui/app/plugins/data_source/Yahoo/YahooService.ts
?? ui/app/plugins/data_source/Yahoo/add/
?? ui/app/plugins/data_source/Yahoo/download/
?? ui/app/plugins/data_source/Yahoo/module.ts
?? ui/app/plugins/data_source/Yahoo/source-map.json
?? ui/app/plugins/data_source/Yahoo/style.css
?? ui/tests/unit/plugins/data_source/Yahoo/sourceMapping.test.ts
?? ui/tests/unit/plugins/data_source/Yahoo/sourceMappingValidation.ts
```

No unrelated changes. Bounded audit log subtree ignored until authorized commit preparation.
Proposed commit message: refactor(ui): align Yahoo UI with DataSourceYahoo structure
No commit/merge/push/history mutation without separate owner authorization.

## Next gate

Owner walkthrough review and separate Yahoo commit authorization. Requested DataSource* structural cohorts are complete; no additional feature implementation authorized by this plan. Follow-up behavioral research, missing ledger setup, theme fixes or backend work require their own bounded plans/approval.
