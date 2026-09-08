/** Compatibility tests for the shared widget renderer (FEAT-UI-EXECUTE_ORDERS). */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../widgets/research", () => ({
  ResearchDashboard: () => <div>V2 Research Dashboard</div>,
}));

import { WidgetContentHost } from "./WidgetContentHost";

describe("WidgetContentHost Research compatibility", () => {
  it("renders the V2 dashboard for a persisted Research widget", async () => {
    render(
      <WidgetContentHost
        widget={{ id: "research-legacy", type: "research", title: "Edge Lab" }}
      />
    );

    expect(await screen.findByText("V2 Research Dashboard")).toBeInTheDocument();
  });
});
