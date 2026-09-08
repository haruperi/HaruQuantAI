"use client";

import { useEffect, type PropsWithChildren, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/workflow";
import { useAuth } from "@/context";

export interface ProtectedLayoutProps extends PropsWithChildren {}

export function ProtectedLayout({ children }: ProtectedLayoutProps): ReactNode {
  const { state, scopeGeneration } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (state === "unauthenticated" || state === "expired") {
      router.replace(state === "expired" ? "/login?reason=expired" : "/login");
    }
  }, [state, router]);

  if (state === "loading") {
    return <div className="protected-loading" role="status" aria-live="polite">Recovering session…</div>;
  }
  if (state === "unauthenticated" || state === "expired") {
    return <div className="protected-redirecting" role="status">{state === "expired" ? "Session expired. Redirecting to sign in…" : "Redirecting to sign in…"}</div>;
  }
  if (state === "unauthorized") {
    return <section role="alert" aria-labelledby="access-denied-title"><h1 id="access-denied-title">Access denied</h1><p>Your current verified session does not authorize this workspace.</p></section>;
  }
  if (state === "unavailable") {
    return <section role="alert" aria-labelledby="access-unavailable-title"><h1 id="access-unavailable-title">Session verification unavailable</h1><p>Protected workspace content remains hidden until current access can be verified.</p></section>;
  }
  return <AppShell key={scopeGeneration}>{children}</AppShell>;
}
