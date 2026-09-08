# `draft-review` — `FEAT-UI-REVIEW_DRAFTS`

> **Feature ID:** `FEAT-UI-REVIEW_DRAFTS`
> **Domain:** `ui` (`D-UI`)
> **Status:** `ACCEPTED`
> **Selected Owner:** `app/ui/src/widgets/draft-review/`
> **First Release Milestone:** `U1`
> **Public Capability:** `ui.draft-review@1`
> **Required Capabilities:** `ui.workspace-layout@1`

---

## 1. Purpose & Architectural Boundaries

`FEAT-UI-REVIEW_DRAFTS` provides the accessible overlay and draft review foundation for HaruQuantAI. It enables operators to safely inspect, edit, abandon, or confirm typed drafts, parameter revisions, and consequential operations with explicit focus management, before/after diffs, and cryptographic hash verification.

Key Architectural Guarantees:
- **Presentation-Only Responsibility**: Reusable overlay, drawer, focus trap, and conflict presentation. It never makes domain validity or authoritative authorization decisions in the browser.
- **Nested Modal Prevention (`MOD-005`)**: Replaces nested modal traps with sequential drawer or sub-route step navigation with explicit back button.
- **Concurrency & Consequential Scope (`FR-003`)**: Binds action confirmation to exact target object, affected record count, dependencies, reversibility classification, retained state, candidate hash, and expected revision. Hash or revision mismatch immediately invalidates execution.
- **Model Prose Security Guard (`AT-003`)**: Unverified LLM or AI markdown prose cannot manufacture clickable server actions without structured, engine-authorized tokens.

---

## 2. Capabilities & Configuration

### 2.1 Provided Capability
- `ui.draft-review@1`: Public overlay foundation, dirty draft state hook, and consequential action review interface.

### 2.2 Required Capability
- `ui.workspace-layout@1` (`FEAT-UI-COMPOSE_WORKSPACE`): Layout and docking host integration.

### 2.3 Strict Configuration
Enforced via `draftReviewConfigSchema` (`config.ts`):
- `autoSaveIntervalMs` (number: 500–60,000, default `2000`): Debounce interval for draft preservation.
- `warnOnUnsavedChanges` (boolean, default `true`): Intercepts dismiss/escape on dirty drafts with confirmation prompt.
- `maxDraftHistory` (number: 1–100, default `20`): Maximum retained revision steps.
- `announceErrors` (boolean, default `true`): Screen reader announcements for validation updates.
- `requireConfirmationWordForIrreversible` (boolean, default `true`): Requires typing confirmation phrase for irreversible actions.

---

## 3. Package File Structure

| File | Responsibility |
| --- | --- |
| `manifest.ts` | Typed widget manifest (`DRAFT_REVIEW_MANIFEST`) for `ui.draft-review@1`. |
| `contracts.ts` | View and review contracts: `OverlayConfig`, `DraftState`, `ConsequentialAction`, `ValidationSummary`. |
| `config.ts` | Strict Zod configuration schema and defaults. |
| `useDraftState.ts` | Custom hook for typed draft tracking, candidate hashing, diff calculation, and unsaved changes warnings. |
| `OverlayFoundation.tsx` | Accessible modal & drawer overlay foundation with focus trap/restore, escape policy, and scroll locking. |
| `DraftReview.tsx` | Visual review of dirty draft changes, validation errors, consequential impact, and concurrency guards. |
| `feature.tsx` | Feature lifecycle adapter supporting standalone or overlay presentation. |
| `index.ts` | Public module exports. |
| `_usage.tsx` | Standalone executable offline usage recipe. |
| `__tests__/traceability.test.tsx` | Traceability tests for `AT-001`, `AT-002`, and `AT-003`. |
| `__tests__/lifecycle.test.tsx` | Lifecycle and removal tests for `ATN-001`. |

---

## 4. Requirements Traceability

| Requirement ID | Description | Acceptance Test | Status |
| --- | --- | --- | --- |
| `FR-TRC-UI-REVIEW_DRAFTS-001` | Provide accessible overlay foundation with focus trap/restore, labelled title/description, escape/scroll policy and restrained announcements. Nested modals are replaced with drawer/route navigation. | `AT-UI-REVIEW_DRAFTS-001` | PASS |
| `FR-TRC-UI-REVIEW_DRAFTS-002` | Preserve typed dirty draft state and show both client hints and authoritative field/summary errors. Cancelling harmless chooser discards no unrelated draft; abandoning long form warns on unsaved changes. | `AT-UI-REVIEW_DRAFTS-002` | PASS |
| `FR-TRC-UI-REVIEW_DRAFTS-003` | Bind confirmation/review to exact object, count, dependencies, reversibility, retained state, candidate hash and expected revision. Changed hash invalidates review; model prose cannot manufacture clickable action. | `AT-UI-REVIEW_DRAFTS-003` | PASS |
| `NFR-TRC-UI-REVIEW_DRAFTS-001` | Removing `FEAT-UI-REVIEW_DRAFTS` withdraws only its declared contribution; no dependent operation may silently select a substitute provider. | `ATN-UI-REVIEW_DRAFTS-001` | PASS |

---

## 5. Removal Behavior

Disabling and physically removing `FEAT-UI-REVIEW_DRAFTS` withdraws `ui.draft-review@1` and its scoped overlay contributions:
- Dependent review operations become unavailable with explicit typed feedback.
- Sibling workspace panels and layouts remain intact.
- Unmount releases focus traps, body scroll locks, and event listeners.
- No retained domain objects or backend state are mutated.
