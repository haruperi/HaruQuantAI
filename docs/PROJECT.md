# HaruQuantAI project charter

Status: reset-aware target charter; P00 evidence infrastructure is the only current
Python delivery cohort. Ratified by the owner-approved P00 plan, 2026-10-06.
Current reference authority is the sole SQX145 downloaded cohort; installed product activation remains unverified.

V2 alignment, 2026-10-07: full product scope and delivery planning are summarized
below; the current implemented cohort remains P00 reference tooling.

## Authority

[AGENTS.md](../AGENTS.md) owns contributor workflow and verification.
[ARCHITECTURE.md](ARCHITECTURE.md) owns structural constraints.
Owning host/workspace/plugin READMEs own local contracts and current status.
[Evidence](dev/evidence/README.md) records observations; donor informs and the
ratified specification owns. Roadmap publication does not register implementations.

[V2](dev/V2/README.md) is the current capability-based planning map; its
[checklist](dev/V2/implementation_checklist.md), thirteen detailed phases and
[nine delivery milestones](dev/V2/delivery-plan.md) organize future work.
[V1](dev/V1/README.md) retains historical JAR/task research and status; the
[coverage map](dev/V2/coverage-map.md) preserves all 366 legacy task dispositions.
F01-F13 and H01-H10 are planning labels, not registered FEAT/FR/DEC identities.
Existing owner-approved P01 contracts remain binding; future files, domain APIs
and operational schemas still require their own approved implementation plans.

## Product purpose and actors

HaruQuantAI is a local-first Python quantitative research workstation accessed
through the retained React web frontend. Researchers prepare
market data, author and generate strategy candidates, run historical experiments,
challenge robustness, compare results, build portfolios and export reviewed
artifacts. Evidence reviewers inspect inputs, assumptions, lineage and limitations.
Extension authors contribute narrow capabilities through typed slots. Operators
manage local resources and bounded automation. AI assistance may explain evidence,
propose reviewable artifacts and orchestrate explicitly authorized typed research
tools. It confers no independent numerical, financial or execution authority.

## Full product scope in thirteen feature groups

| Group | Capability | Included target scope |
| --- | --- | --- |
| F01 | Platform and web shell | Ten host capabilities, navigation/preferences, logs/health and local distribution |
| F02 | Market data | All retained providers/files, instruments/sessions, quality, baskets/custom data and COT |
| F03 | Strategies and authoring | Blocks/indicators, AlgoWizard/CodeEditor/testing, native formats and platform code/packages |
| F04 | Simulation | Qualified execution profiles, orders/fills, management/sizing, costs/accounting and precision |
| F05 | Results and reporting | Databanks, metrics/comparisons/charts, retained analysis views and report/data/image exports |
| F06 | Strategy generation | Random/genetic generation and improvement, fitness/lineage and Builder/retest integration |
| F07 | Optimization and validation | Parameter/sequential/profile/permutation search, walk-forward, both Monte Carlo modes and all cross-checks |
| F08 | Portfolios | Manual/automatic composition/search, weights/correlation, aggregate accounting and retained versions |
| F09 | Research projects | Reusable bounded task/condition workflows, domain/utility tasks and scoped external effects |
| F10 | Compute | Local placement and optional compatible remote workers using the same job contract |
| F11 | Neural models | Temporal inputs/preprocessing, qualified bounded training, retained models and inference |
| F12 | Connections and ecosystem | Terminal/test and separately authorized live operations, Business/MCP, AlgoCloud and Marketplace |
| F13 | AI research assistant | Q chat/completion, memory/procedures, bounded tools/schedules and isolated analysis |

