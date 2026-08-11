# Canonical Data Contracts — Support Package

Owns immutable canonical records, datasets, quality vocabulary, validation, and
deterministic Data errors. Public names are imported from `app.services.data`.
`DataQualityReport` pairs `contract_version="v2"` with the immutable
`schema_id="data.quality_report.v2"` identity.

- Production files: `_base.py`, `dataset.py`, `errors.py`, `records.py`,
  `validation.py`.
- Requirements: FR-DATA-001–005 and FR-DATA-012–013.
- Usage evidence: `tests/data/usage/01_contracts.py`.
- Side effects: none.
