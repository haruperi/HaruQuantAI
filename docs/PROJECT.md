# HaruQuantAI project charter

> **Authority:** This document owns product scope and system outcomes.
> [ARCHITECTURE.md](ARCHITECTURE.md) owns structural rules and the Five Laws;
> [AGENTS.md](../AGENTS.md) owns workflow and verification. The owning
> workspace, plugin, and host READMEs own detailed contracts and current
> implementation state. Donor observations live in the
> [evidence ledger](dev/evidence/reimplementation.json).
>
> **Status:** Target charter at the host-shell baseline, 2026-09-23. A described
> capability is a target unless an owning README and verification evidence
> establish that it works.

## 1. Purpose and product boundary

HaruQuantAI is a local-first quantitative research workstation. A user should
be able to prepare market data, create and revise strategies, test them against
declared historical conditions, challenge their robustness, compare results,
build portfolios, automate bounded research flows, and export reviewed
artifacts. The workstation should make the inputs and limitations behind every
result inspectable. Optional AI assistance can explain evidence and propose
edits; it cannot confer numerical, risk, or execution authority.

The product is a clean-room reimplementation informed by StrategyQuant X
(SQX) build 144.2953. **Donor informs; specification owns.** SQX artifacts and
official documentation guide the capabilities worth studying. HaruQuantAI's
contracts, algorithms, packaging, and acceptance criteria are independently
specified and tested. No SQX binary, source, file format, or result parity is
claimed merely because a similar screen or workflow exists.

The primary user is a strategy researcher who needs repeatable experiments.
The product also serves a reviewer examining lineage and failure states, an
extension author adding a quantitative concept, and an operator administering
local resources. Separate operational roles may be introduced only when
trading integrations have their own authority and qualification.

## 2. Workstation experience

The product is organized around **workspaces** for user tasks and **plugins**
for focused contributions. The host provides navigation, sessions, settings,
catalog discovery, transport, events, and shared presentation chrome. A
workspace may select and arrange plugins; it does not become the implementation
home for every concept it uses.

| User job | Workspace experience and target outcome |
| --- | --- |
| Prepare evidence | Data Manager imports, downloads where explicitly configured, inspects, versions, and binds market data, instruments, sessions, costs, and quality decisions. A result identifies exactly which data and policies it used. |
| Author rules | AlgoWizard and Code Editor support reviewable strategy documents, reusable blocks, parameters, and extension authoring. A visual rule and its executable meaning share one versioned definition. |
| Generate candidates | Builder composes declared blocks under a pinned search space, data binding, fitness policy, and resource budget. Every accepted candidate carries lineage and a reproducible run identity. |
| Test and challenge | Retester, Optimizer, and robustness contributions run explicit tests, parameter studies, and walk-forward or stress scenarios. They preserve failed and partial attempts and do not turn a selected winner into proof of future performance. |
| Inspect results | Results and databank views present metrics, trades, equity, source definitions, and comparisons with units, sample basis, undefined reasons, and provenance. Presentation does not recalculate authoritative statistics. |
| Assemble portfolios | Portfolio Master and Portfolio Composer combine referenced strategy/results evidence, assess dependence and allocation choices, and submit reviewable portfolio artifacts. Portfolio construction does not itself approve trading risk. |
| Automate research | Custom Projects composes finite tasks with explicit inputs, outputs, databanks, conditions, and resource limits. A task flow can be inspected and resumed or failed without silently losing intermediate evidence. |
| Extend the system | Plugins contribute indicators, signals, data sources, cross-checks, metrics, result views, project tasks, exporters, and other focused capabilities through declared extension slots. Unsupported or incompatible contributions remain visible as unavailable, without breaking unrelated work. |

