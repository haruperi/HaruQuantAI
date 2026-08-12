/** Unit tests for IndicatorWorkspace. */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { IndicatorWorkspace } from "./indicators";
import { WorkspaceGrid } from "../layout/WorkspaceGrid";
import { useWorkspaceStore } from "../../features/workspaces";

function successEnvelope(data: unknown, route: string, operation: string): Response {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data,
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_t",
        route,
        operation,
        trace_id: null,
        side_effect: "read",
        duration_ms: 1,
        timestamp: "2026-08-03T12:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
}

const realFetch = globalThis.fetch;

const mockCatalogue = [
  {
    indicator_id: "sma",
    name: "Simple Moving Average",
    indicator_version: "1.0.0",
    formula_version: "1.0.0",
    tier: "core_mvp",
    required_columns: ["close"],
    parameter_schema: { period: { type: "integer", default: 20 } },
    output_templates: ["sma_{period}"],
    warmup_policy: "period",
    vectorized: true,
    multi_symbol: false,
    multi_timeframe: false,
    import_path: "app.services.indicators.trend.sma.sma",
    stability: "stable",
    workflow_eligibility: ["WF-INDI-001"],
  },
];

const mockCapabilities = [
  {
    indicator_id: "sma",
    indicator_version: "1.0.0",
    formula_version: "1.0.0",
    tier: "core_mvp",
    batch: true,
    vectorized: true,
    multi_symbol: false,
    multi_timeframe: false,
    unsupported_optional_modes: [],
    dependencies: ["numpy", "pandas"],
    unsupported_codes: [],
    official_workflow_eligibility: ["WF-INDI-001"],
  },
];

describe("IndicatorWorkspace", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/capabilities")) {
        return successEnvelope(mockCapabilities, "/api/v1/indicators/capabilities", "api.indicators.capabilities");
      }
      return successEnvelope(mockCatalogue, "/api/v1/indicators", "api.indicators.list");
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = realFetch;
    vi.restoreAllMocks();
  });

  it("fetches indicators catalogue and capabilities, rendering summary and list", async () => {
    render(<IndicatorWorkspace />);
    await waitFor(() => {
      expect(screen.getByText("Simple Moving Average")).toBeTruthy();
    });
    expect(screen.getByText("Total Built-ins")).toBeTruthy();
  });

  it("does not render mutation, calculation trigger, or data upload controls", async () => {
    const { container } = render(<IndicatorWorkspace />);
    await waitFor(() => expect(screen.getByText("Simple Moving Average")).toBeTruthy());
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/upload|calculate|compute|mutate|delete|register/i);
  });

  it("is reachable through WorkspaceGrid when rendering a widget of type indicators", async () => {
    // Set initial workspace with an indicators widget
    useWorkspaceStore.setState({
      activeWorkspaceId: 1,
      workspaces: [
        {
          id: 1,
          name: "Main Workspace",
          expandedWidgetId: null,
          widgets: [
            {
              id: "w_ind_1",
              type: "indicators",
              title: "Official Indicators",
              colSpan: 12,
              rowSpan: 4,
            },
          ],
        },
      ],
    });

    render(<WorkspaceGrid />);
    await waitFor(() => {
      expect(screen.getByText("Official Indicators")).toBeTruthy();
      expect(screen.getByText("Simple Moving Average")).toBeTruthy();
    });
  });
});
