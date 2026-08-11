# Dataset Lifecycle — FEAT-DATA-02

Owns verified CSV and Parquet loading from approved local roots.

- Production files: `contracts.py`, `csv_loader.py`, `manifest.py`,
  `parquet_loader.py`.
- Requirement: FR-DATA-017.
- Usage evidence: `tests/data/usage/03_local_datasets.py`.
- Side effects: bounded approved-root reads only.
