# SQX V2 implementation checklist

```text
Progress Bar   [--------------------] 0.00%
Completed      0/72
Current Task   1.1 App/host bootstrap and browser shell
```

- Count the **72 numbered capability tasks** only; thirteen phase checkboxes are rollups. Nested steps, specialist matrix rows and the shared release gate are acceptance conditions, not additional counted tasks.
- Update completed/total, percentage, the twenty-cell progress bar and current task together after actual accepted implementation. Phase rollups complete only when every child task is complete.
- A checked task means approved requirements, real backend behavior, independent evidence and applicable retained UI acceptance have passed. Plans, static donor inventory and production fixture screens are not application completion.
- Existing P00 reference readiness is a prerequisite, not a V2 application task. The [V1 checklist](../V1/implementation_checklist.md) retains its historical 1/366 status.
- Numbers identify ownership. Use the [nine delivery milestones](delivery-plan.md) to sequence small useful slices; basic data/author/run/results work does not wait for remote compute, models or AI.
- Provider/method/format/procedure variants stay in each phase's acceptance matrix. Partial support leaves the owning task unchecked; do not hide missing scope behind a grouped title.
- Owning READMEs remain the status authority. V2 is a proposal; ratified architecture and the already approved P01 contracts remain binding. Every runtime slice needs its own canonical approved plan.

