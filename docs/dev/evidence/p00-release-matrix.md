# Stage 0 (`P00`) Reference Release Matrix

| Gate | Evidence / Expected Result | Qualification Status |
| --- | --- | --- |
| Core donor artifact hashes (`p00-inventory.json`) | Exact SHA-256 fingerprints for launcher configs, 8 encrypted `.jar.enc` libraries, `Snippets.jar`, and 8 `internal/ctemplate/*.xml` schemas | Passed static verification against `SQX_REFERENCE_ROOT` (`tolerance = 0`) |
| Donor directory & snippet counts | `8` encrypted core JARs, `182` JSPF plugin directories in `internal/plugins`, `1,049` Java snippet files in `internal/extend/Snippets/SQ` | Passed static verification (`p00-fixtures.json` & `--check-donor`) |
| Decompiled clean-room reference catalog | Exact SHA-256 fingerprints for `docs/SQX/README.md` and `docs/SQX/sqx-clean-room-reimplementation.md` | Passed repository source verification |
| Atomic evidence ledger (`reimplementation.json`) | Draft 2020-12 schema v4, monotonic `SQX145-EV-NNNNNN` IDs, resolved source catalog & record links, clean-room flags | Passed (`uv run python -m tests.reference.validate`) |
| Domain registry & proposal boundary (`app/host/README.md`) | `FEAT-HOST-EVIDENCE`, 7 `FR-HOST-EVIDENCE-*` requirements, and `DEC-HOST-P00-*` decisions registered; unimplemented `F01`–`F13` capabilities remain `proposed` | Passed ownership gate (`runtime_qualified = false`) |
| Reference tooling test coverage (`tests/reference/`) | Ruff lint/format, `mypy --strict`, and $\ge 80\%$ branch coverage across `manifest.py`, `fixtures.py`, and `validate.py` | Passed (`uv run python scripts/ci_check.py`) |
| Application runtime & numerical parity (`Stages 1–7`) | Connected backend services, simulation engine, indicators, and independent normal/boundary/failure donor comparisons | Unqualified in Stage 0; gated by Stage 1–7 implementation plans |

Use `uv run python -m tests.reference.validate` for offline repository qualification and `uv run python -m tests.reference.validate --check-donor` (with `SQX_REFERENCE_ROOT` configured) for read-only donor reconciliation.
