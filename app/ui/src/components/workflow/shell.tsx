/**
 * Accessible auth-aware application shell (FR-API-046).
 *
 * Wraps the widget workspace with session gating: shows a loading state while
 * the session is being recovered, a login prompt when unauthenticated, and the
 * children when authenticated. A React error boundary catches render failures
 * without hiding governed controls. This is the first real `useAuth()` consumer.
 */

"use client";

import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from "react";

import { useAuth } from "@/context";

/** Props accepted by `AppShell`. */
export interface AppShellProps extends PropsWithChildren {
  /** Optional fallback rendered while the session is recovering. */
  loadingFallback?: ReactNode;
  /** Optional node rendered when the user is unauthenticated. */
  unauthenticatedFallback?: ReactNode;
}

/** Error boundary that surfaces a bounded message without unmounting controls. */
class ShellErrorBoundary extends Component<PropsWithChildren, { error: Error | null }> {
  public override state: { error: Error | null } = { error: null };

  public static getDerivedStateFromError(error: Error): { error: Error | null } {
    return { error };
  }

  public override componentDidCatch(error: Error, info: ErrorInfo): void {
    // Bounded: never log the full component stack or payload to avoid leaking
    // sensitive trading data; the error name/message are safe identifiers.
    void error;
    void info;
  }

  public override render(): ReactNode {
    if (this.state.error) {
      return (
        <div role="alert" className="workflow-error-boundary">
          <strong>Workspace error</strong>
          <p>A component failed to render. Governed controls remain available.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

/**
 * Auth-aware application shell.
 *
 * Renders children only when authenticated; a loading state during session
 * recovery; a login prompt when unauthenticated. An error boundary isolates
 * render failures so a broken widget does not hide the rest of the workspace.
 */
export function AppShell({
  children,
  loadingFallback,
  unauthenticatedFallback,
}: AppShellProps): ReactNode {
  const { state } = useAuth();

  if (state === "loading") {
    return (
      <div className="workflow-loading" role="status" aria-live="polite">
        {loadingFallback ?? <span>Recovering session…</span>}
      </div>
    );
  }

  if (state === "unauthenticated") {
    return (
      <div className="workflow-unauthenticated" role="status">
        {unauthenticatedFallback ?? (
          <span>Session expired or missing. Please sign in.</span>
        )}
      </div>
    );
  }

  return <ShellErrorBoundary>{children}</ShellErrorBoundary>;
}
