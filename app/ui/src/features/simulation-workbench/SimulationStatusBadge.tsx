/**
 * Simulation status and evidence class badges (FEAT-UI-31).
 *
 * Renders high-contrast, accessible visual indicators for engine lifecycle
 * status, evidence classification, archive state, and state freshness.
 */

import type { ReactNode } from "react";
import {
  Activity,
  AlertCircle,
  Archive,
  Ban,
  CheckCircle2,
  Clock,
  Layers,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";

import type {
  ArchiveState,
  CatalogueStatus,
  EvidenceClass,
  StateFreshness,
} from "@/clients";

export interface SimulationStatusBadgeProps {
  status?: CatalogueStatus | string | null;
  evidenceClass?: EvidenceClass | string | null;
  archiveState?: ArchiveState | string | null;
  stateFreshness?: StateFreshness | string | null;
  className?: string;
}

/** Status badge rendering. */
export function SimulationStatusBadge({
  status,
  evidenceClass,
  archiveState,
  stateFreshness,
  className = "",
}: SimulationStatusBadgeProps): ReactNode {
  return (
    <div
      className={`simulation-badge-group inline-flex items-center gap-1.5 flex-wrap ${className}`}
      role="group"
      aria-label="Simulation state indicators"
    >
      {status ? <StatusPill status={status} /> : null}
      {evidenceClass ? <EvidenceClassPill evidenceClass={evidenceClass} /> : null}
      {archiveState === "archived" ? <ArchivePill /> : null}
      {stateFreshness && stateFreshness !== "fresh" ? (
        <FreshnessPill freshness={stateFreshness} />
      ) : null}
    </div>
  );
}

function StatusPill({ status }: { status: string }): ReactNode {
  switch (status.toLowerCase()) {
    case "running":
      return (
        <span
          className="simulation-badge simulation-badge--running"
          role="status"
          aria-label="Status: Running"
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          Running
        </span>
      );
    case "completed":
      return (
        <span
          className="simulation-badge simulation-badge--completed"
          role="status"
          aria-label="Status: Completed"
        >
          <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
          Completed
        </span>
      );
    case "failed":
      return (
        <span
          className="simulation-badge simulation-badge--failed"
          role="status"
          aria-label="Status: Failed"
        >
          <XCircle className="w-3.5 h-3.5" aria-hidden="true" />
          Failed
        </span>
      );
    case "cancelled":
      return (
        <span
          className="simulation-badge simulation-badge--cancelled"
          role="status"
          aria-label="Status: Cancelled"
        >
          <Ban className="w-3.5 h-3.5" aria-hidden="true" />
          Cancelled
        </span>
      );
    case "pending":
    default:
      return (
        <span
          className="simulation-badge simulation-badge--pending"
          role="status"
          aria-label={`Status: ${status}`}
        >
          <Clock className="w-3.5 h-3.5" aria-hidden="true" />
          {status}
        </span>
      );
  }
}

function EvidenceClassPill({ evidenceClass }: { evidenceClass: string }): ReactNode {
  const norm = evidenceClass.toLowerCase();
  switch (norm) {
    case "canonical":
      return (
        <span
          className="simulation-badge simulation-badge--evidence-canonical"
          aria-label="Evidence: Canonical"
          title="Authoritative reproducible simulation record"
        >
          <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
          Canonical
        </span>
      );
    case "batch_member":
      return (
        <span
          className="simulation-badge simulation-badge--evidence-batch_member"
          aria-label="Evidence: Batch Member"
          title="Member of parameter grid or matrix batch"
        >
          <Layers className="w-3.5 h-3.5" aria-hidden="true" />
          Batch Item
        </span>
      );
    case "practice":
      return (
        <span
          className="simulation-badge simulation-badge--evidence-practice"
          aria-label="Evidence: Practice"
          title="Interactive live practice simulation"
        >
          <Activity className="w-3.5 h-3.5" aria-hidden="true" />
          Practice
        </span>
      );
    case "advisory":
      return (
        <span
          className="simulation-badge simulation-badge--evidence-advisory"
          aria-label="Evidence: Advisory"
          title="What-if exploratory branch (advisory only)"
        >
          <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />
          Advisory
        </span>
      );
    case "reproduced":
      return (
        <span
          className="simulation-badge simulation-badge--evidence-reproduced"
          aria-label="Evidence: Reproduced"
          title="Re-executed from finalized advisory journal"
        >
          <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
          Reproduced
        </span>
      );
    default:
      return (
        <span
          className="simulation-badge"
          aria-label={`Evidence: ${evidenceClass}`}
        >
          {evidenceClass}
        </span>
      );
  }
}

function ArchivePill(): ReactNode {
  return (
    <span
      className="simulation-badge simulation-badge--archived"
      aria-label="Archived"
      title="Run is marked archived"
    >
      <Archive className="w-3.5 h-3.5" aria-hidden="true" />
      Archived
    </span>
  );
}

function FreshnessPill({ freshness }: { freshness: string }): ReactNode {
  return (
    <span
      className="simulation-badge simulation-badge--pending"
      aria-label={`State Freshness: ${freshness}`}
    >
      <ShieldAlert className="w-3.5 h-3.5" aria-hidden="true" />
      {freshness.replace(/_/g, " ")}
    </span>
  );
}
