import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TradePlanFeature } from "./feature";

describe("TradePlanFeature (FEAT-UI-10)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<TradePlanFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", { name: "Trade Plan configuration error" }),
    ).toBeInTheDocument();
  });

  it("renders TradePlan presentation when configuration is valid", () => {
    render(<TradePlanFeature />);

    expect(
      screen.getByText("My Trade Plan (Practice Account)"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /SAVE PLAN/i }),
    ).toBeInTheDocument();
  });
});
