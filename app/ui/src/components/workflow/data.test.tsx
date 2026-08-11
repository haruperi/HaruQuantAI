/** Tests for the complete Data capability workspace. */

import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClients } from "@/clients";

import { DataWorkspace } from "./data";

vi.mock("@/clients", async () => {
  const actual = await vi.importActual<typeof import("@/clients")>("@/clients");
  return {
    ...actual,
    apiClients: {
      ...actual.apiClients,
      data: { ...actual.apiClients.data, capabilities: vi.fn() },
    },
  };
});

describe("DataWorkspace", () => {
  beforeEach(() => vi.clearAllMocks());

  it("surfaces all fourteen registered Data capabilities", async () => {
    const capabilities = Array.from({ length: 14 }, (_, index) => ({
      feature_id: `FEAT-DATA-${String(index + 1).padStart(2, "0")}`,
      name: `Capability ${index + 1}`,
      summary: `Evidence ${index + 1}`,
      availability: "available" as const,
    }));
    vi.mocked(apiClients.data.capabilities).mockResolvedValue({
      status: "success",
      message: "ok",
      data: { capabilities },
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req-test",
        route: "/api/v1/data/capabilities",
        operation: "api.data.capabilities",
        side_effect: "read",
        timestamp: "2026-08-10T00:00:00Z",
        stale: false,
        idempotency_replayed: false,
      },
    });

    render(<DataWorkspace />);

    await waitFor(() => expect(screen.getAllByText(/FEAT-DATA-/)).toHaveLength(14));
    expect(screen.getByText("Capability 14")).toBeInTheDocument();
  });
});
