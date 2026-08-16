# Trading Domain Audit Remediation Implementation Plan

Plan ID: TRADING-AUDIT-REMEDIATION-01

Target: app/services/trading and its documented consumers

Audit baseline: 2026-08-06

Status: Implemented and verified on 2026-08-06

## Implementation result

The approved corrected Plan 7 superseded the stale seven-table assumption in
this baseline. Trading currently owns five live target tables and two immutable
migration steps. Remediation completed the authoritative migration runner,
requirement usage output contracts, virtual secret-safe workflows, Risk
compatibility evidence, per-file coverage floor, unit-test latency ceiling, API
route enforcement, typed UI mutations, and schema/document reconciliation.

Final correction Plan 8 removed the duplicate legacy usage program, added exact
registry parity enforcement, passed current Risk producer contracts through the
real Trading readiness consumer, mounted a complete fail-closed governed Trading
form, and reconciled active documentation. Verification on 2026-08-06: all 182
Trading tests pass; all 141 unit tests pass with the slowest at 0.08 seconds; all
16 workflows execute; Trading-only branch coverage is 87% and every production
file is at least 81%; Ruff and Trading mypy pass; and all four targeted Trading
frontend component/client tests pass. Full frontend type checking reaches only
the pre-existing unrelated Indicators unused-variable error at
`app/ui/src/components/workflow/indicators.tsx:25` and reports no Trading error.

## 1. Objective

Remediate every non-conformant, partial, missing, or conflicting item found in
the Trading domain audit while preserving the eleven conformant controls.
Implementation must remain surgical, feature-owned, fail-closed, and compatible
with the public package-root boundaries.

This plan is self-contained. The coding agent must re-read AGENTS.md,
docs/PROJECT.md, docs/ARCHITECTURE.md, docs/CHANGELOG.md, and
app/services/trading/README.md before editing because repository files remain
the authority if the working tree changes after this baseline.

## 2. Audit baseline and required outcomes

| ID | Baseline | Evidence or deviation | Required outcome |
|---|---|---|---|
| REG | PASS | Nine registered features equal nine production feature folders after documented exclusions. | Preserve exact reconciliation. |
| TASK | PASS | README feature and requirement rows are Completed. | Preserve; add only an approved completed requirement with evidence. |
| GATE | PASS | Trading root has a literal function-only public export list. | Preserve package root as sole public boundary. |
| FUNC | PASS | All 69 current public exports resolve to standalone functions. | Any new public export must also be a function. |
| DEEP | PASS | No prohibited deep cross-domain imports were found in audited consumers. | New consumers import from package roots only. |
| ROOT | PASS | Root-file layout conforms. | Do not add production behavior at package root. |
| USE | FAIL | Existing programs execute, but active FR-TRD-069 through FR-TRD-076 have no named usage functions; retired FR-TRD-011 must stay absent; examples do not consistently print an explicit success line plus produced data. | One numbered program per feature; every active FR has a function and prints both required lines. |
| WFE | FAIL | Sixteen active workflow files and run_all.py exist, but run_all fails because WF-TRD-PRI imports real_session through a wrapper that does not re-export it. | Every stage workflow and run_all.py execute successfully. |
| UT | PASS | 130 Trading unit tests passed. | Preserve all behavior. |
| IT | FAIL | Risk compatibility evidence drifted and did not exercise the Trading consumer boundary. | Current Risk producer contracts pass through Trading readiness; incompatibility and staleness fail closed. |
| COV | FAIL | Aggregate coverage was 87%, but monitoring/runtime.py was 31% and state/runtime.py was 79%. | Every Trading production file is at least 80%. |
| HYG | PASS | No bare except, application print, or literal credential finding. | Preserve. |
| DB | FAIL | Trading exposes migration definitions, while callers invoke Data directly and may omit complete_manifest=True. | One Trading-owned authoritative manifest runner always delegates through Data with complete-manifest validation. |
| SCHEMA | FAIL | Seven Trading tables matched source, target, and the development database, but docs/schema/05_reconciliation.md states the migration was never applied. | Record a dated, reproducible Trading-only target/source/live reconciliation. |
| REACH | PASS | All seven Trading tables trace from CRUD to production operations outside persistence. | Preserve traces and tests. |
| CONTRACT | FAIL | Risk compatibility test used stale producer shapes and only instantiated objects. | Producer-consumer compatibility test exercises the actual boundary. |
| LOG | PASS | Required workflow/public/external/state/side-effect logging exists without observed secret exposure. | Preserve and log the new migration boundary. |
| SAFE | FAIL | Safety gates passed, but WF-TRD-003 can print the full demo BrokerAccountInfo payload. | Usage output remains bounded and excludes sensitive account details. |
| QUANT | PASS | No invented fills/results and deterministic test behavior were observed. | Preserve. |
| NFR | FAIL | The subprocess import-safety unit test took about 1.25 seconds, above the 100 ms unit-test ceiling. | Every test retained under tests/trading/unit completes within 100 ms. |
| DOCS | FAIL | README paths/counts/coverage are stale; Architecture conflicts with the API registry; PROJECT audit rows remain unchecked. | Reconcile active documents to verified code and results. |
| UI | FAIL | Session read is surfaced, but submit sends an invalid partial DTO and cancel/close buttons do nothing; the client omits required bodies for cancel/close. | Typed complete requests reach all three governed API mutations without inventing authority. |

