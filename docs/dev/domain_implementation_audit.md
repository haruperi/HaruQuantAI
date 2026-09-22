# Plugin Implementation Audit

> **Purpose:** Companion verification procedure for the Plugin Implementation
> Pipeline. Despite the retained filename, the audit unit is a spatial plugin,
> not a legacy service domain.

An audit reports evidence; it does not repair code unless a separately approved
implementation plan authorizes remediation.

The owner-local topology is ratified in [ARCHITECTURE.md](../ARCHITECTURE.md).
Universal support modules under `app/plugins/` are not concrete audit units or
discovery candidates. This procedure applies to concrete plugins, including
workspaces and comparisons, and their declared operations. Exact source-stage
APIs must exist before implementation compliance can be assessed.

## 1. Audit declaration

Record before inspection:

```text
PLUGIN_ID: <stable namespaced id>
PLUGIN_KIND: <kind>
PRODUCTION_FILE: app/plugins/<kind>/<plugin_slug>.py
FAMILY_README: app/plugins/<kind>/README.md
FOCUSED_TEST: tests/plugins/<kind>/test_<plugin_slug>.py
USAGE_EXAMPLE: <ratified example path/function>
OPERATIONS: <declared operation IDs, effects, state and lifecycle needs>
PUBLIC_HOST_CONTRACTS: <approved app/host/owner.py paths plus contract symbols, or NONE>
BASELINE_COMMIT: <sha>
AUDIT_DATE_UTC: <timestamp>
```

If the architecture has not ratified one of these paths, stop and report the
authority gap rather than inventing it.

## 2. Rating scale

- **PASS:** source-bound evidence proves the complete control.
- **PARTIAL:** some required behavior exists but one or more acceptance elements
  are absent, contradictory, or unverified.
- **FAIL:** the control is violated, missing, or contradicted by runtime/source
  evidence.
- **N/A:** structurally impossible for this plugin; rationale and evidence are
  mandatory.

## 3. Audit sequence

### A. Ownership and locality

1. Map the stable ID to exactly one production file.
2. Inventory every plugin-specific definition across the repository.
3. Fail `PIP-02` if parameters, bounds, outputs, optimizer space, UI metadata,
   lowering rules, or behavior are maintained in another production file.
4. Confirm package README text does not override or duplicate executable schema.
5. Confirm no plugin-specific definitions were moved into `spec.py`, `schema.py`,
   `algebra.py`, `lowering.py`, or `wire.py`. Each host owner's public contracts,
   private implementation, and lifecycle share one `app/host/<owner>.py` file.
   They do not move to an `app/api/` package or the kernel.

### B. Import and orthogonality

1. Parse imports and accessed symbols. Reject host implementation/catalog objects,
   provider construction/lifecycle entry points, UI, concrete sibling plugins, and
   kernel runtime/context/bootstrapper. Permit shared plugin vocabulary, the kernel
   capability type, and designated contract symbols from approved host owner files.
   Check aliases and module-qualified access, not only module paths: definitions
   of public contracts and private provider classes intentionally share a module.
2. Import the module in isolation and prove no I/O, registration, task/thread,
   logging configuration, environment read, or global mutation occurs. Exercise
   the zero-argument `plugin()` factory separately and verify the same purity.
3. Discover the plugin without editing a central source list. Check configured
   concrete-family roots, pre-import exclusions, canonical ordering, bounds, and
   atomic publication. Workspaces must be discovered, not centrally imported.
4. Compare catalog and execution fingerprints before/after add, disable, and
   removal. Whole-catalog fingerprints change with membership; unrelated entry
   and dependency fingerprints, relative execution order, and results must remain
   unchanged. Do not use Python's built-in hash as a persistent fingerprint.
5. Add an independent indicator and comparison in supported families without
   modifying shared schema, algebra, executor, or UI source. Removing one
   workspace must not remove children/services used by another workspace.
6. Reject duplicate IDs across kinds and invalid snapshots. Failed refresh retains
   the last valid snapshot; initial failure exposes unavailable readiness and
   diagnostics. Verify that installation does not enable or start effects.
7. Import a host contract with its optional provider library unavailable. Verify
   that the whole owner module, including annotations/bases/decorators/defaults,
   transitive imports and package initializers, defines but does not instantiate
   or start providers, acquire resources, or perform other import-time effects.
   Optional library imports belong inside the explicit construction/start path.
8. Verify public contract symbols are identified in their owner file and that
   consumers cannot bypass typed binding through provider classes or entry points.
   The host composition root alone may use the construction/lifecycle entry point;
   cross-owner contract imports remain acyclic.

### C. Identity and compatibility

1. Validate lowercase dot-separated IDs and global snapshot uniqueness; initially
   one implementation version per ID. Check implementation version, metamodel
   compatibility, capability majors, graph/wire and artifact versions independently.
2. Verify breaking changes do not masquerade as compatible versions.
3. Verify unsupported newer versions fail closed and older supported versions
   migrate deterministically.
4. Verify exact code/data identities are pinned for admitted runs. Removal or
   refresh never silently binds an existing run to a replacement version; missing
   retained dependencies produce an attributed failure. Migrations retain originals.

### D. Schema and algebra

1. Inspect every parameter for type, default, constraints, unit, optimization
   policy, and presentation hint.
