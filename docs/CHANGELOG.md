# Changelog

## [Unreleased]

### Added

- `ADD-001` Shared contracts: Added immutable `AuthContext v1` and bounded redacted `AuditEvent v1` contracts.
- `ADD-002` Errors: Added typed shared errors, normalized metadata, safe exception mapping, and injected event routing.
- `ADD-003` Identity: Added validated prefixed UUID4 generation, validation, and deterministic stable identifiers.
- `ADD-004` Time: Added injected UTC clocks, strict timestamp parsing and formatting, age calculation, and freshness checks.
- `ADD-005` Serialization: Added bounded JSON-safe conversion and deterministic canonical JSON serialization.
- `ADD-006` Security: Added denylist-first redaction, password hashing, Fernet encryption, and active secret-version selection.
- `ADD-007` Settings: Added immutable Pydantic runtime settings, explicit environment loading, and secret-reference resolution.
- `ADD-008` Logging: Added source-aware structured logging, scoped console color, queued delivery, rotation, redaction, and specialized file routing.

### Status

- Utils foundation is implemented and verified: 74 domain tests pass on Python 3.14 with `ruff`, `ruff format --check`, and strict `mypy` clean; measured branch coverage is 84.77% (≥ 80% gate).
- The Utils-owned scope of `WF-UTL-001` (structured logging and redaction) is complete. `WF-UTL-002` (settings bootstrap) and `WF-UTL-003` (audit-event construction) remain `Partial`: the Brokers `BrokerConnectionConfig v1` injection and Data audit-persistence handoffs land with those domains.
- Shared `AuthContext v1` and `AuditEvent v1` are implemented and tested on the Utils producer side but remain `Partial` until their consumer/persistence domains (UI/API, Data) exist; the top-level contract registry in `docs/PROJECT.md` has been reconciled to `Partial` for these two contracts and `Completed` for the Utils-owned shared settings and policies.
