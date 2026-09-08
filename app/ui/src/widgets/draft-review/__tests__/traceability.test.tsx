import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  DraftReview,
  OverlayFoundation,
  useDraftState,
  type ConsequentialAction,
} from "../index";

describe("FEAT-UI-REVIEW_DRAFTS Traceability Tests", () => {
  describe("AT-UI-REVIEW_DRAFTS-001: Accessible Overlay Foundation, Focus Management & Nested Modal Prevention", () => {
    it("renders dialog with accessible labels, focus trap, and body scroll lock", () => {
      const onClose = vi.fn();
      const priorOverflow = document.body.style.overflow;

      const { unmount } = render(
        <OverlayFoundation
          isOpen={true}
          title="Edit Configuration"
          description="Modify simulator parameters safely"
          role="dialog"
          onClose={onClose}
        >
          <div>
            <button type="button" data-testid="first-btn">First Button</button>
            <input type="text" data-testid="test-input" />
            <button type="button" data-testid="last-btn">Last Button</button>
          </div>
        </OverlayFoundation>,
      );

      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby", "overlay-title");
      expect(dialog).toHaveAttribute("aria-describedby", "overlay-description");
      expect(screen.getByRole("heading", { name: "Edit Configuration" })).toBeInTheDocument();
      expect(screen.getByText("Modify simulator parameters safely")).toBeInTheDocument();

      // Body scroll locked
      expect(document.body.style.overflow).toBe("hidden");

      // Escape closes dialog
      fireEvent.keyDown(dialog, { key: "Escape" });
      expect(onClose).toHaveBeenCalledTimes(1);

      unmount();
      // Body scroll restored
      expect(document.body.style.overflow).toBe(priorOverflow);
    });

    it("restores focus to previously active element upon close", () => {
      const triggerBtn = document.createElement("button");
      triggerBtn.textContent = "Open Modal";
      document.body.appendChild(triggerBtn);
      triggerBtn.focus();
      expect(document.activeElement).toBe(triggerBtn);

      const onClose = vi.fn();
      const { unmount } = render(
        <OverlayFoundation
          isOpen={true}
          title="Accessible Focus Test"
          onClose={onClose}
        >
          <button type="button">Inside Button</button>
        </OverlayFoundation>,
      );

      unmount();
      expect(document.activeElement).toBe(triggerBtn);
      document.body.removeChild(triggerBtn);
    });

    it("prevents nested modal traps by replacing with sequential back navigation (MOD-005)", () => {
      const onBack = vi.fn();
      const onClose = vi.fn();

      render(
        <OverlayFoundation
          isOpen={true}
          title="Step 2: Review Allocations"
          role="drawer"
          onClose={onClose}
          backNavigation={{
            canGoBack: true,
            onBack,
            backLabel: "Back to Step 1",
            stepTitle: "Step 1: Configuration",
          }}
        >
          <div>Step 2 Content</div>
        </OverlayFoundation>,
      );

      const backBtn = screen.getByLabelText("Back to Step 1");
      expect(backBtn).toBeInTheDocument();

      fireEvent.click(backBtn);
      expect(onBack).toHaveBeenCalledTimes(1);
    });
  });

  describe("AT-UI-REVIEW_DRAFTS-002: Typed Dirty Draft State & Unsaved Changes Guard", () => {
    function DraftTestComponent({ onDirtyChange }: { onDirtyChange?: (dirty: boolean) => void }) {
      const { state, diffs, validation, updateField, resetDraft, canSafelyClose } =
        useDraftState({
          initialData: { symbol: "EURUSD", lots: 1.0, stopLoss: 20 },
          clientValidators: {
            lots: (val) => (Number(val) <= 0 ? "Lot size must be positive" : undefined),
          },
          authoritativeErrors: [
            { field: "stopLoss", message: "Server rejects SL < 10 pips", severity: "error", source: "authoritative" },
          ],
        });

      React.useEffect(() => {
        onDirtyChange?.(state.isDirty);
      }, [state.isDirty, onDirtyChange]);

      return (
        <div>
          <span data-testid="is-dirty">{String(state.isDirty)}</span>
          <span data-testid="dirty-count">{state.dirtyFields.length}</span>
          <button type="button" onClick={() => updateField("lots", 2.5)} data-testid="modify-btn">
            Change Lots
          </button>
          <button type="button" onClick={resetDraft} data-testid="reset-btn">
            Reset
          </button>
          <span data-testid="can-close">{String(canSafelyClose())}</span>

          <DraftReview
            diffs={diffs}
            validation={validation}
          />
        </div>
      );
    }

    it("preserves typed dirty state, displays diffs, and combines client hints with authoritative errors", () => {
      render(<DraftTestComponent />);

      expect(screen.getByTestId("is-dirty")).toHaveTextContent("false");
      expect(screen.getByTestId("dirty-count")).toHaveTextContent("0");

      // Authoritative error is rendered
      expect(screen.getByText(/Server Error \(stopLoss\)/)).toBeInTheDocument();

      // Modify field
      fireEvent.click(screen.getByTestId("modify-btn"));
      expect(screen.getByTestId("is-dirty")).toHaveTextContent("true");
      expect(screen.getByTestId("dirty-count")).toHaveTextContent("1");
      expect(screen.getByTestId("can-close")).toHaveTextContent("false");

      // Reset restores original state
      fireEvent.click(screen.getByTestId("reset-btn"));
      expect(screen.getByTestId("is-dirty")).toHaveTextContent("false");
      expect(screen.getByTestId("dirty-count")).toHaveTextContent("0");
      expect(screen.getByTestId("can-close")).toHaveTextContent("true");
    });

    it("warns before discarding long or destructive forms when dirty", () => {
      const onClose = vi.fn();

      render(
        <OverlayFoundation
          isOpen={true}
          title="Dirty Form"
          isDirty={true}
          onClose={onClose}
        >
          <div>Form Content</div>
        </OverlayFoundation>,
      );

      // Attempt to close via close button
      const closeBtn = screen.getByLabelText("Close dialog");
      fireEvent.click(closeBtn);

      // Close must NOT be called immediately; confirmation guard must appear
      expect(onClose).not.toHaveBeenCalled();
      expect(screen.getByRole("alertdialog")).toBeInTheDocument();
      expect(screen.getByText("Discard unsaved changes?")).toBeInTheDocument();

      // Clicking 'Keep Editing' cancels prompt
      fireEvent.click(screen.getByText("Keep Editing"));
      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
      expect(onClose).not.toHaveBeenCalled();

      // Re-trigger and click 'Discard & Exit'
      fireEvent.click(closeBtn);
      fireEvent.click(screen.getByText("Discard & Exit"));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("AT-UI-REVIEW_DRAFTS-003: Consequential Action Binding, Concurrency Invalidation & Model Prose Guard", () => {
    const validAction: ConsequentialAction = {
      actionId: "action-delete-portfolio",
      title: "Delete Portfolio",
      target: {
        id: "port-99",
        type: "PORTFOLIO",
        name: "Growth Strategy Portfolio",
      },
      affectedCount: 28,
      dependencies: ["strategy-alpha", "execution-job-4"],
      reversibility: "IRREVERSIBLE",
      retainedState: ["trade-history-archive"],
      candidateHash: "hash-token-12345",
      expectedRevision: 10,
      requiresExplicitConfirmation: true,
      confirmationPhrase: "DELETE",
      isServerAuthorized: true,
    };

    it("binds confirmation to exact target, affected count, reversibility, and retained state", () => {
      const onConfirm = vi.fn();

      render(
        <DraftReview
          action={validAction}
          currentAuthoritativeHash="hash-token-12345"
          currentAuthoritativeRevision={10}
          onConfirm={onConfirm}
        />,
      );

      expect(screen.getByText("Delete Portfolio")).toBeInTheDocument();
      expect(screen.getByText("Growth Strategy Portfolio (PORTFOLIO)")).toBeInTheDocument();
      expect(screen.getByText(/28 items/)).toBeInTheDocument();
      expect(screen.getByText("IRREVERSIBLE")).toBeInTheDocument();
      expect(screen.getByText("trade-history-archive")).toBeInTheDocument();
      expect(screen.getByText("strategy-alpha")).toBeInTheDocument();

      // Irreversible requires typing phrase before confirmation button is enabled
      const confirmBtn = screen.getByRole("button", { name: /Confirm Irreversible Action/ });
      expect(confirmBtn).toBeDisabled();

      const phraseInput = screen.getByLabelText(/Type "DELETE" to confirm/);
      fireEvent.change(phraseInput, { target: { value: "DELETE" } });
      expect(confirmBtn).not.toBeDisabled();

      fireEvent.click(confirmBtn);
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    it("invalidates review when authoritative candidate hash changes", () => {
      const onConfirm = vi.fn();

      render(
        <DraftReview
          action={validAction}
          currentAuthoritativeHash="changed-server-hash-999" // Mismatch!
          currentAuthoritativeRevision={10}
          onConfirm={onConfirm}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent("Review Invalidated (INVALIDATED)");
      const confirmBtn = screen.getByRole("button", { name: /Confirm Irreversible Action/ });
      expect(confirmBtn).toBeDisabled();
    });

    it("blocks execution when revision conflict occurs", () => {
      const onConfirm = vi.fn();
      render(
        <DraftReview
          action={validAction}
          currentAuthoritativeHash="hash-token-12345"
          currentAuthoritativeRevision={11} // Server is on revision 11, action expected 10!
          onConfirm={onConfirm}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent("Review Invalidated (STALE)");
      expect(screen.getByRole("alert")).toHaveTextContent("expected revision 10, but current revision is 11");
      const confirmBtn = screen.getByRole("button", { name: /Confirm Irreversible Action/ });
      expect(confirmBtn).toBeDisabled();
    });

    it("blocks model prose from manufacturing clickable server actions without server authorization", () => {
      const onConfirm = vi.fn();
      const unverifiedProseAction: ConsequentialAction = {
        ...validAction,
        modelProse: "The assistant recommends purging all accounts immediately.",
        isServerAuthorized: false, // Unauthorized!
      };

      render(
        <DraftReview
          action={unverifiedProseAction}
          currentAuthoritativeHash="hash-token-12345"
          currentAuthoritativeRevision={10}
          onConfirm={onConfirm}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent("Review Invalidated (PROSE_REJECTED)");
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Unverified model prose explanation cannot manufacture executable server actions",
      );
      const confirmBtn = screen.getByRole("button", { name: /Confirm Irreversible Action/ });
      expect(confirmBtn).toBeDisabled();
    });
  });
});
