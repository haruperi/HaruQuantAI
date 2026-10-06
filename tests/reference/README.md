# P00 reference tooling

Owner: FEAT-HOST-EVIDENCE, app/host/README.md. This package is verification tooling,
not a host runtime or donor common-core replacement. Imports perform no I/O.

manifest.py owns explicit root resolution, safe bounded JSON, typed manifests and
read-only inventory reconciliation. fixtures.py owns independently constructed
cases with expected/actual observations and static/runtime provenance. validate.py
owns schema/lineage/registry gates and the offline/explicit-donor CLI.

All concrete classes/functions/private helpers map to their documented module FR;
registered decisions govern schema history, logging adapter, size/path bounds,
validator dependencies, ownership and the P00 release cohort. Log handlers are
configured explicitly by API consumers or CLI; success/error/gap/lifecycle events
carry fr_id and stable codes/counts without values, physical paths or exception text.

```powershell
uv run pytest tests/unit/test_reference_manifest.py tests/unit/test_reference_fixtures.py tests/unit/test_reference_validation.py --no-cov
uv run python -m tests.reference.validate
uv run python -m tests.reference.validate --check-donor
```

The donor command requires explicit SQX_REFERENCE_ROOT. No fallback scans the
machine. Temporary synthetic test archives are separate from donor files and stores.
The coverage.toml config qualifies reference-tool branches and preserves the root
.coverage file. >=80% tooling coverage is not application coverage or donor parity.

Fixtures contain independently authored input and recorded static observations
only. Runtime fixtures remain unavailable. Zero tolerance applies to counts,
fingerprints and discrete order; no financial formula or numerical default is
invented. See docs/dev/evidence/README.md for atomic claim allocation and freshness.
