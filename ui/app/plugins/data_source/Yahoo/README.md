# Yahoo frontend ownership

Status: structurally aligned; qualification recorded in cohort walkthrough. No SQX parity claim.

FEAT-UI-YAHOO-TRACEABILITY owns mapped Yahoo add/download UI.

- FR-UI-YAHOO-source-mapping: exact structure, filenames/casing and provenance.
- FR-UI-YAHOO-workflow-preservation: existing offline catalogue, validation, mock add/download, focus and persistence.
- FR-UI-YAHOO-clean-room: no copied donor implementation or backend code.

DEC-UI-YAHOO-TRACEABILITY: map SQX_REFERENCE_ROOT/internal/plugins/DataSourceYahoo to HARUQUANTAI_ROOT/ui/app/plugins/data_source/Yahoo. Shared YahooModal presentation lives in mapped add/addPopup.tsx, consumed by mapped download view. Service adapts existing rules/store authority; controllers own state/actions. Preserve singular donor style.css.

Exceptions: yahoo.ts and yahooStore.ts retain sibling contracts; README.md owns registry/status; source-map.json records structure/provenance. Backend JAR excluded. Real Yahoo requests, market bars and donor runtime behavior remain unverified. Canonical ledger/schema absent; structural manifest is not behavioral evidence.