2. Exercise invalid values and cross-field constraints.
3. Validate immutable typed ports, units/alignment, named edges, stable node IDs,
   exact plugin references, graph schema version, domain compatibility, cycles,
   resource bounds, and legal algebra placement. No central comparison enum.
4. Serialize/deserialize canonical nodes and compare losslessly.
5. Load an unknown/removed node and prove the document remains readable and
   lossless while execution is explicitly unavailable.
6. Reject unsupported mutable leaves and verify nested descriptor/document values
   cannot change through input aliases. A copied dict or frozen outer dataclass
   is not enough. Retain unsupported whole-document versions read-only.
7. Distinguish validity limits from optimizer search bounds. Validate bounded
   typed values without silent coercion; check canonical JSON round trips and
   explicit missing-value encodings rather than JSON NaN/Infinity.

### E. Behavioral semantics

1. Recompute hand-golden examples independently.
2. Test empty, minimal, warm-up, missing, non-finite, extreme, and malformed data.
3. Verify units, timezone, ordering, precision, rounding, and numerical policy.
4. Repeat identical runs and compare outputs/artifact hashes.
5. Compare scalar and accelerated implementations when both exist.
6. Vary bound parameters and verify lookback/warm-up comes from the plugin's
   validated policy. Test seeding, flat/monotonic series, gap recovery, and invalid
   periods against explicit goldens rather than assuming a named formula is correct.
7. Exercise independent concurrent runs and ensure accumulator state and input
   buffers are not shared mutably. Externally acquired data must be frozen before
   asserting repeatability; live effects are not inherently deterministic.

### F. Capabilities, effects, and security

1. List every required and optional capability and its consuming operation.
2. Prove undeclared capability lookup and ambient registry enumeration are absent.
3. Prove optional absence gates only the relevant operation.
4. For effectful plugins, verify lifecycle ownership, bounds, cancellation,
   cleanup, timeouts, retry/rate policy, authorization, and redaction.
5. Search source, fixtures, logs, and artifacts for credentials or private data.
6. Verify factory purity, operation effects, run-local state, and lifecycle needs
   separately. Workspaces have no automatic service lifecycle and receive scoped
   bindings rather than kernel contexts or live catalog/service locators.
7. Where an operation uses host resources, trace integration evidence for failed
   and cancelled startup, full rollback, admission stop, drain/cancellation,
   awaited async cleanup, and consumer-before-provider withdrawal. Check that
   bindings remain valid for cleanup and are unavailable after scope closure.
8. Verify cleanup failures are attributed/aggregated and unrelated safe cleanup
   continues. A still-live consumer blocks claims of safe withdrawal. Check
   shutdown idempotence and observer failure isolation. Do not count reverse-list
   iteration alone as proof of those lifecycle guarantees.

### G. Consumer parity and UI reflection

1. Enumerate every claimed consumer: UI, builder/generator, simulator, optimizer,
   persistence, exporter, or agentic tool.
2. Trace all consumers to the same catalog descriptor and algebra node.
3. Prove the UI creates controls from schema rather than plugin-specific source.
4. Prove optimizer bounds and exporter lowering match execution semantics.
5. Fail claims for consumers without runnable end-to-end evidence.
6. Every advertised target must have actual node-owned lowering and compatible
   generic target emission. Compare supported numerical/state/missing-data
   semantics; a nonempty output string or presence of a lowering callback is not
   sufficient. Unsupported nodes/targets return attributed failures.
7. Verify shared JSON projections and owner-defined transport/resource envelopes
   drive generated or conformance-checked clients. A route reference does not
   install novel UI behavior; extensions/renderers need separate review.

### H. Tests, evidence, and qualification

1. Map every `PIP-*` control to a test, static check, usage scenario, or explicit
   evidence artifact.
2. Run the focused test without coverage.
3. Run the deterministic usage example.
4. Run architecture, lint, format, strict typing, complete tests, and coverage.
5. Verify evidence source hashes and the clean/expected Git status.

## 4. Required findings table

| Control | Rating | Evidence | Finding / required remediation |
|---|---|---|---|
| PIP-01 OWNER |  |  |  |
| PIP-02 LOCAL |  |  |  |
| PIP-03 IMPORT |  |  |  |
| PIP-04 ID |  |  |  |
| PIP-05 SCHEMA |  |  |  |
| PIP-06 PORTS |  |  |  |
| PIP-07 SEMANTICS |  |  |  |
| PIP-08 CAP |  |  |  |
| PIP-09 DISCOVERY |  |  |  |
| PIP-10 ENABLE |  |  |  |
| PIP-11 ORTHO |  |  |  |
| PIP-12 ALGEBRA |  |  |  |
| PIP-13 UI |  |  |  |
| PIP-14 EFFECT |  |  |  |
| PIP-15 TEST |  |  |  |
| PIP-16 REMOVE |  |  |  |
| PIP-17 PARITY |  |  |  |
| PIP-18 EXAMPLE |  |  |  |
| PIP-19 EVIDENCE |  |  |  |
| PIP-20 QUALIFY |  |  |  |

## 5. Audit outcome

The audit ends with:

- counts of PASS/PARTIAL/FAIL/N/A;
- a statement of whether the plugin may truthfully be called complete;
- prioritized remediation with exact files and controls;
- commands and exit codes actually observed;
- unresolved authority conflicts or missing evidence;
- confirmation that no mutation occurred during an audit-only task.

Any remediation begins with a new or appended implementation plan and owner
approval. An audit finding is not implicit permission to edit.
