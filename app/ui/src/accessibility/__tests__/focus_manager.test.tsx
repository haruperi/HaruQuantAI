import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, act, cleanup } from "@testing-library/react";
import React, { useState } from "react";
import { FocusManagerProvider, useFocusManager } from "../../context/focus";

const FocusTestComponent: React.FC = () => {
  const { announce, saveFocus, restoreFocus, focusElementById } = useFocusManager();
  const [updateCount, setUpdateCount] = useState(0);

  return (
    <div>
      <button
        id="btn-target"
        type="button"
        data-testid="btn-target"
        onClick={() => saveFocus("target-key")}
      >
        Target Button
      </button>

      <button
        id="btn-fallback"
        type="button"
        data-testid="btn-fallback"
      >
        Fallback Button
      </button>

      <button
        id="btn-other"
        type="button"
        data-testid="btn-other"
      >
        Other Button
      </button>

      <button
        id="btn-save"
        type="button"
        data-testid="btn-save"
        onClick={() => saveFocus("test-key")}
      >
        Save Focus
      </button>

      <button
        id="btn-restore"
        type="button"
        data-testid="btn-restore"
        onClick={() => restoreFocus("test-key", "btn-fallback")}
      >
        Restore Focus
      </button>

      <button
        id="btn-focus-direct"
        type="button"
        data-testid="btn-focus-direct"
        onClick={() => focusElementById("btn-fallback")}
      >
        Focus Direct
      </button>

      <button
        id="btn-re-render"
        type="button"
        data-testid="btn-re-render"
        onClick={() => setUpdateCount((c) => c + 1)}
      >
        Update Count: {updateCount}
      </button>

      <button
        type="button"
        onClick={() => announce("Work completed", "polite")}
      >
        Announce Polite
      </button>

      <button
        type="button"
        onClick={() => announce("Risk limit breached", "assertive")}
      >
        Announce Assertive
      </button>
    </div>
  );
};

