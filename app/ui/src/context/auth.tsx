/**
 * Authenticated UI session context (FR-UI-006).
 *
 * Recovers the approved browser session on mount, protects layouts, and
 * clears/redirects on expiration without ever exposing credentials. The
 * session token never touches JavaScript: it lives in the HttpOnly
 * `hq_session` cookie set by the backend. Only non-secret identity metadata
 * (`user_id`, `username`, `expires_at`) is mirrored into `sessionStorage` so
 * the workspace can display the signed-in principal after a page reload.
 *
 * Session validity is probed through `GET /api/v1/health/readiness`, which is
 * auth-gated: a 200 confirms the cookie session is still valid; a 401 means
 * the session is expired/revoked and the user must re-authenticate. The
 * readiness probe returns dependency health, not identity, so identity is
 * recovered from the locally stored metadata written at login/register time.
 *
 * Browser context never confers authority: every subsequent client call
 * re-presents the HttpOnly cookie and the backend re-validates it.
 */

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
  type ReactNode,
} from "react";

import { ApiClientError, apiClients } from "@/clients";
import { useWorkspaceStore } from "@/features/workspaces";

/** sessionStorage key for the non-secret identity metadata. */
const IDENTITY_STORAGE_KEY = "hq:identity";

/** Authenticated principal metadata (non-secret; mirrors login/register body). */
export interface AuthPrincipal {
  readonly user_id: string;
  readonly username: string;
  readonly expires_at: string;
  /** API-authoritative environment; absent until a route returns it. See FR-UI-017. */
  readonly runtime_profile?: string;
}

/** Authentication state machine. */
export type AuthState = "loading" | "authenticated" | "unauthenticated";

/** Shape of the value exposed by the auth context. */
export interface AuthContextValue {
  readonly state: AuthState;
  readonly principal: AuthPrincipal | null;
  readonly error: string | null;
  readonly login: (
    username: string,
    password: string
  ) => Promise<AuthPrincipal>;
  readonly register: (
    username: string,
    password: string
  ) => Promise<AuthPrincipal>;
  readonly logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Persist non-secret identity metadata. */
function writeStoredIdentity(principal: AuthPrincipal): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(
      IDENTITY_STORAGE_KEY,
      JSON.stringify(principal)
    );
  } catch {
    // Storage may be unavailable (private mode, quota); auth still works via
    // the HttpOnly cookie, only the display name is lost on reload.
  }
}

/** Clear the stored identity metadata. */
function clearStoredIdentity(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(IDENTITY_STORAGE_KEY);
  } catch {
    // Best-effort clear.
  }
}

/**
 * Authentication provider.
 *
 * Wrap the protected application root so every descendant can read the
 * session via `useAuth()`. On mount it probes the readiness endpoint to
 * confirm the cookie session is valid; if valid and identity is available,
 * the state becomes `authenticated`, otherwise `unauthenticated`.
 */
export function AuthProvider({ children }: PropsWithChildren): ReactNode {
  const [state, setState] = useState<AuthState>("loading");
  const [principal, setPrincipal] = useState<AuthPrincipal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);

  // Recover the session on mount via the server-authoritative identity route.
  useEffect(() => {
    mounted.current = true;
    let cancelled = false;

    async function recover(): Promise<void> {
      try {
        // `GET /api/v1/auth/me` returns the server-side identity when the
        // cookie session is valid, and a 401 error envelope when not.
        const response = await apiClients.auth.me();
        if (cancelled || !mounted.current) return;
        if (response.status === "error") {
          throw new ApiClientError({
            message: response.error.message,
            status: 401,
            code: response.error.code,
            requestId: response.error.request_id,
            traceId: response.error.trace_id,
            retryable: response.error.retryable,
          });
        }
        // Server-authoritative identity. Mirror it to sessionStorage as a
        // display-name fallback for offline reloads; the cookie is the proof.
        const next: AuthPrincipal = {
          user_id: response.data.user_id,
          username: response.data.username,
          expires_at: response.data.expires_at,
          runtime_profile: response.data.runtime_profile,
        };
        writeStoredIdentity(next);
        setPrincipal(next);
        setState("authenticated");
        useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(next.runtime_profile);
      } catch (cause) {
        if (cancelled || !mounted.current) return;
        // 401 => session expired/revoked. Any other failure is surfaced but
        // defaults to unauthenticated (fail-closed for protected layouts).
        clearStoredIdentity();
        setPrincipal(null);
        setState("unauthenticated");
        useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(undefined);
        if (cause instanceof ApiClientError && cause.code !== "AUTHENTICATION_REQUIRED") {
          setError(cause.message);
        } else {
          setError(null);
        }
      }
    }

    void recover();
    return () => {
      cancelled = true;
      mounted.current = false;
    };
  }, []);

  const login = useCallback(
    async (username: string, password: string): Promise<AuthPrincipal> => {
      const response = await apiClients.auth.login({ username, password });
      if (response.status !== "success" || !response.data) {
        throw new ApiClientError({
          message: response.error?.message ?? "login failed",
          status: 0,
          code: response.error?.code ?? "AUTHENTICATION_REQUIRED",
        });
      }
      const next: AuthPrincipal = {
        user_id: response.data.user_id,
        username: response.data.username,
        expires_at: response.data.expires_at,
        runtime_profile: response.data.runtime_profile,
      };
      writeStoredIdentity(next);
      setPrincipal(next);
      setState("authenticated");
      setError(null);
      useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(next.runtime_profile);
      return next;
    },
    []
  );

  const register = useCallback(
    async (username: string, password: string): Promise<AuthPrincipal> => {
      const response = await apiClients.auth.register({ username, password });
      if (response.status !== "success" || !response.data) {
        throw new ApiClientError({
          message: response.error?.message ?? "registration failed",
          status: 0,
          code: response.error?.code ?? "AUTHENTICATION_REQUIRED",
        });
      }
      const next: AuthPrincipal = {
        user_id: response.data.user_id,
        username: response.data.username,
        expires_at: response.data.expires_at,
        runtime_profile: response.data.runtime_profile,
      };
      writeStoredIdentity(next);
      setPrincipal(next);
      setState("authenticated");
      setError(null);
      useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(next.runtime_profile);
      return next;
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClients.auth.logout();
    } finally {
      // Whether or not the server confirmed, clear local identity and mark
      // unauthenticated so protected layouts redirect.
      clearStoredIdentity();
      setPrincipal(null);
      setState("unauthenticated");
      setError(null);
      useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(undefined);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ state, principal, error, login, register, logout }),
    [state, principal, error, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Read the authenticated session.
 *
 * Raises if called outside an `AuthProvider` so missing wiring fails loudly
 * rather than silently rendering an unauthenticated tree.
 */
export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return value;
}
