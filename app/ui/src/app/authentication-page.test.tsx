/**
 * Unit tests for AuthenticationPage (FR-UI-019).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { AuthenticationPage } from "./authentication-page";

// Mock next/navigation useRouter.
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

// Mock useAuth with controllable login/register.
const loginMock = vi.fn();
const registerMock = vi.fn();
vi.mock("@/context", () => ({
  useAuth: () => ({
    state: "unauthenticated",
    principal: null,
    error: null,
    login: loginMock,
    register: registerMock,
    logout: vi.fn(),
  }),
}));

/** Fill the form inputs and return the submit button. */
function fillForm(username: string, password: string): HTMLElement {
  const inputs = screen.getAllByRole("textbox");
  fireEvent.change(inputs[0], { target: { value: username } });
  const pwd = document.querySelector('input[type="password"]') as HTMLInputElement;
  fireEvent.change(pwd, { target: { value: password } });
  // The submit button is the one inside the form with type=submit.
  return document.querySelector('button[type="submit"]') as HTMLButtonElement;
}

describe("AuthenticationPage — FR-UI-019", () => {
  beforeEach(() => {
    loginMock.mockReset();
    registerMock.mockReset();
    pushMock.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loginLogoutRecovery: successful login pushes to /", async () => {
    loginMock.mockResolvedValue({ user_id: "u1", username: "alice", expires_at: "x" });
    render(<AuthenticationPage />);
    const submit = fillForm("alice", "secretvalue"); // pragma: allowlist secret
    fireEvent.click(submit);
    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith("alice", "secretvalue"); // pragma: allowlist secret
      expect(pushMock).toHaveBeenCalledWith("/");
    });
  });

  it("shows a bounded error on login failure without exposing secrets", async () => {
    loginMock.mockRejectedValue(
      new (class extends Error {
        constructor() {
          super("invalid credentials");
          this.name = "ApiClientError";
        }
      })()
    );
    render(<AuthenticationPage />);
    const submit = fillForm("alice", "secretvalue"); // pragma: allowlist secret
    fireEvent.click(submit);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
    // The DOM must never contain the raw password.
    expect(document.body.textContent ?? "").not.toContain("secretvalue");
  });

  it("toggles to register mode", async () => {
    registerMock.mockResolvedValue({ user_id: "u2", username: "bob", expires_at: "x" });
    render(<AuthenticationPage />);
    // Click the Register tab (the tab button, not the submit).
    const tabs = screen.getAllByRole("tab");
    fireEvent.click(tabs[1]); // second tab = Register
    const submit = fillForm("bob", "secretvalue"); // pragma: allowlist secret
    expect(submit.textContent).toBe("Create Account");
    fireEvent.click(submit);
    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith("bob", "secretvalue"); // pragma: allowlist secret
      expect(pushMock).toHaveBeenCalledWith("/");
    });
  });
});