## 3. Non-negotiable implementation decisions

1. Do not modify the applied Trading migration SQL, migration ID, or checksum.
   The development ledger baseline is migration ID
   001_initial_trading_schema with checksum
   9e5f1be60a498a39fae38f0975bd858733e148fe984438c3ca3b761af2044083.
   A mismatch on re-verification is a blocker, not permission to rewrite history.
2. Assign the migration runner to FEAT-TRD-02 and register FR-TRD-077. Migration
   infrastructure remains the documented reconciliation exclusion; it is not a
   tenth feature.
3. Keep app/services/trading/__init__.py as the only Trading public boundary.
   Its new entry, if implemented, is run_trading_migrations, a standalone
   function.
4. Cross-domain production and integration imports use app.services.data,
   app.services.risk, and app.services.trading package roots only.
5. The UI transports user-supplied, already-governed references. It must never
   generate Risk decisions, policy verdicts, approval tokens, account authority,
   or evidence. Missing fields block submission.
6. Preserve unrelated and in-progress Risk changes in the working tree.
   Do not revert, normalize, or include them in a Trading change.
7. Applied migrations are immutable. Tests use temporary databases. Do not run
   destructive SQL or mutate the owner's development database.

## 4. Implementation sequence

Execute workstreams A through I in order. Stop and issue a plan delta if a new
finding changes feature ownership, public signatures, database history, or the
API contract. After each workstream, run its targeted tests before proceeding.

## 5. Workstream A — DB: authoritative Trading migration runner

### Files

- Edit app/services/trading/migrations/definitions.py.
- Edit app/services/trading/migrations/__init__.py.
- Edit app/services/trading/state/__init__.py.
- Edit app/services/trading/__init__.py.
- Edit app/services/trading/contracts/registry.py.
- Edit app/services/trading/README.md.
- Edit tests/trading/unit/state/test_migrations.py.
- Edit tests/trading/integration/test_runtime_state.py.
- Edit Trading usage callers that currently compose Data directly:
  tests/trading/usage/features/06_monitoring.py and
  tests/trading/integration/test_runtime_state.py.
- Update tests/trading/usage/features/02_state.py for FR-TRD-077 evidence.

### Requirement and exact composition

Register this requirement under FEAT-TRD-02:

FR-TRD-077: Trading shall execute its complete immutable migration manifest
through Data's authoritative migration runner. The request shall declare
domain="trading", include every Trading migration step in canonical order, set
complete_manifest=True, carry the caller's request_id, and fail closed on ledger
verification, lock, checksum, orphaned-step, or transactional execution errors.

In app/services/trading/migrations/definitions.py retain the existing private
tuple returned by _get_trading_migrations_value. Give the authoritative tuple a
single private name, _TRADING_MIGRATION_STEPS, and make both the definition
getter and runner consume that exact tuple. Do not duplicate statements.

The public signature and composition are:

    def run_trading_migrations(request_id: str) -> object:
        """Apply the immutable Trading migration manifest through Data."""
        logger.info("Running Trading-owned schema migrations")
        request = build_migration_request(
            domain="trading",
            steps=_TRADING_MIGRATION_STEPS,
            request_id=request_id,
            complete_manifest=True,
        )
        return run_domain_migrations(request)

