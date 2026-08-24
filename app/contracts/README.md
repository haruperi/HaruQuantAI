# Shared Contracts

> **Package:** `app/contracts/`
> **Category:** Non-domain shared substrate
> **Status:** Contract inventory specified; production contract slices `Missing`
> **Planned inventory:** Maintained in this README

## Purpose

`app/contracts/` owns cross-boundary application/domain DTOs, protocols, events, errors, and domain capability-key declarations. Semantic ownership remains with the responsible producer or receiver domain; physical definitions are centralized here so feature implementations never import one another.

`CapabilityKey`, `FeatureSpec`, lifecycle/context/scope protocols, registry/graph/reconciler primitives, event infrastructure, and state declarations are not application contracts. They live in `app/kernel/`.

## Dependency boundary

- Contracts may import the kernel `CapabilityKey` primitive plus the standard library and approved schema/serialization libraries.
- Contracts never import composition, services, adapters, persistence implementations, provider SDKs, or UI code.
- A type that crosses a feature/application/process/API boundary belongs here; private implementation types remain inside their owning feature.
- Services depend on public contracts and kernel primitives, never another feature implementation.

```text
app/kernel  <-  app/contracts  <-  app/composition
     ^               ^
     └──────── app/services/<domain>/<feature>
```

Arrows point toward dependencies. Service features depend on public contracts and Kernel primitives, while Composition never imports their implementations.

## Contract shape

A namespace contains only the files it needs, commonly `capabilities.py`, `models.py`, `ports.py`, `commands.py`, `queries.py`, `events.py`, `errors.py`, and optional `wire/`. Empty ceremonial files are not required. `__init__.py` remains import-pure.

Runtime capability identifiers use `<lowercase-name>@<major>`, normally `<domain>.<name>@<major>`. Capability constants belong with their public protocol in contracts; the generic key type belongs in kernel. FR IDs are request/operation/test discriminators where useful, not automatically separate runtime capability keys.

## Evolution

- Commands/requests are semantically owned by receivers; results/snapshots/events by producers.
- Provider SDK, ORM, dataframe, database-row, and transport-native objects do not cross public boundaries.
- Additive compatible evolution retains a major version; breaking semantics require a new major and explicit compatibility/migration behavior.
- Each feature defines the minimal public contracts it needs before its vertical implementation. The project does not wait for every planned domain contract to exist before feature work begins.

Creating a contract does not complete its business FR. Completion requires the owning feature implementation and acceptance evidence.

## Planned contract inventory

This is the planned product contract inventory, not a prerequisite that must be implemented in one wave. Each feature adds its minimal contract slice before implementation. An undelivered entry remains `Missing` and does not imply runtime availability.

### 4.1 `app/contracts/workspace/`

**Status:** `ManageWorkspacesCapability` and `ConfigureRuntimeCapability` implemented; remaining domain capability surfaces planned.

**Public records:** `WorkspaceRef`, `WorkspaceVersion`, `WorkspaceConfiguration`, `RuntimeConfiguration`, `StorageGuardPolicy`, `WorkspaceWriterLease`, `WorkspaceWriterFence`, `WorkspaceBackupManifest`, `WorkspaceRestorePlan`, `SecretRef`, `PrincipalRef`, `LocalSession`, `SystemReadiness`, `DiagnosticBundleRef`, `WorkerCapabilityDescriptor`, `WorkerRegistration`, `WorkerLease`, `WorkerTaskEnvelope`, `ArtifactManifest`, `HostedWorkspaceContext`, and `WorkspaceAuthorizationDecision`.

**Capability bundles (6):** `ManageWorkspacesCapability` (implemented), `ConfigureRuntimeCapability` (implemented), `SecureLocalAccessCapability`, `BuildDiagnosticsCapability`, `DistributeWorkersCapability`, and `HostWorkspacesCapability`.

### 4.2 `app/contracts/catalogue/`

**Public records:** `InstrumentRef`, `InstrumentVersion`, `AssetClass`, `ProviderRef`, `BrokerRef`, `ProviderSymbolMapping`, `TradingSessionDefinition`, `MarketCalendarVersion`, `TradingInterval`, `TradingRuleSet`, `OrderConstraints`, `CostModelRef`, `UniverseRef`, `UniverseVersion`, `UniverseMembership`, `FxRateObservation`, `CurrencyConversionPath`, and `CatalogueExchangePackage`.

**Capability bundles (7):** `CatalogInstrumentsCapability`, `MapProvidersCapability`, `DefineSessionsCapability`, `DefineTradingRulesCapability`, `ManageUniversesCapability`, `ConvertCurrenciesCapability`, and `ExchangeCatalogueCapability`.

### 4.3 `app/contracts/data/`

**Public records:** `DataSeriesRef`, `DataSeriesVersion`, `DataConnectionRef`, `DataImportPlan`, `DataImportReceipt`, `Bar`, `Tick`, `SeriesCoverage`, `DataQualityFinding`, `DataQualityDecision`, `AggregationSpec`, `RetentionPolicy`, `RunDataBinding`, `AlignedSeries`, `ConnectorProfile`, `ConnectorSyncPlan`, `ConnectorSyncReceipt`, `VolumeProfileSource`, `ExternalIndicatorSeriesVersion`, `SyntheticModelSpec`, `ScenarioSeriesVersion`, `MarketNewsObservation`, `MarketNewsRevision`, `MarketEvent`, `MarketFeedState`, `MarketReplayRef`, and `QuantDataImportSpec`.

**Capability bundles (14):** `IngestHistoryCapability`, `SyncConnectorsCapability`, `ImportQuantdataCapability`, `NormalizeTicksCapability`, `ResolveQualityCapability`, `AggregateBarsCapability`, `ManageRetentionCapability`, `AlignSeriesCapability`, `PrepareProfilesCapability`, `ImportIndicatorsCapability`, `BindRunDataCapability`, `GenerateScenariosCapability`, `TrackMarketNewsCapability`, and `StreamMarketEventsCapability`.

### 4.4 `app/contracts/strategy/`

**Public records:** `StrategyRef`, `StrategyVersion`, `StrategyAst`, `StrategyNode`, `ExpressionNode`, `BlockDefinition`, `ParameterDefinition`, `ChartDefinition`, `DirectionPolicy`, `VisibilityPolicy`, `StrategyValidationReport`, `StrategyTemplate`, `StrategyExchangePackage`, `AtmExitDefinition`, `PartialExitDefinition`, `PluginNodeRef`, `StrategyArchitecture`, `RandomGroupVersion`, `OppositeMapVersion`, `IndicatorDefinition`, `ExternalIndicatorDefinitionVersion`, `CodeTargetDescriptor`, `CodegenRequest`, `CodegenResult`, `CodeManifest`, and `DeploymentPackage`.

**Capability bundles (13):** `DefineAstCapability`, `CatalogBlocksCapability`, `ConfigureChartsCapability`, `VersionStrategiesCapability`, `EditTemplatesCapability`, `ExchangeStrategiesCapability`, `DefineArchitecturesCapability`, `DefineIndicatorsCapability`, `ModelAtmExitsCapability`, `ExtendPluginNodesCapability`, `GenerateCodeCapability`, `GenerateMql5Capability`, and `GenerateTargetsCapability`.

