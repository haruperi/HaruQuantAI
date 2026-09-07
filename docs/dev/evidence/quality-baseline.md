# HaruQuantAI V3 — Reproducible Quality Baseline Report

**Task:** Preparation 0.06 — Establish a reproducible quality and performance baseline
**Date:** 2026-09-07
**Commit:** `4ba167564a4889fec0d5d52f2ce9072f536a2d05`

## 1. Environment & Toolchain

- **Operating System:** Windows 11
- **Python Version:** 3.14.3
- **Package Manager:** `uv` (frozen lockfile `uv.lock`)
- **Node.js / npm:** Registered in `app/ui/package.json`

## 2. Quality Gates Status

| Tool / Check | Baseline Run | Status | Notes |
| --- | --- | --- | --- |
| **Ruff Check** | `uv run --frozen ruff check .` | **PASS (0 errors)** | 36 initial findings resolved across data reference & orchestration |
| **Ruff Format** | `uv run --frozen ruff format --check .` | **PASS (0 formatting issues)** | 4-space indentation and formatting verified |
| **Architecture AST** | `uv run --frozen python scripts/architecture_check.py` | **PASS (0 violations)** | Cross-feature independence verified; browse reference decoupling complete |
| **Feature Docs** | `uv run --frozen python scripts/validate_feature_docs.py` | **PASS (39/39 match)** | All registered FeatureSpec declarations match READMEs 100% |
| **Mypy Strict** | `uv run --frozen mypy app tests` | **PASS (0 errors in 790 files)** | Strict typing verified across all source files |
| **Pytest Scoped** | `uv run --frozen pytest --no-cov tests/services/data/` | **PASS (281 passed in 6.05s)** | Data reference and store suites green |
| **UI Tests** | `npm run test` (Vitest) | **PASS (769 tests in 114 files)** | Workspaces, clients, stores green |
| **Contracts** | `python scripts/generate_contracts.py --check` | **PASS (0 problems)** | 33 contract artifacts up to date |

## 3. Triage of Baseline CI Findings

Initial CI job run `34051983427` failed with 36 Ruff lint findings and an AST violation (`browse_reference` importing `market_data_store`).
- **AST Architecture Violation Fixed:** Decoupled `MarketDataReferenceRepository` and `mt4_exporter.py` from `market_data_store` into `browse_reference`, perfectly separating `data.market-data-store@1` from `data.browse-reference@1`.
- **Ruff Lints Fixed:** Removed redundant imports, resolved exception logging, refactored cyclomatic route dispatchers, and adjusted query string escaping.
- **Feature Documentation Drift Fixed:** Added standard FeatureSpec sections to `deliver_notifications/README.md` and `manage_jobs/README.md`.

All prerequisite baseline hygiene is completely established.