Import build_migration_request and run_domain_migrations only from
app.services.data. Keep get_trading_migrations() returning the existing
StandardResponse containing the same immutable steps. Export
run_trading_migrations through migrations, state, and the Trading package root.
Add it to the literal root __all__ and contract registry.

### Tests and acceptance

- Unit spy test proves the request uses domain trading, the exact complete
  ordered tuple, caller request ID, and complete_manifest=True.
- Fresh temporary database test proves all seven Trading tables and the ledger
  row are created transactionally.
- Re-run test proves idempotence and an unchanged checksum.
- Checksum mismatch test proves fail-closed behavior with no schema mutation.
- Orphaned applied-step test proves complete-manifest rejection.
- Lock-contention/transaction-failure test proves no partial application.
- No test opens or changes the repository development database.
- Existing consumers stop manually composing MigrationRequest for Trading.

## 6. Workstream B — SCHEMA: current target/source/live reconciliation

### Files

- Edit docs/schema/05_reconciliation.md.
- Read, but do not alter unless an actual Trading mismatch is found:
  docs/schema/01_schema_inventory.md and the remaining docs/schema model files.

### Procedure

Use read-only inspection against the configured development SQLite database.
Record the exact database path in command output but do not publish credentials.
Compare:

1. The seven Trading target tables in docs/schema.
2. _TRADING_SCHEMA_STATEMENTS in
   app/services/trading/migrations/definitions.py.
3. sqlite_master table/index SQL and PRAGMA table_info/index_list output.
4. The migration ledger row and checksum.

The known baseline tables are Trading-owned event, projection, idempotency,
order, fill, position, and evidence records. Use the exact current table names
from the migration definitions in the final reconciliation; do not infer names
from this summary.

Replace the false statement that the Trading migration has never been applied
with a dated Trading-specific result. State target/source/live agreement or list
every divergence explicitly. Preserve unrelated schema findings. If global
schema validation fails for another domain, report it separately and do not
claim Trading failure.

### Acceptance

- The ledger ID and checksum equal the immutable source definition.
- All seven target/source/live table and index definitions are accounted for.
- The document states the database inspected, timestamp, commands, and any
  non-Trading validation limitation.

## 7. Workstream C — USE: feature and FR usage evidence

### Files

Edit the nine existing numbered programs only:

- tests/trading/usage/features/01_contracts.py
- tests/trading/usage/features/02_state.py
- tests/trading/usage/features/03_validation.py
- tests/trading/usage/features/04_routing.py
- tests/trading/usage/features/05_reconciliation.py
- tests/trading/usage/features/06_monitoring.py
- tests/trading/usage/features/07_live.py
- tests/trading/usage/features/08_actions.py
- tests/trading/usage/features/09_reporting.py

Edit tests/trading/integration/test_usage_scripts.py to enforce the convention.
Do not add a tenth feature program. Do not add FR-TRD-011; it is retired.

### Exact convention

Every active requirement in the README must have exactly one function named
fr_trd_NNN in its owning feature program. The active sequence after Workstream A
is 001 through 010 and 012 through 077.

Map the currently missing evidence as follows:

- FR-TRD-069 belongs in 08_actions.py.
- FR-TRD-070 through FR-TRD-077 belong in 02_state.py.

Every FR function must call the documented Trading package-root operation and
print exactly two categories of observable output:

    SUCCESS: FR-TRD-NNN
    Data -> <bounded, secret-safe representation of the actual returned data>

The data line must derive from the function result, not a fabricated expected
value. Existing explanatory headings may remain, but they do not substitute for
the two required lines. Each program defines main(), calls all its FR functions,
has the __main__ guard, remains outside pytest collection, and imports Trading
only through app.services.trading.

### Acceptance

- Static parity test compares active README FR IDs to usage function names.
- Exactly one numbered usage file exists per registered feature.
- Direct execution of all nine files exits zero.
- Each invoked FR prints its success line and actual bounded data.
- No output contains credentials, account secrets, tokens, or full sensitive
  trading payloads.

