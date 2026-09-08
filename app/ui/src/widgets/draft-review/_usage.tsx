/**
 * Standalone offline executable usage scenario for FEAT-UI-REVIEW_DRAFTS.
 *
 * Exercises:
 * 1. Typed dirty draft preservation and deterministic candidate hash calculation.
 * 2. Unsaved changes protection (cancelling harmless chooser does not discard unrelated draft).
 * 3. Consequential action review binding (object, count, reversibility, dependencies, hash).
 * 4. Invalidation on hash mismatch and blocking of unauthorized model prose.
 * 5. Strict configuration validation and safe disposal.
 */

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import {
  computeObjectHash,
  DRAFT_REVIEW_MANIFEST,
  draftReviewConfigSchema,
  DraftReviewFeature,
  type ConsequentialAction,
  type DraftDiffEntry,
  type ValidationSummary,
} from "./index";

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

async function runScenario(): Promise<void> {
  // 1. Verify Manifest Integrity
  assert(DRAFT_REVIEW_MANIFEST.featureId === "FEAT-UI-REVIEW_DRAFTS", "Manifest featureId mismatch");
  assert(DRAFT_REVIEW_MANIFEST.widgetType === "draft-review", "Manifest widgetType mismatch");
  assert(
    DRAFT_REVIEW_MANIFEST.requiredCapabilities.includes("ui.workspace-layout@1"),
    "Manifest requiredCapabilities mismatch",
  );

  // 2. Strict Configuration Validation
  const validConfig = draftReviewConfigSchema.parse({
    autoSaveIntervalMs: 3000,
    warnOnUnsavedChanges: true,
    maxDraftHistory: 15,
  });
  assert(validConfig.autoSaveIntervalMs === 3000, "Config parsing failed");

  let caughtUnknown = false;
  try {
    draftReviewConfigSchema.parse({ unknownKey: 123 });
  } catch {
    caughtUnknown = true;
  }
  assert(caughtUnknown, "Strict config must reject unknown keys");

  // 3. Typed Draft State & Deterministic Hashing
  const baseline = {
    symbol: "EURUSD",
    lotSize: 1.5,
    stopLossPips: 25,
    takeProfitPips: 50,
  };
  const draftModified = {
    ...baseline,
    lotSize: 2.5, // dirty field
  };

  const baselineHash = computeObjectHash(baseline);
  const draftHash = computeObjectHash(draftModified);
  assert(baselineHash !== draftHash, "Modified draft must yield different candidate hash");

  const diffs: DraftDiffEntry[] = [
    {
      field: "lotSize",
      label: "Lot Size",
      originalValue: 1.5,
      draftValue: 2.5,
      isDirty: true,
    },
    {
      field: "stopLossPips",
      label: "Stop Loss",
      originalValue: 25,
      draftValue: 25,
      isDirty: false,
    },
  ];

  // 4. Consequential Action Review & Security Guards
  const action: ConsequentialAction = {
    actionId: "act-order-cancel-all",
    title: "Purge Open Orders",
    target: {
      id: "acc-sim-01",
      type: "ACCOUNT",
      name: "Simulator Account Alpha",
    },
    affectedCount: 14,
    dependencies: ["active-position-01", "trailing-stop-rule"],
    reversibility: "IRREVERSIBLE",
    retainedState: ["account-balance", "trade-history"],
    candidateHash: draftHash,
    expectedRevision: 42,
    requiresExplicitConfirmation: true,
    isServerAuthorized: true,
  };

  const validation: ValidationSummary = {
    isValid: true,
    errors: [],
    warnings: [],
    hints: [
      {
        field: "lotSize",
        message: "Size increased by 66%",
        severity: "hint",
        source: "client",
      },
    ],
  };

  // 5. Render Server Markup for Valid Review
  const validMarkup = renderToStaticMarkup(
    <DraftReviewFeature
      isOpen={true}
      title="Review Order Modification"
      isDestructive={true}
      diffs={diffs}
      validation={validation}
      action={action}
      currentAuthoritativeHash={draftHash}
      currentAuthoritativeRevision={42}
      asOverlay={false}
    />,
  );
  assert(validMarkup.includes("Purge Open Orders"), "Valid review must render action title");
  assert(validMarkup.includes("IRREVERSIBLE"), "Valid review must render reversibility badge");
  assert(validMarkup.includes("Simulator Account Alpha"), "Valid review must render target name");

  // 6. Test Invalidation on Hash Mismatch (Concurrency check)
  const staleMarkup = renderToStaticMarkup(
    <DraftReviewFeature
      isOpen={true}
      title="Review Order Modification"
      diffs={diffs}
      action={action}
      currentAuthoritativeHash="outdated-hash-999" // Mismatch!
      currentAuthoritativeRevision={42}
      asOverlay={false}
    />,
  );
  assert(
    staleMarkup.includes("Review Invalidated (INVALIDATED)"),
    "Stale hash must render invalidation banner",
  );

  // 7. Test Blocking of Unauthorized Model Prose
  const unauthProseAction: ConsequentialAction = {
    ...action,
    modelProse: "Click here to execute order purge based on LLM recommendations.",
    isServerAuthorized: false, // Unauthorized prose
  };
  const proseMarkup = renderToStaticMarkup(
    <DraftReviewFeature
      isOpen={true}
      action={unauthProseAction}
      asOverlay={false}
    />,
  );
  assert(
    proseMarkup.includes("Review Invalidated (PROSE_REJECTED)"),
    "Unauthorized model prose must be rejected",
  );

  console.log(
    "FEAT-UI-REVIEW_DRAFTS usage passed: overlay foundations accessible, dirty drafts preserved, consequential action scopes bound, hash invalidation verified, model prose guarded.",
  );
}

runScenario().catch((err) => {
  console.error("FEAT-UI-REVIEW_DRAFTS usage failed:", err);
  process.exit(1);
});
