# Current reference qualification tooling

Owner: `FEAT-HOST-EVIDENCE`, `app/host/README.md`. No host runtime, donor execution or database access is implied.

- `manifest.py`: explicit `SQX_145_REFERENCE_ROOT`, bounded JSON, strict typed current manifest/index/member models, exact source hashing and exhaustive current metadata reconciliation.
- `fixtures.py`: independent exact current static observations, source provenance and unavailable runtime fixtures.
- `validate.py`: schema v4, source/relationship/registry/proposal gates, allocation floor/high-water mark, ownership and CLI outcomes.
- Constructors/private helpers map to their module FRs and emit structured logs. API callers/CLI configure logging explicitly; no import-time I/O/handlers.
- Current source fingerprint drift, malformed input, escaped paths, missing members, unsupported cohort or runtime claims without authority fail closed. No source substitution is available.

```powershell
uv run pytest tests/unit/test_reference_manifest.py tests/unit/test_reference_fixtures.py tests/unit/test_reference_validation.py --no-cov
uv run python -m tests.reference.validate
uv run python -m tests.reference.validate --check-donor
uv run python scripts/ci_check.py
```

Explicit donor checks use only the configured current root; offline checks need no installation. Tests use synthetic temporary archives/stores. Dedicated branch-aware tooling coverage >=80% is not application coverage or numerical parity. Missing core/runtime evidence remains an application release blocker.