## 8. Workstream D — WFE and SAFE: workflow runner and bounded broker output

### Files

- Edit tests/brokers/usage/_support.py.
- Edit tests/brokers/usage/features/_support.py.
- Edit tests/trading/usage/workflows/wf_trd_003_start_enable_live_session.py.
- Add or edit tests/trading/integration/test_workflow_usage.py.
- Read all stage programs and tests/trading/usage/workflows/run_all.py.

### Wrapper correction

Re-export real_session from tests/brokers/usage/_support.py:

    from tests.brokers.usage.features._support import (
        config,
        create_real_adapter,
        real_session,
        require_error,
        require_success,
    )

and include "real_session" in its literal __all__. Keep the canonical
implementation in features/_support.py.

### Bounded output correction

Extend the teaching-only helpers with an explicit keyword-only output control:

    def require_success(
        label: str,
        result: object,
        *,
        include_data: bool = True,
    ) -> object:

    def show(
        label: str,
        result: object,
        *,
        include_data: bool = True,
    ) -> None:

When include_data is False, print success status and operation metadata but not
repr(result.data). Preserve True as the compatibility default for ordinary
bounded examples. WF-TRD-003 must call the helper with include_data=False for
connection/account-readiness results. Never print account ID, balance, equity,
margin, credential metadata, token material, or the complete BrokerAccountInfo.

### Workflow acceptance

- tests/trading/usage/workflows/run_all.py exits zero.
- Every active WF-TRD-NNN and stage-labelled PRI/SEC/TER program is discovered
  once and executes.
- The test captures WF-TRD-003 output and asserts absence of sensitive account
  field names and sentinel secret values.
- Production behavior is not mocked into a false success; genuine integration
  remains restricted to verified demo/demo/dev targets.

## 9. Workstream E — IT and CONTRACT: Risk producer-consumer compatibility

### Files

- Edit tests/trading/integration/test_risk_contract_compatibility.py.
- Edit app/services/trading/README.md contract evidence.
- Edit app/services/risk/README.md only if the producer contract documentation
  itself is inaccurate; otherwise leave the Risk domain untouched.

### Exact current producer contracts

Construct ActionPolicyVerdict with:

    contract_version="v1"
    schema_id="risk.action_policy_verdict.v1"
    verdict_id, action, scope, policy_version, attestation_id, decision_id
    reservation_id, allowed, reasons, issued_at, expires_at
    request_id, workflow_id, correlation_id

Construct RiskDecisionPackage with:

    contract_version="v1"
    schema_id="risk.risk_decision_package.v1"
    decision_id, intent_id, state, requested_size, approved_size
    ordered_checks, primary_failure_limit, composite_breach_flags
    evidence_refs, config_hash, concurrency_disclosure, recommendations
    issued_at, expires_at, token
    request_id, workflow_id, correlation_id

An approving trade decision has non-null intent_id and approved_size greater
than zero. Use the current Risk package-root factories/functions where available
instead of deep imports.

The compatibility test must pass producer values through:

    assess_execution_readiness(
        request: TradingRequest,
        snapshot: RouteSnapshot,
        risk_decision: RiskDecisionPackage,
        kill_switch_state: KillSwitchState,
        action_policy: Mapping[str, JsonValue],
        max_staleness_seconds: Mapping[str, Decimal],
    ) -> StandardResponse[ReadinessAssessment]

Convert the verdict to the exact mapping expected by Trading through a public
Risk operation or documented serialization, retaining verdict_id, decision
binding, allowed state, scope, reservation, and validity times.

### Acceptance

- A valid current Risk decision and policy verdict produce a successful Trading
  readiness response with the same decision/verdict identifiers.
- Expired, denied, mismatched decision, missing reservation, or incompatible
  schema evidence fails closed.
- The test proves behavior, not merely successful object construction.
- Contract owner, version, schema IDs, compatibility policy, and evidence are
  recorded in the Trading README.

## 10. Workstream F — COV: per-file 80 percent floor

### Files

- Add tests/trading/unit/monitoring/test_runtime.py.
- Add tests/trading/unit/state/test_runtime.py.
- Edit existing focused tests only if branch ownership makes that smaller.

### Required branch coverage

For app/services/trading/monitoring/runtime.py cover:

