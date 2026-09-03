import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PriceLadderFeature } from "./feature";

describe("PriceLadderFeature (FEAT-UI-05)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<PriceLadderFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", {
        name: "Price Ladder (DOM) configuration error",
      }),
    ).toBeInTheDocument();
  });

  it("renders Price Ladder widget when configuration is valid", () => {
    render(<PriceLadderFeature />);

    expect(
      screen.getByRole("region", { name: "Price Ladder (DOM)" }),
    ).toBeInTheDocument();
  });
});