### 4.5 `app/contracts/simulator/`

**Public records:** `RunManifest`, `EngineProfileVersion`, `PrecisionModel`, `SimulationRequest`, `SimulationRunRef`, `SimulationEvent`, `SimOrder`, `SimFill`, `SimPosition`, `SimTrade`, `SizingDecision`, `CostBreakdown`, `ExitSchedule`, `ResultSegment`, `IndicatorRuntimeSpec`, `SimulationResult`, `ResultCommitReceipt`, `EvaluationCacheKey`, `PerturbationSpec`, `DistributedEvaluationPlan`, `StockpickerSimulationSpec`, `VolumeProfileResult`, and `TpoProfileResult`.

**Capability bundles (12):** `ConfigureEngineCapability`, `ModelPrecisionCapability`, `SimulateOrdersCapability`, `CalculateCostsCapability`, `ManageExitsCapability`, `RunIndicatorsCapability`, `CommitResultsCapability`, `CacheEvaluationsCapability`, `CalculateProfilesCapability`, `PerturbInputsCapability`, `DistributeEvaluationsCapability`, and `SimulateStockpickersCapability`.

### 4.6 `app/contracts/analytics/`

**Public records:** `DatabankRef`, `DatabankVersion`, `DatabankItem`, `DatabankDecision`, `ResultQuery`, `SavedResultView`, `ResultPage`, `MetricDefinition`, `MetricValue`, `ResultComparison`, `ChartSpec`, `TradeAnalysis`, `BenchmarkComparison`, `ResultExchangePackage`, `BulkSelectionToken`, `BulkDatabankCommand`, `AnalysisPanelDescriptor`, `SimilarityQuery`, `SimilarityMatch`, `OperationalJournalArtifact`, `QualificationProfileVersion`, and `OperatorQualification`.

**Capability bundles (9):** `DatabankMembershipCapability`, `QueryResultsCapability`, `InterpretResultsCapability`, `AnalyzeTradesCapability`, `ExchangeResultsCapability`, `BulkDatabankCapability`, `MatchResultsCapability`, `CustomPanelsCapability`, and `QualifyOperationsCapability`.

### 4.7 `app/contracts/research/`

**Public records:** `ResearchRunRef`, `ResearchManifest`, `ResearchStatus`, `RobustnessPlan`, `RobustnessResult`, `ParameterSpace`, `OptimizationPlan`, `OptimizationVariant`, `OptimizationResult`, `WalkForwardPlan`, `WalkForwardWindow`, `WalkForwardResult`, `BuilderPlan`, `StrategyCandidate`, `EvolutionPlan`, `AcceptancePipeline`, `AcceptanceDecision`, `ResearchBudget`, `PromotionDecision`, `StockpickerResearchPlan`, `AiResearchDraft`, `AiImprovementProposal`, `NeuralResearchPlan`, `PortfolioFitnessScore`, `MarketIntelligenceObservation`, `DriftState`, and `DriftReport`.

**Capability bundles (13):** `RunResearchCapability`, `TestRobustnessCapability`, `OptimizeParametersCapability`, `ValidateWalkForwardCapability`, `GenerateStrategiesCapability`, `EvolveStrategiesCapability`, `AcceptResearchCapability`, `GovernResearchBudgetsCapability`, `ResearchStockpickersCapability`, `AssistResearchAiCapability`, `ResearchNeuralModelsCapability`, `ScorePortfolioFitnessCapability`, and `MonitorMarketDriftCapability`.

### 4.8 `app/contracts/portfolio/`

**Public records:** `PortfolioRef`, `PortfolioVersion`, `PortfolioMember`, `Allocation`, `PortfolioConstraintSet`, `CorrelationRequest`, `CorrelationMatrix`, `PortfolioSimulationRequest`, `PortfolioResult`, `PortfolioSearchPlan`, `PortfolioCandidate`, `PortfolioRiskReport`, `PortfolioMetricDefinition`, `MarkowitzOptimizationRequest`, `EfficientFrontier`, `PortfolioMergePlan`, `PortfolioSplitPlan`, and `PortfolioMethodDescriptor`.

**Capability bundles (8):** `ComposePortfoliosCapability`, `AnalyzeCorrelationCapability`, `SimulatePortfoliosCapability`, `SearchPortfoliosCapability`, `AnalyzePortfolioRiskCapability`, `OptimizeMarkowitzCapability`, `MergePortfoliosCapability`, and `ExtendPortfolioMethodsCapability`.

### 4.9 `app/contracts/orchestration/`

**Public records:** `ProjectRef`, `ProjectVersion`, `ProjectGraph`, `TaskDefinition`, `TaskContract`, `TaskState`, `ProjectRunRef`, `TaskRunRef`, `TaskAttemptRef`, `TaskLease`, `TaskCheckpoint`, `TaskOutputCommit`, `ProjectVariable`, `ProjectExpression`, `DomainTaskRequest`, `UtilityTaskRequest`, `ExecutableAllowlistEntry`, `NotificationChannelConfig`, `NotificationTemplate`, `NotificationSession`, `NotificationReceipt`, `ProjectProgress`, `ProjectHistoryEntry`, `NetworkTrainingPlan`, and `NetworkTrainingResult`.

**Capability bundles (7):** `DefineProjectsCapability`, `RunTasksCapability`, `EvaluateConditionsCapability`, `RunDomainTasksCapability`, `RunUtilityTasksCapability`, `TrackRunHistoryCapability`, and `TrainNetworksCapability`.

### 4.10 `app/contracts/interfaces/`

**Public records:** `ApiVersion`, `ConcurrencyToken`, `EventCursor`, `EventReplayBatch`, `AsyncJobRef`, `ArtifactDownloadRequest`, `BulkRequestToken`, `AutomationCommand`, `AutomationSchema`, `McpOperation`, `ResearchPreview`, `ProjectGraphProjection`, `PortfolioBuilderProjection`, `CapabilityAdministrationProjection`, `TradingActionPreview`, and `TradingReadinessProjection`.

**Capability bundles (7):** `ServeApiEventsCapability`, `AutomateCommandsCapability`, `OperateResearchCapability`, `EditProjectsCapability`, `OperatePortfoliosCapability`, `AdministerCapabilitiesCapability`, and `OperateTradingCapability`.

### 4.11 `app/contracts/ui/`

**Public records:** `UiFeatureDescriptor`, `NavigationContribution`, `RouteTarget`, `UiCommandDescriptor`, `KeyboardBinding`, `ViewProjection`, `FieldDescriptor`, `ClientSelection`, `ClientPageState`, `ChartAlternative`, `DraftEnvelope`, `DraftConflict`, `ConfirmationPlan`, `UiNotification`, `ProgressPresentation`, `ErrorPresentation`, `LayoutSnapshot`, `PanelContribution`, `TabContribution`, `ViewPreference`, and `AccessibilityPreference`.

**Capability bundles (17):** one presentation capability for each `FEAT-UI-*` feature registered in `app/ui/README.md`. Generated TypeScript clients consume the corresponding wire schemas; React source never becomes the authoritative contract definition.

### 4.12 `app/contracts/plugins/`

