# Portfolio Composer UI

Owns FEAT-UI-PORTFOLIO_COMPOSER_WORKSPACE: independent composition and portfolio
preview UI. State: UI candidate qualified; owner review pending. Product scope is
docs/PROJECT.md portfolio assembly. No detailed FR-/DEC- mappings are established.

The workspace owns its member/configuration drafts, row actions, Buy & Hold and load
modals, local recompute lifecycle and Log/simulation result contributions. It embeds
ProjectWorkbench Results through explicit props and does not import workspace-private
implementations. No backend calls or portfolio calculations are performed.

Weight % is independent per strategy: 100% represents original sizing, 200% double.
It is never normalized to sum to 100. Existing member values seed the local draft and
are preserved, including old saved percentages; new example members start at 100%.
Selection determines the local run input; zero weights are allowed by the edit model.
Edits clear prior preview results. Stop cancels the timer; unmount discards local state.
No persisted portfolio/store values are changed by editing or preview actions.

Load adds example strategies or replaces the draft with a bounded, validated
HaruQuantAI preview JSON document. Save exports that format; Save portfolio exports
a result preview JSON. Neither claims native SQX compatibility. Delete/Clear all
require an in-app confirmation; Cancel leaves the draft unchanged. Buy & Hold uses
example symbols. Recompute and Automatic computation expose fixed result documents;
automatic computation does not optimize or apply weights. The legacy
portfolioOptimization.ts remains for its existing tests but is unused by these screens.

Presentation is based on installed Composer templates, its three settings tabs,
result contributions and common styles. The combined flex order rules support the
settings-left/results-right layout; actual SQX runtime rendering remains unverified.
Master does use the project shell; Composer intentionally has its own layout.
The result whitelist is a target preview choice because donor tab eligibility comes
from backend dataItems/noResultItems. Shared custom-analysis behavior remains local.

Limits: bounded metric/MM/symbol choices, mock mini charts/log/simulation chart,
no native imports, optimization, order-margin computation or verified numerical parity.
The automatic model is the observed Markowitz label; other displayed fitness choices
are fixtures, not an exhaustive backend registry. Donor initial configuration values
are presentation defaults, not evidence of saved project values.

Evidence: SQX144-EV-000073 through SQX144-EV-000082 (applicable workspace claims).
Verification: 277 UI unit tests, 27 shared/portfolio browser journeys, UI typecheck/build
and repository CI passed on 2026-09-25. This qualifies the mock UI candidate only.
