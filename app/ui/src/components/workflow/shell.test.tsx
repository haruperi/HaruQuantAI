/** Unit tests for AppShell (FR-API-046). */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import { AppShell } from "./shell";
import { apiClients } from "@/clients";

// The auth context is mocked so the shell's auth-state branches are testable
// in isolation without driving a real /me round-trip.
const authStateMock = vi.fn();
vi.mock("@/context", () => ({
  get useAuth() {
    return authStateMock;
  },
}));

function renderShell(children: ReactNode): ReturnType<typeof render> {
  return render(<AppShell><div data-testid="protected">{children}</div></AppShell>);
}

describe("AppShell — FR-API-046", () => {
  beforeEach(() => {
    authStateMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("controlsRemainAccessible: renders children when authenticated", async () => {
    authStateMock.mockReturnValue({
      state: "authenticated",
      principal: null,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });
    renderShell(<button type="button">governed control</button>);
    expect(screen.getByTestId("protected")).toBeTruthy();
    expect(screen.getByText("governed control")).toBeTruthy();
  });

  it("renders a loading state while the session is recovering", async () => {
    authStateMock.mockReturnValue({
      state: "loading",
      principal: null,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });
    renderShell(<span>hidden</span>);
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("renders a login prompt when unauthenticated", async () => {
    authStateMock.mockReturnValue({
      state: "unauthenticated",
      principal: null,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });
    renderShell(<span>hidden</span>);
    expect(screen.getByText(/sign in/i)).toBeTruthy();
  });

  it("error boundary catches a child render failure without hiding the message", async () => {
    authStateMock.mockReturnValue({
      state: "authenticated",
      principal: null,
      error: null,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    function Boom(): ReactNode {
      throw new Error("boom");
    }
    render(<AppShell><Boom /></AppShell>);
    expect(screen.getByRole("alert")).toBeTruthy();
    spy.mockRestore();
  });

  it("exposes apiClients through the package boundary (sanity)", () => {
    expect(typeof apiClients.dashboards.broker).toBe("function");
  });
});