**Public records:** `PluginRef`, `PluginVersion`, `PluginManifest`, `PluginCompatibility`, `PluginPermissionSet`, `PluginActivation`, `PluginLifecycleState`, `PluginContribution`, `PluginAnalysisRequest`, `PluginAnalysisResult`, `ResultPanelDescriptor`, `PluginValidationReport`, and `PluginPackageReceipt`.

**Capability bundles (7):** `DeclareManifestsCapability`, `ManageLifecycleCapability`, `SandboxPermissionsCapability`, `RegisterContributionsCapability`, `IsolateAnalysisCapability`, `RenderResultPanelsCapability`, and `MaintainCompatibilityCapability`.

### 4.13 `app/contracts/broker/`

**Public records:** `BrokerProviderProfile`, `BrokerCapabilityMatrix`, `BrokerEnvironment`, `BrokerSessionRef`, `BrokerSessionState`, `BrokerSessionReadiness`, `BrokerAccountSnapshot`, `BrokerTradingState`, `BrokerMarketState`, `ProviderEvent`, `BrokerOperationRequest`, `BrokerOperationReceipt`, `BrokerOperationOutcome`, `ProviderCorrelation`, `BrokerAdapterCertification`, `BrokerWriteCertification`, and `BrokerHistoryPage`.

**Capability bundles (7):** `DeclareCapabilitiesCapability`, `ConfigureProvidersCapability`, `IsolateEnvironmentsCapability`, `ManageSessionsCapability`, `ReadProviderStateCapability`, `TransportOrdersCapability`, and `CertifyAdaptersCapability`.

### 4.14 `app/contracts/risk/`

**Public records:** `RiskDecisionState`, `RiskProfileRef`, `RiskProfileVersion`, `FirmMandateVersion`, `RiskEvidenceRef`, `RiskSnapshot`, `PositionSizeRecommendation`, `StopLossAssessment`, `ProposedAction`, `RiskDecision`, `NoTradeDecision`, `RiskLimitResult`, `RiskApprovalRequest`, `RiskApprovalToken`, `RiskCapacityReservation`, `KillSwitchScope`, `KillSwitchState`, `KillSwitchTransition`, `StrategyEligibilityDecision`, `PortfolioAllocationReview`, `AllocationBudget`, `RiskScenarioRequest`, `RiskScenarioResult`, and `RiskAuditRecord`.

**Capability bundles (7):** `DefineRiskContractsCapability`, `CalculateRiskCapability`, `ControlKillSwitchCapability`, `GovernAdmissionCapability`, `ManageApprovalsCapability`, `GovernAllocationsCapability`, and `AuditRiskDecisionsCapability`.

### 4.15 `app/contracts/trading/`

**Public records:** `TradingMode`, `TradingSessionRef`, `TradingSession`, `TradingSessionState`, `TradingOperationRef`, `TradingOperation`, `TradingOperationState`, `TradeIntentRef`, `TradePlan`, `TradingReadiness`, `ExecutionAuthorityRef`, `DispatchEvidence`, `DispatchReceipt`, `TradingOrder`, `TradingDeal`, `TradingPositionProjection`, `ReconciliationRequest`, `ReconciliationFinding`, `ProtectionSet`, `ProtectionChange`, `TradingJournalRecord`, `ExecutionProvenance`, `OperationalAccount`, `OperationalLedgerEntry`, `OperationalValuation`, `PublicTradingAction`, `TradingStateQuery`, and `TradingEvent`.

**Capability bundles (8):** `ManageTradingSessionsCapability`, `ValidateTradePlansCapability`, `AccountOperationsCapability`, `DispatchOrdersCapability`, `ReconcileTradingCapability`, `ManageProtectionsCapability`, `JournalExecutionCapability`, and `ExecutePublicActionsCapability`.

## Namespace conventions

```text
app/contracts/<namespace>/
├── __init__.py       # empty or module docstring only; no re-exports
├── capabilities.py   # typed CapabilityKey constants
├── models.py         # public DTOs/value objects
├── ports.py          # public protocols
├── commands.py       # when commands exist
├── queries.py        # when queries exist
├── events.py         # when public events exist
├── errors.py         # stable public failures
└── wire/             # when generated/verified transport schemas exist
```

Provider SDK objects, database rows, and implementation classes stay inside the owning feature. Cross-namespace records import the owner type rather than copy it.

## Incremental conformance

A contract slice is complete only when:

1. Its public names, capability identifiers, ownership, and version semantics match the owning domain README.
2. Its feature uses the same keys in `FeatureSpec.provides`/`requires`/`optional`.
3. Serialization, schema, compatibility, and provider/consumer tests pass where applicable.
4. No duplicate public contract is defined under a service implementation.
5. Contract imports remain independent of composition and services.
6. The owning feature and feature-local README pass the repository's documentation, architecture, lifecycle, and physical-removal gates.

---

## Normative Shared Contract Specification

The stable `§x.y` labels below are preserved for cross-document references. They are authoritative here and no longer identify sections in `docs/PROJECT.md`.

### §4 — Common technical contracts

### §4.1 — Identifiers and serialization

- Domain IDs shall be UUIDv7 values serialized as lowercase canonical strings.
- API JSON property names shall use `snake_case`.
- API timestamps shall use RFC 3339 UTC with a `Z` suffix and microsecond precision where available.
- Arbitrary-precision decimal quantities shall be serialized as strings, never binary JSON numbers.
- Enum values shall be stable uppercase ASCII identifiers; display labels shall be localized separately.
- Persisted schemas and event payloads shall carry an integer `schema_version`.
- Hashes shall use lowercase SHA-256 hexadecimal unless a schema explicitly selects another algorithm.

### §4.2 — Typed quantities

| Type | Shape | Rules |
| --- | --- | --- |
| `DecimalValue` | string | Base-10; no exponent in persisted canonical form; normalized trailing zeros. |
| `Money` | `{amount, currency}` | ISO 4217 currency; explicit conversion required before addition across currencies. |
| `Price` | decimal | Rounded using instrument tick size and declared rounding policy. |
| `Quantity` | decimal | Rounded using order-size step; validated against min/max. |
| `Percentage` | decimal | Stored as a ratio in `[0,1]`; UI may render percent. |
| `Duration` | ISO 8601 duration | Positive unless a field explicitly permits zero. |
| `Timeframe` | `{unit, multiple}` | Unit is `MINUTE`, `DAY`, `WEEK`, or `MONTH`; positive integer multiple. |
| `SeriesPointKey` | `{timestamp, sequence}` | Sequence disambiguates equal tick timestamps. |

### §4.3 — Core enums

