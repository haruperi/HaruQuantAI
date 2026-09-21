# Plugin Implementation Audit

> **Purpose:** Companion verification procedure for the Plugin Implementation
> Pipeline. Despite the retained filename, the audit unit is a spatial plugin,
> not a legacy service domain.

An audit reports evidence; it does not repair code unless a separately approved
implementation plan authorizes remediation.

## 1. Audit declaration

Record before inspection:

```text
PLUGIN_ID: <stable namespaced id>
PLUGIN_KIND: <kind>
PRODUCTION_FILE: app/plugins/<kind>/<plugin_slug>.py
FAMILY_README: app/plugins/<kind>/README.md
FOCUSED_TEST: tests/plugins/<kind>/test_<plugin_slug>.py
USAGE_EXAMPLE: <ratified example path/function>
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

### B. Import and orthogonality

1. Parse imports and reject host internals, UI, registry, sibling plugins, and
   private implementation modules.
2. Import the module in isolation and prove no I/O, registration, task/thread,
   logging configuration, environment read, or global mutation occurs.
3. Discover the plugin without editing a central source list.
4. Compare catalog and execution fingerprints before/after add, disable, and
   removal; unrelated entries and results must remain unchanged.

### C. Identity and compatibility

1. Validate ID grammar, uniqueness, implementation version, capability versions,
   schema versions, and artifact versions independently.
2. Verify breaking changes do not masquerade as compatible versions.
3. Verify unsupported newer versions fail closed and older supported versions
   migrate deterministically.

### D. Schema and algebra

1. Inspect every parameter for type, default, constraints, unit, optimization
   policy, and presentation hint.
2. Exercise invalid values and cross-field constraints.
3. Validate immutable typed ports and legal algebra placement.
4. Serialize/deserialize canonical nodes and compare losslessly.
5. Load an unknown/removed node and prove the document remains readable and
   lossless while execution is explicitly unavailable.

### E. Behavioral semantics

1. Recompute hand-golden examples independently.
2. Test empty, minimal, warm-up, missing, non-finite, extreme, and malformed data.
3. Verify units, timezone, ordering, precision, rounding, and numerical policy.
4. Repeat identical runs and compare outputs/artifact hashes.
5. Compare scalar and accelerated implementations when both exist.

### F. Capabilities, effects, and security

1. List every required and optional capability and its consuming operation.
2. Prove undeclared capability lookup and ambient registry enumeration are absent.
3. Prove optional absence gates only the relevant operation.
4. For effectful plugins, verify lifecycle ownership, bounds, cancellation,
   cleanup, timeouts, retry/rate policy, authorization, and redaction.
5. Search source, fixtures, logs, and artifacts for credentials or private data.

### G. Consumer parity and UI reflection

1. Enumerate every claimed consumer: UI, builder/generator, simulator, optimizer,
   persistence, exporter, or agentic tool.
2. Trace all consumers to the same catalog descriptor and algebra node.
3. Prove the UI creates controls from schema rather than plugin-specific source.
4. Prove optimizer bounds and exporter lowering match execution semantics.
5. Fail claims for consumers without runnable end-to-end evidence.

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
