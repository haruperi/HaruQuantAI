import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TradingFeature } from "./feature";

describe("TradingFeature (FEAT-UI-06)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<TradingFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", { name: "Trading configuration error" }),
    ).toBeInTheDocument();
  });

  it("renders Trading widget when configuration is valid", () => {
    render(<TradingFeature />);

    expect(screen.getByRole("region", { name: "Trading" })).toBeInTheDocument();
  });
});
