/**
 * Manual command and session state tests (FEAT-UI-31, P4-T04).
 *
 * These panels must render only authoritative state: no optimistic position,
 * no invented fill, and no locally derived account figure.
 */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { submitCommand, getLiveSession, branchLiveSession } = vi.hoisted(() => ({
  submitCommand: vi.fn(),
  getLiveSession: vi.fn(),
  branchLiveSession: vi.fn(),
}));

vi.mock("@/clients", () => ({
  ApiClientError: class extends Error {},
  apiClients: {
    simulationWorkbench: { submitCommand, getLiveSession, branchLiveSession },
  },
}));

import type { LiveSessionProjection } from "@/clients";
import { ManualCommandPanel } from "./ManualCommandPanel";
import { SessionStatePanels } from "./SessionStatePanels";
import { WhatIfPanel, parseOverrides } from "./WhatIfPanel";

/** One authoritative session projection. */
function session(overrides: Record<string, unknown> = {}) {
  return {
    contract_version: "v1",
    schema_id: "api.live_session_projection.v1",
    session_id: "session-1",
    run_id: "advisory-1",
    mode: "practice",
    evidence_class: "practice",
    cursor: 12,
    timestamp: "2025-03-04T08:00:00Z",
    tick_count: 100,
    completed: false,
    account: {
      currency: "USD",
      balance: "10000.00",
      equity: "10025.00",
      margin: "120.00",
      free_margin: "9905.00",
      margin_level: "8354.17",
    },
    positions: [],
    orders: [],
    pending_intent_count: 0,
    exposure_blocked: false,
    state_hash: "hash",
    state_freshness: "fresh",
    permitted_actions: ["read", "step", "command"],
    ...overrides,
  } as unknown as LiveSessionProjection;
}

describe("ManualCommandPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    submitCommand.mockResolvedValue({
      status: "success",
      data: {
        receipt_id: "receipt-1",
        command_type: "close_position",
        status: "rejected",
        reason: "position not found",
        order_id: null,
        position_id: "pos-1",
      },
    });
    getLiveSession.mockResolvedValue({ status: "success", data: session() });
  });

  it("submits the selected command with only its own fields", async () => {
    render(<ManualCommandPanel sessionId="session-1" session={session()} />);

    fireEvent.change(screen.getByLabelText("Command"), {
      target: { value: "cancel_pending_order" },
    });
    fireEvent.change(screen.getByLabelText("Order ID"), {
      target: { value: "order-7" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send command/i }));

    await waitFor(() => expect(submitCommand).toHaveBeenCalledTimes(1));
    const [, input] = submitCommand.mock.calls[0];
    expect(input.command).toBe("cancel_pending_order");
    expect(input.order_id).toBe("order-7");
    expect(input).not.toHaveProperty("position_id");
  });

  it("renders the server receipt verbatim, including a rejection", async () => {
    render(<ManualCommandPanel sessionId="session-1" session={session()} />);
    fireEvent.click(screen.getByRole("button", { name: /send command/i }));

    const receipt = await screen.findByLabelText("Command receipt");
    expect(within(receipt).getByText("receipt-1")).toBeInTheDocument();
    expect(within(receipt).getByText("rejected")).toBeInTheDocument();
    expect(within(receipt).getByText("position not found")).toBeInTheDocument();
  });

  it("never invents a fill when the server rejects the command", async () => {
    render(<ManualCommandPanel sessionId="session-1" session={session()} />);
    fireEvent.click(screen.getByRole("button", { name: /send command/i }));

    await screen.findByLabelText("Command receipt");
    expect(screen.queryByText(/filled/i)).toBeNull();
  });

  it("re-reads authoritative session state after a command", async () => {
    const onSessionRefreshed = vi.fn();
    render(
      <ManualCommandPanel
        sessionId="session-1"
        session={session()}
        onSessionRefreshed={onSessionRefreshed}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /send command/i }));

    await waitFor(() => expect(getLiveSession).toHaveBeenCalledWith("session-1"));
    await waitFor(() => expect(onSessionRefreshed).toHaveBeenCalledTimes(1));
  });

  it("surfaces a command failure instead of a receipt", async () => {
    submitCommand.mockResolvedValue({
      status: "error",
      error: { message: "SIMULATION_SESSION_FINALIZED" },
    });
    render(<ManualCommandPanel sessionId="session-1" session={session()} />);
    fireEvent.click(screen.getByRole("button", { name: /send command/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "SIMULATION_SESSION_FINALIZED",
    );
    expect(screen.queryByLabelText("Command receipt")).toBeNull();
  });

  it("refuses to send while exposure is blocked", () => {
    render(
      <ManualCommandPanel
        sessionId="session-1"
        session={session({ exposure_blocked: true })}
      />,
    );
    expect(screen.getByRole("button", { name: /send command/i })).toBeDisabled();
    expect(
      screen.getByText("This session does not currently accept manual commands."),
    ).toBeInTheDocument();
  });
});

