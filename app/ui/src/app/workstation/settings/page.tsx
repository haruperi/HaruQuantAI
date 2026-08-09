"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * `/workstation/settings` legacy redirect.
 *
 * System Settings is now an in-place modal popup opened from the sidebar
 * (`SystemSettingsModal`), matching the CME-style cookie-settings interaction
 * model. This route is retained only to redirect stale deep-links back to the
 * workstation root so no bookmark lands on an orphan page.
 */
export default function SettingsPage(): React.JSX.Element {
  const router = useRouter();
  useEffect(() => {
    router.replace("/");
  }, [router]);
  return (
    <main role="status" aria-live="polite" style={{ padding: 24 }}>
      <p>Redirecting to the workstation…</p>
    </main>
  );
}
