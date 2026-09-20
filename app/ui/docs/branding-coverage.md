# HaruQuantAI branding coverage

`FR-UI-034` removes legacy StrategyQuant product names from rendered application surfaces while preserving reference evidence and compatibility identifiers.

## Included behavior

- The browser title, shell, navigation, settings, dialogs, data-source labels, broker labels, status messages, mock notices, and example editor content use HaruQuantAI terminology. The top-left brand contains only the logo and HaruQuantAI name, with no subtitle; its adjacent icon-only topbar control collapses or expands the sidebar without a visible Applications heading.
- Equity and Futures are shown without the legacy `SQ` prefix; the built-in broker label is `Default`.
- Versioned local-storage payloads are recursively normalized before validation, so saved legacy display labels do not reappear or invalidate otherwise compatible records.
- Existing lower-case `sqx-*` storage keys, internal TypeScript identifiers, CSS classes, and source-audit references remain stable because they are compatibility or implementation details rather than rendered branding.
- Legacy commercial destinations have no verified HaruQuantAI equivalent. Their controls therefore produce explicit local mock notices and do not navigate to a StrategyQuant or invented HaruQuantAI URL.

## Verification

- `src/app/branding.test.ts` covers direct and recursive label migration and compatibility-key preservation.
- Data-domain store tests cover normalization before persisted-state validation.
- `tests/branding-cleanup.spec.ts` checks the browser title, shell, one-line brand and adjacent navigation control, representative modules, settings surfaces, and a legacy persisted dataset.
- `tests/sidebar-navigation.spec.ts` checks the topbar control placement, absence of a sidebar Applications heading, persisted expanded/collapsed states, and dark/light presentation.
- Existing feature tests continue to verify the renamed labels and local-action behavior.

## Evidence boundary

StrategyQuant X remains the installed reference used to audit layout and behavior. Its paths, source citations, and explicit historical/reference statements remain in repository documentation; they are not product UI labels.
