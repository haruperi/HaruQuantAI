/** Protected application composition for FEAT-UI-SESSION_ACCESS. */

"use client";

import { useEffect, type PropsWithChildren, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context";

import { SessionAccessBoundary } from "./session-access";

/** Props accepted by `ProtectedLayout`. */
export interface ProtectedLayoutProps extends PropsWithChildren {}

/** Gate the existing application shell on a current server-verified scope. */
export function ProtectedLayout({ children }: ProtectedLayoutProps): ReactNode {
  const { state, principal, error } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (state === "unauthenticated" || state === "expired") {
      router.replace("/login");
    }
  }, [state, router]);

  return (
    <SessionAccessBoundary
      authState={state}
      principal={principal}
      error={error}
    >
      {children}
    </SessionAccessBoundary>
  );
}
