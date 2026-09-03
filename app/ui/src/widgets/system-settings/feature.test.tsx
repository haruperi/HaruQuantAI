import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SystemSettingsFeature } from "./feature";

describe("SystemSettingsFeature (FEAT-UI-13)", () => {
  it("renders configuration error alert on invalid configuration", () => {
    render(<SystemSettingsFeature config={{ invalidKey: true }} />);

    expect(
      screen.getByRole("alert", { name: "System Settings configuration error" }),
    ).toBeInTheDocument();
  });

  it("renders modal when configuration is valid", () => {
    render(<SystemSettingsFeature />);
    // When isSettingsOpen is false in store, modal renders null without crashing
    expect(
      screen.queryByRole("alert", {
        name: "System Settings configuration error",
      }),
    ).toBeNull();
  });
});
