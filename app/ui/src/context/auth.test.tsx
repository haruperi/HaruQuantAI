/**
 * Unit tests for AuthProvider (FR-API-042).
 *
 * Uses a fake `fetch` and `sessionStorage` so no network or real storage is
 * touched. React Testing Library renders a test consumer that reads the auth
 * context.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

import { AuthProvider, useAuth } from "./auth";
import { apiClients, ApiClientError } from "@/clients";

/** Test consumer that exposes the current auth state via the DOM. */
function AuthStateView() {
  const { state, principal } = useAuth();
  return (
    <div>
      <span data-testid="state">{state}</span>
      <span data-testid="username">{principal?.username ?? ""}</span>
    </div>
  );
}

/** Build a successful /auth/me identity response (server-authoritative). */
function okIdentity() {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data: {
        user_id: "u_1",
        username: "alice",
        expires_at: new Date(Date.now() + 3600_000).toISOString(),
      },
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_test",
        route: "/api/v1/auth/me",
        operation: "api.auth.me",
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

/** Build a 401 /auth/me response (no/expired session). */
function unauthorizedIdentity() {
  return new Response(
    JSON.stringify({
      status: "error",
      message: "auth required",
      data: null,
      error: {
        code: "AUTHENTICATION_REQUIRED",
        message: "session expired",
        details: {},
        request_id: "req_test",
        trace_id: null,
        retryable: false,
      },
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_test",
        route: "/api/v1/auth/me",
        operation: "api.auth.me",
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
    { status: 401, headers: { "Content-Type": "application/json" } }
  );
}

/** Build a successful login/register response carrying identity. */
function identityResponse(status = 200) {
  return new Response(
    JSON.stringify({
      status: "success",
      message: "ok",
      data: {
        user_id: "u_1",
        username: "alice",
        expires_at: new Date(Date.now() + 3600_000).toISOString(),
      },
      error: null,
      metadata: {
        contract_version: "v1",
        schema_id: "api.metadata.v1",
        request_id: "req_test",
        route: "/api/v1/auth/login",
        operation: "api.auth.login",
        trace_id: null,
        side_effect: "write",
        duration_ms: 1,
        timestamp: "2026-08-03T12:00:00Z",
        stale: false,
        stale_reason: null,
        next_cursor: null,
        page_size: null,
        idempotency_replayed: false,
      },
    }),
    { status, headers: { "Content-Type": "application/json" } }
  );
}

function installFetch(responder: () => Response): void {
  globalThis.fetch = vi.fn(async () => responder()) as unknown as typeof fetch;
}

const realFetch = globalThis.fetch;

beforeEach(() => {
  // jsdom provides sessionStorage; clear it before each test.
  window.sessionStorage.clear();
});

afterEach(() => {
  globalThis.fetch = realFetch;
  vi.restoreAllMocks();
});

describe("AuthProvider — FR-API-042", () => {
  it("recovery with a valid session and stored identity → authenticated", async () => {
    window.sessionStorage.setItem(
      "hq:identity",
      JSON.stringify({
        user_id: "u_1",
        username: "alice",
        expires_at: new Date(Date.now() + 3600_000).toISOString(),
      })
    );
    installFetch(okIdentity);
    render(
      <AuthProvider>
        <AuthStateView />
      </AuthProvider>
    );
    await waitFor(() => {
      expect(screen.getByTestId("state").textContent).toBe("authenticated");
    });
    expect(screen.getByTestId("username").textContent).toBe("alice");
  });

  it("expiredSessionRedirects: a 401 probe clears identity → unauthenticated", async () => {
    window.sessionStorage.setItem(
      "hq:identity",
      JSON.stringify({
        user_id: "u_1",
        username: "alice",
        expires_at: new Date(Date.now() + 3600_000).toISOString(),
      })
    );
    installFetch(unauthorizedIdentity);
    render(
      <AuthProvider>
        <AuthStateView />
      </AuthProvider>
    );
    await waitFor(() => {
      expect(screen.getByTestId("state").textContent).toBe("unauthenticated");
    });
    expect(screen.getByTestId("username").textContent).toBe("");
    expect(window.sessionStorage.getItem("hq:identity")).toBeNull();
  });

  it("loginStoresIdentity: login persists identity and authenticates", async () => {
    let call = 0;
    globalThis.fetch = vi.fn(async () => {
      call += 1;
      // First call: readiness probe returns 401 (no session yet); the login
      // call follows and returns identity.
      return call === 1 ? unauthorizedIdentity() : identityResponse();
    }) as unknown as typeof fetch;

    const loginResult: { value: { username: string } | null } = { value: null };
    function LoginView(): ReactNode {
      const { state, login } = useAuth();
      return (
        <div>
          <span data-testid="state">{state}</span>
          <button
            type="button"
            onClick={async () => {
              loginResult.value = await login("alice", "test-fixture-password"); // pragma: allowlist secret
            }}
          >
            sign in
          </button>
        </div>
      );
    }

    render(
      <AuthProvider>
        <LoginView />
      </AuthProvider>
    );
    await waitFor(() => {
      expect(screen.getByTestId("state").textContent).toBe("unauthenticated");
    });

    await act(async () => {
      screen.getByText("sign in").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("state").textContent).toBe("authenticated");
    });
    expect(loginResult.value?.username).toBe("alice");
    const stored = window.sessionStorage.getItem("hq:identity");
    expect(stored).toContain("alice");
  });

  it("logoutClearsIdentity: logout removes identity and unauthenticates", async () => {
    let call = 0;
    globalThis.fetch = vi.fn(async () => {
      call += 1;
      // 1: readiness 401 (initial), 2: login identity, 3: logout 204.
      if (call === 1) return unauthorizedIdentity();
      if (call === 2) return identityResponse();
      return new Response(null, { status: 204 });
    }) as unknown as typeof fetch;

    function LogoutView(): ReactNode {
      const { state, login, logout } = useAuth();
      return (
        <div>
          <span data-testid="state">{state}</span>
          <button
            type="button"
            onClick={() => login("alice", "test-fixture-password")} // pragma: allowlist secret
          >
            in
          </button>
          <button type="button" onClick={() => logout()}>
            out
          </button>
        </div>
      );
    }

    render(
      <AuthProvider>
        <LogoutView />
      </AuthProvider>
    );
    await waitFor(() =>
      expect(screen.getByTestId("state").textContent).toBe("unauthenticated")
    );
    await act(async () => screen.getByText("in").click());
    await waitFor(() =>
      expect(screen.getByTestId("state").textContent).toBe("authenticated")
    );
    await act(async () => screen.getByText("out").click());
    await waitFor(() =>
      expect(screen.getByTestId("state").textContent).toBe("unauthenticated")
    );
    expect(window.sessionStorage.getItem("hq:identity")).toBeNull();
  });

  it("tokenNeverInJs: identity storage never contains a session token", async () => {
    let call = 0;
    globalThis.fetch = vi.fn(async () => {
      call += 1;
      if (call === 1) return unauthorizedIdentity();
      return identityResponse();
    }) as unknown as typeof fetch;

    function LoginView(): ReactNode {
      const { login } = useAuth();
      return (
        <button
          type="button"
          onClick={() => login("alice", "test-fixture-password")} // pragma: allowlist secret
        >
          go
        </button>
      );
    }

    render(
      <AuthProvider>
        <LoginView />
      </AuthProvider>
    );
    await act(async () => screen.getByText("go").click());
    await waitFor(() => {
      const stored = window.sessionStorage.getItem("hq:identity") ?? "";
      expect(stored).not.toMatch(/token|password|secret/i);
      expect(stored).toContain("alice");
    });
  });

  it("useAuth throws when mounted outside a provider", () => {
    // Suppress the expected error from React for the assertion.
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<BadConsumer />)).toThrow(/AuthProvider/);
    spy.mockRestore();
  });

  function BadConsumer(): ReactNode {
    useAuth();
    return null;
  }

  it("exposes apiClients through the package boundary (sanity)", () => {
    expect(typeof apiClients.health.readiness).toBe("function");
    expect(ApiClientError).toBeInstanceOf(Function);
  });
});