- Successful event emission and returned standard response.
- Missing/invalid dependency or malformed event mapping.
- Downstream emitter success and failure.
- Cost-budget normal, threshold, and breached branches.
- Incident evidence creation, correlation identifiers, and mapped TradingError.
- Logging occurs at public/side-effect boundaries without payload disclosure.

For app/services/trading/state/runtime.py cover:

- Successful append/read/materialization paths.
- Empty and missing stream/projection behavior.
- Version conflict and invalid transition.
- Idempotency reservation new, replay, conflict, and unknown outcome.
- Persistence delegate failure mapped to the public error response.
- Resource lifecycle cleanup.

Tests must assert public effects through app.services.trading when possible.
Do not test private implementation solely to inflate coverage.

### Acceptance

Run coverage with branch data over every app/services/trading Python file.
No individual file may round up from below 80.00 percent. Record the generated
per-file report in the audit evidence, not as mutable README detail unless the
README explicitly owns the measurement.

## 11. Workstream G — NFR: 100 ms unit-test ceiling

### Files

- Edit tests/trading/unit/contracts/test_registry.py or the exact current file
  containing subprocess import-safety coverage.
- Add tests/trading/structural/__init__.py.
- Add tests/trading/structural/test_import_safety.py.
- Add/update Trading NFR timing enforcement in the appropriate test tooling.

### Composition

Move the process-start/import-safety scenario out of tests/trading/unit into the
structural suite without weakening its assertions. Retain a fast in-process
registry/export assertion in unit scope. Do not fake subprocess duration with a
mock; classify the test according to its real cost.

Measure each Trading unit test independently with pytest durations or a
purpose-built timing plugin already pinned in pyproject.toml. Any test at or
above 0.100 seconds fails the unit ceiling. Avoid sleep, sockets, real databases,
process creation, and unbounded event loops in unit tests.

### Acceptance

- All tests under tests/trading/unit pass.
- Every individual unit test is below 100 ms on the audit environment.
- Import-safety still executes as a real subprocess in structural scope.
- Integration/structural time is reported separately and is not mislabeled.

## 12. Workstream H — UI: complete governed Trading boundary

### Files

- Edit app/services/api/composition/trading_dependencies.py.
- Edit tests/api tests covering Trading composition/runtime policy.
- Edit app/ui/src/clients/trading.ts.
- Edit app/ui/src/clients/trading.test.ts or the existing client test file.
- Edit app/ui/src/components/workflow/trading.tsx.
- Edit app/ui/src/components/workflow/trading.test.tsx.
- Edit app/ui/src/components/workflow/nfr.test.tsx only if accessibility
  expectations change.
- Edit app/services/api/README.md and app/services/trading/README.md.

### Backend runtime-policy correction

TradingMutationRequest declares route: "demo" | "live"; it does not declare
runtime_profile or execution_route. Replace the ineffective field lookups in
_enforce_runtime_policy with:

    if policy is None:
        return
    declared_route = getattr(boundary_request, "route", None)
    expected_route = getattr(policy, "execution_route", None)
    if declared_route is None:
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISSING")
    if declared_route != expected_route:
        raise RuntimeError("TRADING_EXECUTION_ROUTE_MISMATCH")
    if declared_route == "live" and not getattr(
        policy, "allow_live_mutations", False
    ):
        raise RuntimeError("TRADING_LIVE_MUTATIONS_DISABLED")

If the runtime policy uses sim rather than demo, do not silently equate them.
Resolve the contract conflict in the authoritative API specification and issue
a plan delta before changing enum values. Tests must prove demo/live mismatch
and disabled-live fail before Trading delegation.

### Exact frontend request type

