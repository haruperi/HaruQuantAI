/** React presentation bridge for verified session access and scope changes. */

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
  type ReactNode,
} from "react";

import { AppShell } from "@/components/workflow";
import type { AuthPrincipal, AuthState } from "@/context";

import type {
  SessionAccessState,
  SessionScopeSnapshot,
  SessionScopeView,
  VerifiedSessionScope,
} from "./contracts";
import { SessionAccessLifecycle, sessionScopeKey } from "./lifecycle";

const SessionScopeContext = createContext<SessionScopeView | null>(null);

/** Props accepted by the verified session-access boundary. */
export interface SessionAccessBoundaryProps extends PropsWithChildren {
  readonly authState: AuthState;
  readonly principal: AuthPrincipal | null;
  readonly error: string | null;
  readonly lifecycle?: SessionAccessLifecycle;
}

interface DesiredAccess {
  readonly state: SessionAccessState;
  readonly scope: VerifiedSessionScope | null;
}

/** Convert the public auth projection into this feature's display contract. */
export function deriveSessionAccess(
  authState: AuthState,
  principal: AuthPrincipal | null,
): DesiredAccess {
  if (authState !== "authenticated") {
    return {
      state: authState === "loading" ? "recovering" : authState,
      scope: null,
    };
  }
  if (
    principal === null ||
    principal.user_id.trim().length === 0 ||
    principal.account_id.trim().length === 0 ||
    principal.workspace_id.trim().length === 0
  ) {
    return { state: "unavailable", scope: null };
  }
  const expiresAt = Date.parse(principal.expires_at);
  if (!Number.isFinite(expiresAt)) {
    return { state: "unavailable", scope: null };
  }
  if (expiresAt <= Date.now()) {
    return { state: "expired", scope: null };
  }
  return {
    state: "authorized",
    scope: {
      principalId: principal.user_id,
      accountId: principal.account_id,
      workspaceId: principal.workspace_id,
    },
  };
}

/** Render one bounded non-protected state with accessible status semantics. */
function AccessStatus({ state }: { readonly state: SessionAccessState }): ReactNode {
  const content = {
    recovering: ["Recovering session", "Verifying your current account and workspace scope."],
    unauthenticated: ["Sign in required", "Redirecting to the sign-in page."],
    unauthorized: ["Access denied", "Your current account is not authorized for this workspace."],
    expired: ["Session expired", "Redirecting so you can verify your identity again."],
    unavailable: ["Session service unavailable", "Access cannot be verified right now. Try again later."],
    authorized: ["Access verified", "Your current workspace scope is verified."],
  } as const;
  const [heading, detail] = content[state];
  return (
    <section
      className={`session-access session-access-${state}`}
      role={state === "recovering" || state === "unauthenticated" || state === "expired" ? "status" : "alert"}
      aria-live={state === "recovering" ? "polite" : "assertive"}
      aria-labelledby="session-access-heading"
    >
      <h1 id="session-access-heading" tabIndex={-1}>
        {heading}
      </h1>
      <p>{detail}</p>
    </section>
  );
}

/** Gate protected descendants on a current server-verified scope generation. */
export function SessionAccessBoundary({
  authState,
  principal,
  error,
  lifecycle: suppliedLifecycle,
  children,
}: SessionAccessBoundaryProps): ReactNode {
  const ownedLifecycle = useMemo(
    () => suppliedLifecycle ?? new SessionAccessLifecycle(),
    [suppliedLifecycle],
  );
  const ownsLifecycle = suppliedLifecycle === undefined;
  const desired = useMemo(
    () => deriveSessionAccess(authState, principal),
    [authState, principal],
  );
  const desiredKey = desired.scope ? sessionScopeKey(desired.scope) : null;
  const [ready, setReady] = useState<SessionScopeSnapshot | null>(null);
  const [transitionFailed, setTransitionFailed] = useState(false);
  const previousDesiredKey = useRef<string | null>(null);
  const pendingDisposal = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let active = true;
    setTransitionFailed(false);
    void ownedLifecycle
      .transition(desired.scope)
      .then((snapshot) => {
        if (active && desired.scope !== null) setReady(snapshot);
      })
      .catch(() => {
        if (active) {
          setReady(null);
          setTransitionFailed(true);
        }
      });
    previousDesiredKey.current = desiredKey;
    return () => {
      active = false;
    };
  }, [desired, desiredKey, ownedLifecycle]);

  useEffect(() => {
    if (pendingDisposal.current !== null) {
      clearTimeout(pendingDisposal.current);
      pendingDisposal.current = null;
    }
    if (!ownsLifecycle) return;
    return () => {
      pendingDisposal.current = setTimeout(() => {
        pendingDisposal.current = null;
        void ownedLifecycle.dispose();
      }, 0);
    };
  }, [ownedLifecycle, ownsLifecycle]);

  useEffect(() => {
    const heading = document.getElementById("session-access-heading");
    if (heading instanceof HTMLElement) heading.focus();
  }, [authState, transitionFailed]);

  if (transitionFailed) return <AccessStatus state="unavailable" />;
  if (desired.state !== "authorized" || desired.scope === null) {
    void error;
    return <AccessStatus state={desired.state} />;
  }
  if (
    ready?.scope === null ||
    ready?.scope === undefined ||
    sessionScopeKey(ready.scope) !== desiredKey ||
    ready.signal.aborted ||
    previousDesiredKey.current !== desiredKey
  ) {
    return <AccessStatus state="recovering" />;
  }

  const contextValue: SessionScopeView = {
    generation: ready.generation,
    scope: ready.scope,
    signal: ready.signal,
    isCurrent: (generation) => ownedLifecycle.isCurrent(generation),
    registerProjection: (key, clear) =>
      ownedLifecycle.registerProjection(key, clear),
  };
  return (
    <SessionScopeContext.Provider value={contextValue}>
      <AppShell>{children}</AppShell>
    </SessionScopeContext.Provider>
  );
}

/** Read the current verified scope; missing boundary wiring fails closed. */
export function useSessionScope(): SessionScopeView {
  const value = useContext(SessionScopeContext);
  if (value === null) {
    throw new Error("useSessionScope must be used within SessionAccessBoundary");
  }
  return value;
}
