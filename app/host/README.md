# Host Owners

`app/host/` contains the host capability owners of the HaruQuantAI
modular monolith. Every owner is exactly one Python file that carries its
public protocol, capability token, immutable public values, private
implementation, and composition-only lifecycle constructor. Host owners
collaborate exclusively through the kernel `Capability` primitive and
immutable documents — never through registries, globals, private imports,
or filesystem conventions.

Authorities: [`AGENTS.md`](../../AGENTS.md) (workflow and laws),
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) (normative paths and
import matrix), and the stage handoff
[`docs/dev/backend_implementation_handoff_s2_s5.md`](../../docs/dev/backend_implementation_handoff_s2_s5.md)
(behavioral contracts). This README orients; those documents decide.

## Owners

| File | Capability | Owns | Key invariant |
|---|---|---|---|
| `telemetry.py` | `host.telemetry@1` | Bounded telemetry events and diagnostics delivery | Emission never raises into the caller; delivery failures are isolated and reported |
| `catalog.py` | `host.catalog@1` | Bounded plugin discovery, atomic snapshots, selection, exact admission | Whole-registry-then-swap publication; last-good snapshot retained on failed refresh; admission pins exact ref, implementation, and fingerprints |
| `execution.py` | `host.execution@1` | In-process graph execution, batch trials, semantic export | Generic dispatch only — no plugin-specific branches; caller cancellation honored at node/trial boundaries; full reproducibility record |
| `gateway.py` | `host.gateway@1` | Versioned `/api/v1` loopback JSON transport | Optional server libraries imported only inside construction/start; blocking executions offloaded so request timeouts always fire; host-owned authorization |
| `storage.py` | `host.storage@1` | SQLite record persistence, CAS transactions, migrations | Every operation — synchronous or async — serializes on one owned single-writer thread; fail-closed on corrupt or newer-than-supported schemas |
| `artifacts.py` | `host.artifacts@1` | Content-addressed artifact storage and retention | Content published atomically before metadata; two-phase retention with active-reference protection; reads verify digest and size |
| `workers.py` | `host.workers@1` | Process-per-job subprocess supervisor | No shell, sanitized environment, bounded incremental pipe reads, full cancellation escalation (stdin close → grace → terminate → kill) with transport reaping |
| `jobs.py` | `host.jobs@1` | Durable job state machine, scheduling, recovery | Every transition CAS-persisted with an append-only event record; recovery rebinds nothing — exact pinned entry fingerprints or a named failure |
| `bootstrap.py` | — | The composition root | The only composition and `--worker` entry point; there is no `app/main.py` |

Each owner's private `_*_feature(...)` constructor is imported only by
`bootstrap.py` (enforced by ARCH-011), and `__init__.py` files are
docstring-only (ARCH-001).

## Dependency order

Owners depend on each other only through required capabilities, in this
shape:

```text
storage
  └── artifacts
catalog ─┐
execution├── jobs
storage ─┤
artifacts├── jobs
workers ─┘
catalog + execution ── gateway (via required capabilities)
```

`workers.py` has no dependency on jobs or storage; jobs owns all
scheduling and durable state transitions; storage owns SQLite; artifacts
owns artifact-tree mutation; workers owns subprocess creation.

## Composition and lifecycle

`create_runtime()` in `bootstrap.py` composes features in a fixed order —
telemetry first, then optional storage and artifacts, then catalog and
execution (always), then optional workers, jobs, and gateway — and the
kernel closes them in reverse (LIFO). Shutdown therefore stops gateway
admission and drains it before catalog/execution withdraw, and closes
jobs before the storage/artifacts/workers providers it uses during
cleanup.

`bootstrap.py` also implements the worker child mode
(`python -m app.host.bootstrap --worker`): it reads one bounded versioned
JSON request from stdin, verifies the pinned catalog, entry, and
dependency fingerprints before executing (failing closed with stable
codes instead of substituting code), and writes one bounded JSON response
to stdout. Stderr is diagnostics only.

## Enforced boundaries

`scripts/architecture_check.py` enforces, among others:

- ARCH-011 — private host lifecycle symbols are composition-only.
- ARCH-012 — the host file set is exactly the owners above.
- ARCH-015 — gateway imports starlette/uvicorn only inside functions.
- ARCH-017 — `sqlite3` is imported only by `storage.py`; `subprocess`
  only by `workers.py`.
- ARCH-018 — host owners never import concrete plugin modules; plugins
  are reached through catalog discovery.
- ARCH-019 — filesystem mutation calls appear only in `artifacts.py`
  (artifact tree) and `storage.py` (database file).
- ARCH-020 — pickle is banned everywhere under `app/`.

## Runtime expectations

- **Storage** owns a single writer thread; callers never touch SQLite
  directly, and the event loop never blocks on a storage call.
- **Gateway** binds loopback by default, never wildcard-credentialed CORS,
  maps unknown exceptions to generic messages (no path/secret leakage),
  and grants authorization only via composition-time `GatewayConfig`
  policy — request bodies may only narrow it.
- **Jobs** freezes the full execution identity at submission (wire
  version, graph, inputs hash, entry/dependency fingerprints, numerical
  policies, engine version, pure-only effect policy); refresh or restart
  never silently rebinds it.
- No host owner performs plugin-specific branching; all behavior
  dispatches through admitted catalog operations.

## Verification

```powershell
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py        # ruff + mypy strict + tests + coverage + examples
```