| Enum | Values |
| --- | --- |
| Direction | `LONG`, `SHORT`, `BOTH` |
| Side | `BUY`, `SELL` |
| Order type | `MARKET`, `STOP`, `LIMIT`, `STOP_LIMIT` |
| Time in force | `GTC`, `DAY`, `IOC`, `FOK` where supported by the selected engine profile |
| Precision | `SELECTED_TIMEFRAME`, `M1_SIMULATION`, `REAL_TICK_CUSTOM_SPREAD`, `REAL_TICK_RECORDED_SPREAD` |
| Segment | `FULL`, `IS`, `VALIDATION`, `OOS`, `NO_TRADE` |
| P/L unit | `MONEY`, `PERCENT`, `PIPS` |
| Rounding | `DOWN`, `UP`, `HALF_UP`, `HALF_EVEN`, `TOWARD_ZERO` |
| Result state | `STAGED`, `VALIDATING`, `COMMITTED`, `REJECTED`, `CORRUPT` |
| Job state | `QUEUED`, `LEASED`, `RUNNING`, `PAUSING`, `PAUSED`, `RESUMING`, `STOPPING`, `STOPPED`, `COMPLETED`, `FAILED`, `CANCELLED` |
| Feature state | `DISCOVERED`, `DISABLED`, `MISSING`, `BLOCKED`, `PREPARING`, `ACTIVE`, `QUIESCING`, `STOPPING`, `STOPPED`, `FAILED_IMPORT`, `FAILED_CONFIG`, `FAILED_START`, `FAILED_RUNTIME` |
| Replacement outcome | `committed`, `rolled_back`, or committed but `degraded`, as represented by the kernel replacement report |
| Order state | `CREATED`, `ACCEPTED`, `REJECTED`, `PENDING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `EXPIRED` |
| Trading mode | `PAPER`, `DEMO`, `LIVE`; explicit per operational session with no default |
| Trading session state | `CREATED`, `STARTING`, `ACTIVE`, `DEGRADED`, `STOPPING`, `STOPPED`, `ARCHIVED` |
| Trading operation state | `PLANNED`, `ADMITTED`, `DISPATCHING`, `ACCEPTED`, `REJECTED`, `UNKNOWN`, `RECONCILING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `CLOSED`, `FAILED` |
| Runtime Risk decision | `APPROVE`, `WARN`, `NEEDS_APPROVAL`, `NEEDS_MORE_EVIDENCE`, `REJECT`, `BLOCK`, `ERROR` |

### §4.4 — Error contract

All API errors shall use `application/problem+json` with:

```json
{
  "type": "urn:haruquantai:error:validation",
  "title": "Validation failed",
  "status": 422,
  "code": "DATA_TIMEFRAME_UNSUPPORTED",
  "detail": "The selected precision requires M1 or tick source data.",
  "request_id": "0198...",
  "errors": [
    {"path": "precision", "code": "UNSUPPORTED", "message": "...", "context": {}}
  ]
}
```

Error codes are stable. Messages are not used for program logic.

`CAPABILITY_UNAVAILABLE` shall use status `409` when a known operation cannot execute because its required capability is absent/inactive, or `404` when the route/resource itself is no longer contributed and disclosure is not required. Its problem-details extension fields shall contain `capability_key`, `required_version`, `feature_state`, `affected_object_id` where applicable, `missing_dependencies`, and `available_alternatives`. `FEATURE_START_FAILED`, `FEATURE_CLEANUP_FAILED`, `CAPABILITY_DEPENDENCY_CYCLE`, `CAPABILITY_INCOMPATIBLE`, and `FEATURE_EFFECT_LEAK` are likewise stable application error codes when those failures cross an API boundary. None may be translated into an unclassified internal-server error.

### §4.5 — Event contract

Every SSE event shall contain:

```json
{
  "event_id": "0198...",
  "sequence": 42,
  "event_type": "job.progress",
  "schema_version": 1,
  "occurred_at": "2026-08-20T18:30:00.000000Z",
  "request_id": "0198...",
  "project_run_id": null,
  "task_run_id": null,
  "job_id": "0198...",
  "component_instance_id": null,
  "reconciliation_id": null,
  "capability_snapshot_id": "0198...",
  "payload": {}
}
```

Sequences shall be monotonic within a stream scope. Reconnection through `Last-Event-ID` shall not duplicate an externally visible state transition.

Every typed event contract shall declare one dispatch mode:

| Mode | Required semantics |
| --- | --- |
| `PUBLISH` | Deliver an observational fact concurrently to the matching subscriber snapshot; isolate and report handler failures without changing the published fact. |
| `SERIAL` | Invoke matching handlers in deterministic registration order and propagate the first failure. |
| `PARALLEL` | Invoke matching handlers concurrently and propagate the defined aggregate failure outcome. |
| `PIPELINE` | Pass one typed value through handlers in deterministic order; each handler returns the next value and may short-circuit only with the contract's explicit empty/stop result. |

One subscription creates one unique ownership token and one idempotent inverse. Disposing a token removes only that registration, even when the same handler is registered more than once. Dispatch snapshots matching subscriptions before invoking user code and never holds the registry lock while awaiting handlers. Event mode, ordering, retry/replay, and failure-isolation semantics are public compatibility behavior and require a contract-version change when altered incompatibly.

### §5 — Lifecycle specifications

### §5.1 — Job transitions

| From | Command/event | To | Required effect |
| --- | --- | --- | --- |
| `QUEUED` | lease acquired | `LEASED` | Store worker, lease token, and expiry atomically. |
| `LEASED` | worker started | `RUNNING` | Publish start event and begin heartbeat. |
| `RUNNING` | pause requested | `PAUSING` | Stop accepting new work units and write checkpoint. |
| `PAUSING` | checkpoint committed | `PAUSED` | Release compute resources; retain resumable state. |
| `PAUSED` | resume requested | `RESUMING` | Validate checkpoint compatibility and acquire worker. |
| `RESUMING` | worker restored | `RUNNING` | Continue after the last committed unit. |
| `QUEUED/LEASED/RUNNING/PAUSED` | stop requested | `STOPPING` | Prevent new work and request checkpoint/finalization. |
| `STOPPING` | worker stopped | `STOPPED` | Preserve committed outputs and terminal reason. |
| `RUNNING` | all work committed | `COMPLETED` | Commit final manifest and terminal counters. |
| nonterminal | unrecoverable error | `FAILED` | Store classified error; keep committed outputs. |
| nonterminal | cancellation finalized | `CANCELLED` | Store actor/reason and clean staged artifacts. |

Terminal states are immutable. Repeating a command returns the current effective state without a second transition.

### §5.2 — Artifact transitions

| State | Allowed operation |
| --- | --- |
| `STAGED` | Write through a unique temporary name; not visible to domain queries. |
| `VALIDATING` | Verify schema, declared size, checksum, and referential metadata. |
| `COMMITTED` | Rename/publish atomically and create metadata reference in the same logical commit. |
| `REJECTED` | Preserve diagnostic metadata; delete or quarantine payload according to retention settings. |
| `CORRUPT` | Block consumers and require reconstruction/reimport. |

### §5.3 — Order transitions

- An order starts as `CREATED` and becomes `ACCEPTED` or `REJECTED` after validation.
- An accepted market order moves to `FILLED`, `PARTIALLY_FILLED`, or `CANCELLED` at the next eligible execution event according to the engine profile.
- An accepted pending order enters `PENDING` and remains eligible until filled, cancelled, or expired.
- Filled quantity is monotonic and cannot exceed requested quantity.
- Every fill references the order, simulated event, price source, slippage/cost calculation, and reason.
- Position state is derived from fills; no independent position mutation may bypass the order/fill ledger.


### §8 — Typed data dictionary

This dictionary defines the domain shape; §22.2 adds every common physical field, key, uniqueness, audit, and version constraint, and §22.3 defines the complete large-artifact columns. Together they are the complete persistence contract.

