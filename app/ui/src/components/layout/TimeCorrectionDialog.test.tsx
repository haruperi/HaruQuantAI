import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TimeCorrectionDialog } from "./TimeCorrectionDialog";

describe("TimeCorrectionDialog", () => {
  it("applies a valid wall time and fixed UTC offset", async () => {
    const onApply = vi.fn().mockResolvedValue(true);
    render(
      <TimeCorrectionDialog
        currentUtcMs={Date.UTC(2026, 7, 17, 7, 15)}
        timezone="UTC"
        onApply={onApply}
        onClose={vi.fn()}
        onReset={vi.fn().mockResolvedValue(true)}
      />,
    );

    fireEvent.change(screen.getByLabelText("Date and time"), {
      target: { value: "2026-08-17T09:30" },
    });
    fireEvent.change(screen.getByLabelText("Time zone"), {
      target: { value: "UTC+2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));

    await waitFor(() => expect(onApply).toHaveBeenCalledWith({
      correctedUtcMs: Date.UTC(2026, 7, 17, 7, 30),
      timezone: "UTC+2",
    }));
  });

  it("supports cancel, reset, and Escape", async () => {
    const onClose = vi.fn();
    const onReset = vi.fn().mockResolvedValue(true);
    render(
      <TimeCorrectionDialog
        currentUtcMs={Date.UTC(2026, 7, 17, 7, 15)}
        timezone="UTC"
        onApply={vi.fn().mockResolvedValue(true)}
        onClose={onClose}
        onReset={onReset}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Reset to current time" }));
    await waitFor(() => expect(onReset).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("keeps the dialog open and reports a refused update", async () => {
    render(
      <TimeCorrectionDialog
        currentUtcMs={Date.UTC(2026, 7, 17, 7, 15)}
        timezone="UTC"
        onApply={vi.fn().mockResolvedValue(false)}
        onClose={vi.fn()}
        onReset={vi.fn().mockResolvedValue(true)}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("not saved");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("retains control focus when the parent supplies a new close callback", () => {
    const props = {
      currentUtcMs: Date.UTC(2026, 7, 17, 7, 15),
      timezone: "UTC",
      onApply: vi.fn().mockResolvedValue(true),
      onReset: vi.fn().mockResolvedValue(true),
    };
    const { rerender } = render(
      <TimeCorrectionDialog {...props} onClose={vi.fn()} />,
    );
    const timezone = screen.getByLabelText("Time zone");
    timezone.focus();

    rerender(<TimeCorrectionDialog {...props} onClose={vi.fn()} />);

    expect(timezone).toHaveFocus();
  });
});
