# AlgoWizard UI workspace

Owns the local visual strategy-authoring prototype. Product and architecture
boundaries remain in `docs/PROJECT.md` and `docs/ARCHITECTURE.md`.
No backend workspace, plugin catalog or executable strategy contract is defined.

## Feature registry

| Feature ID | Scope | Candidate state |
| --- | --- | --- |
| FEAT-UI-ALGOWIZARD_SHELL | Toolbar, empty state, examples, multiple drafts, file exchange | Implemented local UI; visual/interaction qualification recorded in task walkthrough |
| FEAT-UI-ALGOWIZARD_EDITORS | Full/Simple/picker views, rules, blocks, history | Implemented local editing; catalog and parameter forms are bounded fixtures |
| FEAT-UI-ALGOWIZARD_SETTINGS | Settings, charts, variables, debug, random/custom resources | Implemented local forms and resource editing; donor catalog completeness unverified |
| FEAT-UI-ALGOWIZARD_MOCK_FLOWS | Source preview, results, AI, Retester staging | Explicitly simulated; no quantitative or external-service execution |
| FEAT-UI-ALGOWIZARD_VERIFICATION | Behavioral tests and reference screenshots | See task walkthrough for actual command outcomes and remaining differences |

## State and file boundary

`algoWizardModel.ts` owns immutable UI draft shapes and bounded per-draft
undo/redo. React component state owns selection, menus, dialogs, recent files,
resources and mock result snapshots. Leaving the workspace or reloading resets
this session. Download a draft to preserve it. No database or host persistence
is accessed, and the legacy host rule store is not used by this workspace.

Files use `{format: "haruquantai.algowizard.ui", version: 1, draft: ...}`.
Import validates nested node shapes, identifiers and required display settings;
unknown versions, malformed data and SQX archives are rejected without replacing
the current draft. File imports are capped at 2 MB. Resource files use a separate
`haruquantai.algowizard.resources` envelope. These are prototype formats, not
ratified backend documents or SQX compatibility claims.

Source code is an inspectable pseudo-code/JSON preview, not executable code.
Backtests are cancelable deterministic fixture lifecycles. Results retain the
settings snapshot captured at mock run start. AI requests stay in the browser.
Save to Retester stages a name in the current local session and makes no change
to another workspace. Its confirmation explicitly explains this boundary.

## Donor evidence and limitations

Reference: `SQX_REFERENCE_ROOT/internal/web/AlgoWizard/`, installed build
144.2953. Source observations are paraphrased in the evidence ledger and task
interaction matrix. Vendor JavaScript, CSS, source archives and bitmap assets
are not embedded. Charts are independently drawn SVG illustrations.

The supplied landing, new-strategy, Files-menu and EMA-editor screens guided
visual matching. This candidate does **not** establish 100% SQX parity: nested
block schemas, all catalog entries, advanced ATM details, symmetric-rule
lowering, cloud services, platform source generation and host-native file flows
remain limited or substituted. These limitations concern the UI prototype and
must not be interpreted as backend implementation status.

The old `algoWizardTemplates.ts`, `StrategyTemplatesModal.tsx` and
`StrategyCodeExportModal.tsx` remain for compatibility with existing tests;
the new workspace does not invoke their legacy code generators.

## Verification

- `npm --prefix ui run test -- tests/unit/workspace/AlgoWizard`
- `npm --prefix ui run test:ui -- tests/e2e/algowizard-parity.spec.ts --workers=1`
- Repository qualification commands prescribed by `AGENTS.md`.

Evidence: `.agents/logs/2026-09-25T135524_algowizard-ui-parity/`.
