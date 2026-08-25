import { describe, it, expect } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { FocusManagerProvider, useFocusManager } from "../../context/focus";

const FocusTestComponent = () => {
  const { announce, saveFocus, restoreFocus } = useFocusManager();

  return (
    <div>
      <button id="btn-1" type="button" onClick={() => saveFocus("test-btn")}>
        Save Focus
      </button>
      <button id="btn-2" type="button" onClick={() => restoreFocus("test-btn")}>
        Restore Focus
      </button>
      <button type="button" onClick={() => announce("Work completed", "polite")}>
        Announce Polite
      </button>
      <button type="button" onClick={() => announce("Risk limit breached", "assertive")}>
        Announce Assertive
      </button>
    </div>
  );
};

describe("FocusManager", () => {
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
});