- [ ] 1. [Phase 1 — Platform and web shell](phase-01-platform-host.md)
    - [ ] 1.1 [App/host bootstrap and browser shell](phase-01-platform-host.md#11-apphost-bootstrap-and-browser-shell)
    - [ ] 1.2 [Centralized logging and DebugConsole](phase-01-platform-host.md#12-centralized-logging-and-debugconsole)
    - [ ] 1.3 [System and hardware diagnostics](phase-01-platform-host.md#13-system-and-hardware-diagnostics)
    - [ ] 1.4 [Settings and configurations](phase-01-platform-host.md#14-settings-and-configurations)
    - [ ] 1.5 [Workspace and plugin discovery](phase-01-platform-host.md#15-workspace-and-plugin-discovery)
    - [ ] 1.6 [HTTP and event transport](phase-01-platform-host.md#16-http-and-event-transport)
    - [ ] 1.7 [Local jobs and cancellation](phase-01-platform-host.md#17-local-jobs-and-cancellation)
    - [ ] 1.8 [Resource services and safe artifact access](phase-01-platform-host.md#18-resource-services-and-safe-artifact-access)
    - [ ] 1.9 [Host-owned persistence and restart recovery](phase-01-platform-host.md#19-host-owned-persistence-and-restart-recovery)
    - [ ] 1.10 [Security, sessions and distribution qualification](phase-01-platform-host.md#110-security-sessions-and-distribution-qualification)

- [ ] 2. [Phase 2 — Market data](phase-02-market-data.md)
    - [ ] 2.1 [Dataset catalog, instruments and broker definitions](phase-02-market-data.md#21-dataset-catalog-instruments-and-broker-definitions)
    - [ ] 2.2 [Sessions, clocks and native session import](phase-02-market-data.md#22-sessions-clocks-and-native-session-import)
    - [ ] 2.3 [File import and immutable dataset revisions](phase-02-market-data.md#23-file-import-and-immutable-dataset-revisions)
    - [ ] 2.4 [Data quality, transformations and data export](phase-02-market-data.md#24-data-quality-transformations-and-data-export)
    - [ ] 2.5 [Provider downloads and compatibility matrix](phase-02-market-data.md#25-provider-downloads-and-compatibility-matrix)
    - [ ] 2.6 [Baskets and custom data](phase-02-market-data.md#26-baskets-and-custom-data)
    - [ ] 2.7 [COT catalog, mapping and updates](phase-02-market-data.md#27-cot-catalog-mapping-and-updates)
    - [ ] 2.8 [Connected Data Manager workflow](phase-02-market-data.md#28-connected-data-manager-workflow)

- [ ] 3. [Phase 3 — Strategies and authoring](phase-03-strategies-authoring.md)
    - [ ] 3.1 [Versioned semantic strategy document](phase-03-strategies-authoring.md#31-versioned-semantic-strategy-document)
    - [ ] 3.2 [Blocks, snippets, constants and indicator catalog](phase-03-strategies-authoring.md#32-blocks-snippets-constants-and-indicator-catalog)
    - [ ] 3.3 [COT, market/profile and specialist indicators](phase-03-strategies-authoring.md#33-cot-marketprofile-and-specialist-indicators)
    - [ ] 3.4 [AlgoWizard rule authoring](phase-03-strategies-authoring.md#34-algowizard-rule-authoring)
    - [ ] 3.5 [Code editor, custom code and indicator testing](phase-03-strategies-authoring.md#35-code-editor-custom-code-and-indicator-testing)
    - [ ] 3.6 [Saved revisions and SQ3/SQ4 compatibility](phase-03-strategies-authoring.md#36-saved-revisions-and-sq3sq4-compatibility)
    - [ ] 3.7 [Platform code and package export](phase-03-strategies-authoring.md#37-platform-code-and-package-export)
    - [ ] 3.8 [Connected authoring and round-trip qualification](phase-03-strategies-authoring.md#38-connected-authoring-and-round-trip-qualification)

- [ ] 4. [Phase 4 — Simulation](phase-04-simulation-engine.md)
    - [ ] 4.1 [Run specification and chronological execution](phase-04-simulation-engine.md#41-run-specification-and-chronological-execution)
    - [ ] 4.2 [Orders, fills and platform execution profiles](phase-04-simulation-engine.md#42-orders-fills-and-platform-execution-profiles)
    - [ ] 4.3 [Position management, risk and money sizing](phase-04-simulation-engine.md#43-position-management-risk-and-money-sizing)
    - [ ] 4.4 [Costs, ledger and equity accounting](phase-04-simulation-engine.md#44-costs-ledger-and-equity-accounting)
    - [ ] 4.5 [Precision, multi-series and stock-selection behavior](phase-04-simulation-engine.md#45-precision-multi-series-and-stock-selection-behavior)
    - [ ] 4.6 [Bounded run jobs, caches and performance](phase-04-simulation-engine.md#46-bounded-run-jobs-caches-and-performance)
    - [ ] 4.7 [Independent numerical and connected backtest qualification](phase-04-simulation-engine.md#47-independent-numerical-and-connected-backtest-qualification)

- [ ] 5. [Phase 5 — Results and reporting](phase-05-results-reporting.md)
    - [ ] 5.1 [Databanks, immutable results and saved view settings](phase-05-results-reporting.md#51-databanks-immutable-results-and-saved-view-settings)
    - [ ] 5.2 [Statistics, trade projections and result comparisons](phase-05-results-reporting.md#52-statistics-trade-projections-and-result-comparisons)
    - [ ] 5.3 [Charts, series, distributions and correlation views](phase-05-results-reporting.md#53-charts-series-distributions-and-correlation-views)
    - [ ] 5.4 [Reports, spreadsheets, trades, PDF and image exports](phase-05-results-reporting.md#54-reports-spreadsheets-trades-pdf-and-image-exports)
    - [ ] 5.5 [Connected results and retained analysis surfaces](phase-05-results-reporting.md#55-connected-results-and-retained-analysis-surfaces)

- [ ] 6. [Phase 6 — Strategy generation](phase-06-strategy-generation.md)
    - [ ] 6.1 [Constrained random candidate generation](phase-06-strategy-generation.md#61-constrained-random-candidate-generation)
    - [ ] 6.2 [Genetic generation and strategy improvement](phase-06-strategy-generation.md#62-genetic-generation-and-strategy-improvement)
    - [ ] 6.3 [Fitness, ranking, filters and candidate lineage](phase-06-strategy-generation.md#63-fitness-ranking-filters-and-candidate-lineage)
    - [ ] 6.4 [Builder jobs, automatic retest and connected acceptance](phase-06-strategy-generation.md#64-builder-jobs-automatic-retest-and-connected-acceptance)

- [ ] 7. [Phase 7 — Optimization and validation](phase-07-optimization-validation.md)
    - [ ] 7.1 [Experiment specifications and parameter search](phase-07-optimization-validation.md#71-experiment-specifications-and-parameter-search)
    - [ ] 7.2 [Sequential search, profiles and parameter permutations](phase-07-optimization-validation.md#72-sequential-search-profiles-and-parameter-permutations)
    - [ ] 7.3 [Walk-forward optimization, aggregation and matrices](phase-07-optimization-validation.md#73-walk-forward-optimization-aggregation-and-matrices)
    - [ ] 7.4 [Monte Carlo trade manipulation](phase-07-optimization-validation.md#74-monte-carlo-trade-manipulation)
    - [ ] 7.5 [Monte Carlo input perturbation and retest](phase-07-optimization-validation.md#75-monte-carlo-input-perturbation-and-retest)
    - [ ] 7.6 [Additional-market, higher-precision and What-If checks](phase-07-optimization-validation.md#76-additional-market-higher-precision-and-what-if-checks)
    - [ ] 7.7 [Cross-check chains, thresholds and connected qualification](phase-07-optimization-validation.md#77-cross-check-chains-thresholds-and-connected-qualification)

- [ ] 8. [Phase 8 — Portfolios](phase-08-portfolios.md)
    - [ ] 8.1 [Portfolio membership, weights and revisions](phase-08-portfolios.md#81-portfolio-membership-weights-and-revisions)
    - [ ] 8.2 [Aggregate accounting, exposures and correlations](phase-08-portfolios.md#82-aggregate-accounting-exposures-and-correlations)
    - [ ] 8.3 [Automatic construction, selection and search](phase-08-portfolios.md#83-automatic-construction-selection-and-search)
    - [ ] 8.4 [Composer/Master workflows and independent qualification](phase-08-portfolios.md#84-composermaster-workflows-and-independent-qualification)

- [ ] 9. [Phase 9 — Research projects](phase-09-research-projects.md)
    - [ ] 9.1 [Project documents, tasks and bounded state machine](phase-09-research-projects.md#91-project-documents-tasks-and-bounded-state-machine)
    - [ ] 9.2 [Domain task adapters and mass configuration](phase-09-research-projects.md#92-domain-task-adapters-and-mass-configuration)
    - [ ] 9.3 [Utility, file, notification and external-script tasks](phase-09-research-projects.md#93-utility-file-notification-and-external-script-tasks)
    - [ ] 9.4 [Conditions, recovery and connected project qualification](phase-09-research-projects.md#94-conditions-recovery-and-connected-project-qualification)

- [ ] 10. [Phase 10 — Compute](phase-10-compute.md)
    - [ ] 10.1 [Local capacity and job placement](phase-10-compute.md#101-local-capacity-and-job-placement)
    - [ ] 10.2 [Remote workers, protocol, admission and leases](phase-10-compute.md#102-remote-workers-protocol-admission-and-leases)
    - [ ] 10.3 [Grid Control/Test, recovery and local/remote equivalence](phase-10-compute.md#103-grid-controltest-recovery-and-localremote-equivalence)

- [ ] 11. [Phase 11 — Neural models](phase-11-neural-models.md)
    - [ ] 11.1 [Training features, targets, preprocessing and temporal splits](phase-11-neural-models.md#111-training-features-targets-preprocessing-and-temporal-splits)
    - [ ] 11.2 [Bounded training, backend qualification and metrics](phase-11-neural-models.md#112-bounded-training-backend-qualification-and-metrics)
    - [ ] 11.3 [Model revisions, inference and connected acceptance](phase-11-neural-models.md#113-model-revisions-inference-and-connected-acceptance)

- [ ] 12. [Phase 12 — Connections and ecosystem](phase-12-connections-ecosystem.md)
    - [ ] 12.1 [Terminal lifecycle and read-only/test connections](phase-12-connections-ecosystem.md#121-terminal-lifecycle-and-read-onlytest-connections)
    - [ ] 12.2 [Separately authorized live operations and trading surfaces](phase-12-connections-ecosystem.md#122-separately-authorized-live-operations-and-trading-surfaces)
    - [ ] 12.3 [Business/MCP tools, nodes and lifecycle](phase-12-connections-ecosystem.md#123-businessmcp-tools-nodes-and-lifecycle)
    - [ ] 12.4 [AlgoCloud resources and compatibility](phase-12-connections-ecosystem.md#124-algocloud-resources-and-compatibility)
    - [ ] 12.5 [Marketplace package lifecycle and ecosystem qualification](phase-12-connections-ecosystem.md#125-marketplace-package-lifecycle-and-ecosystem-qualification)

- [ ] 13. [Phase 13 — AI research assistant](phase-13-ai-research-assistant.md)
    - [ ] 13.1 [Q sessions, chat, providers and result-tab completion](phase-13-ai-research-assistant.md#131-q-sessions-chat-providers-and-result-tab-completion)
    - [ ] 13.2 [Memory, knowledge, research records and procedures](phase-13-ai-research-assistant.md#132-memory-knowledge-research-records-and-procedures)
    - [ ] 13.3 [Bounded tool orchestration, schedules and isolated analysis](phase-13-ai-research-assistant.md#133-bounded-tool-orchestration-schedules-and-isolated-analysis)
    - [ ] 13.4 [All Q contributions and connected research qualification](phase-13-ai-research-assistant.md#134-all-q-contributions-and-connected-research-qualification)

## Shared release gate

This gate is excluded from the 72-task denominator and applies to full release.

- [ ] All accepted F01-F13 scope and every named specialist matrix row are qualified; [all 366 legacy rows](legacy-task-map.csv) retain a reviewed disposition, including JVM-only machinery, resources and unresolved gaps.
- [ ] Import -> author -> backtest -> inspect/export, Builder -> Retester -> portfolio/project and selected model/compute/connection/AI journeys run through actual backend capabilities.
- [ ] Independent numerical, file-format and platform/provider tests support stated compatibility; missing native engine/AI bodies or unavailable services remain explicit release limits.
- [ ] Failure/denial/cancellation, queue/resource bounds, worker loss, restart/recovery, disable/removal and clean installation preserve owned and unrelated retained data.
- [ ] Required Python typing/lint/format, meaningful tests and at least 80% branch-aware retained application coverage pass; applicable UI typecheck/tests/build and connected acceptance pass.
- [ ] Live trading, destructive actions, external scripts/mail and paid tools retain separate scoped authority; custom/AI code has qualified isolation.
- [ ] Owner-reviewed release matrix states the actual shipping cohort and limitations. No blanket whole-SQX parity or release claim follows from documentation coverage.

See the [V2 index](README.md), [coverage audit](coverage-map.md), [architecture](architecture.md) and [V1 archive](../V1/README.md).
