/** Focused compatibility tests for the protected application layout. */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { ProtectedLayout } from "./protected-layout";

const replaceMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

const authStateMock = vi.fn();
vi.mock("@/context", () => ({
  get useAuth() {
    return authStateMock;
  },
}));

vi.mock("@/components/workflow", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="shell">{children}</div>
  ),
}));

function authValue(state: string) {
  return {
    state,
    principal:
      state === "authenticated"
        ? {
            user_id: "user-1",
            account_id: "account-1",
            workspace_id: "workspace-1",
            username: "alice",
            expires_at: "2099-01-01T00:00:00Z",
            authentication_audit_ref: "audit-1",
          }
        : null,
    error: state === "unavailable" ? "offline" : null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  };
}

describe("ProtectedLayout — FEAT-UI-SESSION_ACCESS", () => {
  beforeEach(() => {
    authStateMock.mockReset();
    replaceMock.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("redirects unauthenticated access without mounting protected content", async () => {
    authStateMock.mockReturnValue(authValue("unauthenticated"));
    render(
      <ProtectedLayout>
        <span>workspace</span>
      </ProtectedLayout>,
    );
    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("workspace")).toBeNull();
  });

  it("renders recovery without redirecting", () => {
    authStateMock.mockReturnValue(authValue("loading"));
    render(
      <ProtectedLayout>
        <span>workspace</span>
      </ProtectedLayout>,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Recovering session");
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("renders protected children only after scope verification", async () => {
    authStateMock.mockReturnValue(authValue("authenticated"));
    render(
      <ProtectedLayout>
        <span data-testid="child">workspace</span>
      </ProtectedLayout>,
    );
    expect(screen.queryByTestId("child")).toBeNull();
    await waitFor(() => expect(screen.getByTestId("shell")).toBeTruthy());
    expect(screen.getByTestId("child")).toBeTruthy();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it.each(["unauthorized", "unavailable"])(
    "keeps protected content hidden for %s",
    (state) => {
      authStateMock.mockReturnValue(authValue(state));
      render(
        <ProtectedLayout>
          <span>workspace</span>
        </ProtectedLayout>,
      );
      expect(screen.getByRole("alert")).toBeTruthy();
      expect(screen.queryByText("workspace")).toBeNull();
      expect(replaceMock).not.toHaveBeenCalled();
    },
  );

  it("redirects an expired session without mounting protected content", async () => {
    authStateMock.mockReturnValue(authValue("expired"));
    render(
      <ProtectedLayout>
        <span>workspace</span>
      </ProtectedLayout>,
    );
    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("workspace")).toBeNull();
  });
});
