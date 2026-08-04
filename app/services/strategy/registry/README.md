# Strategy Registry

This feature owns immutable strategy registration, parameter-version recording,
deterministic listing, exact reference resolution, and declarative configuration
validation. Mutations initialize Strategy storage through the private migration
support package; read-only operations never execute migrations. The feature retains
authorization, validation, hashing, immutable model construction, and public response
behavior while delegating all registry CRUD statements to the private
`app/services/strategy/persistence/` support package.

`adopt_approved_optimization_parameters` is the Strategy-owned receiver for
`OptimizationResult v1` projections. It requires authenticated owner approval,
checks the exact selected candidate and reproducibility hash without importing
Optimization, and then delegates to the existing immutable parameter-update path.

Its package-root exports and requirements are registered under `FEAT-STR-03` in
the domain README.
