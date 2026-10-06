# Darwinex UI

Donor: `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex`.
Target: `HARUQUANTAI_ROOT/ui/app/plugins/data_source/Darwinex`.
Donor informs; specification owns. All implementation is independently written target code.

## Feature registry

| Feature | Scope | Status |
| --- | --- | --- |
| FEAT-UI-DARWINEX-TRACEABILITY | Donor-relative frontend boundaries with retained mock workflows | implemented; qualification in approved cohort walkthrough |

| Requirement | Target contract |
| --- | --- |
| FR-UI-DARWINEX-source-mapping | Exact relative filenames/casing and complete source/target classification. |
| FR-UI-DARWINEX-workflow-preservation | Preserve selection, mapping/back, consent, folder import, validation, profile gating, focus/Escape, persistence and simulated jobs. |
| FR-UI-DARWINEX-clean-room | Logical roots/fingerprints; no proprietary source, sensitive or personal data. |

## Decision: DEC-UI-DARWINEX-TRACEABILITY

Map HTML to TSX, JS to TS and CSS to CSS. Add view/controller own catalogue/form;
`add/selectInstrumentsPopup.tsx` owns broker identification presentation. Import
view/controller own picker/discovery; download view/controller own range/profile
presentation. `DarwinexService.ts` adapts existing context checks, rules and mock
stores. Modules contribute existing commands to Common ribbon; Data Manager
consumes child module screens. Small shared modal stays in mapped add component.
`style.css` and `add/styles.css` retain independently written styles.

Disclaimer counterparts own reused target free-data consent, close callback and
exported standalone composition. Add footer consumes consent. Standalone is
unmounted; no route added and no donor legal prose copied. This is a structural
responsibility boundary, not disclaimer parity or confirmed donor reachability.

Manifest: 5 template, 10 script, 2 stylesheet counterparts; 2 excluded non-UI
artifacts (JAR and CSV). Total 17 counterparts + 4 exceptions = 21 target files.
Exceptions: existing `darwinex.ts`, `darwinexStore.ts`, README and manifest.
Existing external catalogue CSV and all mock persistence APIs remain unchanged.

## Verification and gaps

Run focused `npm --prefix ui run test -- tests/unit/plugins/data_source/Darwinex`,
then UI typecheck, unit tests, build and
`npm --prefix ui run test:ui -- tests/e2e/data-manager-darwinex.spec.ts --workers=1`.
See approved cohort walkthrough for actual commands/results and inventories.
Mapping validation does not establish SQX behavioral parity. Real folder data
decoding, CDN/network lifecycle and generated bars remain backend gaps.
Canonical reimplementation ledger/schema were absent; this manifest does not
replace the ledger and no new behavioral evidence record is asserted.

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.
