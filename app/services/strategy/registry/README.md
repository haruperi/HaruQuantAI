# Strategy Registry

This feature owns immutable strategy registration, parameter-version recording,
deterministic listing, exact reference resolution, and declarative configuration
validation. Mutations initialize Strategy storage through the private migration
support package; read-only operations never execute migrations.

Its package-root exports and requirements are registered under `FEAT-STR-03` in
the domain README.
