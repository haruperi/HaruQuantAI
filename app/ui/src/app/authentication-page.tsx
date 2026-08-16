/**
 * Login/register access page (FR-UI-019).
 *
 * The access gate rendered at the dedicated `/login` route. Toggles between
 * login and register modes; calls `useAuth().login`/`register`; on success
 * redirects to `/` (the protected workspace). Recovers cleanly from invalid
 * or expired sessions by surfacing the bounded `ApiClientError` message.
 *
 * This is a separate route from the workspace because login/register is an
 * access page, not an internal workspace view. Layout is a split-screen design:
 * the form lives on the left panel, and a marketing/branding panel sits on the
 * right (hidden below ~860px).
 */

"use client";

import { useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  CandlestickChart,
  Lock,
  ShieldCheck,
  TrendingUp,
  User,
} from "lucide-react";

import { ApiClientError } from "@/clients";
import { useAuth } from "@/context";

/** Props accepted by `AuthenticationPage`. */
export interface AuthenticationPageProps {
  /** Optional initial mode; defaults to "login". */
  initialMode?: "login" | "register";
}

/** Marketing highlights shown on the right-hand brand panel. */
const BRAND_FEATURES: ReadonlyArray<{
  icon: typeof Activity;
  title: string;
  body: string;
}> = [
  {
    icon: TrendingUp,
    title: "Real-time market simulation",
    body: "Trade live price action across FX, futures and equities in a demo environment.",
  },
  {
    icon: Activity,
    title: "Analytics & evidence",
    body: "Every fill, drawdown and risk decision captured as auditable evidence.",
  },
  {
    icon: ShieldCheck,
    title: "Strategy governance",
    body: "Deterministic kill-switches and policy guardrails keep risk under control.",
  },
] as const;

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
      {/* Left: form + brand mark */}
      <div className="auth-form-panel">
        <div className="auth-brand-mark">
          <CandlestickChart className="auth-brand-icon" size={26} strokeWidth={2.25} />
          <span className="auth-brand-name">HaruQuantAI</span>
        </div>

        <div className="auth-form-wrap">
          <h1 className="auth-heading">
            {isLogin ? "Welcome back" : "Create your account"}
          </h1>
          <p className="auth-subheading">
            {isLogin
              ? "Sign in to your trading simulator workspace."
              : "Start simulating trades with full risk governance."}
          </p>

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
              <div className="auth-input-wrap">
                <User className="auth-input-icon" size={16} aria-hidden="true" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  placeholder="trader_id"
                  required
                  minLength={1}
                  maxLength={128}
                />
              </div>
            </label>
            <label className="auth-field">
              <span>Password</span>
              <div className="auth-input-wrap">
                <Lock className="auth-input-icon" size={16} aria-hidden="true" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  placeholder="••••••••"
                  required
                  minLength={1}
                  maxLength={1024}
                />
              </div>
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

          <p className="auth-disclaimer">
            Simulation environment only. Risk policy is enforced deterministically by the platform kill-switch.
          </p>
        </div>
      </div>

      {/* Right: marketing / branding panel */}
      <aside className="auth-brand-panel" aria-hidden="true">
        <div className="auth-brand-panel-glow" />
        <div className="auth-brand-panel-content">
          <div className="auth-brand-eyebrow">Trading Simulator</div>
          <h2 className="auth-brand-headline">
            Trade smarter.
            <br />
            Simulate with conviction.
          </h2>
          <p className="auth-brand-tagline">
            A professional-grade trading workspace for strategy research, evidence, and governance.
          </p>

          <ul className="auth-feature-list">
            {BRAND_FEATURES.map(({ icon: Icon, title, body }) => (
              <li key={title} className="auth-feature-item">
                <span className="auth-feature-icon">
                  <Icon size={18} strokeWidth={2} />
                </span>
                <span className="auth-feature-text">
                  <strong>{title}</strong>
                  <em>{body}</em>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
