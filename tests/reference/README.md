# Stage 0 (`P00`) Reference Qualification Tooling (`tests/reference`)

Owner: `FEAT-HOST-EVIDENCE`, [app/host/README.md](../../app/host/README.md).
Uses the central host telemetry facade; importing reference tooling does not
configure handlers or create log files. CLI entrypoints explicitly start and
shut down asynchronous logging. No donor executable or database is accessed.

- `manifest.py`: Resolves explicit `SQX_REFERENCE_ROOT` (or `SQX_145_REFERENCE_ROOT` alias) and `HARUQUANTAI_ROOT`, performs bounded UTF-8 JSON reads (`<= 4 MiB`), validates typed `Manifest` / `DonorArtifact` / `ResourceFile` models, and reconciles exact SHA-256 fingerprints and donor directory counts.
- `fixtures.py`: Validates independent static/runtime fixture definitions (`p00-fixtures.json`), provenance rules, and zero-tolerance exact observations.
- `validate.py`: Validates Draft 2020-12 `reimplementation.schema.json` (v4), monotonic `SQX145-EV-NNNNNN` allocation, source catalog and donor/repository SHA-256 bindings, reciprocal supersession/contradiction links, registry/proposal mappings, and CLI exit codes.

```powershell
uv run pytest tests/unit/test_reference_manifest.py tests/unit/test_reference_fixtures.py tests/unit/test_reference_validation.py --no-cov
uv run python -m tests.reference.validate
uv run python -m tests.reference.validate --check-donor
uv run python scripts/ci_check.py
```
