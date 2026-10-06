# SQX reimplementation V2: a simpler Python web workstation

Version 2 proposal, 2026-10-07. Documentation delivered under an approved plan;
application implementation and architectural adoption require their own plans.

Build the research workflows people use in SQX, with a small Python host and the
existing React frontend. Organize work by product capability. Treat the JAR audit
as a source of behavioral evidence and compatibility requirements.

## The system in 13 feature groups

| ID | Feature | What the user can do |
| --- | --- | --- |
| F01 | Platform and web shell | Start the app, configure it, inspect health/logs and manage capabilities/jobs/resources |
| F02 | Market data | Import/download, inspect and manage instruments, sessions and datasets |
| F03 | Strategies and authoring | Use blocks or code, test indicators, save strategies and export platform code |
| F04 | Simulation | Backtest with explicit execution, costs, sizing and accounting |
| F05 | Results and reporting | Manage databanks, compare results, inspect trades/charts and export reports |
| F06 | Strategy generation | Generate/improve candidates and rank them in Builder |
| F07 | Optimization and validation | Optimize parameters, walk forward and challenge robustness in Retester |
| F08 | Portfolios | Compose, compare and search portfolios |
| F09 | Research projects | Run reusable, bounded research workflows and task conditions |
| F10 | Compute | Scale the same jobs across local processes and remote workers |
| F11 | Neural models | Train, evaluate, retain and use models |
| F12 | Connections and ecosystem | Connect terminals, MCP/business services, AlgoCloud and Marketplace |
| F13 | AI research assistant | Use chat, memory and procedures to orchestrate approved research tools |

F01 contains **10 host capabilities**: bootstrap, centralized logging, diagnostics,
settings, discovery, transport, jobs, resources, persistence and security/sessions.
These are components of one host. F02-F13 are product groups; their indicators,
providers and methods remain locally owned capabilities rather than giant modules.

## What becomes simpler

| Existing planning unit | V2 implementation unit |
| --- | --- |
| Separate SLF4J, Logback, Commons/JBoss logging and telemetry tasks | One explicit Python logging setup, correlation fields and bounded sinks |
| Multiple JSON/reflection/schema library tasks | Domain-owned Pydantic models and validated versioned documents |
| Java utility collections, bytecode, runtime and annotation tasks | Python primitives and tooling; explicit JVM-only dispositions |
| Separate server/reactive/plugin-framework replicas | One FastAPI host, HTTP/event transport and a small manifest loader |
| Independent task/settings/UI wrappers around one operation | One method with its schema, job adapter and connected view |
| Distributed machinery before a useful workstation | Local research first; remote workers reuse its job contract |

The original P01/P02 files contain **75 tasks**, including **72 JAR allocations**.
V2 replaces that library-oriented foundation with ten host capabilities. Across
the whole product, 366 old tasks map into 13 groups and shared qualification gates.
This reduces duplicated implementation and planning; it does not make all trading
algorithms, file formats or provider protocols trivial.

## Implementation tracker and detailed phases

Use the [72-task implementation checklist](implementation_checklist.md) for application progress.
Each of the thirteen linked phase files contains objective, donor research, proposed
files, concrete steps and independent/connected acceptance. Named variants remain
inside their owning task matrices. Initial status is 0/72; documentation is not
application completion. The nine delivery milestones still guide execution order.

| Phase | Detailed implementation | Tasks |
| --- | --- | ---: |
| 1 | [Platform and web shell](phase-01-platform-host.md) | 10 |
| 2 | [Market data](phase-02-market-data.md) | 8 |
| 3 | [Strategies and authoring](phase-03-strategies-authoring.md) | 8 |
| 4 | [Simulation](phase-04-simulation-engine.md) | 7 |
| 5 | [Results and reporting](phase-05-results-reporting.md) | 5 |
| 6 | [Strategy generation](phase-06-strategy-generation.md) | 4 |
| 7 | [Optimization and validation](phase-07-optimization-validation.md) | 7 |
| 8 | [Portfolios](phase-08-portfolios.md) | 4 |
| 9 | [Research projects](phase-09-research-projects.md) | 4 |
| 10 | [Compute](phase-10-compute.md) | 3 |
| 11 | [Neural models](phase-11-neural-models.md) | 3 |
| 12 | [Connections and ecosystem](phase-12-connections-ecosystem.md) | 5 |
| 13 | [AI research assistant](phase-13-ai-research-assistant.md) | 4 |

