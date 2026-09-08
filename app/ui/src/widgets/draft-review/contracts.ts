import type React from "react";

/**
 * Pure D-UI view and contribution contracts for FEAT-UI-REVIEW_DRAFTS.
 *
 * Implements accessible modal & drawer foundations, dirty draft state tracking,
 * and consequential action reviews with concurrency checks.
 * Never performs direct domain mutations or authoritative business decisions in the browser.
 */

/** Overlay display role defining accessibility semantics. */
export type OverlayRole = "dialog" | "alertdialog" | "drawer";

/** Navigation action for multi-step drawers replacing nested modals (MOD-005). */
export interface BackNavigationAction {
  readonly canGoBack: boolean;
  readonly onBack: () => void;
  readonly backLabel?: string;
  readonly stepTitle?: string;
}

/** Configuration options for the overlay foundation. */
export interface OverlayConfig {
  readonly isOpen: boolean;
  readonly title: string;
  readonly description?: string;
  readonly role?: OverlayRole;
  readonly closeOnEscape?: boolean;
  readonly closeOnBackdropClick?: boolean;
  readonly isDestructive?: boolean;
  readonly isDirty?: boolean;
  readonly initialFocusRef?: React.RefObject<HTMLElement | null>;
  readonly returnFocusRef?: React.RefObject<HTMLElement | null>;
  readonly onClose: () => void;
  readonly onWarnUnsavedChanges?: () => boolean;
  readonly backNavigation?: BackNavigationAction;
}

/** Validation error, warning, or client hint on a draft field. */
export interface DraftFieldValidation {
  readonly field: string;
  readonly message: string;
  readonly severity: "error" | "warning" | "hint";
  readonly source: "client" | "authoritative";
}

/** Aggregated validation summary separating client hints from authoritative errors. */
export interface ValidationSummary {
  readonly isValid: boolean;
  readonly errors: readonly DraftFieldValidation[];
  readonly warnings: readonly DraftFieldValidation[];
  readonly hints: readonly DraftFieldValidation[];
}

/** Individual field difference between original baseline and current draft. */
export interface DraftDiffEntry {
  readonly field: string;
  readonly label: string;
  readonly originalValue: unknown;
  readonly draftValue: unknown;
  readonly isDirty: boolean;
  readonly format?: (value: unknown) => string;
}

/** Typed draft container preserving modified form state without discarding unrelated drafts. */
export interface DraftState<T = Record<string, unknown>> {
  readonly original: T;
  readonly draft: T;
  readonly isDirty: boolean;
  readonly dirtyFields: readonly string[];
  readonly candidateHash: string;
}

/** Consequential action reversibility classification. */
export type ActionReversibility =
  | "REVERSIBLE"
  | "IRREVERSIBLE"
  | "REVERSIBLE_WITH_PENALTY";

/** Concrete identity of an object targeted by a consequential action. */
export interface ActionTarget {
  readonly id: string;
  readonly type: string;
  readonly name: string;
}

/** Consequential action review descriptor bound to exact scope, dependencies, and hashes. */
export interface ConsequentialAction {
  readonly actionId: string;
  readonly title: string;
  readonly target: ActionTarget;
  readonly affectedCount: number;
  readonly dependencies: readonly string[];
  readonly reversibility: ActionReversibility;
  readonly retainedState: readonly string[];
  readonly candidateHash: string;
  readonly expectedRevision: number | string;
  readonly requiresExplicitConfirmation?: boolean;
  readonly confirmationPhrase?: string;
  /** Prose explanation from AI/models; cannot synthesize clickable execution alone. */
  readonly modelProse?: string;
  /** Cryptographic or server-verified token proving the action was authorized by an engine. */
  readonly isServerAuthorized?: boolean;
}

/** Verification status of a consequential action review. */
export type ReviewStatus =
  | "VALID"
  | "STALE"
  | "INVALIDATED"
  | "PROSE_REJECTED";

/** Result of validating a consequential action against authoritative current state. */
export interface ConsequentialReviewResult {
  readonly status: ReviewStatus;
  readonly reason?: string;
  readonly canExecute: boolean;
}
