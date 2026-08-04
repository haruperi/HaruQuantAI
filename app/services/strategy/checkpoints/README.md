# Strategy Checkpoints

This feature owns bounded, redacted Strategy-local checkpoint contracts,
creation, persistence, and validation. Creation may initialize Strategy storage;
validation is read-only and fails closed when storage is unavailable. Checkpoint
validation, redaction, bounds, hashing, compatibility, and public responses remain in
this feature; checkpoint insert and lookup statements are delegated to the private
`app/services/strategy/persistence/` support package.

Its package-root exports and requirements are registered under `FEAT-STR-06` in
the domain README.
