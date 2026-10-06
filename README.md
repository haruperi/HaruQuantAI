# HaruQuantAI

HaruQuantAI is a local-first quantitative research workstation at a backend-reset
baseline. The retained React UI includes fixtures and local simulations. Backend
runtime services and quantitative algorithms are absent; no application startup or
SQX parity is claimed.

[Project charter](docs/PROJECT.md), [architecture](docs/ARCHITECTURE.md) and
[contributor constitution](AGENTS.md) define authority. The
[host README](app/host/README.md) registers P00 reference tooling only.

## Development

Use Python >=3.14, uv, and Node.js/npm from the repository root.

```powershell
uv sync --locked
npm --prefix ui install
npm --prefix ui run dev
```

No `app.main` backend entrypoint is available. UI host connection and domain
clients remain provisional until separately approved backend contracts qualify.

## Reference qualification

```powershell
uv run python -m tests.reference.validate
uv run python scripts/ci_check.py
```

The first command checks offline evidence lineage, inventory/ownership proposals,
and fixtures. The second also qualifies typed Python tooling, reference tests and
branch coverage, plus UI typecheck/tests/build. Actual donor inventory comparison
requires an explicitly configured `SQX_REFERENCE_ROOT` and runs read-only:

```powershell
uv run python -m tests.reference.validate --check-donor
```

[Evidence procedure](docs/dev/evidence/README.md) preserves historical records and
separates static observations from donor runtime validation. SQLib/MainApp/
AppSettings implementations, actual installed product build/activation and runtime
output fixtures remain unavailable. P00 baseline delivery does not complete those
prerequisites or qualify later runtime phases. See the
[release matrix](docs/dev/evidence/p00-release-matrix.md).

No live database or donor user state is modified by P00. Future development follows
research, documented plan, owner approval, implementation, focused verification,
walkthrough and separate owner commit authorization.
