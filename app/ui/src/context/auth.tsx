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
import { currentSessionScopeGeneration, rotateSessionScope } from "@/clients/session-scope";
import { useWorkspaceStore } from "@/widgets/workspaces";

const IDENTITY_STORAGE_KEY = "hq:identity";

export interface AuthPrincipal {
  readonly user_id: string;
  readonly account_id: string;
  readonly workspace_id: string;
  readonly username: string;
  readonly expires_at: string;
  readonly authentication_audit_ref: string;
  readonly runtime_profile?: string;
}

export type AuthState =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "unauthorized"
  | "expired"
  | "unavailable";

export interface AuthContextValue {
  readonly state: AuthState;
  readonly principal: AuthPrincipal | null;
  readonly error: string | null;
  readonly scopeGeneration: number;
  readonly login: (username: string, password: string) => Promise<AuthPrincipal>;
  readonly register: (username: string, password: string) => Promise<AuthPrincipal>;
  readonly logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredIdentity(): AuthPrincipal | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(IDENTITY_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthPrincipal) : null;
  } catch {
    return null;
  }
}

function writeStoredIdentity(principal: AuthPrincipal): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(IDENTITY_STORAGE_KEY, JSON.stringify(principal));
  } catch {
    // Display metadata is optional; the HttpOnly cookie remains authoritative.
  }
}

function clearStoredIdentity(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(IDENTITY_STORAGE_KEY);
  } catch {
    // Best-effort cleanup.
  }
}

function principalFromResponse(data: {
  user_id: string;
  account_id: string;
  workspace_id: string;
  username: string;
  expires_at: string;
  authentication_audit_ref: string;
  runtime_profile?: string;
}): AuthPrincipal {
  return { ...data };
}

function classifyAuthFailure(cause: unknown, hadStoredIdentity: boolean): AuthState {
  if (!(cause instanceof ApiClientError)) return "unavailable";
  if (cause.code === "AUTHENTICATION_REQUIRED") {
    return hadStoredIdentity ? "expired" : "unauthenticated";
  }
  if (cause.status === 403 || cause.code === "PERMISSION_DENIED" || cause.code === "AUTHORIZATION_DENIED") {
    return "unauthorized";
  }
  return "unavailable";
}

export function AuthProvider({ children }: PropsWithChildren): ReactNode {
  const [state, setState] = useState<AuthState>("loading");
  const [principal, setPrincipal] = useState<AuthPrincipal | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scopeGeneration, setScopeGeneration] = useState(currentSessionScopeGeneration());
  const mounted = useRef(true);

  const invalidateScope = useCallback((reason: string): void => {
    setScopeGeneration(rotateSessionScope(reason));
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(undefined);
  }, []);

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    async function recover(): Promise<void> {
      const stored = readStoredIdentity();
      try {
        const response = await apiClients.auth.me();
        if (cancelled || !mounted.current) return;
        if (response.status === "error") {
          throw new ApiClientError({
            message: response.error.message,
            status: response.error.code === "AUTHENTICATION_REQUIRED" ? 401 : 0,
            code: response.error.code,
            requestId: response.error.request_id,
            traceId: response.error.trace_id,
            retryable: response.error.retryable,
          });
        }
        const next = principalFromResponse(response.data);
        if (stored && (stored.account_id !== next.account_id || stored.workspace_id !== next.workspace_id || stored.user_id !== next.user_id)) {
          invalidateScope("principal-changed-during-recovery");
        }
        writeStoredIdentity(next);
        setPrincipal(next);
        setState("authenticated");
        setError(null);
        useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(next.runtime_profile);
      } catch (cause) {
        if (cancelled || !mounted.current) return;
        invalidateScope("session-recovery-failed");
        clearStoredIdentity();
        setPrincipal(null);
        setState(classifyAuthFailure(cause, stored !== null));
        setError(cause instanceof ApiClientError && cause.code !== "AUTHENTICATION_REQUIRED" ? cause.message : null);
      }
    }
    void recover();
    return () => {
      cancelled = true;
      mounted.current = false;
    };
  }, [invalidateScope]);

  const applyAuthenticatedPrincipal = useCallback((next: AuthPrincipal): AuthPrincipal => {
    const previous = principal;
    if (previous && (previous.account_id !== next.account_id || previous.workspace_id !== next.workspace_id || previous.user_id !== next.user_id)) {
      invalidateScope("principal-changed");
    }
    writeStoredIdentity(next);
    setPrincipal(next);
    setState("authenticated");
    setError(null);
    useWorkspaceStore.getState().setAccountModeFromRuntimeProfile(next.runtime_profile);
    return next;
  }, [invalidateScope, principal]);

  const login = useCallback(async (username: string, password: string): Promise<AuthPrincipal> => {
    const response = await apiClients.auth.login({ username, password });
    if (response.status !== "success" || !response.data) {
      throw new ApiClientError({ message: response.error?.message ?? "login failed", status: 0, code: response.error?.code ?? "AUTHENTICATION_REQUIRED" });
    }
    return applyAuthenticatedPrincipal(principalFromResponse(response.data));
  }, [applyAuthenticatedPrincipal]);

  const register = useCallback(async (username: string, password: string): Promise<AuthPrincipal> => {
    const response = await apiClients.auth.register({ username, password });
    if (response.status !== "success" || !response.data) {
      throw new ApiClientError({ message: response.error?.message ?? "registration failed", status: 0, code: response.error?.code ?? "AUTHENTICATION_REQUIRED" });
    }
    return applyAuthenticatedPrincipal(principalFromResponse(response.data));
  }, [applyAuthenticatedPrincipal]);

  const logout = useCallback(async (): Promise<void> => {
    invalidateScope("logout");
    clearStoredIdentity();
    setPrincipal(null);
    setState("unauthenticated");
    setError(null);
    try {
      await apiClients.auth.logout();
    } catch {
      // Local scope is already invalidated; server failures cannot preserve UI authority.
    }
  }, [invalidateScope]);

  const value = useMemo<AuthContextValue>(
    () => ({ state, principal, error, scopeGeneration, login, register, logout }),
    [state, principal, error, scopeGeneration, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) throw new Error("useAuth must be used within an AuthProvider");
  return value;
}