| Entity | Principal fields and constraints |
| --- | --- |
| `Workspace` | `id`, `schema_version:int`, `default_timezone:iana`, `settings:json`, `artifact_root`, `created_at`. One active local workspace. |
| `FeatureSpec` | `feature_id`, `domain`, `provides`, `requires`, `optional`, `conflicts`, `description`, optional `StateDeclaration`, and exact `config_keys`. Immutable and validated in code. |
| `FeatureRuntimeStatus` | Feature ID, actual `FeatureState`, stable blocked/failure reason where applicable, and active capability owner/generation evidence exposed by Composition `RuntimeStatus`. It is diagnostic runtime state, not a required database row. |
| `CapabilityKey` | Lowercase capability name plus positive major version, formatted `<name>@<major>`. Provider implementations are held in the in-memory `ServiceRegistry` with owner/generation metadata. |
| `FeatureScope` effect record | Owner feature, effect type, resource name, creation time, cleanup state, and last cleanup error. Records support diagnostics and exact LIFO cleanup; the kernel does not require them to be persisted. |
| `CapabilitySnapshot` | Product record derived from active capability identifiers, provider feature IDs/generations, relevant configuration hashes, and creation/causal evidence. Durable runs reference this application contract when implemented. |
| `ReplacementReport` | Feature ID, committed/rolled-back/degraded outcome, old/new generation evidence, affected consumers, and cleanup/remount diagnostics as exposed by the implemented runtime model. |
| `Project` | `id`, `name:1..160`, `type=MANUAL_RESEARCH`, `state`, `current_version_id`, `notes`, `tags`, `row_version`. Unique normalized name. |
| `ProjectVersion` | `id`, `project_id`, `version:int>0`, `config`, `content_hash`, `created_at`. Immutable. |
| `Job` | `id`, `type`, `state`, `priority`, `idempotency_key`, `lease_token/hash`, `lease_expires_at`, `progress`, `checkpoint_artifact_id`, `error`, timestamps. |
| `Artifact` | `id`, `kind`, `content_hash`, `size>=0`, `media_type`, `schema_version`, `state`, `relative_uri`, `created_at`, `committed_at`. URI contained under artifact root. |
| `InstrumentVersion` | `id`, `instrument_id`, `symbol`, `asset_type`, currencies, `point_value`, `tick_size`, price decimals, quantity constraints, distance, defaults, exchange/timezone, hash. |
| `BrokerProfileVersion` | `id`, stable broker ID, name, timezone, external-symbol mappings, properties, hash. |
| `SessionVersion` | `id`, stable session ID, timezone, ordered intervals, EOD policy, calendar-version ID, hash. |
| `CalendarVersion` | `id`, stable calendar ID, timezone, exceptions, hash. |
| `DataSeries` | `id`, `instrument_id`, broker ID nullable, `timeframe` or tick type, logical timezone, name. |
| `DataSeriesVersion` | `id`, `series_id`, `version`, instrument/session/calendar versions, source artifact, canonical artifact, coverage, row count, precision, import/aggregation policy, findings summary, hash. Immutable. |
| `DataQualityFinding` | `id`, data version, rule code, severity, point/range, observed/expected values, resolution state, derived-version ID nullable. |
| `ExternalIndicatorDefinitionVersion` | stable definition ID/version, value kind, typed ordered output lines, parameters, source platform/version, chart binding defaults, warm-up/shift semantics, target fragments/capabilities, hash. Immutable. |
| `ExternalIndicatorSeriesVersion` | definition version, output-line schema, symbol/timeframe/timezone binding, source artifact/hash, canonical aligned artifact, coverage, alignment/missing policy, synchronization findings, hash. Immutable. |
| `Strategy` | `id`, `name`, status, current-version ID, tags, row version. |
| `StrategyVersion` | `id`, strategy ID, version, architecture style/version, AST artifact/JSON, AST hash, parent-version ID, creation method, dependency manifest, created at. Immutable. |
| `StrategyChart` | strategy version, ordinal, instrument/broker reference, timeframe, role, warm-up bars. Unique ordinal. |
| `BlockDefinition` | stable ID, version, category, input/output types, parameter schema, data/events/target capabilities, status. |
| `RandomGroupVersion` | stable group ID/version, type, ordered weighted block templates, fixed/random parameter policies, applicability, hash. Immutable. |
| `OppositeBlockMapVersion` | stable map ID/version, source block/relation, opposite action (`MAP`, `PRESERVE`, `REJECT`), target block/relation nullable, parameter transform, hash. Immutable. |
| `EngineProfileVersion` | stable profile ID/version, target runtime/version range, evaluation/activation timing, order/position model, path/gap/collision/session/rounding/cost policies, capability matrix, hash. Immutable. |
| `SimulationSettings` | schema version, engine profile, charts/data/external-indicator versions, date range, segments, precision, path/gap policies, costs, sizing, exits/ATM, sessions/calendars, currency, seed set, chart-trace retention. Immutable inside manifest. |
| `RunManifest` | ID, job ID, capability-snapshot ID/hash plus ordered behavior provider/version/implementation hashes, all input/version hashes, environment, seed set, output artifact IDs, state, hash. Immutable after commit. |
| `Result` | ID, strategy version, manifest, state, completion, summary, order/trade/equity/diagnostic artifacts, created/committed times. |
| `ResultSegment` | result, segment enum, `[from,to)` UTC interval, entry/exit policy. Nonoverlapping except `FULL`. |
| `Order` | ID, result, stable entry identity, parent/order group, target identity/Magic Number nullable, symbol, type, side, requested size/prices, protection ownership, activation/expiry, state, filled size, rejection/cancel reason. |
| `Fill` | ID, order, sequence, timestamp, side, size, base/final price, spread/slippage/cost components, source event ID. |
| `Position` | ID, result, symbol, direction, open/close times, max/current size, state, realized/unrealized P/L. Derived from fills. |
| `Trade` | ID, result, position, segment, direction, size, open/close prices/times, gross P/L, each cost, net P/L, pips, close reason, MAE/MFE nullable. |
| `EquitySeries` | result, kind `BALANCE` or `EQUITY`, currency, resolution, artifact ID, count, coverage, hash. |
| `ChartTraceArtifact` | result, data/indicator versions, retained interval, bars, indicator lines, signals, orders/fills/protection events, size/retention policy, hash. Immutable. |
| `BenchmarkComparison` | result, benchmark data/version, holding/allocation method, eligible interval, original/normalized capital, normalization method/version, aligned equity, metric versions, hash. Immutable. |
| `TradeAnalysisArtifact` | result, event basis, timezone, grouping dimension, segment/direction, metric versions, bucket artifact/hash. Immutable. |
| `MetricDefinition` | stable metric ID, version, formula reference, input series, unit, scope, rounding, annualization, minimum sample, null policy. |
| `MetricValue` | result, segment, direction, metric definition, decimal value nullable, null reason nullable. Unique composite key. |
| `Databank` | ID, project, name, capacity nullable, insertion policy, view ID, row version. |
| `DatabankItem` | databank, strategy version, result nullable, accepted at, source, rank/fitness nullable. Unique strategy/result membership. |
| `GeneratedCodeArtifact` | ID, strategy version, target/version, emitter version, source artifact, source hash, compile status/artifacts/diagnostics, parity report ID. |
| `ResearchRun` | ID, method/version, manifest, state, budgets, counters, checkpoint, accepted/rejected outputs, summary artifacts, timestamps. |
| `Simulation` | robustness run ID, ordinal, method/version, seed-stream references, sampled perturbations, result ID or failure, summary membership. |
| `OptimizationVariant` | optimization run ID, canonical parameter vector/hash, result ID, objective values, feasibility, rank/Pareto status. |
| `WalkForwardWindow` | run ID, ordinal, training/selection interval, IS metrics/result references, OOS interval, selected variant, OOS result, eligible-day counts, stitch policy. |
| `DatabankDecision` | databank ID, candidate identity, stage/rule version, observed values, outcome, replacement/duplicate identity, timestamp. |
| `PortfolioVersion` | portfolio ID/version, constituent versions, weights/sizing, capital, currency/alignment/missing-data/overlap policies, constraints, hash. |
| `CorrelationMatrix` | ID, candidate-set hash, method/version, sampling/alignment/overlap policy, observation counts, matrix artifact/hash. |
| `PortfolioResult` | portfolio version, manifest, aggregate result artifacts, constituent attribution, exposure/constraint artifacts, daily-return series, risk-free/confidence/horizon/risk-method inputs, metrics. |
| `PortfolioOptimizationArtifact` | method/version, candidate-set hash, daily-return/covariance inputs, constraints, budget/seeds, evaluated weights, efficient frontier, maximum-Sharpe/minimum-risk selections, metrics, hash. Immutable. |
| `ProjectDefinitionVersion` | project ID/version, typed task instances, transitions, bounds, inputs, referenced versions, content hash. |
| `TaskRun` | project run, task instance, logical state, attempt IDs, resolved inputs, outputs, checkpoint, progress, failure/cancellation record. |
| `WorkerLease` | job/attempt, worker ID, capability/build identity, fencing token, acquired/heartbeat/expiry timestamps, state. |
| `PluginVersion` | plugin ID/version, API range, type, manifest/package hashes, schemas, capabilities, permissions, runtime, state. |
| `TargetDeploymentPackage` | code-generation ID, target/version, engine profile, strategy source/binary, dependency artifacts, installation manifest, checksums, validation result, hash. Immutable. |
| `ConnectorSyncPlan` | connector/version, canonical mappings, requested range, overlap, revision/dedup policies, cursor/checkpoint, limits. |
| `AIProposal` | proposal ID, adapter/model/config identity, redacted input hash, proposed AST/edit artifact, validation, approval state; never executable by itself. |


