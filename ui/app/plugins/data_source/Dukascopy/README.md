# Dukascopy UI

This React plugin is a structural traceability pilot for
`SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy`. The target root is
`HARUQUANTAI_ROOT/ui/app/plugins/data_source/Dukascopy`.

## Feature registry

| Feature | Scope | Status |
| --- | --- | --- |
| FEAT-UI-DUKASCOPY-TRACEABILITY | Donor-relative UI files and retained mock Dukascopy screens | implemented; qualification evidence in the approved pilot walkthrough |

| Requirement | Target contract |
| --- | --- |
| FR-UI-DUKASCOPY-source-mapping | Each scoped HTML, JS and CSS artifact has one exact relative-name counterpart; all additional target files and exclusions are declared. |
| FR-UI-DUKASCOPY-workflow-preservation | Preserve add/filter/selection, broker mappings, error states, disclaimers, confirmation, focus and the simulated download lifecycle. |
| FR-UI-DUKASCOPY-clean-room | Use logical-root provenance and fingerprints; save no proprietary implementation, sensitive data or personal data. |

## Decision: DEC-UI-DUKASCOPY-TRACEABILITY

Preserve donor-relative subdirectories and filename casing. Map `.html` to `.tsx`,
`.js` to `.ts`, and `.css` to `.css`. Component exports use PascalCase. Controllers
are React hooks; services use typed adapters to existing mock stores. The target
architecture owns behavior. Angular implementation, backend routes and lifecycle
machinery are not imported.

`source-map.json` is the complete structural mapping: 6 template counterparts,
8 script counterparts, 2 stylesheet counterparts, and 3 excluded non-UI assets.
It owns provenance and mapping relationships; this README owns feature status.
Mapping coverage does not establish verified behavioral parity.

Owner-approved composition iteration (2026-10-06): fold the original helper
components into mapped UI files. CDN content belongs to
`import/cdnDisclaimerPopup.tsx`; fast confirmation stays local to
`import/importPopup.tsx`. Keep both separately named CDN counterpart boundaries.
The plugin contains 16 mapped files and 4 declared target-only files. Historical
pilot composition remains documented in its original task walkthrough.

## Composition and exceptions

- `module.ts` contributes existing provider commands to the Common ribbon.
  Child modules export commands and screens consumed by Data Manager.
- `add/addPopup.tsx` composes the catalogue view and
  `add/selectInstrumentsPopup.tsx`; `add/addPopupCtrl.ts` owns their shared state.
- `import/importPopup.tsx` composes the form, import-local CDN presentation and
  a file-local fast-download confirmation; `import/importPopupCtrl.ts` owns
  form/navigation state.
- `disclaimer/disclaimerPopup.tsx` is the existing standalone information screen.
  Modal owns Escape/focus restoration; the disclaimer controller unifies closing.
- `disclaimer/cdnDisclaimerPopup.tsx` preserves a separately named exported donor
  variant. No application route is added: external donor reachability is unverified
  from scoped references. It wraps `import/cdnDisclaimerPopup.tsx`, which owns
  the retained shared CDN content and is also mounted in downloads.
- `dukascopy.ts` and `dukascopyDownload.ts` retain shared utility APIs used by
  sibling providers. Their filenames are explicitly target-only exceptions.
- `DukascopyService.ts` delegates to current Common mock stores. Real provider
  downloads, CDN operation and backend behavior remain unimplemented.
- Existing catalogue data remains outside this UI subtree. The donor JAR, CSV and
  icon are excluded from UI counterpart counts; no donor binary is copied.

Existing disclaimer text and styles were relocated from repository UI files.
The two donor CDN templates have distinct fingerprints; the target shares retained
presentation while keeping separate counterpart boundaries. Translation-marker
differences do not imply a new target localization implementation.

## Verification and reuse

Run from `HARUQUANTAI_ROOT`:

```powershell
npm --prefix ui run test -- tests/unit/plugins/data_source/Dukascopy
npm --prefix ui run typecheck
npm --prefix ui run test
npm --prefix ui run build
npm --prefix ui run test:ui -- tests/e2e/data-manager-dukascopy.spec.ts tests/e2e/data-manager-dukascopy-download.spec.ts tests/e2e/data-manager-dukascopy-disclaimer.spec.ts --workers=1
```

Mapping validation rejects missing/misnamed counterparts, collisions, absolute
paths, invalid fingerprints, unresolved ownership/source IDs and unclassified
target files. Focused browser tests exercise retained workflows and accessible
dialog transitions. Tests use isolated browser-local storage and loopback requests.

The canonical reimplementation ledger/schema are absent; this manifest does not
replace them or claim ledger-schema validation. Current donor runtime parity has
not been independently established. Review this pilot's walkthrough before
authorizing equivalent work in other plugins; inventory each plugin independently.

## SQX145 reference qualification

Current donor root: `SQX_145_REFERENCE_ROOT`; source maps bind freshly inspected artifact identities. Retained UI functionality/status is unchanged; source differences and absent counterparts require task-level body/integration research. No runtime or connected backend parity is asserted.
