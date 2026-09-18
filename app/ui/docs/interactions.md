# Interaction map

## Shared rules

- Navigation changes the active application while preserving persisted settings and domain records.
- Project applications expose Progress, Full settings, and Results. The lower databank remains available for research applications.
- Selecting a databank row changes the identity used by every result view. Result views never copy strategy data into local component state.
- Modal `Cancel` closes without committing drafts. `Save` validates required values and commits to the central store. `Escape` restores focus by closing the top modal.
- Job transitions are `idle → running ↔ paused → completed|cancelled`. Results accepted before cancellation remain visible.
- Copy adds memberships to the destination and preserves source membership. Move adds destination membership and removes source membership.
- Theme, performance values, project settings, strategy edits, portfolio weights, workflow tasks, jobs, and databank memberships persist in versioned browser storage.

## Major flows

1. Choose Builder, edit data/genetic/risk/cross-check settings, start the simulated run, pause/resume/stop, and inspect coherent linked results.
2. Select strategies, sort/filter without losing identity, copy or move selected IDs, rename and annotate, or delete after confirmation.
3. Choose an optimization mode. The mode changes its applicable schedule fields; range values calculate the combination count.
4. Select a result view. Every table, metric, chart and source preview reads the same selected strategy revision.
5. Edit AlgoWizard rules, add/remove/reorder blocks, save the definition, and open generation/export entry points.
6. Change portfolio membership and weights; simulation derives a shared-capital series from linked member equity records.
7. Run a custom project. Enabled tasks execute in order and route the prior output label to the next task.
8. Data Manager operations show queued/running/completed status. Upload accepts CSV/TSV as the explicit browser-native mock interchange.

## Keyboard behavior

Tab follows DOM order, Enter activates focused controls, Space toggles checks, and Escape closes dialogs. Native select, input and button semantics provide focus and accessibility behavior. Dockview retains keyboard-enabled panel behavior without exposing arbitrary default rearrangement controls.