describe("SessionStatePanels", () => {
  it("renders authoritative account figures without deriving one", () => {
    render(<SessionStatePanels session={session()} />);
    expect(screen.getByText("10025.00")).toBeInTheDocument();
    expect(screen.getByText("9905.00")).toBeInTheDocument();
    expect(screen.getByText("8354.17")).toBeInTheDocument();
  });

  it("marks an account field the server omitted as unavailable", () => {
    render(
      <SessionStatePanels
        session={session({
          account: { currency: "USD", balance: "10000.00", equity: "10000.00" },
        })}
      />,
    );
    const account = screen.getByRole("region", { name: "Account" });
    expect(within(account).getAllByText("—").length).toBeGreaterThan(0);
    expect(within(account).queryByText("0")).toBeNull();
  });

  it("renders open positions and resting orders from the projection", () => {
    render(
      <SessionStatePanels
        session={session({
          positions: [
            {
              position_id: "pos-1",
              symbol: "EURUSD",
              side: "buy",
              volume: "0.10",
              open_price: "1.0850",
              unrealized_pnl: "12.50",
            },
          ],
          orders: [
            {
              order_id: "order-7",
              symbol: "EURUSD",
              side: "sell",
              order_type: "limit",
              volume: "0.10",
              price: "1.0900",
              status: "resting",
            },
          ],
        })}
      />,
    );
    expect(screen.getByText("pos-1")).toBeInTheDocument();
    expect(screen.getByText("12.50")).toBeInTheDocument();
    expect(screen.getByText("order-7")).toBeInTheDocument();
    expect(screen.getByText("resting")).toBeInTheDocument();
  });

  it("states plainly when nothing is open", () => {
    render(<SessionStatePanels session={session()} />);
    expect(screen.getByText("No position is open.")).toBeInTheDocument();
    expect(screen.getByText("No order is resting.")).toBeInTheDocument();
  });
});

describe("WhatIfPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    branchLiveSession.mockResolvedValue({
      status: "success",
      data: session({
        session_id: "session-2",
        evidence_class: "advisory",
        branch: {
          parent_session_id: "session-1",
          divergence_cursor: 12,
          overrides: {},
        },
      }),
    });
  });

  it("parses operator overrides into a bounded mapping", () => {
    expect(parseOverrides("spread_points=15\n\nvolume = 0.2\nbroken")).toEqual({
      spread_points: "15",
      volume: "0.2",
    });
  });

  it("creates an advisory branch without touching the parent", async () => {
    render(<WhatIfPanel sessionId="session-1" session={session()} />);
    fireEvent.change(screen.getByLabelText("Overrides"), {
      target: { value: "spread_points=15" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create branch/i }));

    await waitFor(() =>
      expect(branchLiveSession).toHaveBeenCalledWith("session-1", {
        overrides: { spread_points: "15" },
      }),
    );
    const result = await screen.findByLabelText("Branch result");
    expect(within(result).getByText("session-2")).toBeInTheDocument();
    expect(within(result).getByText("advisory")).toBeInTheDocument();
  });

  it("surfaces a branch failure instead of a phantom branch", async () => {
    branchLiveSession.mockResolvedValue({
      status: "error",
      error: { message: "branch unavailable" },
    });
    render(<WhatIfPanel sessionId="session-1" session={session()} />);
    fireEvent.click(screen.getByRole("button", { name: /create branch/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "branch unavailable",
    );
    expect(screen.queryByLabelText("Branch result")).toBeNull();
  });
});