## Full V2 planned file structure

This tree consolidates every concrete file path named in all thirteen phase plans,
their owning README files, the existing shared UI host and the V2 planning documents.
`existing` marks retained files; `proposed` marks future implementation targets.
It is a planning view, not a claim that the Python application has been built.
The rest of the retained frontend remains in place; this tree shows its phase-named
entry points rather than every existing component, asset and fixture.

```text
HaruQuantAI/
├── app/
│   ├── host/
│   │   ├── archives.py  # proposed
│   │   ├── attachments.py  # proposed
│   │   ├── bootstrap.py  # proposed
│   │   ├── diagnostics.py  # proposed
│   │   ├── discovery.py  # proposed
│   │   ├── events.py  # proposed
│   │   ├── jobs.py  # proposed
│   │   ├── log_projection.py  # proposed
│   │   ├── logging.py  # proposed
│   │   ├── persistence.py  # proposed
│   │   ├── preferences.py  # proposed
│   │   ├── readiness.py  # proposed
│   │   ├── README.md  # existing
│   │   ├── repositories.py  # proposed
│   │   ├── resources.py  # proposed
│   │   ├── security.py  # proposed
│   │   ├── sessions.py  # proposed
│   │   ├── settings.py  # proposed
│   │   ├── transport.py  # proposed
│   │   └── workers.py  # proposed
│   ├── plugins/
│   │   ├── agentic/
│   │   │   ├── completion.py  # proposed
│   │   │   ├── contributions.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── memory.py  # proposed
│   │   │   ├── orchestration.py  # proposed
│   │   │   ├── procedures.py  # proposed
│   │   │   ├── providers.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   ├── schedules.py  # proposed
│   │   │   ├── sessions.py  # proposed
│   │   │   └── tools.py  # proposed
│   │   ├── analytics/
│   │   │   ├── charts.py  # proposed
│   │   │   ├── databanks.py  # proposed
│   │   │   ├── exporters.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── metrics.py  # proposed
│   │   │   ├── projections.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   └── reports.py  # proposed
│   │   ├── data/
│   │   │   ├── baskets.py  # proposed
│   │   │   ├── catalog.py  # proposed
│   │   │   ├── cot.py  # proposed
│   │   │   ├── custom_data.py  # proposed
│   │   │   ├── ingestion.py  # proposed
│   │   │   ├── instruments.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── providers.py  # proposed
│   │   │   ├── quality.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   ├── sessions.py  # proposed
│   │   │   └── transforms.py  # proposed
│   │   ├── gateway/
│   │   │   ├── algocloud.py  # proposed
│   │   │   ├── business.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── marketplace.py  # proposed
│   │   │   ├── mcp.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   ├── terminals.py  # proposed
│   │   │   └── trading_authority.py  # proposed
│   │   ├── indicators/
│   │   │   └── impl/
│   │   │       ├── cot.py  # proposed
│   │   │       └── profiles.py  # proposed
│   │   ├── optimization/
│   │   │   ├── chains.py  # proposed
│   │   │   ├── experiments.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── monte_carlo_retest.py  # proposed
│   │   │   ├── monte_carlo_trades.py  # proposed
│   │   │   ├── parameter_search.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   ├── retest_scenarios.py  # proposed
│   │   │   ├── search_methods.py  # proposed
│   │   │   └── walk_forward.py  # proposed
│   │   ├── portfolio/
│   │   │   ├── documents.py  # proposed
│   │   │   ├── evaluation.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   └── search.py  # proposed
│   │   ├── research/
│   │   │   ├── compute/
│   │   │   │   ├── integration.py  # proposed
│   │   │   │   ├── local_capacity.py  # proposed
│   │   │   │   ├── protocol.py  # proposed
│   │   │   │   ├── README.md  # proposed owner README
│   │   │   │   └── workers.py  # proposed
│   │   │   ├── generation/
│   │   │   │   ├── fitness.py  # proposed
│   │   │   │   ├── genetic.py  # proposed
│   │   │   │   ├── integration.py  # proposed
│   │   │   │   ├── random_search.py  # proposed
│   │   │   │   └── README.md  # proposed owner README
│   │   │   ├── neural/
│   │   │   │   ├── inference.py  # proposed
│   │   │   │   ├── models.py  # proposed
│   │   │   │   ├── README.md  # proposed owner README
│   │   │   │   ├── training_data.py  # proposed
│   │   │   │   └── training.py  # proposed
│   │   │   └── projects/
│   │   │       ├── conditions.py  # proposed
│   │   │       ├── documents.py  # proposed
│   │   │       ├── integration.py  # proposed
│   │   │       ├── mass_configuration.py  # proposed
│   │   │       ├── README.md  # proposed owner README
│   │   │       ├── runner.py  # proposed
│   │   │       ├── task_adapters.py  # proposed
│   │   │       └── utility_tasks.py  # proposed
│   │   ├── simulator/
│   │   │   ├── accounting.py  # proposed
│   │   │   ├── alignment.py  # proposed
│   │   │   ├── cache.py  # proposed
│   │   │   ├── engine.py  # proposed
│   │   │   ├── execution.py  # proposed
│   │   │   ├── integration.py  # proposed
│   │   │   ├── management.py  # proposed
│   │   │   ├── orders.py  # proposed
│   │   │   ├── README.md  # proposed owner README
│   │   │   ├── run_jobs.py  # proposed
│   │   │   ├── sizing.py  # proposed
│   │   │   ├── specifications.py  # proposed
│   │   │   └── stock_selection.py  # proposed
│   │   └── strategy/
│   │       ├── blocks.py  # proposed
│   │       ├── code_editor.py  # proposed
│   │       ├── documents.py  # proposed
│   │       ├── exporters.py  # proposed
│   │       ├── formats.py  # proposed
│   │       ├── indicator_catalog.py  # proposed
│   │       ├── indicator_testing.py  # proposed
│   │       ├── integration.py  # proposed
│   │       ├── README.md  # proposed owner README
│   │       ├── strategy_store.py  # proposed
│   │       └── wizard.py  # proposed
│   └── workspace/
│       └── <workspace>/  # proposed composition; exact files TBD
├── docs/
│   └── dev/
│       └── V2/
│           ├── architecture.md  # existing plan
│           ├── coverage-map.md  # existing plan
│           ├── delivery-plan.md  # existing plan
│           ├── host-foundation.md  # existing plan
│           ├── implementation_checklist.md  # existing plan
│           ├── legacy-task-map.csv  # existing plan
│           ├── phase-01-platform-host.md  # existing plan
│           ├── phase-02-market-data.md  # existing plan
│           ├── phase-03-strategies-authoring.md  # existing plan
│           ├── phase-04-simulation-engine.md  # existing plan
│           ├── phase-05-results-reporting.md  # existing plan
│           ├── phase-06-strategy-generation.md  # existing plan
│           ├── phase-07-optimization-validation.md  # existing plan
│           ├── phase-08-portfolios.md  # existing plan
│           ├── phase-09-research-projects.md  # existing plan
│           ├── phase-10-compute.md  # existing plan
│           ├── phase-11-neural-models.md  # existing plan
│           ├── phase-12-connections-ecosystem.md  # existing plan
│           ├── phase-13-ai-research-assistant.md  # existing plan
│           ├── product-features.md  # existing plan
│           └── README.md  # existing plan
├── tests/
│   └── unit/
│       └── v2/
│           ├── phase_01/
│           │   ├── test_bootstrap.py  # proposed
│           │   ├── test_diagnostics.py  # proposed
│           │   ├── test_discovery.py  # proposed
│           │   ├── test_jobs.py  # proposed
│           │   ├── test_logging.py  # proposed
│           │   ├── test_persistence.py  # proposed
│           │   ├── test_resources.py  # proposed
│           │   ├── test_security.py  # proposed
│           │   ├── test_settings.py  # proposed
│           │   └── test_transport.py  # proposed
│           ├── phase_02/
│           │   ├── test_catalog.py  # proposed
│           │   ├── test_cot.py  # proposed
│           │   ├── test_custom_data.py  # proposed
│           │   ├── test_ingestion.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   ├── test_providers.py  # proposed
│           │   ├── test_quality.py  # proposed
│           │   └── test_sessions.py  # proposed
│           ├── phase_03/
│           │   ├── test_blocks.py  # proposed
│           │   ├── test_code_editor.py  # proposed
│           │   ├── test_documents.py  # proposed
│           │   ├── test_exporters.py  # proposed
│           │   ├── test_formats.py  # proposed
│           │   ├── test_indicators_cot.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   └── test_wizard.py  # proposed
│           ├── phase_04/
│           │   ├── test_accounting.py  # proposed
│           │   ├── test_alignment.py  # proposed
│           │   ├── test_execution.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   ├── test_management.py  # proposed
│           │   ├── test_run_jobs.py  # proposed
│           │   └── test_specifications.py  # proposed
│           ├── phase_05/
│           │   ├── test_charts.py  # proposed
│           │   ├── test_databanks.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   ├── test_metrics.py  # proposed
│           │   └── test_reports.py  # proposed
│           ├── phase_06/
│           │   ├── test_fitness.py  # proposed
│           │   ├── test_genetic.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   └── test_random_search.py  # proposed
│           ├── phase_07/
│           │   ├── test_chains.py  # proposed
│           │   ├── test_experiments.py  # proposed
│           │   ├── test_monte_carlo_retest.py  # proposed
│           │   ├── test_monte_carlo_trades.py  # proposed
│           │   ├── test_retest_scenarios.py  # proposed
│           │   ├── test_search_methods.py  # proposed
│           │   └── test_walk_forward.py  # proposed
│           ├── phase_08/
│           │   ├── test_documents.py  # proposed
│           │   ├── test_evaluation.py  # proposed
│           │   ├── test_integration.py  # proposed
│           │   └── test_search.py  # proposed
│           ├── phase_09/
│           │   ├── test_conditions.py  # proposed
│           │   ├── test_documents.py  # proposed
│           │   ├── test_task_adapters.py  # proposed
│           │   └── test_utility_tasks.py  # proposed
│           ├── phase_10/
│           │   ├── test_integration.py  # proposed
│           │   ├── test_local_capacity.py  # proposed
│           │   └── test_protocol.py  # proposed
│           ├── phase_11/
│           │   ├── test_models.py  # proposed
│           │   ├── test_training_data.py  # proposed
│           │   └── test_training.py  # proposed
│           ├── phase_12/
│           │   ├── test_algocloud.py  # proposed
│           │   ├── test_marketplace.py  # proposed
│           │   ├── test_mcp.py  # proposed
│           │   ├── test_terminals.py  # proposed
│           │   └── test_trading_authority.py  # proposed
│           └── phase_13/
│               ├── test_contributions.py  # proposed
│               ├── test_memory.py  # proposed
│               ├── test_sessions.py  # proposed
│               └── test_tools.py  # proposed
└── ui/
    └── app/
        ├── host/
        │   ├── App.tsx  # existing shared UI
        │   ├── branding.ts  # existing shared UI
        │   ├── globalSettings.ts  # existing shared UI
        │   ├── GlobalSettingsMenu.tsx  # existing shared UI
        │   ├── HeaderApplications.tsx  # existing shared UI
        │   ├── HostConnection.tsx  # existing shared UI
        │   ├── hostSettings.ts  # existing shared UI
        │   ├── README.md  # existing shared UI
        │   ├── router.tsx  # existing shared UI
        │   ├── store.ts  # existing shared UI
        │   ├── styles.css  # existing shared UI
        │   ├── transport.ts  # existing shared UI
        │   └── types.ts  # existing shared UI
        ├── plugins/  # existing nested plugins/components retained
        └── workspace/
            ├── AIAssistant/
            │   └── AIAssistantWorkspace.tsx  # existing
            ├── AlgoWizard/
            │   └── AlgoWizardWorkspace.tsx  # existing
            ├── Builder/
            │   └── BuilderWorkspace.tsx  # existing
            ├── Business/
            │   └── BusinessWorkspace.tsx  # existing
            ├── Chart/
            │   └── ChartWorkspace.tsx  # existing
            ├── CodeEditor/
            │   └── CodeEditorWorkspace.tsx  # existing
            ├── CustomProjects/
            │   └── CustomProjectsWorkspace.tsx  # existing
            ├── DataManager/
            │   └── DataManager.tsx  # existing
            ├── DebugConsole/
            │   └── DebugConsoleWorkspace.tsx  # existing
            ├── GridControl/
            │   └── GridControlWorkspace.tsx  # existing
            ├── GridTest/
            │   └── GridTestWorkspace.tsx  # existing
            ├── Home/
            │   └── HomeScreen.tsx  # existing
            ├── MTAnalyzer/
            │   └── MTAnalyzerWorkspace.tsx  # existing
            ├── NeuralNetwork/
            │   └── NeuralNetworkTrainer.tsx  # existing
            ├── Optimizer/
            │   └── OptimizerWorkspace.tsx  # existing
            ├── PortfolioComposer/
            │   └── PortfolioComposerWorkspace.tsx  # existing
            ├── PortfolioMaster/
            │   └── PortfolioMasterWorkspace.tsx  # existing
            ├── Results/
            │   └── ResultsWorkspace.tsx  # existing
            ├── Retester/
            │   └── RetesterWorkspace.tsx  # existing
            └── Trading/
                └── TradingDashboard.tsx  # existing
```

