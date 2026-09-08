/**
 * Public surface for FEAT-UI-REVIEW_DRAFTS (Review typed edits and consequential action scope).
 */

export { DRAFT_REVIEW_MANIFEST } from "./manifest";
export {
  draftReviewConfigSchema,
  DEFAULT_DRAFT_REVIEW_CONFIG,
  parseDraftReviewConfig,
  resolveDraftReviewConfig,
  type DraftReviewConfig,
} from "./config";
export {
  type ActionReversibility,
  type ActionTarget,
  type BackNavigationAction,
  type ConsequentialAction,
  type ConsequentialReviewResult,
  type DraftDiffEntry,
  type DraftFieldValidation,
  type DraftState,
  type OverlayConfig,
  type OverlayRole,
  type ReviewStatus,
  type ValidationSummary,
} from "./contracts";
export {
  computeObjectHash,
  useDraftState,
  type UseDraftStateOptions,
  type UseDraftStateReturn,
} from "./useDraftState";
export {
  OverlayFoundation,
  type OverlayFoundationProps,
} from "./OverlayFoundation";
export {
  DraftReview,
  type DraftReviewProps,
} from "./DraftReview";
export {
  DraftReviewFeature,
  type DraftReviewFeatureProps,
} from "./feature";
