/** Bounded safe projection helpers for FEAT-UI-DEBUG_CONSOLE. */

export interface DiagnosticLogEntry {
  readonly sequence: number;
  readonly timestamp: string;
  readonly owner: string;
  readonly severity: string;
  readonly code: string;
  readonly message: string;
  readonly sampled: boolean;
}

export interface DiagnosticWindow {
  readonly entries: readonly DiagnosticLogEntry[];
  readonly truncated: boolean;
  readonly stale: boolean;
}

/** Keep a bounded newest window without changing retained owner evidence. */
export function boundedDiagnosticWindow(
  entries: readonly DiagnosticLogEntry[],
  maxEntries = 500,
): DiagnosticWindow {
  if (maxEntries < 1) throw new Error("diagnostic window bound must be positive");
  const truncated = entries.length > maxEntries;
  return {
    entries: entries.slice(Math.max(0, entries.length - maxEntries)),
    truncated,
    stale: false,
  };
}

/** Treat diagnostic payload as inert text; React escapes this string on render. */
export function diagnosticText(value: unknown, maxChars = 4096): string {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}…[TRUNCATED]`;
}