This table is a **target capability map**, not a feature registry or completion
claim. SQX's [program layout](https://strategyquant.com/doc/strategyquant/program-layout/)
describes Builder, Retester, Optimizer, Data Manager, Custom Projects,
AlgoWizard, Code Editor and supporting tools. The installed build also
registers navigation contributions through plugin modules
([SQX144-EV-000015](dev/evidence/reimplementation.json)). SQX calls even
large application surfaces plugins; HaruQuantAI's top-level “workspace”
category is our product and architecture decision. The installed
[extension manual](https://strategyquant.com/wp-content/uploads/2018/12/Extending_SQX.pdf)
distinguishes larger plugins from focused snippets
([SQX144-EV-000023](dev/evidence/reimplementation.json)).

The UI prototype also contains Home, Business, Neural Network, Grid Control,
Grid Test, Debug Console, MT Analyzer, and Trading surfaces. Their presence
does not establish backend functionality. MT Analyzer, AI-oriented experiences,
and operational Trading are HaruQuantAI scope decisions; they are not
automatically SQX workspace equivalents.

### Extensibility as a product outcome

Adding a compatible concept should let a user discover its purpose, parameters,
bounds, outputs, supported contexts, limitations, and provenance without
editing unrelated workspaces. The same concept should be selectable where its
declared capability fits. Where generic forms or charts cannot express its
interaction, a separately reviewed UI extension may supply that interaction.
A plugin's absence or removal must leave retained research documents
inspectable and mark the missing behavior explicitly.

The installed SQX build provides examples of contributions to cross-check
settings, Results tabs, and Data Manager sources
([SQX144-EV-000018](dev/evidence/reimplementation.json),
[SQX144-EV-000019](dev/evidence/reimplementation.json),
[SQX144-EV-000020](dev/evidence/reimplementation.json)). These observations
show useful extension families; they do not prove HaruQuantAI's planned
discovery, isolation, or removal guarantees.

## 3. Research journey and artifacts

A complete research journey is:

1. Select and inspect instrument and market-data versions, sessions, costs,
   time zones, and quality policy.
2. Author or generate a versioned strategy using declared plugin blocks and
   a typed rule structure.
3. Run a historical simulation with a pinned data binding, execution and
   numerical policy, sample, seed, and resource budget.
4. Examine results and trades in a databank without treating a view or
   membership change as a change to the underlying result.
5. Retest, optimize, and run robustness checks, recording every attempt,
   exclusion, failure, and selection.
6. Compose a portfolio or export a reviewed artifact with explicit lineage.
7. When authorized and separately qualified, hand a reviewed candidate to
   an operational route. Research completion alone never activates trading.

Product documents distinguish a **workspace** (interactive task surface), a
**project** (saved research flow/configuration), a **plugin** (capability
contribution), a **strategy** (versioned trading rule), a **run** (one pinned
execution attempt), a **result** (evidence from that attempt), and a
**databank** (named collection/view of strategy or result references). These
are distinct identities even when one screen displays several of them.
Installed SQX project archives show separate task configuration members and
multiple databank declarations
([SQX144-EV-000021](dev/evidence/reimplementation.json),
[SQX144-EV-000022](dev/evidence/reimplementation.json)); HaruQuantAI's
storage format and semantics remain its own decision. SQX's
[Custom Projects guide](https://strategyquant.com/doc/strategyquant/custom-projects-main-concepts/)
also describes task flow and databank source/target selection.

## 4. System-wide product requirements

These requirements apply to every relevant workspace and plugin. Structural
mechanics and verification methods are owned by ARCHITECTURE.md and AGENTS.md.

- **Truthful outcomes:** Distinguish absent, invalid, unsupported, denied,
  queued, running, partial, failed, canceled, and complete where applicable.
  A fixture or local simulation must be labelled as such.
- **Reproducibility:** A decision-grade output identifies material strategy,
  data, plugin/version, parameter, cost, clock, execution, numerical, sample,
  and random-seed inputs. Corrections publish new attributable versions.
- **No hidden substitution:** A missing provider, unsupported export, lower
  data precision, altered test period, or unavailable plugin cannot silently
  become a different successful operation.
- **Evidence preservation:** Retain attempt history and lineage needed to
  evaluate selection, robustness, and bias. Presentation and databank
  membership are not authority over source records.
- **Bounded operation:** Long-running research has finite admission,
  cancellation, recovery, and resource policies. An automation flow cannot
  create unbounded work or erase intermediate failures.
- **Safety and authority:** Live trading and other irreversible effects are
  disabled by default and require distinct authorization and qualification.
  AI advice, backtest results, or a successful export grant no execution or
  risk approval.
- **Extensibility:** A concept can be added, disabled, upgraded, or removed
  without editing unrelated concepts or corrupting retained artifacts.

These are target outcomes. Each owning workspace/plugin README must turn its
share into concrete requirements, contracts, tests, and status when registered.

## 5. Scope, exclusions, and current baseline

In scope are local research, explicit extension, inspectable artifacts,
headless backend operation through the host, and a browser workstation that
can work offline where the UI clearly identifies local simulation. External
providers, cloud workers, broker routes, and AI services are optional,
separately qualified integrations; the local research core must not require
them merely to start.

Out of scope are guarantees of profitability, investment advice, broker
custody or settlement, exact SQX source/binary compatibility, adoption of V1's
service-domain registry, untrusted arbitrary in-process code, implicit cloud
dependencies, and automatic live deployment. Historical simulation and live
operation have different authority and evidence requirements.

The current candidate baseline has a backend host under [app/host/](../app/host/README.md)
and a connected UI shell under [app/ui/app/host/](../app/ui/app/host/README.md).
The backend workspace/plugin directories are not populated with ratified
quantitative implementations. The retained React UI has workspace folders
and three top-level plugin groups, but many screens still use fixtures,
browser storage, and static routes. An interactive prototype is not a
validated simulator, optimizer, data source, or trading system. Exact
implementation truth belongs to package READMEs and accepted walkthroughs.

The next delivery units are independently owned workspace pairs and concrete
plugin pairs, admitted through the plan and verification process in AGENTS.md.
No backend feature registry exists yet for Custom Projects, databanks,
cross-checks, indicators, code lowering, or the other quantitative families
named above. Proposed first registration homes are
app/workspace/CustomProjects/README.md for task flows,
app/workspace/DataManager/README.md for the data workflow,
app/workspace/Builder/README.md for generation, and concept-owned READMEs
under app/plugins/ for databank views, cross-checks, indicators, and code
lowering. These are proposals, not registered features or implemented
directories. Each owner and its requirements must be approved before
implementation. The files currently named in AGENTS.md as the
workspace/plugin pipeline and audit are absent; their contents must be
authored and approved separately, not inferred from this charter.

## 6. Reference and decision discipline

Use the logical roots SQX_REFERENCE_ROOT and HARUQUANTAI_ROOT in evidence.
The [ledger](dev/evidence/reimplementation.json) records narrow SQX claims,
limitations, validation, and target mappings. Official SQX documentation is
context for product behavior; installed build artifacts decide what was
observed in build 144.2953. A donor fact is never an architecture rule by
itself. A HaruQuantAI rule is never presented as SQX behavior. Where evidence
is insufficient, preserve the question for an owning workspace/plugin plan
rather than claim parity.