Backend workspace composition belongs under `app/workspace/<workspace>/`, as the
phases specify. Its exact manifest, route and composition filenames remain to be
chosen in each workspace implementation plan; they are not defined in the phases
and are not invented here. Concrete numerical/format/provider variants live behind
the owning domain modules and typed contribution slots. This tree does not require
one Python file per provider, JAR, indicator or settings panel.

`tests/unit/v2/phase_01` through `phase_13` contain the 72 proposed task test files.
Connected/reference/numerical fixtures and integration tests still need exact-path
selection in the corresponding runtime plans; they are not yet named by the phases.
Module/package boilerplate, private implementation helpers and build/runtime outputs
are intentionally determined by those plans, with host-only persistence and no
peer business imports. The preserved V1 archive and active evidence remain in
`docs/dev/V1/` and `docs/dev/evidence/` respectively.

## Reading order

1. [Architecture](architecture.md): deployment, ownership and the few shared contracts.
2. [Host foundation](host-foundation.md): the ten capabilities and their acceptance.
3. [Product features](product-features.md): included behavior and simplest implementation.
4. [Delivery plan](delivery-plan.md): usable milestones and completion checks.
5. [Coverage map](coverage-map.md): specialist scope, dispositions and the task appendix.

Start with a working local loop: **import -> author -> backtest -> inspect/export**.
Then add generation, validation and portfolios. Extend that working core with
projects, scale, models, integrations and AI.

## Scope and authority

All product behavior in the [current roadmap](../V1/sqx-full-application-roadmap.md)
has a planned destination, including the specialist and resource-only features.
Later delivery means pending scope, not removal. A provider that is inaccessible
or obsolete needs an explicit availability/compatibility decision; it cannot be
silently replaced and counted as equivalent.

V2 is an alternative proposal. The [V1 archive](../V1/README.md) preserves the old
plan and historical task status. Evidence locators were updated for the archive move,
with original captured observations preserved. Registrations and the already approved
P01 implementation contracts remain unchanged. [Architecture](../../ARCHITECTURE.md),
[project scope](../../PROJECT.md) and [AGENTS.md](../../../AGENTS.md) remain authoritative.
Adoption must reconcile the existing P01 contracts before new runtime work.

The current backend is a reference-tooling baseline, with retained UI fixtures.
These documents claim planning coverage only. Working features require independent
tests and real backend/UI acceptance; SQX numerical parity requires independent
donor comparisons. No application source, live data or Git history is changed here; reference test paths
follow the documentation relocation.
