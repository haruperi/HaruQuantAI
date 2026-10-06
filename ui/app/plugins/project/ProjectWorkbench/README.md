# Project workbench presentation

UI-only shared contribution for project frame, common settings, Results and local
progress previews. Public entrypoint: index.ts. Inputs are explicit props, slots
and callbacks. This package has no workspace imports, store access, quantitative
transport or backend contracts. It is not a dynamically discovered backend plugin.

| Feature | Scope | State |
|---|---|---|
| FEAT-UI-PROJECT_WORKBENCH | Shared project presentation and explicit composition slots | UI prototype; qualified, owner review pending |

Builder remains owner of Build-specific settings/progress fixtures. Its legacy
module paths forward to shared implementations for compatibility. Static donor
declarations inform presentation; shared code does not establish SQX parity.
Existing Results limitations include approximate reports/charts, mock code,
session-only analyses, and unavailable XLSX export.

## Verification and limits

The shared extraction retains Builder compatibility adapters. Builder settings and
Results browser regressions pass. The local preview clock supports Start, Pause,
Resume, Stop and completion; it never submits quantitative jobs. Retester and
Optimizer keep their settings mounted while switching the three project panels.
Workspace unmount resets these drafts; they are not durable project documents.

SQX declarations support shared composition (SQX144-EV-000065). No donor runtime
screenshot comparison or complete pixel-parity qualification has been performed.
Progress configuration/statistic dialogs, charts and reports remain simplified
local previews. Common settings retain earlier Builder approximation gaps; shared
Ranking task filtering is not an exhaustive audit of every donor predicate.
The settings summaries use static data labels rather than derived shared form state.

Verification: UI typecheck, 273 unit tests, production build, Builder regressions,
Retester/Optimizer browser flows and repository CI. The task walkthrough records
exact runs, intermediate failures and screenshots. No backend, database or
quantitative transport contracts changed.

## Portfolio consumers

Portfolio Master composes the shared project frame and progress with its own settings.
Portfolio Composer embeds Results in its distinct layout. ProjectResults accepts
optional embedded layout, standard-tab IDs and empty-state text; defaults retain
existing Builder/Retester/Optimizer behavior. Additional result slots remain explicit.
These inputs define presentation only; they do not infer plugin eligibility or calculate
portfolio metrics. Workspace READMEs own their task-specific status and limitations.

## Structural module boundaries

The stable index forwards ProjectSettings to ../ProjectSettings/module and ProjectProgress to ../EnginePanel/module. SettingsPanel owns shared settings presentation. Contracts, project frame, modal lifecycle, local preview clock and result charts remain shared support.
