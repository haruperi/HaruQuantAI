# Portfolio Master UI

Owns FEAT-UI-PORTFOLIO_MASTER_WORKSPACE: a local UI prototype of the automatic
portfolio-building workflow. State: UI candidate qualified; owner review pending.
Product scope: docs/PROJECT.md portfolio assembly. No registered FR-/DEC- IDs
apply to the detailed presentation. No backend portfolio capability is claimed.

Consumes ProjectWorkbench public frame, progress, settings and Results components.
Master owns its draft, summary, form, genetic/correlation dialogs and fixture result.
Summary and Full settings edit the same draft. Source selection guards Start;
Pause/Resume/Stop and completion use a bounded preview clock. Completion exposes
a fixed example result without writing any databank. Databank activation navigates
to the selected result. Drafts reset on workspace unmount; existing saved settings
and portfolios are not overwritten.

Installed layouts and SettingsAutomaticPortfolioBuilder declarations inform this
implementation. Quantitative search, correlation, ranking and position sizing are
not performed. Active UI no longer imports Composer's private algorithm helpers.
The existing legacy helper file remains untouched and is not qualified by this work.

Limits: source options, fitness/MM dropdowns and example results are bounded fixtures;
no native project serialization, complete dynamic metadata or runtime SQX parity.
The shared progress detail/config dialogs inherit ProjectWorkbench approximation
limits. Continual search is an editable setting but the preview runs one bounded
cycle. Genetic/correlation edits apply immediately; Close retains them, matching
the inspected change handlers. Dates are fixed demo inputs, not installed defaults.
No automatic Master-to-Composer handoff is added: its donor behavior is unverified.

Evidence: retained target UI; current donor equivalence unverified (applicable workspace claims).
Verification: 277 UI unit tests, 27 shared/portfolio browser journeys, UI typecheck/build
and repository CI passed on 2026-09-25. This qualifies the mock UI candidate only.

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.
