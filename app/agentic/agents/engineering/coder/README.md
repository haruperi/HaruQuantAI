# Coder

> **Package:** `app/agentic/agents/engineering/coder`
> **Feature:** `FEAT-AGT-16` Governed Code Generation and Sandbox
> **Status:** `Completed`
> **Last updated:** `2026-07-29`

> This README documents one registered leaf agent package. It is **subordinate
> to the canonical Agentic Feature Registry** in `app/agentic/README.md`, which
> remains the sole authority for feature IDs, statuses, public APIs, contracts,
> and requirements. This file contains no Feature Registry section and defines
> no requirement of its own.

---

## 1. Purpose and Boundary

### Purpose

Turn an authenticated human specification into staged source code — a strategy
evaluator or a candidate indicator — with a complete manifest, and write it
where a human can review it.

### Owns

- The provider-neutral Coder agent definition.
- The immutable base role instruction in `prompt.md`.
- `CodeSpecification`, `CodeArtifact`, `SandboxResult`, `SandboxLease`.
- The staging writer and its path containment rules.
- The sandbox port and its deterministic double.

### Does not own

- Isolation. The bound sandbox runtime provides it; this package checks the
  attestation and refuses without it. See §4.
- Any registration. Indicators are a closed registry and Strategy owns
  `register_strategy_version`; both are source changes a human makes.
- Promotion. `FEAT-AGT-18` decides what advances.
- Execution of anything it writes. Nothing here imports, executes, compiles,
  or loads a generated file, and a test asserts the package never names the
  functions that would.

### Shared contracts

**Owned by this feature** — defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `CodeSpecification` | `v1` | Agentic, UI/API | Authenticated human authorisation to author |
| Completed | `CodeArtifact` | `v1` | Agentic, UI/API | Staged artefact with complete manifest and provenance |
| Completed | `SandboxResult` | `v1` | Agentic | Evidence of exercising staged code |
| Completed | `SandboxLease` | `v1` | Agentic | Attested isolation properties of one environment |

**Consumed from other domains** — referenced only, never redefined:

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `AgentTask` / `AgentResult` / `AgentProvenance` / `BudgetUsage` | `v1` | Agentic `FEAT-AGT-01` | Typed task input and result envelope |
| `RoleManifest` / `FirmMandate` | `v1` | Agentic `FEAT-AGT-02` | Role resolution and prompt-integrity verification |
| `ModelProfile` / `ModelInvocation` / `AdkRuntime` | `v1` | Agentic `FEAT-AGT-03` | Governed provider-neutral execution |
| `AgentPolicy` / `ToolPolicy` / `call_governed_tool` | `v1` | Agentic `FEAT-AGT-05` | Deny-by-default tool authorization |
| `utils.auth_context.v1` | `v1` | Utils | Human authentication of the specification |
| `IndicatorSpec` registry listing | `v1` | Indicators | Deterministic gap detection |
| `SignalEvaluator` / `StrategyManifest` | `v1` | Strategy | The contract a strategy artefact targets |

---

## 2. Package Structure

```text
coder/
├── __init__.py         # Feature Registry public API only
├── agent.py            # Provider-neutral definition and public use case
├── prompt.md           # Immutable base role instruction
├── schemas.py          # Feature-owned typed specification and artefact
├── sandbox.py          # Sandbox port, lease attestation, deterministic double
├── artifact_store.py   # Content-addressed staging writer and path guards
├── tools.py            # Governed Indicators-registry binding
└── README.md           # This file
```

**`tools.py` is an addition to the canonical §4.16 file list.** Whether an
indicator exists is a fact the Indicators registry owns. Reading it through a
direct import would bypass the permission enforcement point that every other
receiver call in this domain traverses, so the lookup goes through
`call_governed_tool` like the rest.

### Public API

| Export | Kind | Purpose |
|---|---|---|
| `author_code_artifact` | function | Author one staged artefact |
| `CodeSpecification` / `CodeArtifact` / `SandboxResult` | classes | Typed contracts |
| `build_code_specification` / `build_code_artifact` / `build_sandbox_result` | functions | Validated constructors |

---

## 3. Prompt Integrity

`prompt.md` is data, never code. `agent.py` loads it, normalizes line endings,
hashes it, and compares the digest against the enabled `RoleManifest` before
constructing anything. A mutated, missing, or empty prompt fails closed before
any model call. The shared implementation is
`app.agentic.governance.registry.verify_prompt_artifact`.

---

## 4. What the sandbox does and does not prove

**The model call and the sandbox are different processes.** The LLM authors in
the Agentic process, where the provider credential and the governed model
profile live. What enters the sandbox is *text*. The sandbox is where that text
would be written and exercised — which is the thing with no legitimate reason
to reach a network.

`SandboxLease` makes each `FR-AGENTIC-046` property its own field, so a lease
attesting to less than all of them is a distinct value rather than a flag that
could be overlooked. `author_code_artifact` refuses `SANDBOX_NOT_ATTESTED`
before any model call when any property is missing.

