/**
 * Shared Analytics evidence-state presentation (FEAT-UI-32).
 *
 * Every Analytics surface renders owner-supplied evidence only. This module
 * holds the one place that decides how loading, error, unavailable, and
 * truncated evidence is shown, so no panel invents a zero, a percentage, or a
 * conclusion the Analytics report did not supply.
 */

"use client";

import type { ReactNode } from "react";

import type { AnalyticsWorkbenchSection } from "@/clients";

/** Exact text rendered when the owner reports no authoritative evidence. */
export const EVIDENCE_UNAVAILABLE_TEXT =
  "Not available in the current authoritative V2 metric catalogue.";

/** Exact reason string the Analytics owner emits for missing evidence. */
export const AUTHORITATIVE_EVIDENCE_UNAVAILABLE =
  "authoritative_evidence_unavailable";

/** Render one value exactly as the owner supplied it, or mark it unavailable. */
export function EvidenceValue({
  value,
  unit,
}: {
  value: unknown;
  unit?: string | null;
}): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <span className="analytics-evidence__unavailable">Unavailable</span>;
  }
  return (
    <span className="analytics-evidence__value">
      {String(value)}
      {unit ? <span className="analytics-evidence__unit"> {unit}</span> : null}
    </span>
  );
}

/** Props accepted by `AnalyticsEvidenceState`. */
export interface AnalyticsEvidenceStateProps {
  loading?: boolean;
  error?: string | null;
  section?: AnalyticsWorkbenchSection | null;
  label: string;
  children?: ReactNode;
}

/**
 * Wrap one Analytics section and render its authoritative state.
 *
 * Children render only when the section is present and completed. An
 * unavailable section renders the owner's exact reason; it never falls back to
 * an empty table that reads as a zero result.
 */
export function AnalyticsEvidenceState({
  loading = false,
  error = null,
  section = null,
  label,
  children,
}: AnalyticsEvidenceStateProps): ReactNode {
  if (loading) {
    return (
      <p className="analytics-evidence__loading" role="status">
        Loading {label}…
      </p>
    );
  }

  if (error) {
    return (
      <p className="analytics-evidence__error" role="alert">
        {label} could not be read: {error}
      </p>
    );
  }

  if (!section) {
    return (
      <p className="analytics-evidence__unavailable">
        {label}: {EVIDENCE_UNAVAILABLE_TEXT}
      </p>
    );
  }

  if (section.status === "unavailable") {
    return (
      <p className="analytics-evidence__unavailable">
        {label}: {section.reason ?? EVIDENCE_UNAVAILABLE_TEXT}
      </p>
    );
  }

  return (
    <div className="analytics-evidence">
      <p className="analytics-evidence__meta">
        Source: {section.source_context} · Samples: {section.sample_count}
        {section.unit ? ` · Unit: ${section.unit}` : ""}
        {section.truncated
          ? ` · Truncated to ${section.items.length} of ${section.total_count}`
          : ""}
      </p>
      {children}
    </div>
  );
}
