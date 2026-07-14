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
