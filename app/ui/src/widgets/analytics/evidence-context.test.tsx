/**
 * Realism and provenance panel tests (FEAT-UI-32, P3-T04).
 *
 * Both panels must render owner evidence verbatim, including exact hashes,
 * assumptions, limitations, diagnostics, and manifest metadata, and must mark
 * anything the owner omitted as unavailable.
 */

import { render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getSimulationResult, getWorkbenchPayload, getArtifacts } = vi.hoisted(
  () => ({
    getSimulationResult: vi.fn(),
    getWorkbenchPayload: vi.fn(),
    getArtifacts: vi.fn(),
  }),
);

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    analyticsWorkbench: {
      getSimulationResult,
      getWorkbenchPayload,
      getArtifacts,
    },
  },
}));

import { RealismPanel } from "./RealismPanel";
import { ProvenancePanel } from "./ProvenancePanel";

const RESULT = {
  run_id: "canonical-1",
  realism: {
    tick_model: "ohlc_interpolated",
    slippage: { model: "fixed_points", points: "1" },
    liquidity: "unbounded",
    sessions: ["london", "new_york"],
    data_quality: { gaps: 1, duplicates: 0 },
    assumptions: ["No partial fills are modelled."],
    limitations: ["Swap is applied at daily rollover only."],
    calibration: null,
    parity: "not_certified",
    fault_scenarios: [],
  },
  diagnostics: { warmup_bars: 50, rejected_signals: 3 },
};

const PAYLOAD = {
  contract_version: "v1",
  schema_id: "analytics.workbench_payload.v1",
  payload_id: "payload-1",
  report_id: "report-1",
  generated_at: "2026-01-02T00:11:00Z",
  warnings: [{ code: "short_sample", message: "Sample is short." }],
  quality_flags: [],
  lineage: {
    request_hash: "0xrequest",
    config_hash: "0xconfig",
    data_hash: "0xdata",
    report_hash: "0xreport",
    strategy_version: "1.2.0",
    dataset_revision: "rev-9",
    engine_version: "2.4.0",
    seed: 4242,
    precision: { decimal_places: 8 },
  },
  truncation: [],
  non_binding: true,
};

describe("RealismPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getSimulationResult.mockResolvedValue({ status: "success", data: RESULT });
  });

  it("renders every Simulation-owned realism block", async () => {
    render(<RealismPanel runId="canonical-1" />);
    expect(await screen.findByText("ohlc_interpolated")).toBeInTheDocument();
    expect(screen.getByText("unbounded")).toBeInTheDocument();
    expect(screen.getByText("london")).toBeInTheDocument();
    expect(
      screen.getByText("No partial fills are modelled."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Swap is applied at daily rollover only."),
    ).toBeInTheDocument();
    expect(screen.getByText("not_certified")).toBeInTheDocument();
  });

  it("marks an omitted realism block as unavailable, not empty", async () => {
    render(<RealismPanel runId="canonical-1" />);
    await screen.findByText("ohlc_interpolated");

    const calibration = screen
      .getByRole("heading", { name: "Calibration" })
      .parentElement as HTMLElement;
    expect(within(calibration).getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders Simulation diagnostics", async () => {
    render(<RealismPanel runId="canonical-1" />);
    const diagnostics = (await screen.findByRole("heading", {
      name: "Diagnostics",
    })).parentElement as HTMLElement;
    expect(within(diagnostics).getByText("warmup_bars")).toBeInTheDocument();
    expect(within(diagnostics).getByText("50")).toBeInTheDocument();
  });

  it("surfaces a read failure instead of an empty realism screen", async () => {
    getSimulationResult.mockResolvedValue({
      status: "error",
      error: { message: "simulation result unavailable" },
    });
    render(<RealismPanel runId="canonical-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "simulation result unavailable",
    );
  });
});

describe("ProvenancePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getWorkbenchPayload.mockResolvedValue({ status: "success", data: PAYLOAD });
    getArtifacts.mockResolvedValue({
      status: "success",
      data: {
        run_id: "canonical-1",
        artifacts: [
          { kind: "analytics-report", ref: "artifacts/analytics-report.json" },
        ],
      },
    });
  });

  it("renders every hash exactly as the owner recorded it", async () => {
    render(<ProvenancePanel runId="canonical-1" />);
    expect(await screen.findByText("0xrequest")).toBeInTheDocument();
    expect(screen.getByText("0xconfig")).toBeInTheDocument();
    expect(screen.getByText("0xdata")).toBeInTheDocument();
    expect(screen.getByText("0xreport")).toBeInTheDocument();
  });

  it("renders seed, versions, revisions, and precision metadata", async () => {
    render(<ProvenancePanel runId="canonical-1" />);
    expect(await screen.findByText("4242")).toBeInTheDocument();
    expect(screen.getByText("2.4.0")).toBeInTheDocument();
    expect(screen.getByText("rev-9")).toBeInTheDocument();
    expect(screen.getByText('{"decimal_places":8}')).toBeInTheDocument();
  });

  it("marks an absent lineage field as unavailable", async () => {
    render(<ProvenancePanel runId="canonical-1" />);
    await screen.findByText("0xrequest");
    const row = screen
      .getByText("Calibration checksum")
      .parentElement as HTMLElement;
    expect(within(row).getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders owner warnings and the artifact manifest", async () => {
    render(<ProvenancePanel runId="canonical-1" />);
    expect(await screen.findByText("Sample is short.")).toBeInTheDocument();
    expect(
      screen.getByText("artifacts/analytics-report.json"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull();
  });
});
