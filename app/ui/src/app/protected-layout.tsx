/**
 * Protected layout (FR-UI-020).
 *
 * Gates the widget workspace on an authenticated session. When the session is
 * loading, renders a spinner. When unauthenticated, redirects to `/login`
 * (the access gate). When authenticated, composes `AppShell` (the error
 * boundary + stale-state surface from §4.11) around the children.
 *
 * In the widget architecture, all internal workflow widgets are children of
 * this layout, so FR-054's protection of dashboard/settings/strategies/
 * operator/Edge Lab is enforced at this single composition point.
 */

"use client";

import { useEffect, type PropsWithChildren, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/workflow";
import { useAuth } from "@/context";

/** Props accepted by `ProtectedLayout`. */
export interface ProtectedLayoutProps extends PropsWithChildren {}

/** Protected composition point for the widget workspace. */
export function ProtectedLayout({ children }: ProtectedLayoutProps): ReactNode {
  const { state } = useAuth();
  const router = useRouter();

  // Redirect unauthenticated visitors to the access gate. Using an effect
  // (rather than conditional render) avoids a flash of content before the
  // navigation commits.
  useEffect(() => {
    if (state === "unauthenticated") {
      router.replace("/login");
    }
  }, [state, router]);

  if (state === "loading") {
    return (
      <div className="protected-loading" role="status" aria-live="polite">
        <span>Recovering session…</span>
      </div>
    );
  }

  if (state === "unauthenticated") {
    // Brief placeholder while the redirect effect fires.
    return (
      <div className="protected-redirecting" role="status">
        <span>Redirecting to sign in…</span>
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
