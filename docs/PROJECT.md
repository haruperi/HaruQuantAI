# HaruQuantAI project charter

Status: reset-aware target charter; P00 evidence infrastructure is the only current
Python delivery cohort. Ratified by the owner-approved P00 plan, 2026-10-06.
Current reference authority is the sole SQX145 downloaded cohort; installed product activation remains unverified.

## Authority

[AGENTS.md](../AGENTS.md) owns contributor workflow and verification.
[ARCHITECTURE.md](ARCHITECTURE.md) owns structural constraints.
Owning host/workspace/plugin READMEs own local contracts and current status.
[Evidence](dev/evidence/README.md) records observations; donor informs and the
ratified specification owns. Roadmap publication does not register implementations.

## Product purpose and actors

HaruQuantAI is a local-first quantitative research workstation. Researchers prepare
market data, author and generate strategy candidates, run historical experiments,
challenge robustness, compare results, build portfolios and export reviewed
artifacts. Evidence reviewers inspect inputs, assumptions, lineage and limitations.
Extension authors contribute narrow capabilities through typed slots. Operators
manage local resources and bounded automation. AI assistance may explain evidence
and propose edits; it confers no numerical, financial or execution authority.

## Target journeys

1. Acquire, import, inspect and version instruments and market data in Data Manager.
2. Author or generate pinned strategy documents in AlgoWizard and Builder.
3. Simulate, optimize and retest with explicit datasets, costs, clocks and seeds.
4. Inspect immutable results, trades, metrics and comparisons in databanks.
5. Challenge candidates using approved walk-forward and stress methods.
6. Compose portfolios or export reviewed code artifacts.
7. Compose finite, bounded research tasks in Custom Projects.

All backend journeys are targets after the reset. Retained React surfaces may use
fixtures or local simulation and do not establish backend availability or parity.
No removed backend service or workflow is reinstated by restoring this charter.

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
applicable donor runtime fixtures, product activation and P01-P19 application
execution remain unqualified and gated by their owning features. See the
[release matrix](dev/evidence/p00-release-matrix.md).

A future feature requires evidence-supported donor behavior, ratified owner/FEAT/FR/
DEC mappings, applicable independent normal/boundary/failure observations, focused
tests, explicit FR log verification and candidate checks. The narrowly approved
source-unavailable universal host services instead require explicit target-owned
contracts/defaults/failures and independent target tests; they cannot claim exact
SQX translation or parity. Application registrations occur in owning feature plans. Full application parity cannot
be claimed from structural inventory, coverage or a similar UI.

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
