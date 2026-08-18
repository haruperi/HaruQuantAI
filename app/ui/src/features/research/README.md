# Research Workbench (`FEAT-UI-28`)

The V2 Research frontend. One feature folder covers the whole workbench: the
research ledger, the run builder, the run shell, every evidence panel, run
comparison, automation, and the expectancy and drift monitors.

## Ownership

Research owns every scientific conclusion rendered here — scores, readiness
verdicts, study classifications, statistics, warnings, and provenance. This
feature reshapes and formats them. It never recomputes one.

Concretely, nothing in this folder:

- computes an indicator, metric, score, or classification;
- decides whether a stage is complete (that arrives as `stage_status`);
- chooses an artifact root or a resource ceiling;
- persists a dataset or a report in browser storage;
- decides an expectancy lifecycle transition or enacts a drift suspension.

## Files

| File | Role |
| --- | --- |
| `ResearchDashboard.tsx` | Research ledger and entry point (V2 realization of V1 "Discovery"). |
| `ResearchRunBuilder.tsx` | Six-section experiment/run builder submitting a safe request. |
| `ResearchWorkbench.tsx` | Layout composition for one run stage. |
| `ResearchStageNav.tsx` | Progressive stage navigation from server-derived status. |
| `ResearchRunHeader.tsx` | Persistent run identity, status, hashes, and actions. |
| `ResearchRunStatus.tsx` | Live status strip plus the `EvidenceGate` state resolver. |
| `ResearchWarnings.tsx` | Warnings grouped by Research-assigned severity. |
| `ResearchArtifactDrawer.tsx` | Artifact references with hash and audit identity. |
| `ResearchComparison.tsx` | Run history and the server-derived comparison. |
| `ResearchAutomation.tsx` | Batch automation with per-symbol status and retry. |
| `ResearchExpectancy.tsx` | Approved expectancy profile, governance state, and permission-gated transition request control. |
| `ResearchDrift.tsx` | Drift evidence and any advisory suspension proposal. |
| `ResearchExperiments.tsx` | Experiment ledger and one experiment's run history. |
| `evidence.tsx` | Shared presentation primitives (badges, tables, heatmap, bars). |
| `research-store.ts` | Display-only Zustand state: draft, filters, comparison, stream. |
| `research-selectors.ts` | Read-only selectors and formatters. |
| `stage-registry.ts` | The navigable stage vocabulary. |
| `use-research.ts` | Data-loading hooks with SSE progress and bounded polling. |
| `panels/` | One panel per API-owned stage view. |
| `research.css` | Feature stylesheet, imported by `app/globals.css`. |

## Routes

```text
/workstation/research
/workstation/research/new
/workstation/research/experiments
/workstation/research/experiments/[experimentId]
/workstation/research/experiments/[experimentId]/runs/[runId]
/workstation/research/experiments/[experimentId]/runs/[runId]/[stage]
/workstation/research/compare
/workstation/research/automation
/workstation/research/expectancy
/workstation/research/drift
```

The URL is the primary navigation state: experiment, run, and stage all live in
the route, so a refresh restores exactly the view that was open and every stage
is shareable.

Cross-domain routes the workbench links to, and does not own:

```text
/workstation/simulator                    # Simulation
/workstation/optimization/monte-carlo     # Optimization
/workstation/strategies/import/sqx        # Strategy / Data import
```

## Backing API

`FEAT-API-26` (`app/services/api/workstation/research/`). Twenty-one registered
routes, including the ordered SSE progress stream at
`GET /api/v1/research/runs/{run_id}/events`. Every client function has a Zod
response schema in `src/clients/research.ts`. The typed transport generates a
fresh `Idempotency-Key` for run and automation-batch creation, matching their
required gateway contracts.

The Expectancy page creates draft profiles only from explicit measurements
bound to an owned completed run. The Stress stage selects one of five
Research-owned, immutable reasoned scenarios; the browser cannot supply or
alter shock magnitudes, units, assumption references, or rationale.

## Evidence states

A panel never collapses non-success into one message. The distinct states are
`queued`, `running`, `completed`, `partial`, `not_selected`, `unavailable`,
`failed`, `cancelled`, and `stale` — each with its own wording and, where the
server supplied one, its symbolic reason code.

The Market Structure Geometry tab renders Research's bounded confirmed swing
points and directional legs, including its total-count and truncation evidence.
It does not recompute geometry. Reports created before geometry was published
retain an explicit not-published fallback.

## Tests

- `ResearchWorkbench.test.tsx` — stage status, warning grouping, readiness and
  score rendering, study classification, heatmap cells, market-structure
  geometry and truncation, legacy geometry fallback, and evidence states.
- `research-client.test.ts` — route contracts, Zod success and failure,
  permission failure, and the assertion that no run request carries an artifact
  root or resource ceiling.
- `v1-coverage.test.ts` — the authoritative executable V1-to-V2 coverage
  manifest required by `FR-UI-243`, `FR-UI-247`, and `FR-UI-249`.
