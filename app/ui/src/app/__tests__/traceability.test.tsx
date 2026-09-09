/** Requirement-level acceptance tests for FEAT-UI-SESSION_ACCESS. */

import { render, screen, waitFor } from "@testing-library/react";
import { StrictMode, useEffect } from "react";
import { describe, expect, it, vi } from "vitest";

import { apiClients } from "@/clients";
import type { AuthPrincipal, AuthState } from "@/context";

import { SessionAccessLifecycle } from "../lifecycle";
import {
  SessionAccessBoundary,
  deriveSessionAccess,
  useSessionScope,
} from "../session-access";

vi.mock("@/components/workflow", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="shell">{children}</div>
  ),
}));

function principal(accountId: string): AuthPrincipal {
  return {
    user_id: `user-${accountId}`,
    account_id: accountId,
    workspace_id: `workspace-${accountId}`,
    username: `operator-${accountId}`,
    expires_at: "2099-01-01T00:00:00Z",
    authentication_audit_ref: `audit-${accountId}`,
  };
}

interface ScopedConsumerProps {
  readonly clear?: () => void | Promise<void>;
  readonly observe?: (
    signal: AbortSignal,
    generation: number,
    isCurrent: (generation: number) => boolean,
  ) => void;
}

function ScopedConsumer({ clear, observe }: ScopedConsumerProps) {
  const scope = useSessionScope();
  useEffect(() => {
    observe?.(scope.signal, scope.generation, scope.isCurrent);
    if (observe) {
      void apiClients.auth.me({ signal: scope.signal }).catch(() => undefined);
    }
    return scope.registerProjection(
      "test.consumer-selection",
      clear ?? (() => undefined),
    );
  }, [clear, observe, scope]);
  return (
    <span data-testid="protected">
      {scope.scope.accountId}:{scope.generation}
    </span>
  );
}

describe("FEAT-UI-SESSION_ACCESS traceability", () => {
  it("test_trc_present_session_access_001", async () => {
    const lifecycle = new SessionAccessLifecycle();
    let releaseClear: (() => void) | undefined;
    let firstClear = true;
    const cleared = vi.fn(() => {
      if (!firstClear) return undefined;
      firstClear = false;
      return new Promise<void>((resolve) => {
        releaseClear = resolve;
      });
    });
    let accountASignal: AbortSignal | undefined;
    let accountAGeneration = -1;
    let accountAIsCurrent: ((generation: number) => boolean) | undefined;
    const observe = vi.fn((
      signal: AbortSignal,
      generation: number,
      isCurrent: (candidate: number) => boolean,
    ) => {
      if (accountASignal === undefined) {
        accountASignal = signal;
        accountAGeneration = generation;
        accountAIsCurrent = isCurrent;
      }
    });
    const request = vi
      .spyOn(apiClients.auth, "me")
      .mockImplementation(
        () =>
          new Promise<Awaited<ReturnType<typeof apiClients.auth.me>>>(
            () => undefined,
          ),
      );
    const view = render(
      <SessionAccessBoundary
        authState="authenticated"
        principal={principal("a")}
        error={null}
        lifecycle={lifecycle}
      >
        <ScopedConsumer clear={cleared} observe={observe} />
      </SessionAccessBoundary>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("protected")).toHaveTextContent("a:"),
    );
    expect(request).toHaveBeenCalledWith({ signal: accountASignal });

    view.rerender(
      <SessionAccessBoundary
        authState="authenticated"
        principal={principal("b")}
        error={null}
        lifecycle={lifecycle}
      >
        <ScopedConsumer clear={cleared} observe={observe} />
      </SessionAccessBoundary>,
    );
    expect(screen.queryByText(/^a:/)).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("Recovering session");
    expect(accountASignal?.aborted).toBe(true);
    expect(cleared).toHaveBeenCalledTimes(1);
    expect(accountAIsCurrent?.(accountAGeneration)).toBe(false);
    expect(screen.queryByText(/^b:/)).toBeNull();
    releaseClear?.();
    await waitFor(() =>
      expect(screen.getByTestId("protected")).toHaveTextContent("b:"),
    );
    expect(cleared).toHaveBeenCalledTimes(1);
    view.unmount();
    await lifecycle.dispose();
    request.mockRestore();
  });

  it("keeps an owned access lifecycle available through Strict Mode replay", async () => {
    const cleared = vi.fn();
    const view = render(
      <StrictMode>
        <SessionAccessBoundary
          authState="authenticated"
          principal={principal("strict")}
          error={null}
        >
          <ScopedConsumer clear={cleared} />
        </SessionAccessBoundary>
      </StrictMode>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("protected")).toHaveTextContent("strict:"),
    );
    expect(screen.queryByText("Session service unavailable")).toBeNull();
    view.unmount();
    await waitFor(() => expect(cleared).toHaveBeenCalledTimes(2));
  });

  it("test_trc_present_session_access_002", async () => {
    const cases: Array<[AuthState, string]> = [
      ["loading", "Recovering session"],
      ["unauthenticated", "Sign in required"],
      ["unauthorized", "Access denied"],
      ["expired", "Session expired"],
      ["unavailable", "Session service unavailable"],
    ];
    for (const [state, heading] of cases) {
      const view = render(
        <SessionAccessBoundary
          authState={state}
          principal={null}
          error={state === "unavailable" ? "offline" : null}
        >
          <span data-testid="forbidden">protected</span>
        </SessionAccessBoundary>,
      );
      expect(screen.getByRole("heading", { name: heading })).toBeTruthy();
      expect(screen.queryByTestId("forbidden")).toBeNull();
      view.unmount();
    }

    expect(deriveSessionAccess("authenticated", null)).toMatchObject({
      state: "unavailable",
      scope: null,
    });
    expect(
      deriveSessionAccess("authenticated", {
        ...principal("invalid-expiry"),
        expires_at: "not-a-timestamp",
      }),
    ).toMatchObject({ state: "unavailable", scope: null });
    expect(
      deriveSessionAccess("authenticated", principal("verified")),
    ).toMatchObject({
      state: "authorized",
      scope: { accountId: "verified", workspaceId: "workspace-verified" },
    });
  });
});
