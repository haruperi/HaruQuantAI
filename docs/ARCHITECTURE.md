# HaruQuantAI Architecture

> **Status:** Normative reset boundary plus ratified Spatial Composability laws.
> Concrete replacement-backend APIs remain subject to a separate approved plan.

## 1. Current topology

```text
app/
|-- __init__.py
|-- kernel/
`-- ui/
```

The absent `contracts/`, `services/`, `registry.py`, and `main.py` paths are
deliberate. They must not be recreated as a shortcut around the new architecture.

## 2. Boundary rules

### Kernel

- Standard library only.
- Business-neutral typed identity, composition, and lifecycle primitives only.
- No plugin definitions, schemas, registry contents, storage, HTTP, UI, broker,
  indicator, strategy, or simulator knowledge.
- No imports from future host/plugin/UI packages.
- The retained event and logging implementations require explicit review before
  being accepted into the final kernel surface.

### UI

- Owns presentation, interaction, accessibility, local view state, and drafts.
- Reads immutable catalog and resource representations through a typed gateway.
- Does not calculate backend metrics, simulate execution, authorize actions,
  persist domain truth, or duplicate plugin parameter schemas.
- Dynamic rendering is limited to an explicit vocabulary of safe generic
  controls and visualizations. Novel UI behavior requires a separately reviewed
  renderer or UI extension.

### Future host

The host will own process lifecycle, discovery, enablement, catalog publication,
execution coordination, persistence, jobs/workers, gateway transport, telemetry,
and external adapters. Host infrastructure is not a quantitative plugin.

### Future plugins

- One concrete quantitative concept per Python file.
- Import only standard library, approved third-party numerical foundations, and
  the universal plugin API.
- Export one side-effect-free factory or immutable contribution object.
- Never import the registry, host implementation, UI, or sibling plugins.
- Never self-register at import time.
- Declare typed inputs/outputs, parameters, bounds, compatibility, deterministic
  semantics, and generic UI hints in the same file as behavior.

## 3. Two composition graphs

The architecture keeps two graphs distinct:

1. **Host capability graph:** long-lived infrastructure services connected by
   `Capability[T]` tokens and owned lifecycles.
2. **Quantitative algebra graph:** immutable strategy/workflow nodes connected by
   typed ports and resolved against a frozen plugin catalog.

A concrete RSI node is not a host capability. The indicator plugin contributes
an algebra node kind to the catalog; an execution engine is a host capability.

## 4. Discovery and enablement

Discovery finds candidate plugin files without editing a central list. Discovery
must be deterministic, bounded to configured roots, and free of import-time
effects. Catalog construction validates all candidates atomically.

Availability and enablement are separate states:

- **available:** installed and compatible enough to describe;
- **enabled:** explicitly permitted for a workspace/profile;
- **unavailable:** missing or incompatible, with a structured reason.

New plugins are disabled by default unless an approved profile says otherwise.
Duplicate stable IDs or incompatible schemas fail catalog publication.

## 5. Schema and algebra

The universal metamodel defines only shared concepts: plugin identity, kind,
compatibility, parameter schema, typed ports, contribution metadata, and callable
protocols. Plugin-specific fields and enums remain in the plugin file.

Algebra documents store stable node IDs, plugin ID/version references, typed
connections, and canonical parameters. Unknown nodes are preserved losslessly
and rendered unavailable; they are never silently discarded or reinterpreted.

All wire and artifact representations use explicit versioned JSON. Runtime
validation is mandatory at trust boundaries.

## 6. Orthogonality constraints

- No central source file is edited to install a plugin.
- No plugin imports another plugin's implementation.
- No plugin mutates process globals, registries, search paths, or UI state.
- Subscriber/observer failure cannot fail an unrelated publisher.
- Catalog order and fingerprints are canonical, not filesystem-enumeration order.
- Removing a plugin invalidates only explicitly referencing documents/operations.
- Every task, resource, subscription, and external connection has one lifecycle
  owner and deterministic cleanup.

## 7. Persistence and reproducibility

Plugins do not own ad-hoc database access. A host persistence capability owns
schemas, migrations, transactions, concurrency, integrity, and retention.

Every reproducible result records at least:

- input artifact/data identities and hashes;
- algebra document identity and schema version;
- plugin IDs, versions, and catalog fingerprint;
- engine/exporter version;
- normalized settings, units, timezone, seed, and numerical policy;
- run identity, timestamps, status, and lineage.

## 8. Enforcement

Architecture is enforced by static checks, schema validation, focused plugin
tests, orthogonality/removal tests, integration tests across generic consumers,
and source-bound acceptance evidence. Documentation alone cannot establish
completion.
