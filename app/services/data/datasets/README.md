# Dataset Lifecycle — FEAT-DATA-02

Owns verified dataset loading, manifests, catalog evidence, and immutable
effective-dated provider-specification revisions.

- Production files: `contracts.py`, `catalog.py`, `csv_loader.py`, `manifest.py`,
  `parquet_loader.py`, and feature-owned immutable definitions in `migrations/`.
- Provider history API: `register_provider_specification_revision`,
  `get_provider_specification_revision`, and
  `get_provider_specification_revisions` through `app.services.data`.
- Requirements: existing dataset/catalog requirements plus `FR-DATA-214`–`216`.
- Usage evidence: `tests/data/usage/features/02_datasets.py`.
- Persistence: migration `010_provider_specification_revisions`; half-open UTC
  intervals, atomic supersession, immutable checksummed payloads, and explicit
  complete-coverage proof. Gaps and unproved backdating fail closed.
- Boundary: accepts canonical JSON-safe Brokers snapshot mappings without
  importing Brokers types or granting trading authority.
