# Walkthrough: SQData equity and futures frontend alignment

Approved plan/version: implementation-plan.md version 1; explicit owner APPROVED: EXECUTE reply on 2026-10-06.
Status: bounded frontend cohort implemented and qualified, with visual-theme qualification limitation below. Full donor behavioral parity is not established.
Candidate source HEAD: 7866f254378fac3b478537d3e59ba01c9976821b. Baseline clean after MetaTrader commit. No commit performed for this cohort.

## Outcome and changes

Confirmed separate mappings: SQX_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData -> HARUQUANTAI_ROOT/ui/app/plugins/data_source/SQData/Equity; DataSourceSQFuturesData -> SQData/Futures. Both outer mappings are explicit in child manifests and root ownership registry.

Before target inventory: SQDataAddDialog.tsx, sqData.css, sqData.ts, sqDataStore.ts (4 files). After: 24 files; see after-inventory.json for complete exact paths and SHA-256 fingerprints. Each child has 9 meaningful counterparts plus source-map.json; parent retains shared rules/store and adds README.md/source-map.json. Counts: 22 donor artifacts, 18 mapped counterparts, 4 exclusions; 24 target files, comprising 18 counterparts and 6 exceptions. Each donor's backend JAR and verified zero-byte update/updatePopup.html are excluded. No empty target counterpart was manufactured.

Moved existing view/CSS into mapped Equity owners, extracted form state/timers/lookup/selection into typed controller, and added distinct Futures composition. Both usage-condition counterparts remain distinct and reuse independent target-authored text. Provider service adapters preserve reservation/error checks and store start; update controllers attach to the existing host simulation callback. Add/update/root modules own the original ribbon commands. Updated Data Manager imports/rendering/dispatch and ribbon registrations together. No new backend, remote subscription, database or dependency.

Ownership: root README registers FEAT-UI-SQEQUITY-TRACEABILITY and FEAT-UI-SQFUTURES-TRACEABILITY, their DEC IDs and source-mapping/workflow-preservation/clean-room FR IDs. Child manifests resolve those registrations. Root manifest delegates both children and classifies shared exceptions without double counting. Fingerprints and logical locators contain no machine-specific paths or proprietary source.

## Verification

Execution date: 2026-10-06, Africa/Cairo; focused unit runs began 13:40:41 and 13:43:12, full unit run 13:41:08. Machine validation timestamp is recorded in mapping-verification.json. Commands below run from HARUQUANTAI_ROOT; donor argument represented by logical root in this report.

| Exact command | Exit/result | Evidence |
| --- | --- | --- |
| npm --prefix ui run test -- tests/unit/plugins/data_source/SQData | 0; 2 files, 13 tests passed, including mapping negative cases, parent delegation and update callbacks | observed tool output; scoped tests |
| npm --prefix ui run typecheck | 0; initial and final repeat passed | observed compiler output |
| npm --prefix ui run test | 0; 75 files, 335 tests passed | observed test summary |
| npm --prefix ui run build | 0; 2071 modules, production build passed | observed Vite output; existing >500 kB chunk warning |
| npm --prefix ui run test:ui -- tests/e2e/data-manager-sq-data.spec.ts --workers=1 | 0; original 5 passed, then final 6 passed in 42.1 s | observed Playwright output; ui/test-results screenshots |
| npm --prefix ui run test:ui -- tests/e2e/data-manager-sq-data.spec.ts --workers=1 --grep 'provider update' | 1 initially; incorrect test expectation exposed existing guard distinction, corrected test subsequently passed in full 6-test run | retained explanation below |
| python -X utf8 .agents/logs/20261006_133334_data-source-sqdata-alignment/verify.py SQX_REFERENCE_ROOT/internal/plugins | 0; donor inventory/hash/size, protected UI/rules/store and relocated CSS checks passed | mapping-verification.json; baseline.json; after-inventory.json |
| rg -n 'SQData/SQDataAddDialog|sqData.css' ui/app ui/tests | no matches; obsolete imports absent | observed search output |
| git diff --check | 0 | observed output |

Negative mapping tests cover missing/mis-cased/unclassified targets, collisions, wrong extensions and unsafe paths, invalid source catalog/fingerprint and unresolved owners. Both donor inventories and all SHA-256 fingerprints match inspected files. Shared rules/store are unchanged; all baseline application files outside the approved SQData and two integration paths are byte-identical. Relocated stylesheet is byte-identical. Existing mock records, storage keys, error strings and timer delays remain preserved.

Browser checks exercise equity/futures lookup, conditions and focus/Escape, eligibility, sorting/selection, duplicate/fixed-shift validation, metadata, paused restoration and persistence, cancellation, offline behavior, active-provider guard, narrow footer and keyboard focus. Reviewed normal/narrow screenshots directly: bounded dialog and accessible footer controls, no visible layout collision. Test selects Light skin, but both captured images retain dark colors; selection action passed, visual Light-skin qualification is not established. Existing shared CSS/theme behavior is retained; no host theme fix authorized.

## Deviations and residual risks

No material scope expansion or plan iteration. Scoped browser harness now disambiguates the Data Manager launcher and uses in-memory AppStore profile fixture, following prior cohorts because host settings are not persisted.

Initial new update test incorrectly assumed paused generic progress blocked another update. Inspection confirmed existing startOperation guards provider-store jobs only; the approved refactor preserves that distinction. Corrected test verifies generic update replacement and a paused SQData add-job guard. This is a target implementation limitation, not a donor behavioral finding; no functionality silently changed.

Both canonical reimplementation ledger/schema remain absent; no behavioral evidence entries, source extraction or ledger validation claimed. Manifests provide structural identity/provenance only. Donor defaults, remote services, subscriptions, algorithms and execution parity remain unverified. Backend binaries were only inventoried/hashed. Lookup cleanup was preserved by direct extraction; no standalone fake-timer test was added. Shared junctions, donor files, live database and schema were untouched.

## Working tree and commit proposal

Observed git status --short:

```text
 M ui/app/plugins/data_source/Common/dataSourceRibbon.ts
 D ui/app/plugins/data_source/SQData/SQDataAddDialog.tsx
 D ui/app/plugins/data_source/SQData/sqData.css
 M ui/app/workspace/DataManager/DataManager.tsx
 M ui/tests/e2e/data-manager-sq-data.spec.ts
?? ui/app/plugins/data_source/SQData/Equity/
?? ui/app/plugins/data_source/SQData/Futures/
?? ui/app/plugins/data_source/SQData/README.md
?? ui/app/plugins/data_source/SQData/source-map.json
?? ui/tests/unit/plugins/data_source/SQData/sourceMapping.test.ts
?? ui/tests/unit/plugins/data_source/SQData/sourceMappingValidation.ts
```

Audit logs live in this bounded ignored log folder, following previous cohorts. No unrelated working-tree changes observed. Before/after inventories classify the removed names as relocations, not lost workflows.

Proposed commit message: refactor(ui): align SQData equity and futures donor structure

## Next gate

Ready for owner walkthrough review and separate commit authorization. Remaining donor cohorts: DataSourceTD and DataSourceYahoo. Audit/plan the next bounded folder after owner instruction; no next-provider implementation authorized here.

Commit preparation: hooks added the baseline JSON final newline. One-off execution/verification scripts are archived as execute.py.txt and verify.py.txt (text evidence, not retained application modules); historical commands above identify the names used during execution. Initial commit attempt was rejected by Python lint for those audit scripts; hooks remain enabled.