Each [detailed phase](dev/V2/README.md#implementation-tracker-and-detailed-phases)
contains its complete method/provider/format/procedure acceptance matrix. Grouping
removes duplicated Java-library work without dropping specialist behavior. A
provider variant, export target or robustness method is not accepted merely because
a generic adapter exists. Explicit unavailable/replacement decisions remain reviewable.
Retained MTAnalyzer and live Trading target additions are distinguished from donor
features. Vendor services, entitlements and licensed packages require actual available
integrations; scope does not imply a license-system emulator or service availability.

## Target journeys

1. Acquire, import, inspect and version instruments and market data in Data Manager.
2. Author or generate pinned strategy documents in AlgoWizard and Builder.
3. Simulate, optimize and retest with explicit datasets, costs, clocks and seeds.
4. Inspect immutable results, trades, metrics and comparisons in databanks.
5. Challenge candidates using approved walk-forward and stress methods.
6. Compose portfolios or export reviewed code artifacts.
7. Compose finite, bounded research tasks and conditions in Custom Projects.
8. Extend qualified local workflows with selected remote compute, neural models,
   terminal/Business/MCP/AlgoCloud/Marketplace adapters and bounded Q research
   orchestration; retain actual inputs/results and explicit authority throughout.

All backend journeys are targets after the reset. Retained React surfaces may use
fixtures or local simulation and do not establish backend availability or parity.
No removed backend service or workflow is reinstated by restoring this charter.

Deliver import -> author -> backtest -> inspect/export first, then generation,
optimization/robustness, portfolios and projects. The nine V2 milestones select
capability subsets; all 72 task acceptance sets remain full-scope obligations.
Remote compute is optional for local research/training, and saved-strategy retest
does not require Builder. Advanced tracks depend only on the capabilities they use.

## System-wide requirements

- Distinguish absent, invalid, unsupported, denied, queued, running, partial, failed
  and complete results. Missing providers/authority report unavailable explicitly.
- A qualified result pins input revisions, strategy semantics, plugin versions,
  costs, clock, numerical policy, sample, exclusions, attempts and random seed.
- No hidden provider substitution, precision change, period change or mock success.
- Preserve evidence lineage, prior attempts and retained resources across removal.
- Long-running work has finite budgets and explicit admission/cancellation/recovery.
- Live trading and irreversible external mutations remain disabled by default and
  require separate authorization and qualification. Backtests grant no live authority.
- Source time/units/rounding and numerical tolerance are feature-specific contracts;
  no global tolerance or donor default is invented by P00.

## Cohort and release truth

Reference cohort label: SQX145 Dev 1 download (145-dev1). Actual installed product build and activation
are unverified; runtime JAR version is not product-version evidence.

P00 delivers inventories, current-source evidence, proposed ownership and
reference validation. Exact SHA/count/order comparisons use zero tolerance.
The approved P00 closure boundary accepts explicit source-gap dispositions.
MainApp/AppSettings/CpuInfo universal host services may follow approved target
contracts; their hidden donor semantics remain unknown. Missing domain algorithms,
applicable donor runtime fixtures, product activation and F01-F13 application
execution remain unqualified and gated by their owning features. Legacy P01-P19
labels identify archived research; the approved P01 host contracts remain applicable. See the
[release matrix](dev/evidence/p00-release-matrix.md).

A future feature requires evidence-supported donor behavior, ratified owner/FEAT/FR/
DEC mappings, applicable independent normal/boundary/failure observations, focused
tests, explicit FR log verification and candidate checks. The narrowly approved
source-unavailable universal host services instead require explicit target-owned
contracts/defaults/failures and independent target tests; they cannot claim exact
SQX translation or parity. Application registrations occur in owning feature plans. Full application parity cannot
be claimed from structural inventory, coverage or a similar UI.

Use the [V2 shared release gate](dev/V2/implementation_checklist.md#shared-release-gate)
for actual connected journeys, independent numerical/format/provider qualification,
failure/cancellation/recovery/removal, resource bounds and clean distribution.
Separate implemented target behavior, external compatibility, independently verified
SQX behavior and pending/unavailable scope. Publish only the named qualified cohort;
all promised specialist rows must pass before a full-scope claim.

## Persistence and external effects

Host-owned resource custody and explicitly ratified schema interfaces mediate
persistence. No operational store location, schema, migration, reset or plugin SQL
is authorized by P00. Temporary isolated stores are used for tests. Retained bytes
survive producer removal. External capabilities require typed ownership, bounded
timeouts/retries/rates, redaction and explicit lifecycle. No donor executable is
launched against the installed user's state by this task.

## Change process

Research, exact-path documented plan, owner execution approval, surgical changes,
focused checks, canonical walkthrough, separate owner commit approval. Material
scope/contract/dependency changes require a recorded iteration and renewed approval.
