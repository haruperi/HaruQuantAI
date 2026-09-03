import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PositionsFeature } from "./feature";

describe("PositionsFeature (FEAT-UI-09)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<PositionsFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", {
        name: "Positions & Orders configuration error",
      }),
    ).toBeInTheDocument();
  });

  it("renders Positions & Orders grid when configuration is valid", () => {
    render(<PositionsFeature />);

    expect(
      screen.getByRole("region", { name: "Positions & Orders" }),
    ).toBeInTheDocument();
  });
});