Replace the open index signature with a typed projection of
TradingMutationRequest:

    export interface TradingMutationInput {
      contract_version?: "v1";
      schema_id?: "trading.trading_request.v1";
      request_id: string;
      workflow_id: string;
      correlation_id: string;
      causation_id?: string | null;
      route: "demo" | "live";
      action: string;
      provider_id?: string | null;
      account_id: string;
      portfolio_id?: string | null;
      strategy_id: string;
      strategy_version: string;
      intent_id: string;
      symbol?: string | null;
      side?: "BUY" | "SELL" | null;
      order_type: "MARKET" | "LIMIT" | "STOP" | "STOP_LIMIT";
      quantity_unit: string;
      quantity?: string | null;
      price?: string | null;
      stop_price?: string | null;
      stop_loss?: string | null;
      take_profit?: string | null;
      time_in_force?: "GTC" | "IOC" | "FOK" | "GTD" | "DAY" | null;
      expiration?: string | null;
      target_broker_order_id?: string | null;
      target_broker_position_id?: string | null;
      order_id?: string | null;
      position_id?: string | null;
      expected_version?: number | null;
      risk_decision_id: string;
      action_policy_verdict_id: string;
      approval_token_ref: string;
      eligibility_decision_id?: string | null;
      allocation_decision_id?: string | null;
      scope_level?: "global" | "portfolio" | "strategy" | "symbol" | null;
      control_reason?: string | null;
      idempotency_key: string;
      canonical_material_version: string;
      system_time: string;
      broker_time?: string | null;
      valid_until: string;
      instrument_min_quantity?: string | null;
      instrument_max_quantity?: string | null;
      instrument_quantity_step?: string | null;
      instrument_price_tick?: string | null;
      redaction_applied: true;
    }

Use decimal strings in JSON. Derive specialized aliases if helpful:
SubmitTradingMutationInput, CancelTradingMutationInput, and
CloseTradingMutationInput. They must narrow action and require the corresponding
target fields; they must not omit governed authority fields.

Client signatures:

    submitOrder(
      input: SubmitTradingMutationInput,
      options?: RequestOptions
    ): Promise<ApiResponse<ExecutionReceipt>>

    cancelOrder(
      orderId: string,
      input: CancelTradingMutationInput,
      options?: RequestOptions
    ): Promise<ApiResponse<ExecutionReceipt>>

    closePosition(
      positionId: string,
      input: CloseTradingMutationInput,
      options?: RequestOptions
    ): Promise<ApiResponse<ExecutionReceipt>>

All three send body: input. Cancel must enforce action="cancel_order" and
target_broker_order_id equals the path orderId. Close must enforce
action="close_position" and target_broker_position_id equals path positionId.
The request body's idempotency_key must equal the governed transport
idempotency key; reject a mismatch before the request is sent.

### TradingView behavior

Replace the hard-coded incomplete submit object with controlled, validated
fields for the complete DTO or accept an injected request-builder callback that
returns a complete DTO from an authenticated owner-controlled context. The
preferred component API is:

    export interface TradingViewProps {
      className?: string;
      buildMutationInput?: (
        action: "submit_order" | "cancel_order" | "close_position",
        targetId?: string
      ) => TradingMutationInput | null;
    }

Null means authority is unavailable and the action remains blocked. The view
may collect ordinary order parameters and target IDs, but it must receive Risk
and approval references from the injected governed context. It must call
buildGovernedOptions immediately before each mutation and pass those options to
the client. Arming is not reusable authorization; it only enables deliberate
user action. Disable buttons while pending, show bounded success/error status,
and refresh the session after success. Cancel and Close require explicit target
selection and click handlers.

### UI/API acceptance

- Client tests assert exact method, route/path, body, CSRF, and idempotency.
- Missing/mismatched authority or path/body IDs are rejected without transport.
- Component tests prove all buttons start disabled, require deliberate arming,
  call the correct client once, never auto-submit, and surface failures.
- Accessibility tests prove labels, keyboard activation, focus, and pending
  state.
- API tests prove route mismatch and disabled live requests fail closed.
- No UI fixture or code invents decision IDs, verdicts, tokens, fills, or live
  performance.

## 13. Workstream I — DOCS: reconcile authoritative documents

### Files and exact updates

1. app/services/trading/README.md
   - Register FR-TRD-077 under FEAT-TRD-02.
   - Add run_trading_migrations to FEAT-TRD-02 public API and evidence.
   - Replace stale state/migrations.py references with
     migrations/definitions.py and its re-export path.
   - Record all FR usage evidence functions, current Risk contract ownership and
     versions, migration manifest policy, UI/API reachability, NFR budget, and
     verified test/coverage results.
   - Remove resolved rows from Open Decisions; do not preserve decision history.
