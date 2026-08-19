/**
 * Analytics workspace route tests (FEAT-UI-32 / P1-T05).
 *
 * Verifies that the analytics routes parse run identifiers, multi-run query parameters,
 * and analytical segment sub-tabs correctly.
 */

import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AnalyticsLandingPage from "./page";
import AnalyticsComparePage from "./compare/page";
import AnalyticsRunPage from "./[runId]/[[...segments]]/page";

vi.mock("@/app/protected-layout", () => ({
  ProtectedLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-layout">{children}</div>
  ),
}));

let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  const unavailable = async () => ({
    status: "error" as const,
    error: { message: "not wired in this route test" },
  });
  return {
    ...actual,
    apiClients: {
      analyticsWorkbench: {
        getRun: unavailable,
        getWorkbenchPayload: unavailable,
        getTrades: unavailable,
        getTrade: unavailable,
        getArtifacts: unavailable,
        getReplayAnchors: unavailable,
        getSimulationResult: unavailable,
        listRuns: unavailable,
        archiveRun: unavailable,
      },
    },
  };
});

/** Render and flush the panels' authoritative reads before asserting. */
async function renderSettled(element: React.ReactElement) {
  let result!: ReturnType<typeof render>;
  await act(async () => {
    result = render(element);
  });
  return result;
}

describe("Analytics Routes", () => {
  it("AnalyticsLandingPage renders AnalyticsWorkspace with simulation link", () => {
    render(<AnalyticsLandingPage />);
    expect(screen.getByTestId("protected-layout")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /analytics workspace/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /launch simulation/i })).toHaveAttribute(
      "href",
      "/workstation/simulator/new",
    );
  });

  it("AnalyticsComparePage parses runs query parameter", () => {
    mockSearchParams = new URLSearchParams("runs=run-alpha,run-beta");
    render(<AnalyticsComparePage />);

    expect(screen.getByText(/comparing 2 runs: run-alpha, run-beta/i)).toBeInTheDocument();
  });

  it("AnalyticsRunPage defaults to overview tab when no segments provided", async () => {
    await renderSettled(<AnalyticsRunPage params={{ runId: "run-anlt-100" }} />);
    expect(screen.getByRole("heading", { level: 1, name: /run analysis: run-anlt-100/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /overview/i })).toHaveAttribute("aria-selected", "true");
  });

  it("AnalyticsRunPage renders the trade detail panel for a ticket segment", async () => {
    await renderSettled(
      <AnalyticsRunPage
        params={{ runId: "run-anlt-100", segments: ["trades", "1001"] }}
      />,
    );
    expect(
      screen.getByRole("region", { name: /trade detail/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /replay this trade/i }),
    ).toHaveAttribute(
      "href",
      "/workstation/simulator/replay/run-anlt-100?ticket=1001&return=" +
        encodeURIComponent("/workstation/analytics/run-anlt-100/trades/1001"),
    );
  });

  it("AnalyticsRunPage renders the trade ledger without a ticket segment", async () => {
    await renderSettled(
      <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["trades"] }} />,
    );
    expect(
      screen.getByRole("region", { name: /canonical trade ledger/i }),
    ).toBeInTheDocument();
  });

  it("AnalyticsRunPage selects correct tab based on segment parameter", async () => {
    const { rerender } = await renderSettled(
      <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["returns"] }} />,
    );
    expect(screen.getByRole("tab", { name: /returns & vami/i })).toHaveAttribute("aria-selected", "true");

    await act(async () => {
      rerender(
        <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["drawdown"] }} />,
      );
    });
    expect(screen.getByRole("tab", { name: /drawdown & risk/i })).toHaveAttribute("aria-selected", "true");

    await act(async () => {
      rerender(
        <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["trades"] }} />,
      );
    });
    expect(screen.getByRole("tab", { name: /trade analysis/i })).toHaveAttribute("aria-selected", "true");

    await act(async () => {
      rerender(
        <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["grouped"] }} />,
      );
    });
    expect(screen.getByRole("tab", { name: /grouped performance/i })).toHaveAttribute("aria-selected", "true");

    await act(async () => {
      rerender(
        <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["benchmark"] }} />,
      );
    });
    expect(screen.getByRole("tab", { name: /benchmark & costs/i })).toHaveAttribute("aria-selected", "true");

    await act(async () => {
      rerender(
        <AnalyticsRunPage params={{ runId: "run-anlt-100", segments: ["artifacts"] }} />,
      );
    });
    expect(screen.getByRole("tab", { name: /artifacts & replay/i })).toHaveAttribute("aria-selected", "true");
  });
});