### §21.6 — Connector and distributed-worker protocols

A connector exposes `DESCRIBE`, `TEST`, `LIST_INSTRUMENTS`, `PLAN`, and paged `FETCH`. A page has cursor, inclusive requested range, records, provider revision IDs, next cursor, completeness flag, and checksum. Sync writes to staging, normalizes using §§15–16, resolves duplicates by `(timestamp,source_sequence)` with explicit `KEEP_FIRST|KEEP_LAST|REJECT`, compares overlap revisions, and publishes a new immutable version only after complete range and quality validation. Credentials are opaque secret IDs and never enter manifests/logs.

A worker registers build hash, OS/architecture, CPU/memory, supported task/profile/plugin versions, and artifact-locality hashes. Lease fields are job/attempt, worker, monotonically increasing fencing token, expiry, heartbeat interval, and scoped artifact credentials. A commit is accepted only for the current token, before expiry, with manifest/output hashes. Scheduler choice is capability first, then locality score, available resources, current load, and worker ID. Assignment cannot change seeds or canonical output.

The following recovered universal labels complete the shared representation, conformance, resolution, and serialization authority.

### §2 — Normative conventions

- **Shall** identifies a mandatory requirement.
- **Should** identifies a preferred requirement that may be waived through an explicit architecture decision.
- **May** identifies optional behavior.
- `Parity` requirements must match verified reference fixtures within the specified tolerance.
- `Target` requirements intentionally define improved or previously unspecified behavior.
- `Adapter` requirements apply at a file, tool, or platform boundary.
- `Experimental` requirements are disabled by default and cannot be dependencies of stable workflows.
- Priorities are `P0` release-blocking, `P1` required for the release, and `P2` deferrable without breaking the core loop.
- Source/confidence text records provenance only. Every requirement is normative as written regardless of whether its source was verified, inferred, partial, or previously open.
- Feature identifiers use `FEAT-<DOMAIN>-<ACTION_OBJECT>` and functional-requirement identifiers use `FR-<DOMAIN>-<ACTION_OBJECT>`, for example `FEAT-DATA-INGEST_HISTORY` and `FR-DATA-PREVIEW_DATA_COVERAGE`.
- The descriptive suffix shall contain two words where practical and no more than three uppercase words joined by underscores. It shall begin with a concise action and describe the behavior without requiring an ordinal lookup.
- Every complete Feature and functional-requirement identifier shall be globally unique. Numeric ordinal suffixes and abbreviated numeric aliases are forbidden; every reference shall use the complete descriptive identifier.
- `FR-KERN-*` requirements are Phase 0 and constrain every later phase. A business requirement is Phase 1 unless its statement, feature description, dependency, or release gate explicitly assigns it to Phase 2, 3, or 4; a later-phase assignment wins over this default.
- Domain, feature, responsibility, and requirement-behavior identifiers in §6 are stable architecture identifiers. Renaming a display label or moving a file does not change the identifier; changing ownership or observable behavior requires an explicit migration and compatibility record.
- A compact table row is the normative requirement record. Its statement supplies behavior and persisted effect; its acceptance/failure cell supplies observable acceptance and required failure behavior. Sections 15–23 in this file contain the complete schemas, catalogues, algorithms, platform matrices, and executable fixture definitions needed to implement those rows.

No supported behavior may depend on an unspecified or external decision. If a legacy/reference behavior is unknown or contradictory, the explicit target behavior in §§15–23 prevails. Anything not enumerated in this SRS is unsupported and shall fail capability validation rather than be guessed.


### §12 — Verification fixture catalogue

Release implementation shall not begin engine feature expansion without these fixture families.

