/** Bounded presentation model for FEAT-UI-RUN_MONITOR. */

export interface RunMonitorRow {
  readonly jobId: string;
  readonly infrastructureState: string;
  readonly domainOutcome: string;
  readonly desiredControl: string;
  readonly acknowledgedControl: string;
  readonly workerActive: boolean;
  readonly completedUnits: number | null;
  readonly totalUnits: number | null;
  readonly exactProgress: boolean;
  readonly attemptId: string;
  readonly fence: number;
  readonly stale: boolean;
}

export interface ProgressLabel {
  readonly text: string;
  readonly determinate: boolean;
}

export function progressLabel(row: RunMonitorRow): ProgressLabel {
  if (row.completedUnits === null || row.totalUnits === null) {
    return { text: "Progress total unknown", determinate: false };
  }
  if (row.totalUnits <= 0) {
    return { text: "Progress total unavailable", determinate: false };
  }
  const qualifier = row.exactProgress ? "exact" : "sampled";
  return {
    text: `${row.completedUnits}/${row.totalUnits} (${qualifier})`,
    determinate: true,
  };
}

export function outcomeLabel(row: RunMonitorRow): string {
  if (row.domainOutcome === "REFUSED") return "Refused by domain policy";
  if (row.domainOutcome === "PARTIAL") return "Partial domain result";
  if (row.domainOutcome === "FAILED") return "Domain failure";
  if (row.domainOutcome === "SUCCESS") return "Domain success";
  return "Domain outcome unknown";
}

export function controlLabel(row: RunMonitorRow): string {
  if (row.desiredControl !== row.acknowledgedControl) {
    return `${row.desiredControl} requested; awaiting acknowledgement`;
  }
  return row.acknowledgedControl === "NONE"
    ? "No pending control"
    : `${row.acknowledgedControl} acknowledged`;
}

export function boundedRows(
  rows: readonly RunMonitorRow[],
  limit = 200,
): readonly RunMonitorRow[] {
  if (limit < 1) throw new Error("run-monitor row limit must be positive");
  return rows.slice(0, limit);
}
