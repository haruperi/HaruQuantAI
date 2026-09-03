import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TradeLogFeature } from "./feature";

describe("TradeLogFeature (FEAT-UI-08)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<TradeLogFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", {
        name: "Trade Log configuration error",
      }),
    ).toBeInTheDocument();
  });

  it("renders Trade Log presentation when configuration is valid", () => {
    render(<TradeLogFeature />);

    expect(
      screen.getByRole("region", { name: "Trade Log" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("PRACTICE SIMULATOR TRADE LOG"),
    ).toBeInTheDocument();
  });
});
