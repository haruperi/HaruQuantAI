/**
 * Immutable playback tests (FEAT-UI-31, P5-T01).
 *
 * Playback must replay ordered journal frames with their chain hashes, track
 * the resume cursor, carry the exact return URL back to Analytics, offer no
 * mutating control, and never show an order ticket.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { createSession, streamFrames } = vi.hoisted(() => ({
  createSession: vi.fn(),
  streamFrames: { current: [] as { sequence: number; payload: unknown }[] },
}));

vi.mock("@/clients", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    ApiClientError: class extends Error {},
    apiClients: { simulationSessions: { createSession } },
  };
});

vi.mock("@/context/streams", () => ({
  consumeStream: () => ({
    async *[Symbol.asyncIterator]() {
      for (const event of streamFrames.current) {
        yield event;
      }
    },
  }),
}));

vi.mock("@/clients/routes", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    simulationSessionRoutes: { frames: { id: "api.simulation.session_frames" } },
  };
});

import {
  SimulationPlaybackWorkspace,
  withoutOrderTickets,
} from "./SimulationPlaybackWorkspace";

const SESSION = {
  session_id: "playback-1",
  run_id: "canonical-1",
  journal_ref: "artifacts/journal.ndjson",
  journal_hash: "0xjournal",
  result_hash: "0xresult",
  engine_version: "2.4.0",
  read_only: true,
};

describe("SimulationPlaybackWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    streamFrames.current = [];
    createSession.mockResolvedValue({ status: "success", data: SESSION });
  });

  it("opens one playback session anchored on the requested trade", async () => {
    render(
      <SimulationPlaybackWorkspace runId="canonical-1" ticket="1001" />,
    );
    await waitFor(() =>
      expect(createSession).toHaveBeenCalledWith({
        run_id: "canonical-1",
        anchor_ticket: "1001",
      }),
    );
    expect(await screen.findByText("1001")).toBeInTheDocument();
  });

  it("renders the journal and result hashes the owner recorded", async () => {
    render(<SimulationPlaybackWorkspace runId="canonical-1" />);
    expect(await screen.findByText("0xjournal")).toBeInTheDocument();
    expect(screen.getByText("0xresult")).toBeInTheDocument();
    expect(screen.getByText("artifacts/journal.ndjson")).toBeInTheDocument();
  });

  it("replays frames in journal order and tracks the resume cursor", async () => {
    streamFrames.current = [
      {
        sequence: 1,
        payload: {
          event_type: "order_accepted",
          frame_hash: "0xf1",
          previous_hash: "0xf0",
          detail: { symbol: "EURUSD" },
        },
      },
      {
        sequence: 2,
        payload: {
          event_type: "position_opened",
          frame_hash: "0xf2",
          previous_hash: "0xf1",
          detail: { symbol: "EURUSD" },
        },
      },
    ];
    render(<SimulationPlaybackWorkspace runId="canonical-1" />);

    const table = await screen.findByRole("table");
    await waitFor(() =>
      expect(within(table).getByText("order_accepted")).toBeInTheDocument(),
    );
    const text = table.textContent ?? "";
    expect(text.indexOf("order_accepted")).toBeLessThan(
      text.indexOf("position_opened"),
    );
    expect(within(table).getByText("0xf2")).toBeInTheDocument();

    const facts = screen.getByText("Last-Event-ID").parentElement;
    expect(facts?.textContent).toContain("2");
  });

  it("never shows an order ticket beside immutable evidence", async () => {
    streamFrames.current = [
      {
        sequence: 1,
        payload: {
          event_type: "order_accepted",
          detail: {
            symbol: "EURUSD",
            ticket: "77777",
            client_order_id: "coid-9",
            order_id: "order-9",
          },
        },
      },
    ];
    render(<SimulationPlaybackWorkspace runId="canonical-1" />);

    const table = await screen.findByRole("table");
    await waitFor(() =>
      expect(within(table).getByText("order_accepted")).toBeInTheDocument(),
    );
    expect(table.textContent).toContain("EURUSD");
    expect(table.textContent).not.toContain("77777");
    expect(table.textContent).not.toContain("coid-9");
    expect(table.textContent).not.toContain("order-9");
  });

  it("strips every live-order identifier from a recorded detail", () => {
    expect(
      withoutOrderTickets({
        symbol: "EURUSD",
        ticket: "1",
        order_ticket: "2",
        client_order_id: "3",
        order_id: "4",
        price: "1.08",
      }),
    ).toEqual({ symbol: "EURUSD", price: "1.08" });
  });

  it("carries the exact return URL back to Analytics", async () => {
    const returnHref = "/workstation/analytics/canonical-1/trades/1001";
    render(
      <SimulationPlaybackWorkspace
        runId="canonical-1"
        ticket="1001"
        returnHref={returnHref}
      />,
    );
    const link = await screen.findByRole("link", {
      name: /return to analytics/i,
    });
    expect(link).toHaveAttribute("href", returnHref);
  });

  it("offers no mutating control", async () => {
    render(<SimulationPlaybackWorkspace runId="canonical-1" />);
    await screen.findByText("0xjournal");
    expect(screen.queryByRole("button")).toBeNull();
    expect(
      screen.getByText(/No order can be placed, modified, or cancelled here\./),
    ).toBeInTheDocument();
  });

  it("surfaces a stream failure instead of a silent stop", async () => {
    createSession.mockResolvedValue({
      status: "error",
      error: { message: "journal unavailable" },
    });
    render(<SimulationPlaybackWorkspace runId="canonical-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "journal unavailable",
    );
  });
});
