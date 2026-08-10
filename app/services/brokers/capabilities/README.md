# Adapter Capability Matrix

`FEAT-BRK-01` owns the single immutable declaration of adapter and route
capabilities. The matrix records every canonical read and write operation plus
order, time-in-force, bracket/OCO, position-mode, partial-fill, modification,
cancellation, and sandbox traits. Missing evidence remains fail-closed.

Capability metadata is version-controlled application data. It is not mutable
database state and this feature owns no table.

Adapter construction and provider connection composition belong to
`adapter_runtime/`. Provider-symbol mapping administration belongs to
`instrument_profiles/`.
