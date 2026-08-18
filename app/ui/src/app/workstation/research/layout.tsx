/**
 * Research workbench layout (FEAT-UI-28).
 *
 * Every research route is protected: the workbench is only reachable with an
 * authenticated session, enforced at this single composition point.
 */

"use client";

import type { ReactNode } from "react";

import { ProtectedLayout } from "@/app/protected-layout";

export default function ResearchLayout({
  children,
}: {
  children: ReactNode;
}): ReactNode {
  return (
    <ProtectedLayout>
      <div className="research-root">{children}</div>
    </ProtectedLayout>
  );
}
