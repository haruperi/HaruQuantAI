/**
 * Unit tests for ProtectedLayout (FR-API-054).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { ProtectedLayout } from "./protected-layout";

// Mock next/navigation useRouter.
const replaceMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

// Controllable auth state mock.
const authStateMock = vi.fn();
vi.mock("@/context", () => ({
  get useAuth() {
    return authStateMock;
  },
}));

// Mock AppShell to isolate layout behavior.
vi.mock("@/components/workflow", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div data-testid="shell">{children}</div>,
}));

function authValue(state: string) {
  return {
    state,
    principal: null,
    error: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  };
}

describe("ProtectedLayout — FR-API-054", () => {
  beforeEach(() => {
    authStateMock.mockReset();
    replaceMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("unauthenticatedAccessRedirects: unauthenticated triggers redirect to /login", async () => {
    authStateMock.mockReturnValue(authValue("unauthenticated"));
    render(<ProtectedLayout><span>workspace</span></ProtectedLayout>);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/login");
    });
  });

  it("renders a loading state without redirecting", async () => {
    authStateMock.mockReturnValue(authValue("loading"));
    render(<ProtectedLayout><span>workspace</span></ProtectedLayout>);
    expect(screen.getByRole("status")).toBeTruthy();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("authenticated renders children via AppShell", async () => {
    authStateMock.mockReturnValue(authValue("authenticated"));
    render(<ProtectedLayout><span data-testid="child">workspace</span></ProtectedLayout>);
    expect(screen.getByTestId("shell")).toBeTruthy();
    expect(screen.getByTestId("child")).toBeTruthy();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
