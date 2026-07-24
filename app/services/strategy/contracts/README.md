# Strategy Contracts

This feature owns Strategy's immutable enums, policies, manifests, references,
commands, evaluation contracts, signal evidence, and structured outcomes. It
performs validation only and has no persistence or external side effects.

Its package-root exports and requirements are registered under `FEAT-STR-01` in
the domain README. Consumers import them only from `app.services.strategy`.
