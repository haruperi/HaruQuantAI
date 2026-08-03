/**
 * Login/register access page (FR-API-053).
 *
 * The access gate rendered at the dedicated `/login` route. Toggles between
 * login and register modes; calls `useAuth().login`/`register`; on success
 * redirects to `/` (the protected workspace). Recovers cleanly from invalid
 * or expired sessions by surfacing the bounded `ApiClientError` message.
 *
 * This is a separate route from the workspace because login/register is an
 * access page, not an internal workspace view.
 */

"use client";

import { useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { ApiClientError } from "@/clients";
import { useAuth } from "@/context";

/** Props accepted by `AuthenticationPage`. */
export interface AuthenticationPageProps {
  /** Optional initial mode; defaults to "login". */
  initialMode?: "login" | "register";
}

/** Access-gate authentication page. */
export function AuthenticationPage({
  initialMode = "login",
}: AuthenticationPageProps = {}): ReactNode {
  const router = useRouter();
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
      }
      // On success, navigate to the protected workspace.
      router.push("/");
    } catch (cause) {
      setError(cause instanceof ApiClientError ? cause.message : "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  }

  const isLogin = mode === "login";

  return (
    <div className="auth-page" role="main" aria-label="Authentication">
      <div className="auth-card">
        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={isLogin}
            className={isLogin ? "auth-tab active" : "auth-tab"}
            onClick={() => {
              setMode("login");
              setError(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!isLogin}
            className={!isLogin ? "auth-tab active" : "auth-tab"}
            onClick={() => {
              setMode("register");
              setError(null);
            }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-field">
            <span>Username</span>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              minLength={1}
              maxLength={128}
            />
          </label>
          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isLogin ? "current-password" : "new-password"}
              required
              minLength={1}
              maxLength={1024}
            />
          </label>
          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}
          <button type="submit" className="auth-submit" disabled={submitting || !username.trim() || !password}>
            {submitting ? "…" : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
