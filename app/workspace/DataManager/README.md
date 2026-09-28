# Data Manager backend

Status: resource/attachment boundary candidate; no acquisition provider backend.
The workspace owns workflow semantics, not host resource custody or plugin logic.
`workspace.py` declares the `data_source.presentation@1.0.0` slot and prepares
`resources.list`, `resources.read` and `capabilities` operations. With no providers,
retained authorized resources remain inspectable; acquisition stays unavailable.

Preparation requires `host.resources@1.0.0`; there are no peer imports or raw SQL.
The host validates packaging and literal metadata before loading `prepare` and
injects immutable child bindings. Shutdown drops local handles, never stored data.
The corresponding UI migration/removal qualification is pending. This README does
not claim full workspace qualification, market-data ingestion or live persistence
migration. See the current ownership-removal task walkthrough for actual evidence.