2. app/services/api/README.md
   - Reconcile the Trading route count and exact session/submit/cancel/close
     operations with the registry and code.
   - State body/path matching, runtime-route enforcement, and client reachability.
3. docs/ARCHITECTURE.md
   - Remove the conflicting claim that Trading has 23 API operations or no
     Trading mutations if current code exposes governed mutations.
   - Describe Trading package-root ownership, Risk authority, Data migration
     execution, API composition, and frontend boundary.
4. docs/PROJECT.md
   - Mark only the twenty-two Trading audit rows whose final validation passes.
   - Leave any failed row open with deviation and remediation.
   - Keep system-level relationships only; do not duplicate feature internals.
5. docs/CHANGELOG.md
   - Add concise one-line Unreleased bullets under canonical categories.
   - Do not add test inventories, measurements, decision logs, or a second
     feature registry.
6. docs/schema/05_reconciliation.md
   - Apply Workstream B's verified Trading-only reconciliation.

Every completed implementation-plan checklist item added to an active document
must end with supporting code/test path and line number. Line numbers must be
captured after formatting, not guessed in advance.

### Documentation acceptance

- README feature count remains nine and contains exactly one Feature Registry.
- Code exports, registry, README public API, and usage files reconcile.
- Architecture and API route counts agree with code.
- No resolved Open Decisions row remains.
- Changelog follows Unreleased/category rules.
- Search finds no stale state/migrations.py or obsolete Trading measurements.

## 14. Anticipated file set

The coding agent may modify only the files listed in Workstreams A through I.
The expected additions are:

- tests/trading/unit/monitoring/test_runtime.py
- tests/trading/unit/state/test_runtime.py
- tests/trading/structural/__init__.py
- tests/trading/structural/test_import_safety.py
- tests/trading/integration/test_workflow_usage.py

Before editing, run git status --short. If any listed file already has owner
changes, preserve them and integrate surgically. Any required file outside this
set is a plan delta requiring a new dry run and approval.

## 15. Dependencies and contracts

- Data package root: build_migration_request and run_domain_migrations.
  Data owns ledger verification, write locks, checksum comparison, busy timeout,
  and transactional execution.
- Risk package root: current RiskDecisionPackage, ActionPolicyVerdict,
  RiskApprovalToken, DecisionState, and public factories/serialization.
- Brokers package root in production; tests may use the documented usage support
  wrapper solely for standalone demo workflow composition.
- API contract: app/services/api/contracts/models.py TradingMutationRequest.
- Frontend transport: app/ui/src/clients/request.ts RequestOptions and governed
  preflight utilities under app/ui/src/context.
- Versions: use only versions pinned by pyproject.toml and app/ui package lock.
  Do not add or upgrade dependencies.

Unresolved dependency: the API runtime policy may name simulation as sim while
TradingMutationRequest accepts demo/live. Verify the deployed settings contract
before implementation. If no explicit mapping is documented, stop and request
an owner decision; do not invent a mapping.

## 16. Validation commands

Run from repository root, using the pinned uv/npm tooling. Targeted checks come
first.

    uv run ruff check app/services/trading app/services/api/composition/trading_dependencies.py tests/trading tests/brokers/usage
    uv run ruff format --check app/services/trading app/services/api/composition/trading_dependencies.py tests/trading tests/brokers/usage
    uv run mypy app/services/trading app/services/api/composition/trading_dependencies.py
    uv run pytest tests/trading/unit/state/test_migrations.py -q
    uv run pytest tests/trading/integration/test_runtime_state.py -q
    uv run pytest tests/trading/integration/test_risk_contract_compatibility.py -q
    uv run pytest tests/trading/integration/test_workflow_usage.py -q
    uv run pytest tests/trading/integration/test_usage_scripts.py -q
    uv run pytest tests/trading/unit/monitoring/test_runtime.py -q
    uv run pytest tests/trading/unit/state/test_runtime.py -q
    uv run pytest tests/api -q
    uv run pytest tests/trading/unit -q --durations=0
    uv run pytest tests/trading/integration tests/trading/structural -q
    uv run pytest tests/trading --cov=app.services.trading --cov-branch --cov-report=term-missing
    uv run python tests/trading/usage/features/01_contracts.py
    uv run python tests/trading/usage/features/02_state.py
    uv run python tests/trading/usage/features/03_validation.py
    uv run python tests/trading/usage/features/04_routing.py
    uv run python tests/trading/usage/features/05_reconciliation.py
    uv run python tests/trading/usage/features/06_monitoring.py
    uv run python tests/trading/usage/features/07_live.py
    uv run python tests/trading/usage/features/08_actions.py
    uv run python tests/trading/usage/features/09_reporting.py
    uv run python tests/trading/usage/workflows/run_all.py
    npm --prefix app/ui test -- --run
    npm --prefix app/ui run typecheck
    npm --prefix app/ui run lint

