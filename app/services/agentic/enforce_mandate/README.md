# FEAT-AGT-ENFORCE_MANDATE

Provides `agentic.mandate@1` as a stateless, fail-closed, authority-narrowing boundary.

Validity is half-open: `effective_at <= now < expires_at`. Integrity is canonical SHA-256 over UTF-8/NFC-normalized semantic fields, excluding only `integrity_digest`; `signature_ref` is opaque provenance and is included in the digest. Scope uses exact membership and empty sets grant nothing. Effective budgets are the minima of the mandate and remaining parent ceilings.

Agentic can never gain broker credentials, executable order authority, Risk approval, kill-switch clearing, live deployment, receiver authority or receiver bypass from a mandate. This feature owns no durable state.

Run: `uv run python -m app.services.agentic.enforce_mandate._usage`.
