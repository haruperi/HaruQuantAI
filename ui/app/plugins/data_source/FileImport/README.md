# FileImport UI

Donor: `SQX_REFERENCE_ROOT/internal/plugins/DataSourceFiles`.
Target: `HARUQUANTAI_ROOT/ui/app/plugins/data_source/FileImport`.
Outer names intentionally differ. Donor informs; specification owns.

## Feature registry

| Feature | Scope | Status |
| --- | --- | --- |
| FEAT-UI-FILEIMPORT-TRACEABILITY | Donor-relative frontend boundaries for retained symbol/single/mass workflows | implemented; qualification in approved cohort walkthrough; installation import excluded |

| Requirement | Target contract |
| --- | --- |
| FR-UI-FILEIMPORT-source-mapping | Exact relative names/casing; complete donor/target classification including scoped UI exclusions. |
| FR-UI-FILEIMPORT-workflow-preservation | Preserve nested instruments/help, format CRUD, parser options, async cancellation, naming policies, errors, focus/Escape, persistence and simulation. |
| FR-UI-FILEIMPORT-clean-room | Logical-root locators/fingerprints; no proprietary source, sensitive or personal data. |

## Decision: DEC-UI-FILEIMPORT-TRACEABILITY

Map HTML to TSX, JS to TS, CSS to CSS. Add, import and massImport modules own
existing screens/commands; root module contributes the same File import provider.
DataSourceFiles-prefixed controller hooks own state/navigation/submission.
Add view retains local commission/swap/instrument/help helpers and optional mass
composition contract. Import view composes separately mapped new-format fields;
delete-format confirmation remains local. Mass view reuses mapped add form.
DataSourceFilesService adapts existing stores, file reads and cross-provider
context; parsing/persistence remain in unchanged shared target utilities.
styles.css consolidates existing independently written styles in cascade order.
No backend, new routes, installation discovery or licensing behavior introduced.

Manifest counts: donor 17; mapped 13 (4 templates, 8 scripts, 1 stylesheet);
excluded 4 (1 template, 2 scripts for appImport, 1 JAR). Target: 13 counterparts
+ 6 exceptions = 19 files. Four existing rule/store utilities, README and manifest
are target-only exceptions. No empty appImport facade is created.

## Verification and gaps

Run focused `npm --prefix ui run test -- tests/unit/plugins/data_source/FileImport`,
then UI typecheck, unit tests, build and
`npm --prefix ui run test:ui -- tests/e2e/data-manager-file-import.spec.ts tests/e2e/data-manager-file-symbol.spec.ts --workers=1`.
Actual results/inventories belong to the cohort walkthrough. Structural mapping
does not establish SQX behavioral parity. Application-installation import remains
unsupported: appImport/appImportPopup.html, appImport/DataSourceFilesAppImportCtrl.js
and appImport/module.js are explicitly excluded. Backend import and donor runtime
semantics remain separate gaps. Canonical behavioral ledger/schema were absent;
no new behavioral record is asserted and this manifest does not replace the ledger.
