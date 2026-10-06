# TickDownloader frontend ownership

Status: structurally aligned; verification recorded in cohort walkthrough.

FEAT-UI-TD-TRACEABILITY owns mapped TickDownloader UI.

- FR-UI-TD-source-mapping: exact donor-relative structure/casing and provenance.
- FR-UI-TD-workflow-preservation: retain existing metadata-only discovery, mock import, errors, selection, focus and persistence.
- FR-UI-TD-clean-room: independently authored target code; no donor backend implementation.

DEC-UI-TD-TRACEABILITY: map SQX_REFERENCE_ROOT/internal/plugins/DataSourceTD to HARUQUANTAI_ROOT/ui/app/plugins/data_source/TickDownloader. Shared Common/dataManagerStore.ts retains persistence/job lifecycle ownership; service attaches to existing capabilities. tickDownloader.ts is a preserved shared utility exception; README.md and source-map.json are target-only documentation.

The backend JAR is excluded. Real directory parsing, TickDownloader execution and SQX parity are unverified. Existing utility comment attributing nested tickdata discovery to SQX lacks ledger support and remains a research gap. Canonical evidence ledger/schema are absent; structural manifest does not replace them.