**Known limit, stated plainly.** Agentic declares the port and checks the
lease. It does not implement isolation. The tests here prove that an
under-attested lease is refused; they do **not** prove that a bound runtime is
actually ephemeral, credential-free, or network-denied — no in-process double
could. Binding a runtime that genuinely provides those properties is the
composition root's obligation, and until one is bound, generated code executed
elsewhere in this process would have that process's full privileges, including
no direct credential or bootstrap-setting access.

`build_bound_sandbox` is the seam for that runtime. Adding one is a binding
change, not a redesign.

---

## 5. Behaviour

### Authentication comes from a human, not a model

`author_code_artifact` refuses `SPECIFICATION_NOT_AUTHENTICATED` when the
principal is not a `USER`, does not match the specification, lacks
`agentic:author_code`, or names a different environment than the specification
or the agent policy. A model-authored specification cannot self-authenticate.

### The registry decides which indicators exist

`indicators.list_indicators` is called through the governed tool path; the
registered identifiers come from the receiver. The model is never asked, and
never believed, about whether an indicator exists.

- **Indicator candidates not authorised** → `INDICATOR_NOT_REGISTERED`,
  naming the missing identifiers, refused before any model call.
- **Authorised** → generation proceeds, the gap is recorded on the artefact,
  and `promotion_status` becomes `blocked_on_indicator_merge`.

`CodeArtifact` rejects `promotion_status = "ready"` while any required
indicator is unregistered, so a strategy can never present itself as promotable
on top of a primitive no human has merged. It also rejects `ready` when the
sandbox run was not clean.

### Staging containment is the guarantee that does not depend on a runtime

Every declared path is validated on the **raw text** before parsing —
`PurePosixPath` silently drops a `.` component, so parsing first would accept
`a/./b.py`, and normalizing an attacker's path is how containment fails. Then
the path is resolved against the artefact root and re-checked, including every
parent, so a symlink cannot carry a write outside the tree.

Rejected: absolute paths, drive letters, UNC paths, `~`, `..` and `.`
components, empty components, backslashes, NTFS alternate data streams
(`f.py:evil`), Windows reserved device names (`CON`, `NUL`, `COM1`–`9`,
`LPT1`–`9`, with or without extension), trailing dots and spaces, paths deeper
than eight components, and any suffix outside `.py`, `.md`, `.toml`, `.txt`,
`.json`.

Artefact identities become directory names and are held to a stricter rule:
letters, digits, dashes, and underscores only.

### Refusal is a complete outcome

| Reason | Condition | Before the model? |
|---|---|---|
| `SPECIFICATION_NOT_AUTHENTICATED` | Principal, permission, or environment mismatch | Yes |
| `ARTIFACT_KIND_NOT_AUTHORISED` | The specification does not authorise this kind | Yes |
| `SANDBOX_NOT_ATTESTED` | The lease omits an isolation property | Yes |
| `REGISTRY_TOOL_DENIED` | The registry tool is unregistered or denied | Yes |
| `INDICATOR_NOT_REGISTERED` | A required indicator is missing and candidates are unauthorised | Yes |
| `NO_FILES_GENERATED` | The model returned no files | No |
| `STAGING_PATH_REJECTED` | A declared path failed containment | No |
| *model reasons* | The coder itself declined | — |

---

## 6. Tests and Evidence

| Level | Location |
|---|---|
| Unit | `tests/agentic/unit/test_coder.py` |
| Usage | `tests/agentic/usage/16_coding.py` |
| Integration | `tests/agentic/integration/test_code_artifact.py` |

```bash
uv run pytest tests/agentic/unit/test_coder.py -o addopts="" -q
```

```bash
uv run python tests/agentic/usage/16_coding.py
```

Every test writes only under a `tmp_path`; the usage program creates and
removes its own temporary staging root. Nothing is written inside the
repository.

### Known limits

- The sandbox double is not isolation. See §4.
- `forbidden_source_markers` is a **review signal**, not a control. Staged code
  is never imported here, so a marker in generated content is something a human
  should look at, not something the system defends against.
- Generated code is not checked against the real `SignalEvaluator` protocol or
  the real `IndicatorSpec` — doing so would require importing it, which this
  feature must not do. Conformance is `FEAT-AGT-17`'s evaluation problem.
- Neither `StrategyManifest` nor `IndicatorSpec` is constructed here. The
  artefact carries the digests those manifests need; assembling them belongs to
  promotion.
- `WF-AGT-005` remains `Missing`: `open_sandbox` and `stage_code_artifact` are
  public-root exports assigned to `FEAT-AGT-22`.

---

## 7. Change Process

1. Update the canonical Agentic README first — it owns the registry row.
2. Update this file.
3. Change `prompt.md` and the manifest `base_prompt_hash` together; they are
   verified against each other at startup.
4. Never loosen a path guard without a test that shows what the loosening
   admits.
5. Update `schemas.py`, `sandbox.py`, `artifact_store.py`, `tools.py`, tests,
   and the usage program.
6. Change status only after every gate passes.