| Fixture family | Minimum coverage |
| --- | --- |
| Composition | Cold/live deletion and reinstall of every domain, feature, responsibility, and behavior; provider replacement; required/optional dependency changes; isolation realms; dependency cycles; partial activation; LIFO/idempotent disposal; async transition inertia; HMR rollback; effect/resource leak audit; retained opaque data. |
| Time/session | UTC, positive/negative offsets, DST spring gap/fall overlap, overnight session, weekend, holiday, early close. |
| Bars | Bull, bear, doji, gap up/down, equal OHLC, missing bar, duplicate source row, session boundary. |
| Ticks | Bid-only/custom spread, recorded bid/ask, duplicate timestamp sequence, variable spread, gap tick. |
| Multi-chart | M1/H1, H1/D1, two symbols, simultaneous closes, missing secondary bar, warm-up boundary. |
| Orders | Market, stop, limit, stop-limit, cancellation, expiry, partial fill model where enabled, opposite-side action. |
| Exits | Stop, target, collision, trailing activation/update, breakeven, bars exit, rule exit, EOD, Friday. |
| Engine profiles | MT5 evaluation/activation/order semantics in Phase 1; MT4, TradeStation, and MultiCharts profile differences with target-runtime differential results before Phase 3 advertisement. |
| Strategy architectures | Classic rules, signal-gated truth-table conflicts, weighted/unweighted fuzzy thresholds and ties, custom templates, opposite-block mappings. |
| External indicators | All four value kinds, multiple lines, fixed/random parameters, symbol/timeframe bindings, gaps, alignment, shift/look-ahead sentinels, target fragments. |
| Costs | Fixed/custom spread, slippage, per-trade, size-based, turnover commission, daily/triple swap, conversion. |
| Sizing | Fixed, fixed amount, percent balance/equity, risk by stop, min/max/step/rounding boundaries. |
| Segments | IS/validation/OOS/no-trade exact boundary events and open-position transitions. |
| Metrics | No trades, all winners, all losers, breakeven, zero loss, zero drawdown, nonpositive equity, sparse daily equity. |
| Durability | Kill before/after every metadata/artifact/checkpoint commit; disk full; corrupt staged/committed payload; expired lease. |
| MQL5 | One minimal strategy per supported block/action plus composed strategies exercising costs, sessions, multi-chart, exits, same-direction entry identities/Magic Numbers, support packages, and external indicators. |

Phase 2–4 extend the catalogue with:

| Fixture family | Minimum coverage |
| --- | --- |
| Search | Random grammar/property corpus, typed Random Groups and precedence, strict/reference-relaxed genetic behavior, semantic and result-fingerprint duplicates, finite/grid domains, genetic island migration, every checkpoint boundary, budget exhaustion. |
| Robustness | Zero perturbation, seeded trade manipulation, parameter/data/cost perturbations, percentile calculations, stop-first/evaluate-all pipelines. |
| Walk-forward | Anchored/rolling unequal-duration windows, boundary positions, selection-only data visibility, stitching, matrix ranking, failed cells, stability/score/OOS-IS ratios, run extrema, stagnation, minimum trades, profitable-run percentage. |
| Databanks/results | Concurrent admission, capacity ties, semantic/result-fingerprint duplicate and replacement policies, pinned bulk selections, formula types/nulls/cycles, correlation filters, benchmark normalization, temporal trade buckets, retained chart overlays. |
| Portfolio | Asynchronous constituents, missing overlap, currency triangulation, rebalance costs, overlapping instruments, exposure limits, candidate-plus-existing-portfolio fitness, Markowitz covariance/frontier, VaR/CVaR/risk-free objectives, merge/split, infeasible search, Pareto ties. |
| Orchestration | Every lifecycle transition, bounded loops, all stable task types, lease loss, stale commit, retry, pause/resume, checkpoint incompatibility, restart. |
| Plugins | Manifest/package corruption, API incompatibility, permission denial, timeout/crash, schema failure, panel sandbox, upgrade/rollback. |
| Distributed | Local/remote equivalence, reassignment, duplicate completion, partition, credential expiry/replay, corrupt/resumed artifact transfer. |
| Specialized | Historical-universe membership, all Stockpicker evaluation timings and shift-0 visibility, daily-OHLC ambiguity/protection rules, rotation/rebalance, Volume Profile/TPO independent calculations, AI-invalid proposals, neural-task disabled state. |


### §15 — Normative implementation constants and resolution rules

This section closes all cross-cutting implementation choices. The words “reference”, “parity”, “source”, and hyperlinks elsewhere in this document identify provenance only. They do not delegate behavior outside this SRS.

### §15.1 — Resolution order

When two statements appear to conflict, the implementation shall apply this order:

1. an explicit field/value or algorithm in §§15–23;
2. a functional requirement in §6;
3. a lifecycle contract in §5;
4. the typed data dictionary in §8;
5. a general convention in §§2–4;
6. provenance/source text, which is nonnormative.

Within the same level, the more specific rule wins. A versioned run manifest value wins over a workspace default. No implicit fallback is permitted unless this SRS names it.

### §15.2 — Canonical representation

- All external JSON is UTF-8 without BOM and rejects duplicate object keys, invalid Unicode scalar values, `NaN`, positive/negative infinity, and numbers outside the declared field domain.
- Canonical JSON sorts object keys by Unicode code point, preserves array order, emits no insignificant whitespace, emits `true`, `false`, and `null` in lowercase, and writes decimal values as normalized base-10 strings without exponent notation. Zero is `0`; negative zero normalizes to `0`; trailing fractional zeros are removed.
- Domain decimals are transported as JSON strings matching `^-?(0|[1-9][0-9]*)(\.[0-9]+)?$`. Counts, ordinals, schema versions, and safe bounded integers are JSON numbers.
- Content identity is lowercase hexadecimal `SHA-256(canonical_bytes)`. Artifact identity includes media type and schema version: `SHA-256(schema_version || 0x00 || media_type || 0x00 || payload)`.
- UUIDs are lowercase RFC 4122 strings. New domain IDs use UUIDv7; deterministic fixture IDs use UUIDv5 under namespace `5a4f0954-1a9c-5c3e-8f35-bc57dc0df11a` and the fixture's canonical name.
- Timestamps are UTC RFC 3339 with exactly six fractional digits and suffix `Z`. Intervals are half-open `[from,to)` unless a field explicitly says otherwise.
- Enumerations are uppercase ASCII snake case. Unknown enum values are rejected on writes; newer unknown values may be preserved only when an object is opened read-only.
- Every persisted versioned object contains `schema_version`, `id`, `version`, `created_at`, `content_hash`, and an immutable canonical payload. Mutable heads contain `row_version` incremented by exactly one per successful mutation.

### §15.3 — Numeric model

- Prices, quantities, money, rates, percentages, and metric accumulators use decimal arithmetic, never binary floating point, at domain boundaries and in canonical artifacts.
- Internal indicator kernels may use IEEE-754 binary64 only when deterministic mode fixes operation order, disables fused/nonportable reductions, canonicalizes negative zero, and converts outputs to decimal strings using round-half-even at 15 significant decimal digits.
- Price normalization uses `tick_size`; quantity normalization uses `size_step`. Order quantities round toward zero to the nearest step so risk is never increased. Price rounding uses round-half-even except stop-distance enforcement, which rounds away from the market, and limit-price enforcement, which rounds toward the market.
- Currency values use the instrument/result currency minor-unit scale; unknown currencies default to scale 2 only if the run manifest explicitly selects `UNKNOWN_CURRENCY_SCALE_2`, otherwise admission fails.
- Comparisons use exact normalized decimal values. A user-configured tolerance is applied only by an explicitly tolerant operator or a parity assertion.
- Division by zero, invalid logarithm/root, overflow, or insufficient lookback yields typed `NULL` with a reason code; it never yields infinity or silently coerces to zero.

### §15.4 — Time, calendar, and bar conventions