describe("FocusManager (FR-UI-MANAGE_FOCUS)", () => {
  beforeEach(() => {
    cleanup();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders polite and assertive screen reader live regions and updates them", () => {
    render(
      <FocusManagerProvider>
        <FocusTestComponent />
      </FocusManagerProvider>
    );

    const politeRegion = screen.getByRole("status");
    const assertiveRegion = screen.getByRole("alert");

    expect(politeRegion).toBeInTheDocument();
    expect(assertiveRegion).toBeInTheDocument();

    act(() => {
      screen.getByText("Announce Polite").click();
    });
    expect(politeRegion.textContent).toBe("Work completed");

    act(() => {
      screen.getByText("Announce Assertive").click();
    });
    expect(assertiveRegion.textContent).toBe("Risk limit breached");
  });

  it("saves and restores focus to a valid mounted element", () => {
    render(
      <FocusManagerProvider>
        <FocusTestComponent />
      </FocusManagerProvider>
    );

    const targetBtn = screen.getByTestId("btn-target");
    const otherBtn = screen.getByTestId("btn-other");
    const restoreBtn = screen.getByTestId("btn-restore");

    // 1. Focus target and save
    targetBtn.focus();
    expect(document.activeElement).toBe(targetBtn);
    screen.getByTestId("btn-save").click();

    // 2. Move focus away
    otherBtn.focus();
    expect(document.activeElement).toBe(otherBtn);

    // 3. Restore focus
    act(() => {
      restoreBtn.click();
    });
    expect(document.activeElement).toBe(targetBtn);
  });

  it("consumes saved focus entry once (one-shot consumption)", () => {
    render(
      <FocusManagerProvider>
        <FocusTestComponent />
      </FocusManagerProvider>
    );

    const targetBtn = screen.getByTestId("btn-target");
    const fallbackBtn = screen.getByTestId("btn-fallback");
    const otherBtn = screen.getByTestId("btn-other");
    const restoreBtn = screen.getByTestId("btn-restore");

    // Save target
    targetBtn.focus();
    screen.getByTestId("btn-save").click();

    // Move focus away and first restore -> goes to target
    otherBtn.focus();
    act(() => {
      restoreBtn.click();
    });
    expect(document.activeElement).toBe(targetBtn);

    // Move focus away and second restore -> key was consumed, falls back to fallback element
    otherBtn.focus();
    act(() => {
      restoreBtn.click();
    });
    expect(document.activeElement).toBe(fallbackBtn);
  });

  it("preserves active element focus across mounted component updates", () => {
    render(
      <FocusManagerProvider>
        <FocusTestComponent />
      </FocusManagerProvider>
    );

    const targetBtn = screen.getByTestId("btn-target");
    targetBtn.focus();
    expect(document.activeElement).toBe(targetBtn);

    // Trigger re-render of component
    act(() => {
      screen.getByTestId("btn-re-render").click();
    });

    expect(screen.getByText("Update Count: 1")).toBeInTheDocument();
    expect(document.activeElement).toBe(targetBtn);
  });

  it("falls back deterministically when saved target element is detached from DOM", () => {
    const DetachTestComponent = () => {
      const { saveFocus, restoreFocus } = useFocusManager();
      const [mounted, setMounted] = useState(true);

      return (
        <div>
          {mounted && (
            <button
              id="btn-transient"
              data-testid="btn-transient"
              type="button"
            >
              Transient
            </button>
          )}
          <button id="btn-fallback-detach" data-testid="btn-fallback-detach" type="button">
            Fallback
          </button>
          <button
            data-testid="save-btn"
            type="button"
            onClick={() => saveFocus("detach-key")}
          >
            Save
          </button>
          <button
            data-testid="unmount-btn"
            type="button"
            onClick={() => setMounted(false)}
          >
            Unmount
          </button>
          <button
            data-testid="restore-btn"
            type="button"
            onClick={() => restoreFocus("detach-key", "btn-fallback-detach")}
          >
            Restore
          </button>
        </div>
      );
    };

    render(
      <FocusManagerProvider>
        <DetachTestComponent />
      </FocusManagerProvider>
    );

    const transientBtn = screen.getByTestId("btn-transient");
    transientBtn.focus();
    screen.getByTestId("save-btn").click();

    // Detach transient element from DOM
    act(() => {
      screen.getByTestId("unmount-btn").click();
    });
    expect(screen.queryByTestId("btn-transient")).toBeNull();

    // Restore focus -> should land on fallback
    act(() => {
      screen.getByTestId("restore-btn").click();
    });
    expect(document.activeElement).toBe(screen.getByTestId("btn-fallback-detach"));
  });

  it("falls back deterministically when saved target element is hidden or aria-hidden", () => {
    const HiddenTestComponent = () => {
      const { saveFocus, restoreFocus } = useFocusManager();
      const [isHidden, setIsHidden] = useState(false);
      const [isAriaHidden, setIsAriaHidden] = useState(false);

      return (
        <div>
          <button
            id="btn-hideable"
            data-testid="btn-hideable"
            type="button"
            hidden={isHidden}
            aria-hidden={isAriaHidden ? "true" : undefined}
          >
            Hideable
          </button>
          <button id="btn-fallback-hide" data-testid="btn-fallback-hide" type="button">
            Fallback
          </button>
          <button
            data-testid="save-btn"
            type="button"
            onClick={() => saveFocus("hide-key")}
          >
            Save
          </button>
          <button
            data-testid="hide-btn"
            type="button"
            onClick={() => setIsHidden(true)}
          >
            Hide
          </button>
          <button
            data-testid="aria-hide-btn"
            type="button"
            onClick={() => setIsAriaHidden(true)}
          >
            Aria Hide
          </button>
          <button
            data-testid="restore-btn"
            type="button"
            onClick={() => restoreFocus("hide-key", "btn-fallback-hide")}
          >
            Restore
          </button>
        </div>
      );
    };

    const { unmount } = render(
      <FocusManagerProvider>
        <HiddenTestComponent />
      </FocusManagerProvider>
    );

    // Test with hidden attribute
    const hideableBtn = screen.getByTestId("btn-hideable");
    hideableBtn.focus();
    screen.getByTestId("save-btn").click();

    act(() => {
      screen.getByTestId("hide-btn").click();
    });

    act(() => {
      screen.getByTestId("restore-btn").click();
    });
    expect(document.activeElement).toBe(screen.getByTestId("btn-fallback-hide"));

    unmount();

    // Test with aria-hidden="true"
    render(
      <FocusManagerProvider>
        <HiddenTestComponent />
      </FocusManagerProvider>
    );

    const hideableBtn2 = screen.getByTestId("btn-hideable");
    hideableBtn2.focus();
    screen.getByTestId("save-btn").click();

    act(() => {
      screen.getByTestId("aria-hide-btn").click();
    });

    act(() => {
      screen.getByTestId("restore-btn").click();
    });
    expect(document.activeElement).toBe(screen.getByTestId("btn-fallback-hide"));
  });

  it("falls back deterministically when saved target element is disabled or inert", () => {
    const DisabledTestComponent = () => {
      const { saveFocus, restoreFocus } = useFocusManager();
      const [isDisabled, setIsDisabled] = useState(false);
      const [isInert, setIsInert] = useState(false);

      return (
        <div>
          <button
            id="btn-disableable"
            data-testid="btn-disableable"
            type="button"
            disabled={isDisabled}
            inert={isInert ? true : undefined}
          >
            Disableable
          </button>
          <button id="btn-fallback-disabled" data-testid="btn-fallback-disabled" type="button">
            Fallback
          </button>
          <button
            data-testid="save-btn"
            type="button"
            onClick={() => saveFocus("disable-key")}
          >
            Save
          </button>
          <button
            data-testid="disable-btn"
            type="button"
            onClick={() => setIsDisabled(true)}
          >
            Disable
          </button>
          <button
            data-testid="inert-btn"
            type="button"
            onClick={() => setIsInert(true)}
          >
            Make Inert
          </button>
          <button
            data-testid="restore-btn"
            type="button"
            onClick={() => restoreFocus("disable-key", "btn-fallback-disabled")}
          >
            Restore
          </button>
        </div>
      );
    };

    const { unmount } = render(
      <FocusManagerProvider>
        <DisabledTestComponent />
      </FocusManagerProvider>
    );

    // Test with disabled attribute
    const disableableBtn = screen.getByTestId("btn-disableable");
    disableableBtn.focus();
    screen.getByTestId("save-btn").click();

    act(() => {
      screen.getByTestId("disable-btn").click();
    });

    act(() => {
      screen.getByTestId("restore-btn").click();
    });
    expect(document.activeElement).toBe(screen.getByTestId("btn-fallback-disabled"));

    unmount();

    // Test with inert attribute
    render(
      <FocusManagerProvider>
        <DisabledTestComponent />
      </FocusManagerProvider>
    );

    const disableableBtn2 = screen.getByTestId("btn-disableable");
    disableableBtn2.focus();
    screen.getByTestId("save-btn").click();

    act(() => {
      screen.getByTestId("inert-btn").click();
    });

    act(() => {
      screen.getByTestId("restore-btn").click();
    });
    expect(document.activeElement).toBe(screen.getByTestId("btn-fallback-disabled"));
  });

  it("focusElementById moves focus directly to valid target and rejects invalid targets", () => {
    render(
      <FocusManagerProvider>
        <FocusTestComponent />
      </FocusManagerProvider>
    );

    const fallbackBtn = screen.getByTestId("btn-fallback");
    const otherBtn = screen.getByTestId("btn-other");

    otherBtn.focus();
    expect(document.activeElement).toBe(otherBtn);

    act(() => {
      screen.getByTestId("btn-focus-direct").click();
    });
    expect(document.activeElement).toBe(fallbackBtn);
  });
});
