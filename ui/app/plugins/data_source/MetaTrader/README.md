# MetaTrader UI

Donor: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api`.
Target: `HARUQUANTAI_ROOT/ui/app/plugins/data_source/MetaTrader`.
Outer names intentionally differ. Donor informs; specification owns.

## Feature registry

| Feature | Scope | Status |
| --- | --- | --- |
| FEAT-UI-MT5-TRACEABILITY | Donor-relative frontend boundaries with retained mock MT5 import | implemented; qualification in approved cohort walkthrough |

| Requirement | Target contract |
| --- | --- |
| FR-UI-MT5-source-mapping | Exact relative filenames/casing and complete donor/target classification. |
| FR-UI-MT5-workflow-preservation | Preserve folder metadata discovery, mock fetch timing/cleanup, selections, presets, broker/postfix, focus/Escape, errors, persistence and simulation. |
| FR-UI-MT5-clean-room | Logical roots/locators/fingerprints; no proprietary source, sensitive or personal data. |

## Decision: DEC-UI-MT5-TRACEABILITY

Map HTML to TSX, JS to TS, CSS to CSS. `import/importPopup.tsx` owns retained
form/table/disclaimer presentation; `import/DataSourceMt5ApiImportCtrl.ts` owns
state, folder picker, mock fetch timer/cleanup, presets and submission validation.
`DataSourceMt5Api.ts` adapts existing metadata/catalogue/context/store capabilities.
Its filename matches donor DataSourceMt5Api.js despite the donor's internal service
name. Root/child modules contribute the same provider/command and export screen
to Data Manager. styles.css retains independently written target styles.
No helper directory, networking, terminal execution or new persistence capability.

Manifest: 1 template, 4 script, 1 stylesheet counterparts; 1 excluded JAR.
Target: 6 counterparts + 4 exceptions = 10 files. Existing mt5Import.ts,
mt5ImportStore.ts, README and manifest are explicit exceptions. Rules/store and
mock fixture symbols remain unchanged for all sibling consumers.

## Verification and gaps

Run focused `npm --prefix ui run test -- tests/unit/plugins/data_source/MetaTrader`,
then UI typecheck, unit tests, build and
`npm --prefix ui run test:ui -- tests/e2e/data-manager-mt5-import.spec.ts --workers=1`.
See approved cohort walkthrough for actual verification/inventories.
Structural mapping does not establish SQX behavioral parity. Real terminal APIs,
broker discovery, market bars and donor backend lifecycle remain unimplemented.
Canonical reimplementation ledger/schema were absent; no new behavioral evidence
record or ledger-schema validation is asserted. Manifest does not replace ledger.
