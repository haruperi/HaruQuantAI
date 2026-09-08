import type { WidgetManifest } from "../../types/widget-manifest";

/**
 * Manifest declaration for FEAT-UI-REVIEW_DRAFTS.
 *
 * Implements capability `ui.draft-review@1`, providing accessible modal/drawer overlay
 * foundations, focus traps, dirty draft state preservation, and consequential action reviews.
 */
export const DRAFT_REVIEW_MANIFEST: WidgetManifest = {
  featureId: "FEAT-UI-REVIEW_DRAFTS",
  widgetType: "draft-review",
  widgetVersion: 1,
  title: "Draft Review & Action Confirmation",
  description:
    "Review typed edits, form drafts, and consequential destructive operations with focus traps, diffs, and concurrency checks.",
  requiredCapabilities: ["ui.workspace-layout@1"],
  optionalCapabilities: [],
  placement: {
    defaultPanel: "center",
  },
  defaultDimensions: {
    width: 600,
    height: 480,
  },
  minimumDimensions: {
    width: 360,
    height: 300,
  },
  commands: [
    {
      id: "review-draft.confirm",
      title: "Confirm Action",
      destructive: false,
    },
    {
      id: "review-draft.cancel",
      title: "Cancel Review",
      destructive: false,
    },
    {
      id: "review-draft.discard",
      title: "Discard Unsaved Changes",
      destructive: true,
    },
  ],
  subscriptions: [],
  effects: {
    network: false,
    browserStorage: false,
    systemSettings: false,
  },
  accessibility: {
    ariaLive: "polite",
    landmarkRole: "dialog",
    keyboardNavigable: true,
  },
  removal: {
    persistedState: "none",
    description:
      "Removes draft-review contribution and overlay foundation. Transient draft state is cleared without mutating underlying backend data.",
  },
};
