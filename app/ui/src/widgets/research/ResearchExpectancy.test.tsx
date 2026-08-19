/** Expectancy governance interaction evidence (FEAT-UI-28). */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ResearchExpectancy } from "./ResearchExpectancy";

const mocks = vi.hoisted(() => ({
  createExpectancy: vi.fn(),
  transitionExpectancy: vi.fn(),
  reload: vi.fn(),
  state: { transitionPermitted: false },
}));

vi.mock("@/clients", () => ({
  ApiClientError: class ApiClientError extends Error {},
  apiClients: {
    research: {
      createExpectancy: mocks.createExpectancy,
      transitionExpectancy: mocks.transitionExpectancy,
    },
  },
}));

vi.mock("./use-research", () => ({
  useExpectancy: () => ({
    data: {
      available: true,
      reason: null,
      profile: {
        profile_id: "exp-1",
        governance_state: "draft",
        strategy_ref: "strategy-1",
      },
      transition_permitted: mocks.state.transitionPermitted,
    },
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));

describe("ResearchExpectancy governance", () => {
  beforeEach(() => {
    mocks.state.transitionPermitted = false;
    mocks.transitionExpectancy.mockReset();
    mocks.createExpectancy.mockReset();
    mocks.reload.mockReset();
  });

  it("creates a draft from explicit completed-run measurements", async () => {
    mocks.state.transitionPermitted = true;
    mocks.createExpectancy.mockResolvedValue({
      status: "success",
      data: { available: true, profile: { profile_id: "id-created" } },
    });
    render(<ResearchExpectancy />);

    for (const [label, value] of [
      ["Completed run id", "rrn-1"],
      ["Exact version", "1"],
      ["Strategy ref", "strategy-demo"],
      ["Sample from", "2026-01-01T00:00"],
      ["Sample to", "2026-06-01T00:00"],
      ["Sample size", "100"],
      ["Win rate", "0.6"],
      ["Average win (R)", "2"],
      ["Average loss (R)", "1"],
      ["Expected value (R)", "0.8"],
      ["Max drawdown (R)", "4"],
      ["Minimum reward/risk", "1.5"],
    ]) {
      fireEvent.change(screen.getAllByLabelText(label)[0], {
        target: { value },
      });
    }
    fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

    await waitFor(() => expect(mocks.createExpectancy).toHaveBeenCalledOnce());
    expect(
      await screen.findByText("Draft profile id-created."),
    ).toBeInTheDocument();
  });

  it("does not expose mutation controls without research:govern", () => {
    render(<ResearchExpectancy />);

    expect(
      screen.queryByRole("button", { name: "Apply transition" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("caller lacks research:govern"),
    ).toBeInTheDocument();
  });

  it("submits bounded review evidence and refreshes owner truth", async () => {
    mocks.state.transitionPermitted = true;
    mocks.transitionExpectancy.mockResolvedValue({
      status: "success",
      data: { available: true, reason: null, profile: {} },
    });
    render(<ResearchExpectancy />);

    fireEvent.change(screen.getByLabelText("Target state"), {
      target: { value: "under_review" },
    });
    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "submit" },
    });
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "Evidence is ready for review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply transition" }));

    await waitFor(() =>
      expect(mocks.transitionExpectancy).toHaveBeenCalledWith("exp-1", {
        target_state: "under_review",
        decision: "submit",
        reason: "Evidence is ready for review.",
      }),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Transitioned to under_review.",
    );
    expect(mocks.reload).toHaveBeenCalledOnce();
  });

  it("disables the action while the governed request is pending", async () => {
    mocks.state.transitionPermitted = true;
    mocks.transitionExpectancy.mockReturnValue(new Promise(() => undefined));
    render(<ResearchExpectancy />);

    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "submit" },
    });
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "Evidence is ready for review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply transition" }));

    expect(
      await screen.findByRole("button", { name: "Transitioning…" }),
    ).toBeDisabled();
  });

  it("renders a bounded transition error", async () => {
    mocks.state.transitionPermitted = true;
    mocks.transitionExpectancy.mockResolvedValue({
      status: "error",
      error: { message: "Transition not permitted" },
    });
    render(<ResearchExpectancy />);

    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "approve" },
    });
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "Insufficient evidence." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply transition" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Transition not permitted",
    );
    expect(mocks.reload).not.toHaveBeenCalled();
  });
});
