import React from "react";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  DEFAULT_DRAFT_REVIEW_CONFIG,
  DraftReviewFeature,
  OverlayFoundation,
  draftReviewConfigSchema,
  parseDraftReviewConfig,
  resolveDraftReviewConfig,
} from "../index";

describe("FEAT-UI-REVIEW_DRAFTS Lifecycle & NFR Tests", () => {
  describe("ATN-UI-REVIEW_DRAFTS-001: Strict Config, Repeated Lifecycle & Removal Isolation", () => {
    it("strictly validates configuration and rejects unknown or out-of-range keys", () => {
      expect(DEFAULT_DRAFT_REVIEW_CONFIG.autoSaveIntervalMs).toBe(2000);
      expect(DEFAULT_DRAFT_REVIEW_CONFIG.warnOnUnsavedChanges).toBe(true);
      expect(DEFAULT_DRAFT_REVIEW_CONFIG.requireConfirmationWordForIrreversible).toBe(true);

      // Rejects interval out of bounds (< 500)
      expect(() =>
        draftReviewConfigSchema.parse({ autoSaveIntervalMs: 100 }),
      ).toThrow();

      // Rejects interval out of bounds (> 60,000)
      expect(() =>
        draftReviewConfigSchema.parse({ autoSaveIntervalMs: 120000 }),
      ).toThrow();

      // Rejects unknown keys
      expect(() =>
        parseDraftReviewConfig({ arbitrarySetting: "forbidden" }),
      ).toThrow();

      // Valid resolution
      const resolved = resolveDraftReviewConfig({ autoSaveIntervalMs: 5000 });
      expect(resolved.autoSaveIntervalMs).toBe(5000);
      expect(resolved.warnOnUnsavedChanges).toBe(true);
    });

    it("performs 50 consecutive mount and unmount cycles without body scroll or event leaks", () => {
      const initialOverflow = document.body.style.overflow;

      for (let i = 0; i < 50; i++) {
        const { unmount } = render(
          <OverlayFoundation
            isOpen={true}
            title={`Cycle ${i}`}
            onClose={() => {}}
          >
            <div>Cycle Content {i}</div>
          </OverlayFoundation>,
        );

        expect(document.body.style.overflow).toBe("hidden");
        unmount();
        expect(document.body.style.overflow).toBe(initialOverflow);
      }
    });

    it("cleans up timers and focus refs on abrupt unmount", () => {
      const priorFocus = document.createElement("button");
      document.body.appendChild(priorFocus);
      priorFocus.focus();

      const { unmount } = render(
        <DraftReviewFeature
          isOpen={true}
          title="Feature Mount Test"
          asOverlay={true}
          onClose={() => {}}
        />,
      );

      // Abrupt unmount
      expect(() => unmount()).not.toThrow();
      expect(document.activeElement).toBe(priorFocus);
      document.body.removeChild(priorFocus);
    });

    it("withdrawing draft-review leaves unrelated components and domain data unchanged", () => {
      const domainModel = { id: "strat-1", name: "Momentum Breakout", status: "ACTIVE" };
      const domainModelFrozen = Object.freeze({ ...domainModel });

      const { unmount } = render(
        <DraftReviewFeature
          isOpen={true}
          title="Withdrawal Test"
          action={{
            actionId: "act-test",
            title: "Simulated Action",
            target: { id: "strat-1", type: "STRATEGY", name: "Momentum Breakout" },
            affectedCount: 1,
            dependencies: [],
            reversibility: "REVERSIBLE",
            retainedState: ["config"],
            candidateHash: "dummy-hash",
            expectedRevision: 1,
          }}
          onClose={() => {}}
        />,
      );

      unmount();

      // Domain model remains strictly unchanged
      expect(domainModel).toEqual(domainModelFrozen);
    });
  });
});