- Stored event time is UTC. Human schedules are interpreted in their pinned IANA timezone and converted using the timezone-database version recorded in the manifest.
- A nonexistent DST local time advances to the first valid instant. An ambiguous repeated local time uses the earlier offset for session open and the later offset for session close, ensuring the full repeated interval is included.
- A bar is keyed by its opening instant and represents `[open_time, close_time)`. Daily/weekly/monthly bars open at the effective session boundary, not UTC midnight, unless the instrument explicitly uses a 24-hour UTC session.
- OHLC aggregation is `open=first`, `high=max`, `low=min`, `close=last`, `volume=sum`; bid/ask volume and trade count are summed separately. An empty bucket is absent; synthetic gap bars are never created by default.
- `day_of_week` is ISO Monday=1 through Sunday=7. `day_of_month` is 1–31. Week one begins Monday. Month/week/session attributes are evaluated in the session timezone.
- A chart shift is a nonnegative integer. At a bar-open strategy event, shift `0` exposes the new bar's open and timestamp only; high, low, close, and final volume at shift `0` are `NULL_NOT_CLOSED`. Shift `1` is the immediately preceding closed bar. Tick-event profiles expose the current bid/ask/last and current forming-bar OHLC accumulated only through that tick.

### §15.5 — Randomness

- Unsigned arithmetic wraps modulo `2^64` or `2^128` as indicated. For stream name `N`, root seed is exactly 16-byte big-endian `R`. `initstate` is the first 16 bytes, interpreted big-endian, of `SHA-256(R || 0x00 || UTF8(N))`; `initseq` uses `0x01` instead. Set `inc=(2*initseq+1) mod 2^128`; set state=0; perform one transition; add `initstate` modulo `2^128`; perform one transition. This is the initialized PCG64-DXSM stream.
- One draw reads pre-transition state `S`. Let `hi=(S>>64) mod 2^64`, `lo=S mod 2^64`, `lo=lo OR 1`, then `hi=hi XOR (hi>>32)`, `hi=(hi*0xda942042e4dd58b5) mod 2^64`, `hi=hi XOR (hi>>48)`, and output `(hi*lo) mod 2^64`. After computing the output, transition state to `(S*0xda942042e4dd58b5 + inc) mod 2^128`. Draw count increments once.
- For a positive bound `b<=2^64`, bounded integer computes `threshold=((2^64-b) mod b)`, draws `r` until `r>=threshold`, and returns `r mod b`. A binary64 uniform `[0,1)` is `(r>>11)/2^53`. A uniform open `(0,1)` for logarithms is `(r+0.5)/2^64` evaluated in binary64. Weighted choice requires finite nonnegative binary64 weights with a positive sum, draws `u=[0,1)*sum`, and chooses the first cumulative sum strictly greater than `u`, falling back to the final positive-weight item only for roundoff. Shuffle is Fisher–Yates for `i=n-1..1`, swapping i with bounded integer `[0,i]`.
- Standard normal uses noncached Box–Muller: draw open uniforms `u1,u2`, return `sqrt(-2*ln(u1))*cos(2*pi*u2)` and discard the sine variate. Uniform `[a,b]` is `a+(b-a)u`; triangular `(a,mode,b)` uses inverse CDF; Bernoulli(p) is `u<p`. These operations consume exactly the draws stated, even at p=0 or p=1.
- Stream names are lowercase ASCII path segments and include method/ordinal, for example `builder/grammar`, `builder/params`, `genetic/island/3/mutation`, and `mc/simulation/42/spread`. Adding a random feature requires a new name and cannot consume an existing stream. Checkpoints persist name, state, increment, and draw count.

### §15.6 — Default/failure rule

- Every optional field has an explicit default in this SRS or the relevant schema. Absence and explicit `null` are distinct; `null` is allowed only where the schema says nullable.
- Validation returns all independent errors ordered by JSON pointer, then code. No domain mutation or queued job is created after validation failure.
- Unsupported combinations return `CAPABILITY_UNSUPPORTED` with target/profile, feature, responsible AST node or field, and supported alternatives. The implementation shall never remove a node, reduce precision, change an engine profile, or substitute a metric silently.
- Experimental capabilities are fully specified but disabled by default. Enabling them requires only the feature flag and release gate stated here; it never requires another document.

### §15.7 — Operational and safety defaults

Any configurable field not assigned a default elsewhere is required. Desktop defaults are: worker count `max(1,logical_cpu_count-1)` capped at 8; one thread per deterministic Simulator worker; 4 GiB memory and 10 GiB temporary disk per core worker; 1 GiB memory, one CPU core, 60-second call deadline, 64 MiB combined output, and no network for plugins/scripts/compilers unless their manifest grants narrower values; job event retention 7 days; checkpoint interval 5 minutes or 10,000 evaluated candidates, whichever occurs first; graceful cancellation deadline 30 seconds then termination.

One uploaded/archive file is limited to 20 GiB compressed, 50 GiB expanded, 100,000 members, 1 GiB per member unless the endpoint explicitly accepts a larger data artifact, nesting depth 2, and expansion ratio 100:1. Violations reject before extraction/commit. API request JSON is limited to 16 MiB, header block 64 KiB, request duration 30 seconds excluding job execution, and query result 500 rows/16 MiB before pagination/artifact export. Logs rotate at 64 MiB per file and retain 10 files per process; audit retention follows §22.7 instead. Operators may lower these values; raising them is a versioned workspace setting recorded in affected manifests.


### §23.1 — Canonical serialization and RNG

Canonicalizing an object inserted in order `b`, then `a`, with value `b=[true,"x"]`, `a=1.0`, must yield the 24 UTF-8 bytes `{"a":1,"b":[true,"x"]}` and SHA-256 `63e8063d9dc6f0fd5a24b4706818a165fd57c3531b74466cf5dea62bff09b0b6`. Inputs containing duplicate `a` keys, NaN, Infinity, `-0`, or an unpaired surrogate are rejected.

For root seed 0 encoded as 16 zero bytes and stream `test`, §15.5 must produce:

| Item | Exact hexadecimal value |
| --- | --- |
| initstate | `f5397289d0c71e5cdadf5e5ab6e20b3e` |
| initseq | `1f47db956634ad68a3042b314a427d99` |
| increment | `3e8fb72acc695ad1460856629484fb33` |
| outputs 0..4 | `d22bee78b4bb12c1`, `ee8b7aac53250638`, `b9afff6af3282687`, `4f338865396249e4`, `5d353a3fd1607294` |

Their unsigned decimals are respectively `15144460374159069889`, `17188967283337528888`, `13380193852752144007`, `5707055121144367588`, and `6716338465063072404`. Saving after draw 2, restoring, and drawing three values must reproduce outputs 2..4 exactly. Drawing another named stream cannot alter these values.


### §23.12 — Persistence, API, failure, and recovery

Submitting the same backtest request twice with the same idempotency key/body returns the same job ID/status/body and creates one job. Reusing the key with one changed setting returns 409 `IDEMPOTENCY_CONFLICT`. Updating row version 4 with `If-Match:"3"` returns 412/`VERSION_CONFLICT` and leaves the row unchanged. A list cursor reused after changing its filter returns 422. An SSE reconnect at the last received sequence emits only later sequences.

Fault injection after artifact staging, after blob rename, before database commit, and after database commit must yield respectively: no committed reference; orphan blob later quarantined; orphan blob later quarantined; and one valid committed artifact. Replaying the command never creates a second logical result. A worker with fencing token 7 cannot commit after token 8 is issued. A checkpoint with one changed input hash is rejected `CHECKPOINT_INCOMPATIBLE`.
