# SQData frontend ownership

Status: structurally aligned; qualification recorded in the cohort walkthrough. No SQX behavioral parity claim.

## Equity

FEAT-UI-SQEQUITY-TRACEABILITY owns the Equity mapped UI and existing mock capabilities.

- FR-UI-SQEQUITY-source-mapping: exact scoped filenames, casing and provenance.
- FR-UI-SQEQUITY-workflow-preservation: existing frontend workflows and host simulation callbacks.
- FR-UI-SQEQUITY-clean-room: independent target code, no donor implementation copying.

DEC-UI-SQEQUITY-TRACEABILITY: map DataSourceSQEquityData to SQData/Equity; retain shared rules/store at the parent. Shared view/hook/conditions/styles are owned by mapped Equity files and composed by distinct Futures counterparts. Empty update template and backend binary are excluded.

## Futures

FEAT-UI-SQFUTURES-TRACEABILITY owns the Futures mapped UI and existing mock capabilities.

- FR-UI-SQFUTURES-source-mapping: exact scoped filenames, casing and provenance.
- FR-UI-SQFUTURES-workflow-preservation: existing frontend workflows and host simulation callbacks.
- FR-UI-SQFUTURES-clean-room: independent target code, no donor implementation copying.

DEC-UI-SQFUTURES-TRACEABILITY: map DataSourceSQFuturesData to SQData/Futures; retain shared rules/store at the parent. Shared view/hook/conditions/styles are owned by mapped Equity files and composed by distinct Futures counterparts. Empty update template and backend binary are excluded.

Shared exceptions: sqData.ts and sqDataStore.ts retain existing sibling contracts; README.md owns registry/status; source-map.json delegates provider manifests. Provider manifests are declared target-only files. No backend/subscription/network capability added. Donor runtime defaults, remote services and algorithmic parity remain unverified. Canonical behavioral ledger/schema are absent; structural manifests do not replace them.


## Backend historical ingestion

The Data Manager source-menu entry points now use the shared
`Common/HistoricalSourceDialog.tsx` and `Common/historicalSourceStore.ts`.
Registration and downloads use SQLite-backed datasets and real broker requests;
progress and controls come from backend jobs. Earlier offline/mock modules remain
for their isolated fixtures, but the live source-menu paths no longer run them.
See `docs/data-manager/historical-sources.md` for supported native resolutions,
canonical storage, source limitations, CLI usage and MT5 connection requirements.
