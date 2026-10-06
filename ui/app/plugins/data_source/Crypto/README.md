# Crypto UI

Donor: `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`.
Target: `HARUQUANTAI_ROOT/ui/app/plugins/data_source/Crypto`.
Donor informs; specification owns. Independently written React code is retained.

## Feature registry

| Feature | Scope | Status |
| --- | --- | --- |
| FEAT-UI-CRYPTO-TRACEABILITY | Donor-relative frontend boundaries with retained mock workflows | implemented; qualification results in approved cohort walkthrough |

| Requirement | Target contract |
| --- | --- |
| FR-UI-CRYPTO-source-mapping | Preserve exact donor-relative names/casing and account for all source/target files. |
| FR-UI-CRYPTO-workflow-preservation | Retain catalogue, consent, validation, selection, focus/Escape, persistence and simulated progress. |
| FR-UI-CRYPTO-clean-room | Logical-root provenance and fingerprints; no proprietary source, sensitive or personal data. |

## Decision: DEC-UI-CRYPTO-TRACEABILITY

Map HTML to TSX, JS to TS, CSS to CSS. `add/addPopup.tsx` owns catalogue/modal
presentation; `add/addPopupCtrl.ts` owns form state. `import/importPopup.tsx`
owns download presentation; `import/importPopupCtrl.ts` owns range/form state.
Child modules export screens/commands; `module.ts` contributes the existing
provider to Common ribbon. Data Manager consumes child module exports.
`DataSourceCryptoService.ts` adapts current mock catalogues and stores, including
existing cross-provider context checks. Shared modal remains in mapped add view.
No helper folders, backend requests or changes to mock persistence are introduced.

Manifest counts: 2 template, 6 script, 1 stylesheet counterparts; 1 excluded JAR.
Target: 9 counterparts and 4 declared exceptions (13 files). `crypto.ts` and
`cryptoStore.ts` retain independent rules/state; README and manifest are target
documentation exceptions. JAR is fingerprinted only, never copied or executed.

## Verification and gaps

Run `npm --prefix ui run test -- tests/unit/plugins/data_source/Crypto`,
`npm --prefix ui run typecheck`, `npm --prefix ui run test`,
`npm --prefix ui run build`, and
`npm --prefix ui run test:ui -- tests/e2e/data-manager-crypto.spec.ts --workers=1`.
Mapping tests cover completeness, exact casing, collisions, provenance and owner
IDs; browser tests exercise retained mock workflows. Actual results and inventory
fingerprints belong to the cohort walkthrough.

Structural alignment does not establish SQX behavioral parity. Real exchange
catalogue loading, market bars and backend lifecycle remain unsupported by this
frontend cohort. Canonical reimplementation ledger/schema were not found;
this manifest does not replace them and no new behavioral claim is recorded.

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.