Also run repository-provided schema reconciliation and secret-scanning commands
documented in pyproject.toml/pre-commit configuration. Do not substitute an
unversioned global tool. A global failure outside Trading must be reported with
scope and must not be silently repaired.

## 17. Final acceptance matrix

Implementation is complete only when:

- REG/TASK/GATE/FUNC/DEEP/ROOT/HYG/REACH/LOG/QUANT remain PASS.
- USE, WFE, IT, COV, DB, SCHEMA, CONTRACT, SAFE, NFR, DOCS, and UI have direct,
  current evidence and pass independently.
- All Trading unit and integration tests pass.
- Every Trading production file has at least 80.00 percent coverage.
- Every Trading unit test is below 100 ms.
- All feature and workflow programs execute directly.
- No live broker or production mutation occurred during verification.
- No secrets or sensitive account payloads appear in code, logs, fixtures, or
  captured output.
- The final git diff contains only approved files and no unrelated Risk changes.

## 18. Scope boundaries

Included:

- The eleven failed Trading audit controls and documentation needed to evidence
  them.
- Narrow Brokers usage-support changes required to execute and safely display
  the Trading workflow.
- Narrow API/frontend changes required for actual UI reachability.

Excluded:

- New Trading features beyond FR-TRD-077.
- Changes to migration history or target schema.
- Risk redesign or unrelated Risk audit remediation.
- Broker adapter redesign, live broker calls, production database mutation.
- Dependency upgrades, broad formatting, unrelated schema reconciliation.
- Commits, pushes, releases, or deployment.

## 19. Risks and stop conditions

- Existing owner modifications overlap a listed file: inspect and preserve; stop
  if intent cannot be reconciled.
- Migration source checksum differs from the recorded ledger: stop immediately.
- Runtime sim/demo vocabulary lacks an authoritative mapping: request decision.
- Current Risk contract changes again: regenerate fixtures from the current
  public producer contract and document the compatibility version.
- UI cannot obtain governed references from authenticated context: leave
  mutation controls disabled and report the dependency; never synthesize them.
- A test requires a real/live account: replace with demo/demo or a deterministic
  contract test; never relax environment gates.
- Per-file coverage needs production-only branches that cannot be safely
  exercised: document and redesign the seam through a plan delta rather than
  adding pragma exclusions.

## 20. Rollback

Rollback is file-scoped and must preserve pre-existing owner changes.

1. Capture git status and diff before implementation.
2. Revert only the approved hunks in files listed in Workstreams A through I.
3. Remove only newly added tests listed in Section 14 after verifying their
   absolute paths are inside this repository.
4. Remove run_trading_migrations from the Trading export chain, registry, and
   README together; leave immutable migration SQL and ledger untouched.
5. Restore the previous frontend client/component signatures and API policy
   hunks only if they were introduced by this implementation.
6. Do not use git reset, git clean, or broad checkout commands.
7. Re-run the baseline unit tests, integration tests, feature programs, workflow
   runner, frontend tests, and git diff --check after rollback.

## 21. Coding-agent final report requirements

The implementation report must include:

- Scope followed and every file changed.
- Decisions made and implications.
- FR-TRD-077 and every remediated audit control with file:line evidence.
- Dependency contracts used.
- Every command run with pass/fail result and measured unit/coverage evidence.
- Usage and workflow execution results.
- Secret/safety verification.
- Active documents updated.
- Remaining deviations or blockers; never label partial evidence PASS.
- The exact rollback path.

Do not begin remediation merely because this plan exists. Obtain a new
standalone owner message whose trimmed entire content is exactly
APPROVED: EXECUTE for this numbered plan before modifying implementation files.
