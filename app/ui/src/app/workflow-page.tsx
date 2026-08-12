/**
 * Workflow page (FR-UI-021).
 *
 * Composes the protected workspace exclusively from public clients, context,
 * and workflow components. This is the root route's framework entry: it wraps
 * the widget workspace (`App`) in `ProtectedLayout`, which enforces the
 * authenticated session and composes `AppShell`.
 */

"use client";

import type { ReactNode } from "react";

import App from "../App";
import { ProtectedLayout } from "./protected-layout";

/** Props accepted by `WorkflowPage`. */
export interface WorkflowPageProps {
  /** Optional children override; defaults to the widget workspace. */
  children?: ReactNode;
}

/** Root workflow page composing the protected widget workspace. */
export function WorkflowPage({ children }: WorkflowPageProps = {}): ReactNode {
  return <ProtectedLayout>{children ?? <App />}</ProtectedLayout>;
}
