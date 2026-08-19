/**
 * Portfolio destination tests (FEAT-UI-31, P7-T02).
 *
 * A portfolio simulation must be configured explicitly: every component,
 * weight, risk budget, window bound, currency, and FX evidence reference is
 * required, and no portfolio is ever inferred from a multi-symbol batch.
 */

import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  PortfolioSimulationPanel,
  NO_PORTFOLIO_INFERENCE,
} from "./PortfolioSimulationPanel";

/** Fill the single default component and the shared fields. */
function fillValidConfiguration(): void {
  fireEvent.change(screen.getByLabelText("Component 1 symbol"), {
    target: { value: "EURUSD" },
  });
  fireEvent.change(screen.getByLabelText("Component 1 strategy"), {
    target: { value: "trend" },
  });
  fireEvent.change(screen.getByLabelText("Component 1 weight"), {
    target: { value: "1" },
  });
  fireEvent.change(screen.getByLabelText("Component 1 risk budget"), {
    target: { value: "0.02" },
  });
  fireEvent.change(screen.getByLabelText("Start"), {
    target: { value: "2025-01-01" },
  });
  fireEvent.change(screen.getByLabelText("End"), {
    target: { value: "2025-12-31" },
  });
  fireEvent.change(screen.getByLabelText("Account currency"), {
    target: { value: "USD" },
  });
  fireEvent.change(screen.getByLabelText("FX evidence reference"), {
    target: { value: "fx/2025-eod" },
  });
}

describe("PortfolioSimulationPanel", () => {
  it("states that a batch is not a portfolio", () => {
    render(<PortfolioSimulationPanel />);
    expect(screen.getByText(NO_PORTFOLIO_INFERENCE)).toBeInTheDocument();
  });

  it("refuses to submit an unconfigured portfolio", () => {
    const onSubmit = vi.fn();
    render(<PortfolioSimulationPanel onSubmit={onSubmit} />);
    expect(
      screen.getByRole("button", { name: /submit portfolio simulation/i }),
    ).toBeDisabled();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("requires an explicit weight and risk budget for every component", () => {
    render(<PortfolioSimulationPanel />);
    const problems = screen.getByRole("alert");
    expect(
      within(problems).getByText("Component 1 needs an explicit weight."),
    ).toBeInTheDocument();
    expect(
      within(problems).getByText("Component 1 needs an explicit risk budget."),
    ).toBeInTheDocument();
  });

  it("requires an explicit window, currency, and FX evidence", () => {
    render(<PortfolioSimulationPanel />);
    const problems = screen.getByRole("alert");
    expect(
      within(problems).getByText(
        "A portfolio simulation needs an explicit window.",
      ),
    ).toBeInTheDocument();
    expect(
      within(problems).getByText(
        "A portfolio simulation needs an explicit account currency.",
      ),
    ).toBeInTheDocument();
    expect(
      within(problems).getByText(
        "A portfolio simulation needs an FX evidence reference.",
      ),
    ).toBeInTheDocument();
  });

  it("requires component weights to sum to exactly one", () => {
    render(<PortfolioSimulationPanel />);
    fillValidConfiguration();
    fireEvent.click(screen.getByRole("button", { name: /add component/i }));
    fireEvent.change(screen.getByLabelText("Component 2 symbol"), {
      target: { value: "GBPUSD" },
    });
    fireEvent.change(screen.getByLabelText("Component 2 strategy"), {
      target: { value: "trend" },
    });
    fireEvent.change(screen.getByLabelText("Component 2 weight"), {
      target: { value: "0.4" },
    });
    fireEvent.change(screen.getByLabelText("Component 2 risk budget"), {
      target: { value: "0.02" },
    });

    expect(
      screen.getByText("Component weights must sum to exactly 1."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /submit portfolio simulation/i }),
    ).toBeDisabled();
  });

  it("submits an explicitly configured portfolio", () => {
    const onSubmit = vi.fn();
    render(<PortfolioSimulationPanel onSubmit={onSubmit} />);
    fillValidConfiguration();

    fireEvent.click(
      screen.getByRole("button", { name: /submit portfolio simulation/i }),
    );

    expect(onSubmit).toHaveBeenCalledWith({
      components: [
        {
          symbol: "EURUSD",
          strategyId: "trend",
          weight: "1",
          riskBudget: "0.02",
        },
      ],
      start: "2025-01-01",
      end: "2025-12-31",
      account_currency: "USD",
      fx_evidence_ref: "fx/2025-eod",
    });
  });

  it("rejects an inverted measurement window", () => {
    render(<PortfolioSimulationPanel />);
    fillValidConfiguration();
    fireEvent.change(screen.getByLabelText("End"), {
      target: { value: "2024-12-31" },
    });
    expect(
      screen.getByText("The start date must not be after the end date."),
    ).toBeInTheDocument();
  });
});
